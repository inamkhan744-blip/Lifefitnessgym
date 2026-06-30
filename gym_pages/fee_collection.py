# fee_collection.py - COMPLETE FIXED VERSION

import streamlit as st
import pandas as pd
import io
import os
import uuid
from datetime import date, timedelta, datetime
import database as db
import base64
import object_store

# ============================================
# PIL IMPORT (Image Optimization)
# ============================================

try:
    from PIL import Image, ImageOps, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    st.warning("⚠️ PIL not installed. Run: pip install Pillow")

# ============================================
# PRINTER UTILITY
# ============================================

from printer_utils import (
    format_receipt, render_print_preview,
    render_print_component
)

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
def _get_cached_image(photo_path: str, max_size: tuple = (200, 200), quality: int = 60) -> str | None:
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

def get_photo_b64(photo_field: str, serial_number: str = "", max_size: tuple = (200, 200)) -> str | None:
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
                if img.mode not in ('RGB', 'L'):
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

# ============================================
# SHOW MEMBER PHOTO
# ============================================

def show_member_photo(photo_path, serial_number="", width=140, height=140):
    """Display member photo with orientation fix"""
    photo_b64 = get_photo_b64(photo_path, serial_number, max_size=(width, height))
    
    if photo_b64:
        st.markdown(f"""
        <div style="width:{width}px; height:{height}px; border-radius:12px;
                    border:3px solid #7C3AED; overflow:hidden;
                    background:#1E293B; box-shadow:0 4px 15px rgba(124,58,237,0.3);
                    flex-shrink:0;">
            <img src="{photo_b64}" style="width:100%; height:100%;
                                          object-fit:cover; display:block;
                                          image-orientation:from-image;" />
        </div>
        """, unsafe_allow_html=True)
        return True
    else:
        st.markdown(f"""
        <div style="width:{width}px; height:{height}px; border-radius:12px;
                    background:linear-gradient(135deg,#7C3AED,#6D28D9);
                    display:flex; align-items:center; justify-content:center;
                    font-size:{width//2}px; color:white; font-weight:700;
                    border:3px solid #7C3AED33; flex-shrink:0;">
            👤
        </div>
        """, unsafe_allow_html=True)
        return False

# ============================================
# HELPERS
# ============================================

def get_member_payment_status(member):
    if not member or not hasattr(member, 'expiry_date') or not member.expiry_date:
        return "unpaid", "No expiry", "#F59E0B", "#1E293B"
    
    try:
        expiry = pd.to_datetime(member.expiry_date).date()
        today = date.today()
        
        if expiry >= today:
            days_left = (expiry - today).days
            if days_left <= 7:
                return "upcoming", f"🟡 Upcoming ({days_left}d left)", "#F59E0B", "#1E293B"
            else:
                return "paid", f"✅ Paid ({days_left}d left)", "#10B981", "white"
        else:
            days_expired = (today - expiry).days
            return "unpaid", f"🔴 Unpaid ({days_expired}d ago)", "#EF4444", "white"
    except:
        return "unpaid", "⚠️ Invalid", "#F59E0B", "#1E293B"

# ============================================
# TAB 1: COLLECT FEE
# ============================================

def render_collect_fee(gym_id, current_user):
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    pending = st.session_state.pop('pending_print', None)
    if pending:
        st.success("✅ Payment recorded! Print dialog should open automatically — or press the PRINT button below:")
        render_print_component(pending['data'], copies=pending['copies'])
        st.divider()

    st.subheader("➕ Collect Fee")

    gym_opts = {g.name: g.id for g in gyms}
    default_gym = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)

    c1, c2 = st.columns(2)

    with c1:
        gym_sel = st.selectbox(
            "🏋️ Gym *",
            list(gym_opts.keys()),
            index=list(gym_opts.keys()).index(default_gym),
            key="cf_gym_sel"
        )
        sel_gym_id = gym_opts[gym_sel]
        members = db.get_members(gym_id=sel_gym_id)

        search_query = st.text_input(
            "🔍 Search Member",
            key="cf_search",
            placeholder="Type name or serial number..."
        )

        if search_query:
            q = search_query.lower().strip()
            filtered_members = [
                m for m in members
                if q in m.full_name.lower() or q in str(m.serial_number).lower()
            ]
        else:
            filtered_members = members

        st.markdown("**Filter by Status:**")
        status_filter = st.radio(
            "Filter by Status",
            ["All Members", "✅ Paid", "⏳ Unpaid", "🟡 Upcoming"],
            horizontal=True,
            key="status_filter",
            label_visibility="collapsed",
        )
        
        if status_filter == "✅ Paid":
            filtered_members = [
                m for m in filtered_members 
                if m.expiry_date and pd.to_datetime(m.expiry_date).date() >= date.today() + timedelta(days=7)
            ]
        elif status_filter == "⏳ Unpaid":
            filtered_members = [
                m for m in filtered_members 
                if not m.expiry_date or pd.to_datetime(m.expiry_date).date() < date.today()
            ]
        elif status_filter == "🟡 Upcoming":
            filtered_members = [
                m for m in filtered_members 
                if m.expiry_date and 0 <= (pd.to_datetime(m.expiry_date).date() - date.today()).days <= 7
            ]

        mem_opts = {}
        for m in filtered_members:
            label = f"{m.serial_number} — {m.full_name}"
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
        
        pic_col, info_col = st.columns([1, 3])
        
        with pic_col:
            show_member_photo(sel_mem.photo_path, sel_mem.serial_number, width=140, height=140)
        
        with info_col:
            status_type, status_text, bg_color, text_color = get_member_payment_status(sel_mem)
            
            st.markdown(f"### {sel_mem.full_name}")
            st.caption(f"🔢 {sel_mem.serial_number}")
            
            st.markdown(
                f"<span style='background:{bg_color};color:{text_color};"
                f"padding:4px 12px;border-radius:9999px;font-size:0.8rem;font-weight:600;'>"
                f"{status_text}</span>",
                unsafe_allow_html=True
            )
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.metric("💰 Fee", f"PKR {sel_mem.fee_amount:,.2f}")
            with col_f2:
                st.metric("📅 Expiry", sel_mem.expiry_date or "—")

    with st.form("collect_fee_form", clear_on_submit=True):
        st.markdown("---")
        st.subheader("💳 Payment Details")
        
        f_c1, f_c2 = st.columns(2)

        with f_c1:
            # 🔥 FIXED: Ensure default_amount is never 0
            if sel_mem and hasattr(sel_mem, 'fee_amount') and sel_mem.fee_amount and sel_mem.fee_amount > 0:
                default_amount = float(sel_mem.fee_amount)
            else:
                default_amount = 0.01  # Minimum value
            
            amount = st.number_input(
                "💰 Amount (PKR) *",
                min_value=0.01,
                value=default_amount,
                step=5.0,
                format="%.2f",
                key="cf_amount"
            )
            payment_method = st.selectbox("💳 Payment Method *", db.PAYMENT_METHODS, key="cf_method")

        with f_c2:
            payment_date = st.date_input("📅 Payment Date *", value=date.today(), key="cf_date")
            period_start = st.date_input("📅 Period Start", value=date.today(), key="cf_period_start")
            
            default_end = date.today() + timedelta(days=30)
            if sel_mem and sel_mem.expiry_date:
                try:
                    current_expiry = pd.to_datetime(sel_mem.expiry_date).date()
                    if current_expiry > date.today():
                        default_end = current_expiry + timedelta(days=30)
                except:
                    pass
            
            period_end = st.date_input("📅 Period End", value=default_end, key="cf_period_end")

        notes = st.text_area("📝 Notes (optional)", height=60, key="cf_notes")

        st.markdown("---")
        st.subheader("🖨️ Print Options")
        
        col_print1, col_print2 = st.columns(2)
        with col_print1:
            print_receipt = st.checkbox("🖨️ Print Receipt", value=True, key="cf_print")
        with col_print2:
            print_copies = st.radio(
                "📄 Copies",
                ["2 (Member + Gym)", "1 (Member only)"],
                index=0,
                key="cf_copies"
            )

        submitted = st.form_submit_button(
            "✅ Record Payment & Print Slip",
            type="primary",
            use_container_width=True
        )

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
                    member_id=member_id, gym_id=sel_gym_id, amount=amount,
                    payment_method=payment_method, payment_date=payment_date,
                    period_start=period_start, period_end=period_end,
                    collected_by=current_user, notes=notes
                )

                if ok:
                    db.update_member(member_id, expiry_date=str(period_end), status="Active")

                    receipt_no = generated_rcp

                    receipt_data = {
                        'gym_name':     gym_sel,
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
                    }

                    try:
                        if hasattr(db, 'log_receipt'):
                            db.log_receipt(
                                fee_record_id=None,
                                gym_id=sel_gym_id,
                                member_name=sel_mem.full_name,
                                receipt_number=receipt_no,
                                amount=amount,
                                collected_by=current_user,
                                print_issued=False,
                            )
                        else:
                            import sqlite3
                            conn = sqlite3.connect('gym_app.db')
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO receipt_logs 
                                (member_name, member_id, date, time, amount, receipt_no, print_issued, collected_by)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                sel_mem.full_name,
                                member_id,
                                date.today().strftime('%Y-%m-%d'),
                                datetime.now().strftime('%H:%M'),
                                amount,
                                receipt_no,
                                'No',
                                current_user
                            ))
                            conn.commit()
                            conn.close()
                    except Exception as e:
                        st.warning(f"Receipt logging failed: {e}")

                    if print_receipt:
                        copies = 2 if "2" in print_copies else 1
                        st.session_state['pending_print'] = {
                            'data': receipt_data,
                            'copies': copies,
                        }
                        if hasattr(db, 'update_print_issued'):
                            try:
                                db.update_print_issued(receipt_no, True)
                            except Exception:
                                pass

                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

# ============================================
# TAB 2: HISTORY & ADMIN
# ============================================

def render_history_admin(gym_id, role):
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    st.subheader("📋 Payment History")
    
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        if gym_id:
            sel_gid = gym_id
            st.text_input("🏋️ Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True, key="fc_gym_display")
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("🏋️ Select Gym", list(opts.keys()), key="fc_gym")
            sel_gid = opts[chosen]
    with col_f2:
        date_from = st.date_input("📅 From Date", value=date.today().replace(day=1), key="fc_from")
    with col_f3:
        date_to = st.date_input("📅 To Date", value=date.today(), key="fc_to")

    records = db.get_fee_records(gym_id=sel_gid, date_from=date_from, date_to=date_to)

    all_members = db.get_members(gym_id=sel_gid) if sel_gid else []
    
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
        else:
            upcoming_members.append(member)
            upcoming_total += fee

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

    # ============================================
    # ADMIN PANEL (WITH REPRINT)
    # ============================================
    
    st.divider()
    st.subheader("🔐 Admin Panel")
    st.caption("Edit, delete, or reprint payment records")
    
    if str(role).lower() in ["admin", "owner"]:
        if records:
            admin_rows = []
            for r in records:
                mem = db.get_member(r.member_id)
                admin_rows.append({
                    "ID": r.id,
                    "Receipt": r.receipt_number,
                    "Member": mem,
                    "Member ID": r.member_id,
                    "Amount": r.amount,
                    "Date": r.payment_date,
                    "Method": r.payment_method,
                    "Period End": r.period_end,
                    "Notes": r.notes or "",
                })
            
            record_opts = {}
            for r in admin_rows:
                if r['Member']:
                    label = f"👤 {r['Member'].full_name} — {r['Receipt']} (PKR {r['Amount']:,.2f})"
                else:
                    label = f"❓ Unknown — {r['Receipt']} (PKR {r['Amount']:,.2f})"
                record_opts[label] = r['ID']
            
            selected_label = st.selectbox("Select Record to Manage", list(record_opts.keys()), key="admin_record_select")
            selected_id = record_opts[selected_label]
            selected_record = next((r for r in admin_rows if r['ID'] == selected_id), None)
            
            if selected_record:
                col_pic, col_info = st.columns([1, 4])
                
                with col_pic:
                    if selected_record['Member']:
                        show_member_photo(
                            selected_record['Member'].photo_path,
                            selected_record['Member'].serial_number,
                            width=120,
                            height=120
                        )
                    else:
                        st.markdown(
                            """
                            <div style="width:120px;height:120px;border-radius:50%;
                                        background:#334155;display:flex;align-items:center;
                                        justify-content:center;font-size:40px;color:white;">
                                ?
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                with col_info:
                    if selected_record['Member']:
                        st.markdown(f"### {selected_record['Member'].full_name}")
                        st.caption(f"🔢 {selected_record['Member'].serial_number}")
                        date_str = selected_record['Date']
                        if hasattr(date_str, 'strftime'):
                            date_str = date_str.strftime('%Y-%m-%d')
                        st.caption(f"📅 {date_str} · 💰 PKR {selected_record['Amount']:,.2f}")
                    else:
                        st.markdown("### Unknown Member")
                
                st.markdown("---")
                st.subheader("Reprint Receipt")

                if role == 'admin':
                    mem = selected_record['Member']
                    date_val = selected_record['Date']
                    date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)
                    period_end_val = selected_record['Period End']
                    period_end_str = period_end_val.strftime('%Y-%m-%d') if hasattr(period_end_val, 'strftime') else (str(period_end_val) if period_end_val else "N/A")

                    reprint_data = {
                        'gym_name':     selected_record.get('Gym', 'Gym'),
                        'gym_address':  "",
                        'gym_phone':    "",
                        'receipt_no':   selected_record['Receipt'],
                        'date':         date_str,
                        'time':         datetime.now().strftime('%I:%M %p'),
                        'collected_by': "Admin (Reprint)",
                        'member_name':  mem.full_name if mem else "Unknown",
                        'serial':       mem.serial_number if mem else "N/A",
                        'phone':        mem.phone if mem else "N/A",
                        'amount':       selected_record['Amount'],
                        'method':       selected_record['Method'],
                        'period_start': "N/A",
                        'period_end':   period_end_str,
                    }

                    col_r1, col_r2, col_r3 = st.columns(3)

                    with col_r1:
                        if st.button("Reprint 2 Copies", use_container_width=True, type="primary"):
                            st.session_state['reprint_copies'] = 2
                            st.session_state['reprint_data'] = reprint_data
                            try:
                                db.update_print_issued(selected_record['Receipt'], True)
                            except Exception:
                                pass

                    with col_r2:
                        if st.button("Reprint 1 Copy", use_container_width=True):
                            st.session_state['reprint_copies'] = 1
                            st.session_state['reprint_data'] = reprint_data
                            try:
                                db.update_print_issued(selected_record['Receipt'], True)
                            except Exception:
                                pass

                    with col_r3:
                        if st.button("Print Preview", use_container_width=True):
                            st.session_state['show_reprint_preview'] = not st.session_state.get('show_reprint_preview', False)

                    rp_data = st.session_state.get('reprint_data')
                    rp_copies = st.session_state.get('reprint_copies', 2)
                    if rp_data and rp_data.get('receipt_no') == reprint_data.get('receipt_no'):
                        render_print_component(rp_data, copies=rp_copies)

                    if st.session_state.get('show_reprint_preview', False):
                        render_print_preview(reprint_data, copies=2)
                else:
                    st.info("Reprint is restricted to Admin users only.")
                
                st.divider()
                
                col_edit, col_delete = st.columns(2)
                
                with col_edit:
                    with st.expander("✏️ Edit Record", expanded=False):
                        with st.form("edit_fee_form"):
                            new_amount = st.number_input(
                                "Amount (PKR)", 
                                min_value=0.01, 
                                value=float(selected_record['Amount']), 
                                step=5.0, 
                                format="%.2f"
                            )
                            new_method = st.selectbox(
                                "Payment Method", 
                                db.PAYMENT_METHODS, 
                                index=db.PAYMENT_METHODS.index(selected_record['Method']) if selected_record['Method'] in db.PAYMENT_METHODS else 0
                            )
                            
                            period_end_val = selected_record['Period End']
                            if hasattr(period_end_val, 'strftime'):
                                default_end = period_end_val
                            else:
                                try:
                                    default_end = pd.to_datetime(period_end_val).date() if period_end_val else date.today()
                                except:
                                    default_end = date.today()
                            
                            new_end = st.date_input(
                                "Period End", 
                                value=default_end
                            )
                            new_notes = st.text_area("Notes", value=selected_record['Notes'])
                            
                            if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                                if hasattr(db, 'update_fee_record'):
                                    ok, msg = db.update_fee_record(
                                        selected_record['ID'], 
                                        new_amount, 
                                        new_method, 
                                        None,
                                        new_end, 
                                        new_notes
                                    )
                                    if ok:
                                        db.update_member(selected_record['Member ID'], expiry_date=str(new_end))
                                        st.success("✅ Record updated!")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                                else:
                                    st.error("⚠️ Update function not available")
                
                with col_delete:
                    with st.expander("🗑️ Delete Record", expanded=False):
                        st.warning(f"⚠️ Delete Receipt **{selected_record['Receipt']}**?")
                        st.caption("This cannot be undone!")
                        if st.button("🚨 Confirm Delete", type="primary", use_container_width=True):
                            if hasattr(db, 'delete_fee_record'):
                                ok, msg = db.delete_fee_record(selected_record['ID'])
                                if ok:
                                    st.success("✅ Record deleted!")
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("⚠️ Delete function not available")
        else:
            st.info("No records available to manage.")
    else:
        st.warning("🔒 Only Admin can access this section.")

# ============================================
# RECEIPT AUDIT LOG (Admin only)
# ============================================

def render_receipt_audit(gym_id):
    st.subheader("Receipt Audit Log")
    st.caption("Every fee payment is logged here. PrintIssued = Yes means receipt was physically printed.")

    try:
        logs = db.get_receipt_logs(gym_id=gym_id)
    except Exception as e:
        st.error(f"Could not load receipt logs: {e}")
        return

    if not logs:
        st.info("No receipt logs yet. Logs appear after fee payments are recorded.")
        return

    import pandas as pd
    df = pd.DataFrame(logs)
    df = df.rename(columns={
        "receipt_number": "Receipt No",
        "member_name":    "Member",
        "amount":         "Amount (PKR)",
        "collected_by":   "Collected By",
        "pay_date":       "Date",
        "pay_time":       "Time",
        "print_issued":   "Print Issued",
    })
    df["Print Issued"] = df["Print Issued"].map({True: "YES", False: "NO"})

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_print = st.selectbox("Filter by Print Issued", ["All", "YES", "NO"], key="al_filter")
    with col_f2:
        search_name = st.text_input("Search member", key="al_search")

    if filter_print != "All":
        df = df[df["Print Issued"] == filter_print]
    if search_name:
        df = df[df["Member"].str.contains(search_name, case=False, na=False)]

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
    st.download_button("Download CSV", data=csv, file_name="receipt_audit_log.csv", mime="text/csv")


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role, current_user):
    """Main render function - called from app.py"""
    
    st.title("💰 Fee Collection")
    st.caption("Collect membership fees and manage payment records")
    
    tabs = ["📝 Collect Fee", "📋 History & Admin"]
    if role == 'admin':
        tabs.append("📊 Receipt Audit Log")
    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        render_collect_fee(gym_id, current_user)

    with tab_objs[1]:
        render_history_admin(gym_id, role)

    if role == 'admin' and len(tab_objs) > 2:
        with tab_objs[2]:
            render_receipt_audit(gym_id)