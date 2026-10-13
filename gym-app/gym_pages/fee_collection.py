# fee_collection.py - ULTIMATE PROFESSIONAL VERSION
# WITH ENHANCED OCR, PARTIAL PAYMENT, PDF/EXCEL EXPORT, MEMBER HISTORY, ADMIN PANEL WITH PHOTO
# FIXED: Admin panel shows ALL records (not just current month)
# FIXED: Today's collection uses created_at (collection date) not payment_date
# FIXED: Plain text receipt (NO HTML/CSS - works everywhere)
# FIXED: Auto-fill fee amount, period start, period end when member selected
# FIXED: Dynamic keys for number_input so values update properly
# NEW: Search in History tab
# FIXED: Payment Date = Today (LOCKED - cannot change)
# FIXED: Period Start = Today
# FIXED: Period End = Period Start + 30 days
# FIXED: Admin Panel shows ALL months entries
# FIXED: Fee Status shows ONLY Active members

import streamlit as st
import pandas as pd
import io
import os
import uuid
from datetime import date, timedelta, datetime
import database as db
import base64
import object_store
import plotly.graph_objects as go
import plotly.express as px
import re
import numpy as np
import json
import sqlite3


# ═══════════════════════════════════════════════════════════
# 🚀 CACHED DB HELPERS — speed boost
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def _cached_members(gym_id):
    """Cached members list — 60 sec TTL"""
    if gym_id is None:
        all_m = []
        for g in db.get_all_gyms():
            all_m.extend(db.get_members(gym_id=g.id))
        return all_m
    return db.get_members(gym_id=gym_id)

@st.cache_data(ttl=60, show_spinner=False)
def _cached_fee_records(gym_id, date_from=None, date_to=None):
    """Cached fee records — 60 sec TTL"""
    df = str(date_from) if date_from else None
    dt = str(date_to) if date_to else None
    return db.get_fee_records(gym_id=gym_id, date_from=df, date_to=dt)

@st.cache_data(ttl=60, show_spinner=False)
def _cached_all_fee_records(gym_id):
    """All fee records — cached"""
    if gym_id is None:
        all_r = []
        for g in db.get_all_gyms():
            all_r.extend(db.get_fee_records(gym_id=g.id))
        return all_r
    return db.get_fee_records(gym_id=gym_id)

@st.cache_data(ttl=60, show_spinner=False)
def _cached_fee_records_by_member(member_id):
    """Fee records for a member"""
    return db.get_fee_records(member_id=member_id)



# ============================================
# PDF EXPORT (ReportLab)
# ============================================

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ============================================
# PIL IMPORT (Image Optimization)
# ============================================

try:
    from PIL import Image, ImageOps, ExifTags, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ============================================
# OCR LAZY LOADING - ONLY LOADS WHEN USED
# ============================================

try:
    import easyocr
    HAS_OCR = True
    OCR_READER = None
except ImportError:
    HAS_OCR = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

def get_ocr_reader():
    """Get or create OCR reader instance - LAZY LOAD (only when called)"""
    global OCR_READER
    if OCR_READER is None and HAS_OCR:
        with st.spinner("🔄 Loading OCR model... (first time only)"):
            OCR_READER = easyocr.Reader(['en'], gpu=False)
    return OCR_READER

# ============================================
# PRINTER UTILITY
# ============================================

from printer_utils import (
    format_receipt, render_print_preview,
    render_print_component
)


# ═══════════════════════════════════════════════════════════
# 🚀 BULK STATUS LOADER
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def _bulk_member_status(gym_id, member_ids_tuple):
    """Load payment status for ALL members in ONE query"""
    if not member_ids_tuple:
        return {}
    
    # Get ALL records once
    if gym_id is None:
        all_records = []
        for g in db.get_all_gyms():
            all_records.extend(db.get_fee_records(gym_id=g.id))
    else:
        all_records = db.get_fee_records(gym_id=gym_id)
    
    # Group by member (latest first)
    member_latest = {}
    for r in all_records:
        mid = r.member_id
        if mid not in member_latest:
            member_latest[mid] = r
        else:
            try:
                if r.payment_date and member_latest[mid].payment_date:
                    if str(r.payment_date) > str(member_latest[mid].payment_date):
                        member_latest[mid] = r
            except Exception:
                pass
    
    today = date.today()
    result = {}
    
    for mid in member_ids_tuple:
        r = member_latest.get(mid)
        if r and r.period_end:
            try:
                pe = pd.to_datetime(r.period_end).date()
                if pe >= today:
                    dl = (pe - today).days
                    if dl <= 7:
                        result[mid] = ("upcoming", f"🟡 {dl}d left", "#F59E0B", "#1E293B")
                    else:
                        result[mid] = ("paid", f"✅ Paid ({dl}d left)", "#10B981", "white")
                else:
                    do = (today - pe).days
                    result[mid] = ("unpaid", f"🔴 Expired ({do}d)", "#EF4444", "white")
            except Exception:
                result[mid] = ("unpaid", "⏳ Pending", "#F59E0B", "#1E293B")
        else:
            result[mid] = ("unpaid", "⏳ Pending", "#F59E0B", "#1E293B")
    
    return result




# ============================================
# IMAGE HELPERS (OPTIMIZED + ORIENTATION FIX)
# ============================================

def fix_image_orientation(img):
    """Fix image orientation using EXIF data"""
    try:
        if hasattr(img, '_getexif'):
            exif = img._getexif()
            if exif:
                orientation = exif.get(274)
                if orientation:
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
    except:
        pass
    
    try:
        img = ImageOps.exif_transpose(img)
    except:
        pass
    
    return img

@st.cache_data(ttl=3600)
def _get_cached_image(photo_path: str, max_size: tuple = (300, 350), quality: int = 60) -> str | None:
    """Cached image with compression AND orientation fix"""
    if not HAS_PIL:
        return None
    
    try:
        img = Image.open(photo_path)
        img = fix_image_orientation(img)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode()
    except Exception as e:
        print(f"Image cache error: {e}")
        return None

def get_photo_b64(photo_field: str, serial_number: str = "", max_size: tuple = (300, 350)) -> str | None:
    """Get member photo from Object Storage with orientation fix"""
    if not photo_field:
        return None
    
    photo_str = str(photo_field).strip()
    if "<div" in photo_str or "style=" in photo_str:
        return None
    
    try:
        b64, mime = object_store.get_photo_b64(photo_str)
        if b64:
            try:
                img_bytes = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_bytes))
                img = fix_image_orientation(img)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                if img.mode not in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=60, optimize=True)
                fixed_b64 = base64.b64encode(output.getvalue()).decode()
                return f"data:image/jpeg;base64,{fixed_b64}"
            except:
                return f"data:image/{mime};base64,{b64}"
    except Exception as e:
        print(f"Object storage error: {e}")
    
    if os.path.exists(photo_str):
        cached = _get_cached_image(photo_str, max_size)
        if cached:
            return f"data:image/jpeg;base64,{cached}"
    
    if serial_number:
        for ext in ['.jpg', '.jpeg', '.png']:
            path = f"member_photos/{serial_number}{ext}"
            if os.path.exists(path):
                cached = _get_cached_image(path, max_size)
                if cached:
                    return f"data:image/jpeg;base64,{cached}"
    
    return None

def show_member_photo(photo_path, serial_number="", width=200, height=250):
    """Display member photo with orientation fix"""
    photo_b64 = get_photo_b64(photo_path, serial_number, max_size=(width, height))
    
    if photo_b64:
        st.markdown(f"""
        <div style="width:{width}px; height:{height}px; border-radius:16px;
                    border:3px solid #7C3AED; overflow:hidden;
                    background:#1E293B; box-shadow:0 4px 20px rgba(124,58,237,0.4);
                    flex-shrink:0;">
            <img src="{photo_b64}" style="width:100%; height:100%;
                                          object-fit:cover; display:block;
                                          image-orientation:from-image;" />
        </div>
        """, unsafe_allow_html=True)
        return True
    else:
        st.markdown(f"""
        <div style="width:{width}px; height:{height}px; border-radius:16px;
                    background:linear-gradient(135deg,#7C3AED,#6D28D9);
                    display:flex; align-items:center; justify-content:center;
                    font-size:{width//2}px; color:white; font-weight:700;
                    border:3px solid #7C3AED33; flex-shrink:0;">
            👤
        </div>
        """, unsafe_allow_html=True)
        return False


# ============================================
# PARTIAL PAYMENT SYSTEM
# ============================================

def get_member_balance(member_id):
    """Get member's remaining balance"""
    try:
        records = db.get_fee_records(member_id=member_id)
        
        total_paid = sum(r.amount for r in records)
        
        member = db.get_member(member_id)
        if member and member.fee_amount:
            total_due = member.fee_amount
            remaining = total_due - total_paid
            return max(0, remaining)
        return 0
    except Exception as e:
        print(f"Balance error: {e}")
        return 0

def get_member_payment_summary(member_id):
    """Get full payment summary for a member"""
    try:
        records = db.get_fee_records(member_id=member_id)
        
        total_paid = sum(r.amount for r in records)
        count = len(records)
        
        member = db.get_member(member_id)
        if member:
            total_due = member.fee_amount or 0
            remaining = max(0, total_due - total_paid)
            return {
                'total_due': total_due,
                'total_paid': total_paid,
                'remaining': remaining,
                'payment_count': count,
                'last_payment': records[0].payment_date if records else None,
                'is_fully_paid': remaining <= 0
            }
        return None
    except Exception as e:
        print(f"Summary error: {e}")
        return None


# ============================================
# PDF REPORT GENERATOR
# ============================================

def generate_pdf_report(records, gym_name="Gym", date_from=None, date_to=None):
    """Generate PDF report for fee collection"""
    if not HAS_REPORTLAB:
        return None
    
    buffer = io.BytesIO()
    
    try:
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#7C3AED'),
            spaceAfter=30
        )
        
        elements.append(Paragraph(f"💰 Fee Collection Report", title_style))
        elements.append(Paragraph(f"<b>Gym:</b> {gym_name}", styles['Normal']))
        if date_from and date_to:
            elements.append(Paragraph(f"<b>Period:</b> {date_from} to {date_to}", styles['Normal']))
        elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        total_amount = sum(r.amount for r in records)
        total_count = len(records)
        unique_members = len(set(r.member_id for r in records))
        avg_amount = total_amount / total_count if total_count > 0 else 0
        
        stats_data = [
            ['Metric', 'Value'],
            ['Total Collection', f'PKR {total_amount:,.2f}'],
            ['Total Transactions', str(total_count)],
            ['Unique Members', str(unique_members)],
            ['Average Payment', f'PKR {avg_amount:,.2f}'],
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1E293B')),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 30))
        
        if records:
            elements.append(Paragraph("<b>Payment Records</b>", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            table_data = [['#', 'Date', 'Member', 'Serial', 'Amount', 'Method', 'Collected By']]
            for i, r in enumerate(records[:100], 1):
                member = db.get_member(r.member_id)
                member_name = member.full_name if member else "Unknown"
                serial = member.serial_number if member else "—"
                
                if r.payment_date:
                    if isinstance(r.payment_date, str):
                        date_str = r.payment_date
                    else:
                        date_str = r.payment_date.strftime('%Y-%m-%d')
                else:
                    date_str = "—"
                
                table_data.append([
                    str(i),
                    date_str,
                    member_name[:20],
                    serial,
                    f'PKR {r.amount:,.2f}',
                    r.payment_method or 'Cash',
                    r.collected_by or '—'
                ])
            
            if len(records) > 100:
                table_data.append(['', '', f'... and {len(records)-100} more records', '', '', '', ''])
            
            record_table = Table(table_data, colWidths=[0.5*inch, 0.8*inch, 1.5*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch])
            record_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#60A5FA')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0F172A')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#1E293B')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0F172A'), colors.HexColor('#1A1A2E')]),
            ]))
            elements.append(record_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"PDF error: {e}")
        return None


# ============================================
# EXCEL EXPORT
# ============================================

def generate_excel_report(records, gym_name="Gym"):
    """Generate Excel report for fee collection"""
    if not records:
        return None
    
    try:
        data = []
        for r in records:
            member = db.get_member(r.member_id)
            
            if r.payment_date:
                if isinstance(r.payment_date, str):
                    date_str = r.payment_date
                else:
                    date_str = r.payment_date.strftime('%Y-%m-%d')
            else:
                date_str = ''
            
            if r.period_start:
                if isinstance(r.period_start, str):
                    period_start_str = r.period_start
                else:
                    period_start_str = r.period_start.strftime('%Y-%m-%d')
            else:
                period_start_str = ''
            
            if r.period_end:
                if isinstance(r.period_end, str):
                    period_end_str = r.period_end
                else:
                    period_end_str = r.period_end.strftime('%Y-%m-%d')
            else:
                period_end_str = ''
            
            data.append({
                'Date': date_str,
                'Member Name': member.full_name if member else 'Unknown',
                'Serial Number': member.serial_number if member else '',
                'Amount (PKR)': r.amount,
                'Payment Method': r.payment_method or 'Cash',
                'Collected By': r.collected_by or '',
                'Notes': r.notes or '',
                'Period Start': period_start_str,
                'Period End': period_end_str,
            })
        
        df = pd.DataFrame(data)
        
        total = df['Amount (PKR)'].sum()
        summary_df = pd.DataFrame([{
            'Date': 'TOTAL',
            'Member Name': '',
            'Serial Number': '',
            'Amount (PKR)': total,
            'Payment Method': '',
            'Collected By': '',
            'Notes': '',
            'Period Start': '',
            'Period End': '',
        }])
        
        df = pd.concat([df, summary_df], ignore_index=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Fee Collection', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Fee Collection']
            
            money_format = workbook.add_format({'num_format': 'PKR #,##0.00'})
            worksheet.set_column('D:D', 15, money_format)
            
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 25)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('E:E', 15)
            worksheet.set_column('F:F', 18)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 15)
            worksheet.set_column('I:I', 15)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        print(f"Excel error: {e}")
        return None


# ============================================
# MEMBER PAYMENT HISTORY VIEW
# ============================================

def render_member_payment_history(member_id, gym_id):
    """Render complete payment history for a member"""
    member = db.get_member(member_id)
    if not member:
        st.error("Member not found!")
        return
    
    records = db.get_fee_records(member_id=member_id)
    
    st.markdown("---")
    st.markdown(f"### 👤 {member.full_name}")
    st.caption(f"🔢 Serial: {member.serial_number} | 📱 Phone: {member.phone or '—'}")
    
    summary = get_member_payment_summary(member_id)
    if summary:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total Due", f"PKR {summary['total_due']:,.2f}")
        with col2:
            st.metric("💳 Total Paid", f"PKR {summary['total_paid']:,.2f}")
        with col3:
            st.metric("📊 Remaining", f"PKR {summary['remaining']:,.2f}", delta="Fully Paid" if summary['is_fully_paid'] else f"Remaining: PKR {summary['remaining']:,.2f}", delta_color="normal")
        with col4:
            st.metric("📋 Payments", str(summary['payment_count']))
    
    st.markdown("---")
    st.markdown("### 📋 Payment History")
    
    if not records:
        st.info("No payment records found for this member.")
        return
    
    history_data = []
    for r in records:
        payment_date = r.payment_date
        if payment_date:
            if isinstance(payment_date, str):
                date_str = payment_date
            else:
                date_str = payment_date.strftime('%Y-%m-%d')
        else:
            date_str = "—"
        
        period_start = r.period_start
        if period_start:
            if isinstance(period_start, str):
                period_start_str = period_start
            else:
                period_start_str = period_start.strftime('%Y-%m-%d')
        else:
            period_start_str = "—"
        
        period_end = r.period_end
        if period_end:
            if isinstance(period_end, str):
                period_end_str = period_end
            else:
                period_end_str = period_end.strftime('%Y-%m-%d')
        else:
            period_end_str = "—"
        
        history_data.append({
            "Date": date_str,
            "Amount": f"PKR {r.amount:,.2f}",
            "Method": r.payment_method or "Cash",
            "Period Start": period_start_str,
            "Period End": period_end_str,
            "Collected By": r.collected_by or "—",
            "Notes": r.notes or "—",
        })
    
    df = pd.DataFrame(history_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if len(records) > 1:
        try:
            chart_data = []
            for r in records:
                if r.payment_date:
                    if isinstance(r.payment_date, str):
                        try:
                            date_val = pd.to_datetime(r.payment_date)
                        except:
                            date_val = None
                    else:
                        date_val = r.payment_date
                    
                    if date_val:
                        chart_data.append({
                            'date': date_val,
                            'amount': r.amount
                        })
            
            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                chart_df = chart_df.dropna(subset=['date'])
                if not chart_df.empty:
                    chart_df['date'] = pd.to_datetime(chart_df['date'])
                    chart_df = chart_df.sort_values('date')
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=chart_df['date'],
                        y=chart_df['amount'],
                        mode='lines+markers',
                        name='Payment History',
                        line=dict(color='#10B981', width=3),
                        marker=dict(size=10, color='#34D399'),
                        fill='tozeroy',
                        fillcolor='rgba(16,185,129,0.15)'
                    ))
                    fig.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=250,
                        margin=dict(l=0, r=0, t=20, b=20),
                        xaxis=dict(gridcolor='#1E293B', title='Date'),
                        yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        except Exception as e:
            print(f"Chart error: {e}")
    
    st.markdown("---")
    st.markdown("### 📥 Export History")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        if st.button("📊 Export as Excel", use_container_width=True):
            excel_data = generate_excel_report(records, member.full_name)
            if excel_data:
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"member_{member.serial_number}_history.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.error("❌ Failed to generate Excel")
    
    with col_exp2:
        if st.button("📄 Export as PDF", use_container_width=True):
            pdf_data = generate_pdf_report(records, member.full_name)
            if pdf_data:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_data,
                    file_name=f"member_{member.serial_number}_history.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.error("❌ Failed to generate PDF")


# ============================================
# OCR FUNCTIONS (Lazy Load)
# ============================================

def preprocess_image_for_ocr(image_bytes):
    """Preprocess image for better OCR - handles handwriting"""
    if not HAS_PIL:
        return image_bytes
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = fix_image_orientation(img)
        img = img.convert('L')
        
        if HAS_PIL:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.5)
        
        img_np = np.array(img)
        
        if HAS_CV2:
            _, img_np = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img_np = cv2.medianBlur(img_np, 3)
        
        img = Image.fromarray(img_np)
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"Preprocess error: {e}")
        return image_bytes


def extract_text_from_image_enhanced(image_bytes):
    """Extract text with multiple strategies - handles handwriting"""
    
    if HAS_OCR and HAS_CV2:
        try:
            processed_bytes = preprocess_image_for_ocr(image_bytes)
            reader = get_ocr_reader()
            if reader:
                temp_path = "temp_ocr_enhanced.jpg"
                with open(temp_path, "wb") as f:
                    f.write(processed_bytes)
                
                result = reader.readtext(temp_path, detail=0, paragraph=True)
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if result:
                    text = " ".join(result)
                    text = re.sub(r'\s+', ' ', text).strip()
                    if len(text) > 5:
                        return text, None
        except Exception as e:
            print(f"EasyOCR error: {e}")
    
    if HAS_OCR:
        try:
            reader = get_ocr_reader()
            if reader:
                temp_path = "temp_ocr_raw.jpg"
                img = Image.open(io.BytesIO(image_bytes))
                img.save(temp_path, "JPEG", quality=90)
                
                result = reader.readtext(temp_path, detail=0, paragraph=True)
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if result:
                    text = " ".join(result)
                    text = re.sub(r'\s+', ' ', text).strip()
                    if len(text) > 5:
                        return text, None
        except Exception as e:
            print(f"EasyOCR raw error: {e}")
    
    return None, "⚠️ Could not read handwriting. Please enter manually below."


def parse_member_info_from_text(text):
    """Parse member information from extracted text"""
    if not text:
        return {}
    
    info = {}
    text = re.sub(r'[^a-zA-Z0-9\s.,\-/]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', text)
    if name_match:
        info['name'] = name_match.group(0).strip()
    else:
        words = text.split()
        non_name_words = ['pkr', 'rs', 'date', 'month', 'year', 'fee', 'amount', 'total', 'paid', 'cash']
        name_words = []
        for w in words:
            w_clean = re.sub(r'[^a-zA-Z]', '', w)
            if len(w_clean) > 2 and w_clean.lower() not in non_name_words:
                name_words.append(w_clean)
        if len(name_words) >= 2:
            info['name'] = " ".join(name_words[:3])
        elif len(name_words) == 1:
            info['name'] = name_words[0]
    
    amount_patterns = [
        r'(?:PKR|Rs\.?)\s*([0-9,]+(?:\.[0-9]{2})?)',
        r'([0-9,]+)\s*(?:PKR|Rs)',
        r'\b([0-9,]+)\s*\/\s*-\s*',
        r'\b([0-9,]+)\s*\.\s*00\b',
    ]
    for pattern in amount_patterns:
        amount_match = re.search(pattern, text, re.IGNORECASE)
        if amount_match:
            try:
                num_str = amount_match.group(1).replace(",", "").strip()
                if num_str:
                    info['amount'] = float(num_str)
                    break
            except:
                pass
    
    if 'amount' not in info:
        amount_match3 = re.search(r'\b([0-9,]{3,6})\b', text)
        if amount_match3:
            try:
                num = float(amount_match3.group(1).replace(",", ""))
                if 100 <= num <= 100000:
                    info['amount'] = num
            except:
                pass
    
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{2}-\d{2}-\d{4})',
        r'(\d{2}\.\d{2}\.\d{4})',
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            info['date'] = date_match.group(0)
            break
    
    serial_match = re.search(r'(PF-[0-9]{5}|[A-Z]{2}-[0-9]{5})', text, re.IGNORECASE)
    if serial_match:
        info['serial'] = serial_match.group(0).upper()
    
    phone_match = re.search(r'(03[0-9]{2}[- ]?[0-9]{7}|03[0-9]{9})', text)
    if phone_match:
        info['phone'] = phone_match.group(0).replace(" ", "").replace("-", "")
    
    return info


def search_member_in_db(search_info):
    """Search for member in database based on extracted info"""
    if not search_info:
        return None, "No search info provided"
    
    results = []
    
    if 'name' in search_info:
        all_members = db.get_members()
        search_name = search_info['name'].lower().strip()
        name_parts = search_name.split()
        
        for m in all_members:
            if m.full_name:
                m_name_lower = m.full_name.lower()
                score = 0
                matched_parts = sum(1 for part in name_parts if part in m_name_lower)
                if len(name_parts) > 0:
                    score += (matched_parts / len(name_parts)) * 60
                if m_name_lower == search_name:
                    score = 100
                elif m_name_lower.startswith(search_name):
                    score += 20
                elif search_name in m_name_lower:
                    score += 10
                
                if score >= 50:
                    results.append({
                        'member': m,
                        'match_type': 'Name',
                        'confidence': min(100, int(score))
                    })
    
    if 'serial' in search_info and len(results) == 0:
        member = db.get_member_by_serial(search_info['serial'])
        if member:
            results.append({
                'member': member,
                'match_type': 'Serial Number',
                'confidence': 100
            })
    
    if 'phone' in search_info and len(results) == 0:
        all_members = db.get_members()
        phone_clean = ''.join(c for c in search_info['phone'] if c.isdigit())
        for m in all_members:
            if m.phone:
                m_phone_clean = ''.join(c for c in m.phone if c.isdigit())
                if phone_clean == m_phone_clean:
                    results.append({
                        'member': m,
                        'match_type': 'Phone',
                        'confidence': 90
                    })
                elif phone_clean in m_phone_clean or m_phone_clean in phone_clean:
                    results.append({
                        'member': m,
                        'match_type': 'Phone (partial)',
                        'confidence': 60
                    })
    
    results.sort(key=lambda x: x['confidence'], reverse=True)
    
    if results:
        return results[0]['member'], results
    
    return None, None


# ============================================
# OCR MEMBER MATCHER TAB
# ============================================

def render_ocr_member_matcher(gym_id, current_user):
    """OCR Member Matcher Tab - Name, Amount, Date Search + Handwriting Support"""
    
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                border:1px solid #A78BFA;border-radius:16px;
                padding:1.2rem 1.5rem;margin-bottom:1rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
            <div>
                <div style="font-size:1.5rem;font-weight:800;color:#A78BFA;">📸 OCR Member Matcher</div>
                <div style="color:#94A3B8;font-size:0.85rem;">
                    Staff register/copy ki photo upload karein → App auto-match karega
                </div>
                <div style="color:#FBBF24;font-size:0.75rem;margin-top:0.3rem;">
                    💡 Handwriting supported! Name, Amount aur Date extract hoga
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not HAS_OCR:
        st.error("""
        ❌ **EasyOCR not installed!**
        
        Please run this command in terminal:
        ```
        pip install easyocr opencv-python-headless
        ```
        """)
        return
    
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return
    
    user = db.get_user_by_username(current_user)
    
    if user and user.role.lower() == "staff" and user.gym_id:
        sel_gid = user.gym_id
        staff_gym = db.get_gym(user.gym_id)
        st.text_input("🏋️ Gym", value=staff_gym.name if staff_gym else "Assigned Gym", disabled=True, key="ocr_gym_display")
    else:
        gym_opts = {g.name: g.id for g in gyms}
        sel_gid = gym_opts[st.selectbox("🏋️ Select Gym", list(gym_opts.keys()), key="ocr_gym")]
    
    st.markdown("---")
    
    st.markdown("### 📤 Upload Register/Copy Photo")
    st.caption("Staff ne jo copy/register par entry likhi hai — uski photo upload karein")
    st.info("💡 **Tips for better OCR:**\n- Clear photo with good lighting\n- Write in capital letters\n- Use dark ink on white paper")
    
    uploaded_file = st.file_uploader(
        "Choose image file",
        type=["jpg", "jpeg", "png", "heic", "heif"],
        help="Clear photo of the register/copy page",
        key="ocr_upload"
    )
    
    if uploaded_file:
        try:
            img = Image.open(uploaded_file)
            img = fix_image_orientation(img)
            st.image(img, caption="Uploaded Image", width=400)
        except Exception as e:
            st.error(f"Error loading image: {e}")
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 Extract & Match", type="primary", use_container_width=True):
                with st.spinner("🔄 Processing image with OCR (this may take a few seconds)..."):
                    uploaded_file.seek(0)
                    extracted_text, error = extract_text_from_image_enhanced(uploaded_file.read())
                    
                    if error:
                        st.warning(error)
                        st.session_state['ocr_extraction_failed'] = True
                    elif extracted_text:
                        st.session_state['ocr_extracted_text'] = extracted_text
                        st.session_state['ocr_parsed_info'] = parse_member_info_from_text(extracted_text)
                        st.session_state['ocr_extraction_failed'] = False
                        st.success("✅ Text extracted successfully!")
                    else:
                        st.warning("⚠️ No text extracted. Try a clearer photo or use manual entry below.")
                        st.session_state['ocr_extraction_failed'] = True
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                for key in ['ocr_extracted_text', 'ocr_parsed_info', 'ocr_search_results', 
                           'ocr_best_match', 'ocr_all_matches', 'ocr_extraction_failed', 'ocr_no_match']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    if st.session_state.get('ocr_extracted_text'):
        st.markdown("### 📝 Extracted Text")
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;
                    padding:0.8rem 1rem;margin-bottom:0.5rem;">
            <div style="color:#94A3B8;font-size:0.8rem;white-space:pre-wrap;">{st.session_state['ocr_extracted_text']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        parsed_info = st.session_state.get('ocr_parsed_info', {})
        
        if parsed_info:
            st.markdown("### 📋 Parsed Information")
            
            cols = st.columns(4)
            info_items = [
                ("👤 Name", parsed_info.get('name', '—')),
                ("💰 Amount", f"PKR {parsed_info.get('amount', 0):,.2f}" if parsed_info.get('amount') else '—'),
                ("📅 Date", parsed_info.get('date', '—')),
                ("🔢 Serial", parsed_info.get('serial', '—')),
            ]
            
            for i, (label, value) in enumerate(info_items):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div style="background:#0F172A;border:1px solid #1E293B;border-radius:8px;
                                padding:0.5rem;text-align:center;">
                        <div style="color:#94A3B8;font-size:0.6rem;text-transform:uppercase;letter-spacing:1px;">{label}</div>
                        <div style="color:#F8FAFC;font-weight:700;font-size:0.9rem;">{value}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 🔍 Search in Database")
            st.caption("App name, amount aur date ke basis par search karega")
            
            if st.button("🔍 Search Member in Database", type="primary", use_container_width=True):
                with st.spinner("Searching database..."):
                    best_match, all_matches = search_member_in_db(parsed_info)
                    
                    if best_match:
                        st.session_state['ocr_best_match'] = best_match
                        st.session_state['ocr_all_matches'] = all_matches
                        st.session_state['ocr_no_match'] = False
                        st.success(f"✅ Found: {best_match.full_name} ({best_match.serial_number})")
                    else:
                        st.warning("❌ No matching member found in database!")
                        st.session_state['ocr_no_match'] = True
                    st.rerun()
        else:
            st.warning("⚠️ No information could be parsed from the extracted text.")
            st.info("💡 Try a clearer photo with better handwriting.")
            
            st.markdown("---")
            st.markdown("### ✍️ Manual Entry (If OCR failed)")
            
            with st.form("manual_member_entry"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    manual_name = st.text_input("👤 Member Name *", placeholder="e.g. Muhammad Ali", key="manual_name")
                    manual_amount = st.number_input("💰 Amount (PKR)", min_value=0.0, value=1000.0, step=100.0, key="manual_amount")
                with col_m2:
                    manual_serial = st.text_input("🔢 Serial Number (optional)", placeholder="e.g. PF-00001", key="manual_serial")
                    manual_date = st.date_input("📅 Date", value=date.today(), key="manual_date")
                
                if st.form_submit_button("🔍 Search with Manual Entry", type="primary", use_container_width=True):
                    if manual_name.strip():
                        manual_info = {
                            'name': manual_name.strip(),
                            'amount': manual_amount if manual_amount > 0 else None,
                            'date': str(manual_date) if manual_date else None,
                            'serial': manual_serial.strip().upper() if manual_serial else None,
                        }
                        st.session_state['ocr_parsed_info'] = manual_info
                        st.session_state['ocr_extracted_text'] = f"Manual entry: {manual_name}"
                        st.rerun()
                    else:
                        st.error("❌ Name is required!")
    
    if st.session_state.get('ocr_no_match'):
        st.markdown("---")
        st.markdown("### ➕ Create New Member")
        st.info("No matching member found. Would you like to create a new member?")
        
        parsed_info = st.session_state.get('ocr_parsed_info', {})
        
        with st.form("create_member_from_ocr"):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                new_name = st.text_input("👤 Full Name *", value=parsed_info.get('name', ''), key="new_ocr_name")
                new_phone = st.text_input("📱 Phone", value=parsed_info.get('phone', ''), key="new_ocr_phone")
            with col_c2:
                new_serial = st.text_input("🔢 Serial Number", placeholder="Auto-generated if empty", key="new_ocr_serial")
                new_amount = st.number_input("💰 Fee Amount (PKR)", min_value=0.0, value=float(parsed_info.get('amount', 1000)), step=100.0, key="new_ocr_amount")
            
            new_expiry = st.date_input("📅 Expiry Date", value=date.today() + timedelta(days=30), key="new_ocr_expiry")
            
            if st.form_submit_button("➕ Create Member", type="primary", use_container_width=True):
                if new_name.strip():
                    if not new_serial.strip():
                        new_serial = f"PF-{str(db.get_next_member_serial()).zfill(5)}"
                    
                    member_id = db.add_member(
                        gym_id=sel_gid,
                        serial_number=new_serial.upper(),
                        full_name=new_name.strip(),
                        phone=new_phone.strip() if new_phone else None,
                        fee_amount=new_amount,
                        expiry_date=str(new_expiry),
                        status="Active"
                    )
                    
                    if member_id:
                        db.log_activity(
                            user=current_user,
                            action="MEMBER_CREATED_FROM_OCR",
                            details=f"Member: {new_name} ({new_serial}) created from OCR match",
                            gym_id=sel_gid
                        )
                        st.success(f"✅ Member created successfully! Serial: {new_serial}")
                        st.balloons()
                        st.session_state['ocr_no_match'] = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to create member")
                else:
                    st.error("❌ Name is required!")
    
    if st.session_state.get('ocr_best_match'):
        best_match = st.session_state['ocr_best_match']
        all_matches = st.session_state.get('ocr_all_matches', [])
        parsed_info = st.session_state.get('ocr_parsed_info', {})
        
        st.markdown("---")
        st.markdown("### ✅ Match Results")
        
        st.markdown(f"""
        <div style="background:#064E3B;border:2px solid #34D399;border-radius:16px;
                    padding:1.2rem;margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                <div>
                    <div style="color:#34D399;font-weight:700;font-size:0.8rem;">🏆 BEST MATCH</div>
                    <div style="color:#F8FAFC;font-size:1.4rem;font-weight:800;">{best_match.full_name}</div>
                    <div style="color:#94A3B8;font-size:0.9rem;">{best_match.serial_number}</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#34D399;font-size:1.5rem;font-weight:900;">✅</div>
                    <div style="color:#94A3B8;font-size:0.8rem;">Match Found</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if all_matches and len(all_matches) > 1:
            st.markdown("### 🔄 Multiple Matches Found")
            st.caption("Multiple members with similar names. Select the correct one:")
            
            match_options = {}
            for i, match in enumerate(all_matches[:5]):
                m = match['member']
                label = f"{m.serial_number} — {m.full_name} — {m.phone or 'No phone'} — {match['confidence']}% match"
                match_options[label] = m.id
            
            selected_label = st.selectbox("Select Member", list(match_options.keys()), key="match_select")
            selected_id = match_options[selected_label]
            
            if selected_id != best_match.id:
                best_match = db.get_member(selected_id)
                st.session_state['ocr_best_match'] = best_match
                st.rerun()
        
        st.markdown("---")
        st.markdown("### ⚡ Actions")
        
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            if st.button("💰 Collect Fee", use_container_width=True):
                st.session_state['collect_fee_member'] = best_match.id
                st.success("✅ Member selected for fee collection!")
                st.rerun()
        
        with col_action2:
            if st.button("📋 View History", use_container_width=True):
                st.session_state['view_member_history'] = best_match.id
                st.rerun()


# ============================================
# MEMBER PAYMENT STATUS HELPER
# ============================================

def get_member_payment_status(member):
    """Check actual fee records, not just expiry date"""
    if not member or not hasattr(member, 'id'):
        return "unpaid", "No data", "#F59E0B", "#1E293B"
    
    try:
        fee_records = db.get_fee_records(member_id=member.id, limit=1)
        
        if fee_records:
            latest_fee = fee_records[0]
            if hasattr(latest_fee, 'period_end') and latest_fee.period_end:
                try:
                    period_end = latest_fee.period_end
                    if isinstance(period_end, str):
                        period_end = pd.to_datetime(period_end).date()
                    else:
                        period_end = period_end.date() if hasattr(period_end, 'date') else period_end
                    
                    today = date.today()
                    
                    if period_end >= today:
                        days_left = (period_end - today).days
                        if days_left <= 7:
                            return "upcoming", f"🟡 Upcoming ({days_left}d left)", "#F59E0B", "#1E293B"
                        else:
                            return "paid", f"✅ Paid ({days_left}d left)", "#10B981", "white"
                    else:
                        days_expired = (today - period_end).days
                        return "unpaid", f"🔴 Unpaid ({days_expired}d ago)", "#EF4444", "white"
                except:
                    pass
        
        if hasattr(member, 'expiry_date') and member.expiry_date:
            try:
                expiry = member.expiry_date
                if isinstance(expiry, str):
                    expiry = pd.to_datetime(expiry).date()
                else:
                    expiry = expiry.date() if hasattr(expiry, 'date') else expiry
                
                today = date.today()
                
                if expiry >= today:
                    days_left = (expiry - today).days
                    if days_left <= 7:
                        return "upcoming", f"🟡 Upcoming ({days_left}d left)", "#F59E0B", "#1E293B"
                    else:
                        return "pending", f"⏳ Pending (No fee record)", "#F59E0B", "#1E293B"
                else:
                    days_expired = (today - expiry).days
                    return "unpaid", f"🔴 Unpaid ({days_expired}d ago)", "#EF4444", "white"
            except:
                pass
        
        return "unpaid", "⏳ Pending", "#F59E0B", "#1E293B"
        
    except Exception:
        return "unpaid", "⚠️ Error", "#EF4444", "white"


# ============================================
# COLLECTION SUMMARY CARDS - FIXED VERSION
# ============================================

def render_collection_summary(sel_gym_id, date_from, date_to, gyms=None):
    """Render collection summary cards at top - FIXED: Uses created_at for today's collection"""
    
    if sel_gym_id is None and gyms:
        all_records = []
        for g in gyms:
            records = db.get_fee_records(gym_id=g.id, date_from=date_from, date_to=date_to)
            all_records.extend(records)
        records = all_records
    else:
        records = db.get_fee_records(gym_id=sel_gym_id, date_from=date_from, date_to=date_to)
    
    total_collected = sum(r.amount for r in records)
    total_members = len(set(r.member_id for r in records))
    avg_payment = total_collected / total_members if total_members > 0 else 0
    
    today = date.today()
    
    # 🔥 FIXED: Today's collection = records where created_at == today
    today_records = []
    for r in records:
        if hasattr(r, 'created_at') and r.created_at:
            try:
                if isinstance(r.created_at, str):
                    created_date = pd.to_datetime(r.created_at).date()
                else:
                    created_date = r.created_at.date() if hasattr(r.created_at, 'date') else r.created_at
                if created_date == today:
                    today_records.append(r)
                    continue
            except:
                pass
        
        # Fallback: agar created_at nahi hai toh payment_date use karein
        if r.payment_date:
            if isinstance(r.payment_date, str):
                try:
                    r_date = pd.to_datetime(r.payment_date).date()
                except:
                    r_date = None
            else:
                r_date = r.payment_date.date() if hasattr(r.payment_date, 'date') else r.payment_date
            
            if r_date == today:
                today_records.append(r)
    
    # 🔥 If no records found in current date range, fetch today's records separately
    if not today_records:
        try:
            if sel_gym_id is None and gyms:
                for g in gyms:
                    recs = db.get_fee_records(gym_id=g.id, date_from=today, date_to=today)
                    for r in recs:
                        if hasattr(r, 'created_at') and r.created_at:
                            try:
                                if isinstance(r.created_at, str):
                                    created_date = pd.to_datetime(r.created_at).date()
                                else:
                                    created_date = r.created_at.date() if hasattr(r.created_at, 'date') else r.created_at
                                if created_date == today:
                                    today_records.append(r)
                            except:
                                pass
            else:
                recs = db.get_fee_records(gym_id=sel_gym_id, date_from=today, date_to=today)
                for r in recs:
                    if hasattr(r, 'created_at') and r.created_at:
                        try:
                            if isinstance(r.created_at, str):
                                created_date = pd.to_datetime(r.created_at).date()
                            else:
                                created_date = r.created_at.date() if hasattr(r.created_at, 'date') else r.created_at
                            if created_date == today:
                                today_records.append(r)
                        except:
                            pass
        except:
            pass
    
    today_total = sum(r.amount for r in today_records)
    
    # This month
    month_start = today.replace(day=1)
    if sel_gym_id is None and gyms:
        month_records = []
        for g in gyms:
            recs = db.get_fee_records(gym_id=g.id, date_from=month_start, date_to=today)
            month_records.extend(recs)
    else:
        month_records = db.get_fee_records(gym_id=sel_gym_id, date_from=month_start, date_to=today)
    month_total = sum(r.amount for r in month_records)
    
    # 🚀 FAST: use cached members + bulk status
    all_members = _cached_members(sel_gym_id)
    
    member_ids = tuple(m.id for m in all_members)
    status_map = _bulk_member_status(sel_gym_id, member_ids)
    
    paid_count = 0
    unpaid_count = 0
    upcoming_count = 0
    
    for m in all_members:
        st_type = status_map.get(m.id, ("unpaid",))[0]
        if st_type == "paid":
            paid_count += 1
        elif st_type == "unpaid":
            unpaid_count += 1
        elif st_type == "upcoming":
            upcoming_count += 1
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0F172A,#1E293B);
                    border:1px solid #10B981;border-radius:12px;padding:0.8rem;text-align:center;">
            <div style="color:#94A3B8;font-size:0.65rem;font-weight:600;">💰 TOTAL COLLECTED</div>
            <div style="color:#34D399;font-size:1.3rem;font-weight:700;">PKR {total_collected:,.0f}</div>
            <div style="color:#64748B;font-size:0.6rem;">{len(records)} transactions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0F172A,#1E293B);
                    border:1px solid #FFC947;border-radius:12px;padding:0.8rem;text-align:center;">
            <div style="color:#94A3B8;font-size:0.65rem;font-weight:600;">📅 TODAY</div>
            <div style="color:#FFC947;font-size:1.3rem;font-weight:700;">PKR {today_total:,.0f}</div>
            <div style="color:#64748B;font-size:0.6rem;">{len(today_records)} payments</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0F172A,#1E293B);
                    border:1px solid #3B82F6;border-radius:12px;padding:0.8rem;text-align:center;">
            <div style="color:#94A3B8;font-size:0.65rem;font-weight:600;">📆 THIS MONTH</div>
            <div style="color:#60A5FA;font-size:1.3rem;font-weight:700;">PKR {month_total:,.0f}</div>
            <div style="color:#64748B;font-size:0.6rem;">{len(month_records)} payments</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0F172A,#1E293B);
                    border:1px solid #8B5CF6;border-radius:12px;padding:0.8rem;text-align:center;">
            <div style="color:#94A3B8;font-size:0.65rem;font-weight:600;">👥 MEMBERS</div>
            <div style="color:#A78BFA;font-size:1.3rem;font-weight:700;">{len(all_members)}</div>
            <div style="color:#64748B;font-size:0.6rem;">{paid_count} paid · {unpaid_count} unpaid</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0F172A,#1E293B);
                    border:1px solid #F59E0B;border-radius:12px;padding:0.8rem;text-align:center;">
            <div style="color:#94A3B8;font-size:0.65rem;font-weight:600;">📊 AVG PAYMENT</div>
            <div style="color:#FBBF24;font-size:1.3rem;font-weight:700;">PKR {avg_payment:,.0f}</div>
            <div style="color:#64748B;font-size:0.6rem;">per member</div>
        </div>
        """, unsafe_allow_html=True)
    
    return records


# ============================================
# COLLECTION TREND CHART
# ============================================

def render_collection_chart(records):
    """Render collection trend chart"""
    if not records:
        st.info("No data available for chart")
        return
    
    try:
        df = pd.DataFrame([{
            'date': r.payment_date,
            'amount': r.amount
        } for r in records if r.payment_date])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.groupby('date')['amount'].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['amount'],
            mode='lines+markers',
            name='Collection',
            line=dict(color='#10B981', width=3),
            marker=dict(size=8, color='#34D399'),
            fill='tozeroy',
            fillcolor='rgba(16,185,129,0.15)'
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=200,
            margin=dict(l=0, r=0, t=20, b=20),
            xaxis=dict(gridcolor='#1E293B'),
            yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except Exception as e:
        print(f"Chart error: {e}")
        st.info("Insufficient data for chart")


# ============================================
# PAYMENT METHOD DISTRIBUTION
# ============================================

def render_payment_method_chart(records):
    """Render payment method distribution pie chart"""
    if not records:
        return
    
    try:
        df = pd.DataFrame([{
            'method': r.payment_method or 'Cash',
            'amount': r.amount
        } for r in records])
        
        df = df.groupby('method')['amount'].sum().reset_index()
        
        colors = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899']
        
        fig = go.Figure(data=[go.Pie(
            labels=df['method'],
            values=df['amount'],
            hole=0.4,
            marker=dict(colors=colors[:len(df)]),
            textinfo='label+percent',
            textfont=dict(color='white', size=12)
        )])
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=200,
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except Exception as e:
        print(f"Pie chart error: {e}")


# ============================================
# STAFF PERFORMANCE SUMMARY
# ============================================

def render_staff_performance(records, current_user):
    """Render staff performance summary"""
    if not records:
        return
    
    staff_records = [r for r in records if r.collected_by == current_user]
    
    if not staff_records:
        return
    
    total_collected = sum(r.amount for r in staff_records)
    total_transactions = len(staff_records)
    avg_amount = total_collected / total_transactions if total_transactions > 0 else 0
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                border:1px solid #3B82F6;border-radius:12px;padding:0.8rem;margin:0.5rem 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
            <div>
                <div style="color:#94A3B8;font-size:0.65rem;font-weight:600;">🎯 YOUR PERFORMANCE</div>
                <div style="color:#60A5FA;font-size:1.1rem;font-weight:700;">PKR {total_collected:,.0f}</div>
            </div>
            <div style="text-align:center;">
                <div style="color:#94A3B8;font-size:0.6rem;">Transactions</div>
                <div style="color:#F8FAFC;font-size:1rem;font-weight:600;">{total_transactions}</div>
            </div>
            <div style="text-align:center;">
                <div style="color:#94A3B8;font-size:0.6rem;">Average</div>
                <div style="color:#FBBF24;font-size:1rem;font-weight:600;">PKR {avg_amount:,.0f}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:#94A3B8;font-size:0.6rem;">Status</div>
                <div style="color:#34D399;font-size:0.8rem;font-weight:600;">✅ Active</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# GYM-WISE COMPARISON
# ============================================

def render_gym_comparison(gyms, date_from, date_to):
    """Render gym-wise collection comparison"""
    if not gyms or len(gyms) < 2:
        return
    
    st.markdown("### 🏋️ Gym-wise Collection Comparison")
    
    gym_data = []
    for g in gyms:
        records = db.get_fee_records(gym_id=g.id, date_from=date_from, date_to=date_to)
        total = sum(r.amount for r in records)
        count = len(records)
        gym_data.append({
            "Gym": g.name,
            "Collection": total,
            "Transactions": count,
            "Avg": total / count if count > 0 else 0
        })
    
    df_gym = pd.DataFrame(gym_data)
    
    colors = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#EF4444', '#06B6D4']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_gym['Gym'],
        y=df_gym['Collection'],
        marker=dict(color=colors[:len(df_gym)]),
        text=[f'PKR {c:,.0f}' for c in df_gym['Collection']],
        textposition='outside',
        textfont=dict(color='white', size=11)
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=250,
        margin=dict(l=0, r=0, t=30, b=20),
        xaxis=dict(gridcolor='#1E293B'),
        yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


# ============================================
# STAFF RANKING
# ============================================

def render_staff_ranking(records):
    """Render staff ranking based on collection"""
    if not records:
        return
    
    staff_data = {}
    for r in records:
        staff = r.collected_by or "Unknown"
        if staff not in staff_data:
            staff_data[staff] = {"total": 0, "count": 0}
        staff_data[staff]["total"] += r.amount
        staff_data[staff]["count"] += 1
    
    if not staff_data:
        return
    
    ranking = []
    for staff, data in staff_data.items():
        ranking.append({
            "Staff": staff,
            "Collection": data["total"],
            "Transactions": data["count"],
            "Avg": data["total"] / data["count"] if data["count"] > 0 else 0
        })
    
    ranking.sort(key=lambda x: x["Collection"], reverse=True)
    
    st.markdown("### 🏆 Staff Performance Ranking")
    
    cols = st.columns(min(len(ranking), 4))
    for i, r in enumerate(ranking[:4]):
        medal = ["🥇", "🥈", "🥉", "4️⃣"][i] if i < 4 else f"{i+1}."
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div style="background:#0F172A;border:1px solid #1E293B;
                        border-radius:12px;padding:0.8rem;text-align:center;">
                <div style="font-size:2rem;">{medal}</div>
                <div style="color:#F8FAFC;font-weight:700;font-size:0.9rem;">{r['Staff']}</div>
                <div style="color:#FFC947;font-size:1.1rem;font-weight:700;">PKR {r['Collection']:,.0f}</div>
                <div style="color:#94A3B8;font-size:0.7rem;">{r['Transactions']} transactions</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================
# TOP PAYING MEMBERS
# ============================================

def render_top_paying_members(records, limit=10):
    """Render top paying members"""
    if not records:
        return
    
    member_data = {}
    for r in records:
        mid = r.member_id
        if mid not in member_data:
            member_data[mid] = {"total": 0, "count": 0}
        member_data[mid]["total"] += r.amount
        member_data[mid]["count"] += 1
    
    if not member_data:
        return
    
    top_members = []
    for mid, data in member_data.items():
        member = db.get_member(mid)
        if member:
            top_members.append({
                "Serial": member.serial_number,
                "Name": member.full_name,
                "Total Paid": data["total"],
                "Transactions": data["count"],
                "Avg": data["total"] / data["count"] if data["count"] > 0 else 0
            })
    
    top_members.sort(key=lambda x: x["Total Paid"], reverse=True)
    top_members = top_members[:limit]
    
    st.markdown("### 💰 Top Paying Members")
    if top_members:
        st.dataframe(pd.DataFrame(top_members), use_container_width=True, hide_index=True)
    else:
        st.info("No payment data available")


# ============================================
# EXPORT REPORT SECTION
# ============================================

def render_export_section(records, gym_name="Gym", date_from=None, date_to=None):
    """Render export report section with PDF and Excel options"""
    if not records:
        st.info("No data to export")
        return
    
    st.markdown("### 📥 Export Reports")
    st.caption("Download collection report in PDF or Excel format")
    
    col_pdf, col_excel = st.columns(2)
    
    with col_pdf:
        if st.button("📄 Download PDF Report", use_container_width=True):
            with st.spinner("Generating PDF..."):
                pdf_data = generate_pdf_report(records, gym_name, date_from, date_to)
                if pdf_data:
                    st.download_button(
                        label="📥 Click to Download PDF",
                        data=pdf_data,
                        file_name=f"fee_collection_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Failed to generate PDF. Make sure reportlab is installed.")
                    st.info("Run: pip install reportlab")
    
    with col_excel:
        if st.button("📊 Download Excel Report", use_container_width=True):
            with st.spinner("Generating Excel..."):
                excel_data = generate_excel_report(records, gym_name)
                if excel_data:
                    st.download_button(
                        label="📥 Click to Download Excel",
                        data=excel_data,
                        file_name=f"fee_collection_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.error("❌ Failed to generate Excel. Make sure openpyxl and xlsxwriter are installed.")
                    st.info("Run: pip install openpyxl xlsxwriter")


# ============================================
# PLAIN TEXT RECEIPT (NO HTML/CSS - WORKS EVERYWHERE)
# ============================================

def render_receipt_plain(receipt_data):
    """Render plain text receipt - NO HTML, works on all devices"""
    if not receipt_data:
        return
    
    remaining = receipt_data.get('remaining', '')
    is_partial = remaining and remaining != "Fully Paid" and "PKR" in str(remaining)
    
    gym_name = receipt_data.get('gym_name', 'GymPro')
    receipt_no = receipt_data.get('receipt_no', '')
    member_name = receipt_data.get('member_name', '')
    serial = receipt_data.get('serial', '')
    phone = receipt_data.get('phone', 'N/A')
    date_str = receipt_data.get('date', '')
    time_str = receipt_data.get('time', '')
    method = receipt_data.get('method', 'Cash')
    collected_by = receipt_data.get('collected_by', '')
    amount = receipt_data.get('amount', 0)
    period_start = receipt_data.get('period_start', '')
    period_end = receipt_data.get('period_end', '')
    
    # Build plain text receipt
    receipt_text = f"""
╔═══════════════════════════════════════╗
║           {gym_name}              ║
║        PAYMENT RECEIPT              ║
╠═══════════════════════════════════════╣
║  Receipt #: {receipt_no}
║  Member:   {member_name}
║  Serial:   {serial}
║  Phone:    {phone}
║  Date:     {date_str}
║  Time:     {time_str}
║  Method:   {method}
║  Collected By: {collected_by}
╠═══════════════════════════════════════╣
║  Amount:   PKR {amount:,.2f}
"""
    
    if is_partial:
        receipt_text += f"""
║  ⚠️ Partial Payment
║  Remaining: {remaining}
"""
    elif remaining == "Fully Paid":
        receipt_text += """
║  ✅ Fully Paid
"""
    
    receipt_text += f"""
╠═══════════════════════════════════════╣
║  Period: {period_start} → {period_end}
╠═══════════════════════════════════════╣
║  Thank you for your payment!
"""
    
    if is_partial:
        receipt_text += f"""
║  ⚠️ Remaining balance: {remaining}
"""
    
    receipt_text += """
║  This is a computer-generated receipt
╚═══════════════════════════════════════╝
"""
    
    st.code(receipt_text, language="text")


# ============================================
# TAB 1: COLLECT FEE (WITH AUTO-FILL + WARNING + DYNAMIC KEYS)
# ============================================

def render_collect_fee(gym_id, current_user):
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    # 🖨️ PRINT — Show print button (not text receipt)
    pending = st.session_state.pop('pending_print', None)
    if pending:
        st.success("✅ Payment recorded!")
        st.divider()
        # 🖨️ Print button — actual print dialog
        render_print_component(pending['data'], copies=pending['copies'])
        st.divider()

    st.subheader("➕ Collect Fee")

    user = db.get_user_by_username(current_user)
    
    if user and user.role.lower() == "staff" and user.gym_id:
        staff_gym = db.get_gym(user.gym_id)
        if staff_gym:
            gym_opts = {staff_gym.name: staff_gym.id}
        else:
            st.error("❌ Staff account has no assigned gym. Contact admin.")
            return
    elif user and user.role.lower() in ["admin", "owner"]:
        gym_opts = {"🌐 All Gyms": None}
        for g in gyms:
            gym_opts[g.name] = g.id
    else:
        gym_opts = {g.name: g.id for g in gyms}
    
    if len(gym_opts) == 1:
        default_gym_name = list(gym_opts.keys())[0]
    else:
        valid_gym_ids = [gid for gid in gym_opts.values() if gid is not None]
        if gym_id in valid_gym_ids:
            default_gym_name = next((name for name, gid in gym_opts.items() if gid == gym_id), list(gym_opts.keys())[0])
        else:
            default_gym_name = list(gym_opts.keys())[0]

    if 'cf_date_from' not in st.session_state:
        st.session_state['cf_date_from'] = date.today().replace(day=1)
    if 'cf_date_to' not in st.session_state:
        st.session_state['cf_date_to'] = date.today()
    
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        date_from = st.date_input("📅 From Date", value=st.session_state['cf_date_from'], key="cf_date_from_input")
        st.session_state['cf_date_from'] = date_from
    with col_date2:
        date_to = st.date_input("📅 To Date", value=st.session_state['cf_date_to'], key="cf_date_to_input")
        st.session_state['cf_date_to'] = date_to
    
    col_qf1, col_qf2, col_qf3, col_qf4 = st.columns(4)
    with col_qf1:
        if st.button("📅 Today", use_container_width=True, key="cf_today"):
            st.session_state['cf_date_from'] = date.today()
            st.session_state['cf_date_to'] = date.today()
            st.rerun()
    with col_qf2:
        if st.button("📆 This Week", use_container_width=True, key="cf_week"):
            week_start = date.today() - timedelta(days=date.today().weekday())
            st.session_state['cf_date_from'] = week_start
            st.session_state['cf_date_to'] = date.today()
            st.rerun()
    with col_qf3:
        if st.button("📅 This Month", use_container_width=True, key="cf_month"):
            month_start = date.today().replace(day=1)
            st.session_state['cf_date_from'] = month_start
            st.session_state['cf_date_to'] = date.today()
            st.rerun()
    with col_qf4:
        if st.button("📆 All Time", use_container_width=True, key="cf_all"):
            st.session_state['cf_date_from'] = date(2020, 1, 1)
            st.session_state['cf_date_to'] = date.today()
            st.rerun()
    
    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        if user and user.role.lower() == "staff" and user.gym_id:
            staff_gym = db.get_gym(user.gym_id)
            st.text_input("🏋️ Gym", value=staff_gym.name if staff_gym else "Assigned Gym", disabled=True, key="cf_gym_display")
            sel_gym_id = user.gym_id
            gym_sel_name = staff_gym.name if staff_gym else ""
        else:
            gym_sel = st.selectbox("🏋️ Gym *", list(gym_opts.keys()), index=list(gym_opts.keys()).index(default_gym_name) if default_gym_name in gym_opts else 0, key="cf_gym_sel")
            sel_gym_id = gym_opts[gym_sel]
            gym_sel_name = gym_sel
        
        # 🚀 FAST: cached members
        members = _cached_members(sel_gym_id)
        if sel_gym_id is None:
            st.info(f"📊 Showing members from ALL gyms ({len(members)} total)")

        search_query = st.text_input("🔍 Search Member", key="cf_search", placeholder="Type name or serial number...")

        if search_query:
            q = search_query.lower().strip()
            filtered_members = [m for m in members if q in m.full_name.lower() or q in str(m.serial_number).lower()]
        else:
            filtered_members = members

        st.markdown("**Filter by Status:**")
        status_filter = st.radio("Filter by Status", ["All Members", "✅ Paid", "⏳ Unpaid", "🟡 Upcoming"], horizontal=True, key="status_filter", label_visibility="collapsed")
        
        if status_filter == "✅ Paid":
            paid_members_list = []
            for m in filtered_members:
                fee_records = db.get_fee_records(member_id=m.id, limit=1)
                if fee_records:
                    latest = fee_records[0]
                    if hasattr(latest, 'period_end') and latest.period_end:
                        try:
                            period_end = latest.period_end
                            if isinstance(period_end, str):
                                period_end = pd.to_datetime(period_end).date()
                            else:
                                period_end = period_end.date() if hasattr(period_end, 'date') else period_end
                            if period_end >= date.today():
                                paid_members_list.append(m)
                        except:
                            pass
            filtered_members = paid_members_list
        elif status_filter == "⏳ Unpaid":
            unpaid_members_list = []
            for m in filtered_members:
                fee_records = db.get_fee_records(member_id=m.id, limit=1)
                if not fee_records:
                    unpaid_members_list.append(m)
                else:
                    latest = fee_records[0]
                    if hasattr(latest, 'period_end') and latest.period_end:
                        try:
                            period_end = latest.period_end
                            if isinstance(period_end, str):
                                period_end = pd.to_datetime(period_end).date()
                            else:
                                period_end = period_end.date() if hasattr(period_end, 'date') else period_end
                            if period_end < date.today():
                                unpaid_members_list.append(m)
                        except:
                            unpaid_members_list.append(m)
                    else:
                        unpaid_members_list.append(m)
            filtered_members = unpaid_members_list
        elif status_filter == "🟡 Upcoming":
            upcoming_members_list = []
            for m in filtered_members:
                fee_records = db.get_fee_records(member_id=m.id, limit=1)
                if fee_records:
                    latest = fee_records[0]
                    if hasattr(latest, 'period_end') and latest.period_end:
                        try:
                            period_end = latest.period_end
                            if isinstance(period_end, str):
                                period_end = pd.to_datetime(period_end).date()
                            else:
                                period_end = period_end.date() if hasattr(period_end, 'date') else period_end
                            days_left = (period_end - date.today()).days
                            if 0 <= days_left <= 7:
                                upcoming_members_list.append(m)
                        except:
                            pass
            filtered_members = upcoming_members_list

        mem_opts = {}
        for m in filtered_members:
            fee_records = db.get_fee_records(member_id=m.id, limit=1)
            status_icon = "⏳"
            if fee_records:
                latest = fee_records[0]
                if hasattr(latest, 'period_end') and latest.period_end:
                    try:
                        period_end = latest.period_end
                        if isinstance(period_end, str):
                            period_end = pd.to_datetime(period_end).date()
                        else:
                            period_end = period_end.date() if hasattr(period_end, 'date') else period_end
                        if period_end >= date.today():
                            status_icon = "✅"
                        else:
                            status_icon = "🔴"
                    except:
                        status_icon = "⏳"
            
            label = f"{status_icon} {m.serial_number} — {m.full_name}"
            mem_opts[label] = m.id

        member_id = None
        sel_mem = None

        if not members:
            st.warning("No members in this gym.")
        elif not mem_opts:
            st.warning("No members match your search.")
        else:
            mem_sel = st.selectbox("👤 Select Member *", list(mem_opts.keys()), key="cf_member_sel")
            member_id = mem_opts[mem_sel]
            sel_mem = next((m for m in filtered_members if m.id == member_id), None)

    if sel_mem:
        st.markdown("---")
        
        pic_col, info_col = st.columns([1.2, 3])
        
        with pic_col:
            show_member_photo(sel_mem.photo_path, sel_mem.serial_number, width=200, height=250)
        
        with info_col:
            fee_records = db.get_fee_records(member_id=sel_mem.id, limit=1)
            status_type = "unpaid"
            status_text = "⏳ Pending"
            bg_color = "#F59E0B"
            text_color = "#1E293B"
            
            if fee_records:
                latest = fee_records[0]
                if hasattr(latest, 'period_end') and latest.period_end:
                    try:
                        period_end = latest.period_end
                        if isinstance(period_end, str):
                            period_end = pd.to_datetime(period_end).date()
                        else:
                            period_end = period_end.date() if hasattr(period_end, 'date') else period_end
                        today = date.today()
                        days_left = (period_end - today).days
                        
                        if days_left < 0:
                            status_type = "unpaid"
                            status_text = f"🔴 Expired ({abs(days_left)}d ago)"
                            bg_color = "#EF4444"
                            text_color = "white"
                        elif days_left <= 7:
                            status_type = "upcoming"
                            status_text = f"🟡 {days_left}d left"
                            bg_color = "#F59E0B"
                            text_color = "#1E293B"
                        else:
                            status_type = "paid"
                            status_text = f"✅ Paid ({days_left}d left)"
                            bg_color = "#10B981"
                            text_color = "white"
                    except:
                        pass
            
            st.markdown(f"### {sel_mem.full_name}")
            st.caption(f"🔢 {sel_mem.serial_number}")
            
            st.markdown(f"<span style='background:{bg_color};color:{text_color};padding:4px 12px;border-radius:9999px;font-size:0.8rem;font-weight:600;'>{status_text}</span>", unsafe_allow_html=True)
            
            # Check if member already paid this month
            today = date.today()
            month_start = today.replace(day=1)
            
            # 🚀 FAST: cached member records
            all_records = _cached_fee_records_by_member(sel_mem.id)
            this_month_payments = []
            for r in all_records:
                if r.payment_date:
                    if isinstance(r.payment_date, str):
                        try:
                            pay_date = pd.to_datetime(r.payment_date).date()
                        except:
                            pay_date = None
                    else:
                        pay_date = r.payment_date.date() if hasattr(r.payment_date, 'date') else r.payment_date
                    
                    if pay_date and pay_date >= month_start and pay_date <= today:
                        this_month_payments.append(r)
            
            # Show warning if already paid this month
            if this_month_payments:
                total_this_month = sum(r.amount for r in this_month_payments)
                st.warning(f"""
                ⚠️ **This member has already paid this month!**
                - Total paid this month: **PKR {total_this_month:,.2f}**
                - Number of payments: **{len(this_month_payments)}**
                - You can still collect again if needed (e.g., advance payment, extra charges)
                """)
            
            balance = get_member_balance(sel_mem.id)
            if balance > 0:
                st.warning(f"⚠️ Remaining Balance: PKR {balance:,.2f}")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.metric("💰 Fee", f"PKR {sel_mem.fee_amount:,.2f}")
                if balance > 0:
                    st.caption(f"Paid: PKR {sel_mem.fee_amount - balance:,.2f} • Remaining: PKR {balance:,.2f}")
            with col_f2:
                st.metric("📅 Expiry", sel_mem.expiry_date or "—")
            
            if not fee_records:
                st.warning("⚠️ This member has no fee record yet. Collect fee to activate.")
            
            if sel_mem.expiry_date:
                try:
                    exp = sel_mem.expiry_date
                    if isinstance(exp, str):
                        exp = pd.to_datetime(exp).date()
                    else:
                        exp = exp.date() if hasattr(exp, 'date') else exp
                    if exp < date.today():
                        if st.button("🔄 Quick Renew", type="secondary", use_container_width=True):
                            st.session_state['renew_member'] = sel_mem.id
                            st.rerun()
                except:
                    pass
            
            if st.button("📋 View Full Payment History", use_container_width=True):
                st.session_state['view_member_history'] = sel_mem.id
                st.rerun()

    # 🔥 FIXED: Form ke ANDAR dynamic keys use karo
    with st.form("collect_fee_form", clear_on_submit=True):
        st.markdown("---")
        st.subheader("💳 Payment Details")
        
        f_c1, f_c2 = st.columns(2)

        with f_c1:
            # 🔥 FIXED: Get member fee amount
            if sel_mem and hasattr(sel_mem, 'fee_amount') and sel_mem.fee_amount and sel_mem.fee_amount > 0:
                default_amount = float(sel_mem.fee_amount)
            else:
                default_amount = 0.01
            
            balance = get_member_balance(sel_mem.id) if sel_mem else 0
            
            # 🔥 CRITICAL FIX: Dynamic key so value updates when member changes
            amount_key = f"cf_amount_{member_id}" if member_id else "cf_amount_default"
            
            if balance > 0:
                st.info(f"💡 Remaining balance: PKR {balance:,.2f}")
                col_amt1, col_amt2 = st.columns([3, 1])
                with col_amt1:
                    amount = st.number_input(
                        "💰 Amount (PKR) *",
                        min_value=0.01,
                        value=min(default_amount, balance) if balance > 0 else default_amount,
                        step=5.0,
                        format="%.2f",
                        key=amount_key
                    )
                with col_amt2:
                    if st.form_submit_button("💰 Full Amount", use_container_width=True):
                        st.session_state[amount_key] = balance
                        st.rerun()
            else:
                amount = st.number_input(
                    "💰 Amount (PKR) *",
                    min_value=0.01,
                    value=default_amount,
                    step=5.0,
                    format="%.2f",
                    key=amount_key,
                    help=f"Default: PKR {default_amount:,.2f} (Member's fee)"
                )
            
            payment_method = st.selectbox("💳 Payment Method *", db.PAYMENT_METHODS, key="cf_method")

        with f_c2:
            # 🔥 FIXED: Payment Date = Today (LOCKED - cannot change)
            today = date.today()
            st.date_input(
                "📅 Payment Date *",
                value=today,
                key="cf_date",
                disabled=True,
                help="Payment date is always today's date"
            )
            payment_date = today  # Always today's date
            
                        # 🔥 FIXED: Period Start = TODAY (not expiry date)
            period_start_key = f"cf_period_start_{member_id}" if member_id else "cf_period_start_default"
            
            today = date.today()
            default_start = today
            
            period_start = st.date_input(
                "📅 Period Start",
                value=default_start,
                key=period_start_key,
                help="Auto-filled: Today's date. Change manually if needed."
            )
            
            # 🔥 FIXED: Period End = Period Start + 30 days
            period_end_key = f"cf_period_end_{member_id}" if member_id else "cf_period_end_default"
            
            default_end = period_start + timedelta(days=30)
            
            period_end = st.date_input(
                "📅 Period End",
                value=default_end,
                key=period_end_key,
                help="Auto-filled: 30 days from Period Start. Change manually if needed."
            )

        notes = st.text_area("📝 Notes (optional)", height=60, key="cf_notes", placeholder="e.g., Partial payment, remaining PKR 3000")

        st.markdown("---")
        st.subheader("🖨️ Print Options")
        
        col_print1, col_print2 = st.columns(2)
        with col_print1:
            print_receipt = st.checkbox("🖨️ Print Receipt", value=True, key="cf_print")
        with col_print2:
            print_copies = st.radio("📄 Copies", ["2 (Member + Gym)", "1 (Member only)"], index=0, key="cf_copies")

        submitted = st.form_submit_button("✅ Record Payment & Print Slip", type="primary", use_container_width=True)

        if submitted:
            if not member_id:
                st.error("❌ Select a member first!")
            elif amount <= 0:
                st.error("❌ Amount must be positive!")
            elif not sel_mem:
                st.error("❌ Member details missing!")
            else:
                generated_rcp = f"RCP-{uuid.uuid4().hex[:8].upper()}"
                
                ok, msg = db.add_fee_record(
                    member_id=member_id, gym_id=sel_gym_id if sel_gym_id else sel_mem.gym_id, 
                    amount=amount,
                    payment_method=payment_method, payment_date=payment_date,
                    period_start=period_start, period_end=period_end,
                    collected_by=current_user, notes=notes
                )

                if ok:
                    balance_after = get_member_balance(member_id)
                    if balance_after <= 0:
                        db.update_member(member_id, expiry_date=str(period_end), status="Active")
                    else:
                        db.update_member(member_id, status="Active")
                    
                    try:
                        db.log_activity(
                            user=current_user, action="FEE_COLLECTED",
                            details=f"Member: {sel_mem.full_name} ({sel_mem.serial_number}) | Method: {payment_method} | Period: {period_start} → {period_end} | Amount: PKR {amount:,.2f}",
                            gym_id=sel_gym_id if sel_gym_id else sel_mem.gym_id, 
                            amount=amount,
                            record_ref=generated_rcp,
                        )
                    except Exception:
                        pass

                    receipt_no = generated_rcp

                    # Get correct gym name
                    if sel_gym_id:
                        gym_obj = db.get_gym(sel_gym_id)
                        gym_name_display = gym_obj.name if gym_obj else gym_sel_name
                    else:
                        gym_name_display = gym_sel_name or "GymPro"
                    
                    if gym_name_display == "🌐 All Gyms" or not gym_name_display:
                        gym_name_display = "GymPro"

                    receipt_data = {
                        'gym_name':     gym_name_display,
                        'gym_address':  "",
                        'gym_phone':    "",
                        'receipt_no':   receipt_no,
                        'date':         payment_date.strftime('%Y-%m-%d'),
                        'time':         datetime.now().strftime('%I:%M %p'),
                        'collected_by': current_user,
                        'member_name':  sel_mem.full_name,
                        'serial':       sel_mem.serial_number,
                        'phone':        sel_mem.phone or "N/A",
                        'amount':       amount,
                        'method':       payment_method,
                        'period_start': period_start.strftime('%Y-%m-%d'),
                        'period_end':   period_end.strftime('%Y-%m-%d'),
                        'remaining':    f"PKR {balance_after:,.2f}" if balance_after > 0 else "Fully Paid",
                    }

                    if print_receipt:
                        copies = 2 if "2" in print_copies else 1
                        st.session_state['pending_print'] = {
                            'data': receipt_data,
                            'copies': copies,
                        }

                    st.success(f"✅ Payment recorded! Receipt: {receipt_no}")
                    if balance_after > 0:
                        st.info(f"⚠️ Remaining balance: PKR {balance_after:,.2f}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ============================================
# TAB 2: HISTORY & ADMIN (WITH SEARCH) - FIXED: SHOWS ALL RECORDS
# ============================================

def render_history_admin(gym_id, role, current_user=""):
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    st.subheader("📋 Payment History")
    
    user = db.get_user_by_username(current_user)
    
    if user and user.role.lower() in ["admin", "owner"]:
        gym_opts = {"🌐 All Gyms": None}
        for g in gyms:
            gym_opts[g.name] = g.id
    else:
        gym_opts = {g.name: g.id for g in gyms}
    
    # 🔍 SEARCH IN HISTORY - Added 4th column
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1.5])
    
    with col_f1:
        if user and user.role.lower() == "staff" and user.gym_id:
            staff_gym = db.get_gym(user.gym_id)
            sel_gid = user.gym_id
            st.text_input("🏋️ Gym", value=staff_gym.name if staff_gym else "Assigned Gym", disabled=True, key="fc_gym_display_staff")
        elif user and user.role.lower() in ["admin", "owner"]:
            gym_sel = st.selectbox("🏋️ Select Gym", list(gym_opts.keys()), key="fc_gym_admin")
            sel_gid = gym_opts[gym_sel]
        elif gym_id:
            sel_gid = gym_id
            st.text_input("🏋️ Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True, key="fc_gym_display")
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("🏋️ Select Gym", list(opts.keys()), key="fc_gym")
            sel_gid = opts[chosen]
    
    # Default to current month
    today = date.today()
    month_start = today.replace(day=1)
    
    with col_f2:
        date_from = st.date_input("📅 From Date", value=month_start, key="fc_from")
    with col_f3:
        date_to = st.date_input("📅 To Date", value=today, key="fc_to")
    
    # 🔍 SEARCH INPUT
    with col_f4:
        st.write("")
        st.write("")
        search_history = st.text_input("🔍 Search", placeholder="Name or Serial...", key="history_search")

    records = render_collection_summary(sel_gid, date_from, date_to, gyms)
    
    # 🔍 Filter records by search
    if search_history and records:
        search_lower = search_history.lower().strip()
        filtered_records = []
        for r in records:
            member = db.get_member(r.member_id)
            if member:
                if (search_lower in (member.full_name or "").lower() or 
                    search_lower in (member.serial_number or "").lower()):
                    filtered_records.append(r)
        records = filtered_records

    if user and user.role.lower() == "staff":
        render_staff_performance(records, current_user)

    chart_col1, chart_col2 = st.columns([2, 1])
    with chart_col1:
        render_collection_chart(records)
    with chart_col2:
        render_payment_method_chart(records)
    
    if sel_gid is None and gyms and len(gyms) > 1:
        render_gym_comparison(gyms, date_from, date_to)
    
    render_staff_ranking(records)
    render_top_paying_members(records)
    
    st.divider()
    
    gym_name = "All Gyms" if sel_gid is None else (db.get_gym(sel_gid).name if sel_gid else "Gym")
    render_export_section(records, gym_name, date_from.strftime('%Y-%m-%d') if date_from else None, date_to.strftime('%Y-%m-%d') if date_to else None)
    
    st.divider()

    # 🚀 FAST: cached members
    _all = _cached_members(sel_gid)
    all_members = [m for m in _all if m.status == "Active"]
    
    paid_members = []
    unpaid_members = []
    upcoming_members = []
    paid_total = 0
    unpaid_total = 0
    upcoming_total = 0
    
    for member in all_members:
        status_type, status_text, _, _ = get_member_payment_status(member)
        fee = member.fee_amount or 0
        
        if status_type == "paid":
            paid_members.append(member)
            paid_total += fee
        elif status_type == "unpaid":
            unpaid_members.append(member)
            unpaid_total += fee
        elif status_type == "upcoming":
            upcoming_members.append(member)
            upcoming_total += fee
        else:
            unpaid_members.append(member)
            unpaid_total += fee

    st.subheader("📋 Member-wise Fee Status")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    
    with col_t1:
        st.markdown(f"""
        <div style="background:#0F172A;border:2px solid #10B981;border-radius:10px;padding:0.8rem;text-align:center;margin-bottom:0.5rem;">
            <span style="color:#10B981;font-weight:700;font-size:1.1rem;">✅ PAID MEMBERS</span>
            <span style="color:#94A3B8;font-size:0.9rem;margin-left:0.5rem;">({len(paid_members)})</span>
        </div>
        """, unsafe_allow_html=True)
        
        if paid_members:
            paid_data = []
            for m in paid_members:
                paid_data.append({
                    "Serial": m.serial_number,
                    "Name": m.full_name,
                    "Fee": f"PKR {m.fee_amount:,.2f}",
                    "Expiry": m.expiry_date,
                })
            paid_df = pd.DataFrame(paid_data)
            st.dataframe(paid_df, use_container_width=True, hide_index=True, height=300)
            
            st.markdown(f"""
            <div style="background:#0F172A;border:2px solid #10B981;border-radius:10px;padding:0.8rem;text-align:center;margin-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.9rem;">Total Amount: </span>
                <span style="color:#34D399;font-weight:700;font-size:1.3rem;">PKR {paid_total:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No paid members")
    
    with col_t2:
        st.markdown(f"""
        <div style="background:#0F172A;border:2px solid #EF4444;border-radius:10px;padding:0.8rem;text-align:center;margin-bottom:0.5rem;">
            <span style="color:#EF4444;font-weight:700;font-size:1.1rem;">⏳ UNPAID MEMBERS</span>
            <span style="color:#94A3B8;font-size:0.9rem;margin-left:0.5rem;">({len(unpaid_members)})</span>
        </div>
        """, unsafe_allow_html=True)
        
        if unpaid_members:
            unpaid_data = []
            for m in unpaid_members:
                unpaid_data.append({
                    "Serial": m.serial_number,
                    "Name": m.full_name,
                    "Fee": f"PKR {m.fee_amount:,.2f}",
                    "Expiry": m.expiry_date or "—",
                })
            unpaid_df = pd.DataFrame(unpaid_data)
            st.dataframe(unpaid_df, use_container_width=True, hide_index=True, height=300)
            
            st.markdown(f"""
            <div style="background:#0F172A;border:2px solid #EF4444;border-radius:10px;padding:0.8rem;text-align:center;margin-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.9rem;">Total Amount: </span>
                <span style="color:#F87171;font-weight:700;font-size:1.3rem;">PKR {unpaid_total:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No unpaid members")
    
    with col_t3:
        st.markdown(f"""
        <div style="background:#0F172A;border:2px solid #F59E0B;border-radius:10px;padding:0.8rem;text-align:center;margin-bottom:0.5rem;">
            <span style="color:#F59E0B;font-weight:700;font-size:1.1rem;">🟡 UPCOMING MEMBERS</span>
            <span style="color:#94A3B8;font-size:0.9rem;margin-left:0.5rem;">({len(upcoming_members)})</span>
        </div>
        """, unsafe_allow_html=True)
        
        if upcoming_members:
            upcoming_data = []
            for m in upcoming_members:
                upcoming_data.append({
                    "Serial": m.serial_number,
                    "Name": m.full_name,
                    "Fee": f"PKR {m.fee_amount:,.2f}",
                    "Expiry": m.expiry_date,
                })
            upcoming_df = pd.DataFrame(upcoming_data)
            st.dataframe(upcoming_df, use_container_width=True, hide_index=True, height=300)
            
            st.markdown(f"""
            <div style="background:#0F172A;border:2px solid #F59E0B;border-radius:10px;padding:0.8rem;text-align:center;margin-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.9rem;">Total Amount: </span>
                <span style="color:#FBBF24;font-weight:700;font-size:1.3rem;">PKR {upcoming_total:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No upcoming members")

    st.divider()
    st.subheader("📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background:#0F172A;border:2px solid #10B981;border-radius:10px;padding:0.5rem;text-align:center;">
            <div style="font-size:0.8rem;color:#94A3B8;">✅ PAID</div>
            <div style="font-size:1.8rem;font-weight:800;color:#F8FAFC;">{len(paid_members)}</div>
            <div style="font-size:0.9rem;font-weight:600;color:#34D399;">PKR {paid_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:#0F172A;border:2px solid #EF4444;border-radius:10px;padding:0.5rem;text-align:center;">
            <div style="font-size:0.8rem;color:#94A3B8;">⏳ UNPAID</div>
            <div style="font-size:1.8rem;font-weight:800;color:#F8FAFC;">{len(unpaid_members)}</div>
            <div style="font-size:0.9rem;font-weight:600;color:#F87171;">PKR {unpaid_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background:#0F172A;border:2px solid #F59E0B;border-radius:10px;padding:0.5rem;text-align:center;">
            <div style="font-size:0.8rem;color:#94A3B8;">🟡 UPCOMING</div>
            <div style="font-size:1.8rem;font-weight:800;color:#F8FAFC;">{len(upcoming_members)}</div>
            <div style="font-size:0.9rem;font-weight:600;color:#FBBF24;">PKR {upcoming_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("🔄 Recent Payments (Current Month)")
    
    recent_records = records
    
    if recent_records:
        recent_data = []
        for r in recent_records:
            mem = db.get_member(r.member_id)
            recent_data.append({
                "Date": r.payment_date,
                "Member": mem.full_name if mem else "—",
                "Serial": mem.serial_number if mem else "—",
                "Amount": f"PKR {r.amount:,.2f}",
                "Method": r.payment_method,
                "Collected By": r.collected_by or "—",
            })
        
        st.dataframe(pd.DataFrame(recent_data), use_container_width=True, hide_index=True)
        
        total_collected = sum(r.amount for r in recent_records)
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;
                    padding:0.8rem;text-align:center;margin-top:0.5rem;">
            <span style="color:#94A3B8;">Total Collection (This Month): </span>
            <span style="color:#FFC947;font-weight:700;font-size:1.3rem;">PKR {total_collected:,.2f}</span>
            <span style="color:#64748B;font-size:0.8rem;margin-left:1rem;">
                ({len(recent_records)} payments)
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No payments in current month")

    # ============================================
    # 🔐 ADMIN PANEL - SHOWS ALL RECORDS (FIXED)
    # ============================================
    
    st.divider()
    st.subheader("🔐 Admin Panel - Manage Fee Records (All Months)")
    st.caption("Edit or delete **fee records** only. Members will NOT be deleted. All months entries shown.")
    
    if str(role).lower() in ["admin", "owner"]:
        # 🔥 FIXED: Get ALL fee records (not just current month)
        if sel_gid is None and gyms:
            all_fee_records = []
            for g in gyms:
                records = db.get_fee_records(gym_id=g.id, date_from=date(2020,1,1), date_to=date.today())
                all_fee_records.extend(records)
        else:
            all_fee_records = db.get_fee_records(gym_id=sel_gid, date_from=date(2020,1,1), date_to=date.today()) if sel_gid else []
        
        if all_fee_records:
            # Sort by date (newest first)
            all_fee_records = sorted(all_fee_records, key=lambda r: r.payment_date if r.payment_date else "", reverse=True)
            
            # Create selectable options
            record_opts = {}
            for r in all_fee_records:
                mem = db.get_member(r.member_id)
                mem_name = mem.full_name if mem else "Unknown"
                mem_serial = mem.serial_number if mem else "N/A"
                
                # Get date string
                if r.payment_date:
                    if isinstance(r.payment_date, str):
                        date_str = r.payment_date
                    else:
                        date_str = r.payment_date.strftime('%Y-%m-%d')
                else:
                    date_str = "—"
                
                label = f"{mem_serial} — {mem_name} — PKR {r.amount:,.2f} ({date_str})"
                record_opts[label] = r.id
            
            selected_label = st.selectbox("📋 Select Fee Record to Manage", list(record_opts.keys()), key="admin_fee_select")
            selected_record_id = record_opts[selected_label]
            
            # Find the selected record
            selected_record = None
            for r in all_fee_records:
                if r.id == selected_record_id:
                    selected_record = r
                    break
            
            if selected_record:
                # Get member info for display
                member = db.get_member(selected_record.member_id)
                
                # Show Member Photo
                st.markdown("### 📸 Member Photo")
                pic_col1, info_col1 = st.columns([1, 3])
                with pic_col1:
                    if member:
                        show_member_photo(
                            member.photo_path, 
                            member.serial_number, 
                            width=180, 
                            height=220
                        )
                    else:
                        st.markdown("""
                        <div style="width:180px;height:220px;border-radius:16px;
                                    background:#334155;display:flex;align-items:center;
                                    justify-content:center;font-size:60px;color:white;">
                            ?
                        </div>
                        """, unsafe_allow_html=True)
                
                with info_col1:
                    if member:
                        st.markdown(f"""
                        <div style="display:flex;flex-direction:column;justify-content:center;height:100%;">
                            <div style="color:#F8FAFC;font-size:1.2rem;font-weight:700;">{member.full_name}</div>
                            <div style="color:#94A3B8;font-size:0.9rem;">🔢 {member.serial_number}</div>
                            <div style="color:#94A3B8;font-size:0.9rem;">📱 {member.phone or 'N/A'}</div>
                            <div style="color:#94A3B8;font-size:0.9rem;">💰 Fee: PKR {member.fee_amount:,.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("### Unknown Member")
                
                st.markdown("---")
                
                # Show Record Details
                st.markdown("### 📋 Fee Record Details")
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric("💰 Amount", f"PKR {selected_record.amount:,.2f}")
                    st.metric("💳 Method", selected_record.payment_method or "Cash")
                with col_r2:
                    date_str = selected_record.payment_date
                    if date_str:
                        if isinstance(date_str, str):
                            date_str = date_str
                        else:
                            date_str = date_str.strftime('%Y-%m-%d')
                    st.metric("📅 Date", date_str or "—")
                    
                    period_end_str = selected_record.period_end
                    if period_end_str:
                        if isinstance(period_end_str, str):
                            period_end_str = period_end_str
                        else:
                            period_end_str = period_end_str.strftime('%Y-%m-%d')
                    st.metric("📅 Period End", period_end_str or "—")
                
                st.markdown(f"**Collected By:** {selected_record.collected_by or '—'}")
                st.markdown(f"**Notes:** {selected_record.notes or '—'}")
                
                st.markdown("---")
                
                col_edit, col_delete = st.columns(2)
                
                # EDIT FEE RECORD
                with col_edit:
                    with st.expander("✏️ Edit Fee Record", expanded=True):
                        with st.form("edit_fee_record_form"):
                            col_e1, col_e2 = st.columns(2)
                            
                            with col_e1:
                                edit_amount = st.number_input(
                                    "💰 Amount (PKR)", 
                                    min_value=0.01, 
                                    value=float(selected_record.amount), 
                                    step=5.0, 
                                    format="%.2f",
                                    key="edit_fee_amount"
                                )
                                edit_method = st.selectbox(
                                    "💳 Payment Method", 
                                    db.PAYMENT_METHODS, 
                                    index=db.PAYMENT_METHODS.index(selected_record.payment_method) if selected_record.payment_method in db.PAYMENT_METHODS else 0,
                                    key="edit_fee_method"
                                )
                            
                            with col_e2:
                                # Handle date
                                pay_date = selected_record.payment_date
                                if pay_date:
                                    if isinstance(pay_date, str):
                                        try:
                                            pay_date = pd.to_datetime(pay_date).date()
                                        except:
                                            pay_date = date.today()
                                    else:
                                        pay_date = pay_date.date() if hasattr(pay_date, 'date') else pay_date
                                else:
                                    pay_date = date.today()
                                
                                edit_date = st.date_input("📅 Payment Date", value=pay_date, key="edit_fee_date")
                                
                                period_end = selected_record.period_end
                                if period_end:
                                    if isinstance(period_end, str):
                                        try:
                                            period_end = pd.to_datetime(period_end).date()
                                        except:
                                            period_end = date.today() + timedelta(days=30)
                                    else:
                                        period_end = period_end.date() if hasattr(period_end, 'date') else period_end
                                else:
                                    period_end = date.today() + timedelta(days=30)
                                
                                edit_period_end = st.date_input("📅 Period End", value=period_end, key="edit_fee_period_end")
                            
                            edit_notes = st.text_area("📝 Notes", value=selected_record.notes or "", key="edit_fee_notes")
                            
                            if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                                if hasattr(db, 'update_fee_record'):
                                    ok, msg = db.update_fee_record(
                                        selected_record.id,
                                        edit_amount,
                                        edit_method,
                                        edit_date,
                                        edit_period_end,
                                        edit_notes
                                    )
                                    if ok:
                                        # Update member expiry if needed
                                        if member:
                                            db.update_member(member.id, expiry_date=str(edit_period_end))
                                        
                                        db.log_activity(
                                            user=current_user,
                                            action="FEE_RECORD_EDITED",
                                            details=f"Fee record {selected_record.id} updated: PKR {edit_amount:,.2f}",
                                            gym_id=sel_gid,
                                            amount=edit_amount
                                        )
                                        st.success("✅ Fee record updated successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {msg}")
                                else:
                                    st.error("⚠️ Update function not available")
                
                # DELETE FEE RECORD (ONLY FEE, NOT MEMBER)
                with col_delete:
                    with st.expander("🗑️ Delete Fee Record", expanded=False):
                        st.warning(f"⚠️ Are you sure you want to delete this fee record?")
                        
                        if member:
                            st.caption(f"Member: **{member.full_name}** ({member.serial_number})")
                        st.caption(f"Amount: **PKR {selected_record.amount:,.2f}**")
                        st.caption(f"Date: **{date_str}**")
                        
                        st.info("⚠️ **Note:** Only the fee record will be deleted. The member will **NOT** be deleted.")
                        
                        if st.button("🚨 Confirm Delete Fee Record", type="primary", use_container_width=True):
                            if hasattr(db, 'delete_fee_record'):
                                ok, msg = db.delete_fee_record(selected_record.id)
                                if ok:
                                    db.log_activity(
                                        user=current_user,
                                        action="FEE_RECORD_DELETED",
                                        details=f"Fee record {selected_record.id} (PKR {selected_record.amount:,.2f}) deleted",
                                        gym_id=sel_gid,
                                        amount=selected_record.amount
                                    )
                                    st.success("✅ Fee record deleted successfully! Member is still in database.")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                            else:
                                # Direct SQL delete if function not available
                                try:
                                    import sqlite3
                                    conn = sqlite3.connect('gym_app.db')
                                    cursor = conn.cursor()
                                    cursor.execute("DELETE FROM fee_records WHERE id = ?", (selected_record.id,))
                                    conn.commit()
                                    conn.close()
                                    
                                    db.log_activity(
                                        user=current_user,
                                        action="FEE_RECORD_DELETED",
                                        details=f"Fee record {selected_record.id} (PKR {selected_record.amount:,.2f}) deleted via SQL",
                                        gym_id=sel_gid,
                                        amount=selected_record.amount
                                    )
                                    st.success("✅ Fee record deleted successfully! Member is still in database.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting fee record: {str(e)}")
        else:
            st.info("No fee records found in database.")
    else:
        st.warning("🔒 Only Admin can access this section.")


# ============================================
# TAB 3: SHIFT MANAGEMENT
# ============================================

def render_shift_management(gym_id, role, current_user):
    st.markdown("### 💼 Shift Cash Management")
    st.caption("Shift start mein opening cash declare karein, shift end mein actual cash submit karein.")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Pehle gym add karein.")
        return

    user = db.get_user_by_username(current_user)
    
    if user and user.role.lower() == "staff" and user.gym_id:
        sel_gid = user.gym_id
        staff_gym = db.get_gym(user.gym_id)
        st.text_input("🏋️ Gym", value=staff_gym.name if staff_gym else "Assigned Gym", disabled=True, key="shift_gym_display")
    elif gym_id:
        sel_gid = gym_id
    else:
        opts = {g.name: g.id for g in gyms}
        sel_gid = opts[st.selectbox("🏋️ Gym", list(opts.keys()), key="shift_gym")]

    active = db.get_active_shift(sel_gid, current_user)

    col_open, col_close = st.columns(2)

    with col_open:
        st.markdown("""
        <div style="background:#0F172A;border:2px solid #34D399;border-radius:12px;padding:1rem;">
        <div style="color:#34D399;font-weight:700;font-size:1rem;margin-bottom:0.5rem;">▶️ Shift Shuru Karein</div>
        """, unsafe_allow_html=True)
        if active:
            opened_str = active.opened_at.strftime('%d %b %Y %H:%M') if active.opened_at else "—"
            st.success(f"✅ Aapki shift {opened_str} se open hai")
            st.caption(f"Opening cash: PKR {active.opening_cash:,.0f}")
        else:
            with st.form("open_shift_form", clear_on_submit=True):
                opening_cash = st.number_input("Opening Cash (PKR)", min_value=0.0, value=0.0, step=100.0, key="shift_open_cash")
                if st.form_submit_button("▶️ Shift Shuru Karein", type="primary", use_container_width=True):
                    ok, result = db.open_shift(sel_gid, current_user, role, opening_cash)
                    if ok:
                        st.success("✅ Shift shuru ho gayi!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_close:
        st.markdown("""
        <div style="background:#0F172A;border:2px solid #F87171;border-radius:12px;padding:1rem;">
        <div style="color:#F87171;font-weight:700;font-size:1rem;margin-bottom:0.5rem;">⏹️ Shift Band Karein</div>
        """, unsafe_allow_html=True)
        if active:
            with st.form("close_shift_form", clear_on_submit=True):
                closing_cash = st.number_input("Actual Cash on Hand (PKR)", min_value=0.0, value=0.0, step=100.0, key="shift_close_cash")
                st.caption("Shift ke douran collect ki gayi saari fees + opening cash = expected amount")
                if st.form_submit_button("⏹️ Shift Band Karein", type="primary", use_container_width=True):
                    ok, result = db.close_shift(active.id, closing_cash)
                    if ok:
                        exp = result["expected"]
                        diff = result["discrepancy"]
                        stat = result["status"]
                        if stat == "flagged":
                            st.error(f"🚨 DISCREPANCY! Expected: PKR {exp:,.0f} | Submitted: PKR {closing_cash:,.0f} | SHORT: PKR {abs(diff):,.0f}")
                        else:
                            st.success(f"✅ Shift band! Expected: PKR {exp:,.0f} | Submitted: PKR {closing_cash:,.0f} ✔️")
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
        else:
            st.info("Pehle shift shuru karein.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 📋 Aaj Ki Shifts")
    try:
        all_shifts = db.get_today_shifts(gym_id=sel_gid)
        if role not in ["admin", "owner"]:
            all_shifts = [s for s in all_shifts if s.staff_user == current_user]

        if all_shifts:
            rows_html = ""
            for s in all_shifts:
                status_map = {
                    "open":    ("#34D399", "#065F46", "🟢 Open"),
                    "closed":  ("#60A5FA", "#1E3A5F", "✅ Closed"),
                    "flagged": ("#F87171", "#7F1D1D", "🚨 Flagged"),
                }
                sc, sbg, slabel = status_map.get(s.status, ("#94A3B8", "#1E293B", s.status))
                diff_str = ""
                if s.discrepancy is not None and s.status != "open":
                    color = "#34D399" if s.discrepancy >= 0 else "#F87171"
                    sign = "+" if s.discrepancy >= 0 else ""
                    diff_str = f'<span style="color:{color};font-weight:700;">{sign}PKR {s.discrepancy:,.0f}</span>'

                opened_str = s.opened_at.strftime('%H:%M') if s.opened_at else "—"
                closed_str = s.closed_at.strftime('%H:%M') if s.closed_at else "—"
                expected_str = f"PKR {s.expected_cash:,.0f}" if s.expected_cash is not None else "—"
                closing_str = f"PKR {s.closing_cash:,.0f}" if s.closing_cash is not None else "—"

                rows_html += f"""
                <tr style="border-bottom:1px solid #1E293B;">
                    <td style="padding:0.5rem 0.75rem;color:#F8FAFC;font-weight:600;">{s.staff_user}</td>
                    <td style="padding:0.5rem 0.75rem;color:#94A3B8;">{opened_str}</td>
                    <td style="padding:0.5rem 0.75rem;color:#94A3B8;">{closed_str}</td>
                    <td style="padding:0.5rem 0.75rem;color:#34D399;font-weight:700;">PKR {s.opening_cash:,.0f}</td>
                    <td style="padding:0.5rem 0.75rem;color:#FBBF24;font-weight:700;">{expected_str}</td>
                    <td style="padding:0.5rem 0.75rem;color:#F8FAFC;">{closing_str}</td>
                    <td style="padding:0.5rem 0.75rem;">{diff_str}</td>
                    <td style="padding:0.5rem 0.75rem;"><span style="background:{sbg};color:{sc};padding:0.2rem 0.5rem;border-radius:6px;font-size:0.75rem;font-weight:700;">{slabel}</span></td>
                </tr>"""

            st.markdown(f"""
            <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;background:#0F172A;border-radius:8px;overflow:hidden;">
                <thead>
                    <tr style="background:#1E3A5F;">
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:left;">Staff</th>
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;">Open</th>
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;">Close</th>
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;">Opening Cash</th>
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;">Expected</th>
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;">Submitted</th>
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;">Difference</th>
                        <th style="padding:0.6rem 0.75rem;color:#60A5FA;">Status</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aaj koi shift record nahi.")
    except Exception as e:
        st.warning(f"Shifts load nahi ho sake: {e}")


# ============================================
# TAB 4: RECEIPT AUDIT LOG
# ============================================

def render_receipt_audit(gym_id):
    st.subheader("📊 Receipt Audit Log")
    st.caption("Every fee payment is logged here.")

    try:
        logs = db.get_receipt_logs(gym_id=gym_id)
    except Exception as e:
        st.error(f"Could not load receipt logs: {e}")
        return

    if not logs:
        st.info("No receipt logs yet.")
        return

    df = pd.DataFrame(logs)
    df = df.rename(columns={
        "receipt_number": "Receipt No",
        "member_name": "Member",
        "amount": "Amount (PKR)",
        "collected_by": "Collected By",
        "pay_date": "Date",
        "pay_time": "Time",
        "print_issued": "Print Issued",
    })
    df["Print Issued"] = df["Print Issued"].map({True: "YES", False: "NO"})

    total = len(df)
    printed = (df["Print Issued"] == "YES").sum()
    not_printed = total - printed

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Receipts", total)
    m2.metric("Printed", printed)
    m3.metric("Not Printed", not_printed)

    st.dataframe(
        df[["Receipt No", "Member", "Amount (PKR)", "Date", "Time", "Collected By", "Print Issued"]],
        use_container_width=True,
        hide_index=True,
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv, file_name="receipt_audit_log.csv", mime="text/csv")


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role, current_user):
    """Main render function - called from app.py"""
    
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                border:1px solid #7C3AED;border-radius:16px;
                padding:1.2rem 1.5rem;margin-bottom:1.2rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
            <div>
                <div style="font-size:1.8rem;font-weight:800;color:#FFFFFF;">💰 Fee Collection</div>
                <div style="color:#94A3B8;font-size:0.85rem;">Collect membership fees and manage payment records</div>
            </div>
            <div style="text-align:right;">
                <div style="color:#7C3AED;font-size:0.7rem;font-weight:600;">📅 {datetime.now().strftime('%A, %d %B %Y')}</div>
                <div style="color:#64748B;font-size:0.7rem;">🕐 {datetime.now().strftime('%I:%M %p')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.get('view_member_history'):
        member_id = st.session_state['view_member_history']
        render_member_payment_history(member_id, gym_id)
        if st.button("🔙 Back to Fee Collection"):
            del st.session_state['view_member_history']
            st.rerun()
        return
    
    tabs = ["📝 Collect Fee", "📋 History & Admin", "💼 Shift Management", "📸 OCR Matcher"]
    if role == 'admin':
        tabs.append("📊 Receipt Audit Log")
    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        render_collect_fee(gym_id, current_user)

    with tab_objs[1]:
        render_history_admin(gym_id, role, current_user)

    with tab_objs[2]:
        render_shift_management(gym_id, role, current_user)

    with tab_objs[3]:
        render_ocr_member_matcher(gym_id, current_user)

    if role == 'admin' and len(tab_objs) > 4:
        with tab_objs[4]:
            render_receipt_audit(gym_id)