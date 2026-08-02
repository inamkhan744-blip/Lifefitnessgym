# fee_collection.py - ULTIMATE PROFESSIONAL VERSION
# WITH ALL FEATURES INCLUDED + FIXED CHARTS + FIXED FILTERS

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
# SHOW MEMBER PHOTO (BIGGER SIZE)
# ============================================

def show_member_photo(photo_path, serial_number="", width=200, height=250):
    """Display member photo with orientation fix - BIGGER SIZE"""
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
# MEMBER PAYMENT STATUS HELPER - FIXED
# ============================================

def get_member_payment_status(member):
    """FIXED: Check actual fee records, not just expiry date"""
    if not member or not hasattr(member, 'id'):
        return "unpaid", "No data", "#F59E0B", "#1E293B"
    
    try:
        # 🔥 Check fee records first
        fee_records = db.get_fee_records(member_id=member.id, limit=1)
        
        if fee_records:
            latest_fee = fee_records[0]
            if hasattr(latest_fee, 'period_end') and latest_fee.period_end:
                try:
                    period_end = pd.to_datetime(latest_fee.period_end).date()
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
        
        # No fee record found - check expiry date as fallback
        if hasattr(member, 'expiry_date') and member.expiry_date:
            try:
                expiry = pd.to_datetime(member.expiry_date).date()
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
# 📊 COLLECTION SUMMARY CARDS
# ============================================

def render_collection_summary(sel_gym_id, date_from, date_to, gyms=None):
    """Render collection summary cards at top - supports All Gyms"""
    
    # 🔥 If All Gyms, get all records
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
    
    # Today's collection
    today = date.today()
    if sel_gym_id is None and gyms:
        today_records = []
        for g in gyms:
            recs = db.get_fee_records(gym_id=g.id, date_from=today, date_to=today)
            today_records.extend(recs)
    else:
        today_records = db.get_fee_records(gym_id=sel_gym_id, date_from=today, date_to=today)
    today_total = sum(r.amount for r in today_records)
    
    # This month's collection
    month_start = today.replace(day=1)
    if sel_gym_id is None and gyms:
        month_records = []
        for g in gyms:
            recs = db.get_fee_records(gym_id=g.id, date_from=month_start, date_to=today)
            month_records.extend(recs)
    else:
        month_records = db.get_fee_records(gym_id=sel_gym_id, date_from=month_start, date_to=today)
    month_total = sum(r.amount for r in month_records)
    
    # Count by status
    if sel_gym_id is None and gyms:
        all_members = []
        for g in gyms:
            all_members.extend(db.get_members(gym_id=g.id))
    else:
        all_members = db.get_members(gym_id=sel_gym_id)
    
    paid_count = 0
    unpaid_count = 0
    upcoming_count = 0
    
    for m in all_members:
        status_type, _, _, _ = get_member_payment_status(m)
        if status_type == "paid":
            paid_count += 1
        elif status_type == "unpaid":
            unpaid_count += 1
        elif status_type == "upcoming":
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
# 📈 COLLECTION TREND CHART
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
# 💳 PAYMENT METHOD DISTRIBUTION
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
# 📋 STAFF PERFORMANCE SUMMARY
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
# 📊 GYM-WISE COMPARISON - FIXED
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
    
    # 🔥 FIXED: Removed 'gradient' property
    colors = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#EF4444', '#06B6D4']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_gym['Gym'],
        y=df_gym['Collection'],
        marker=dict(
            color=colors[:len(df_gym)]
        ),
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
# 🏆 STAFF RANKING
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
# 📋 TOP PAYING MEMBERS
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
# TAB 1: COLLECT FEE - PROFESSIONAL WITH FIXED FILTERS
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

    # 🔥 FIXED: Admin ko All Gyms option mile
    user = db.get_user_by_username(current_user)
    
    # Build gym options based on role
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

    # ── 🔥 Date Range Filter ──────────────────────────────────────────────────
    if 'cf_date_from' not in st.session_state:
        st.session_state['cf_date_from'] = date.today().replace(day=1)
    if 'cf_date_to' not in st.session_state:
        st.session_state['cf_date_to'] = date.today()
    
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        date_from = st.date_input(
            "📅 From Date", 
            value=st.session_state['cf_date_from'], 
            key="cf_date_from_input"
        )
        st.session_state['cf_date_from'] = date_from
    with col_date2:
        date_to = st.date_input(
            "📅 To Date", 
            value=st.session_state['cf_date_to'], 
            key="cf_date_to_input"
        )
        st.session_state['cf_date_to'] = date_to
    
    # ── 🔥 Quick Filters ────────────────────────────────────────────────────
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
            gym_sel = st.selectbox(
                "🏋️ Gym *",
                list(gym_opts.keys()),
                index=list(gym_opts.keys()).index(default_gym_name) if default_gym_name in gym_opts else 0,
                key="cf_gym_sel"
            )
            sel_gym_id = gym_opts[gym_sel]
            gym_sel_name = gym_sel
        
        if sel_gym_id is None:
            all_members = []
            for g in gyms:
                all_members.extend(db.get_members(gym_id=g.id))
            members = all_members
            st.info(f"📊 Showing members from ALL gyms ({len(members)} total)")
        else:
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

        # ── 🔥 FIXED FILTER LOGIC ──
        st.markdown("**Filter by Status:**")
        status_filter = st.radio(
            "Filter by Status",
            ["All Members", "✅ Paid", "⏳ Unpaid", "🟡 Upcoming"],
            horizontal=True,
            key="status_filter",
            label_visibility="collapsed",
        )
        
        if status_filter == "✅ Paid":
            paid_members_list = []
            for m in filtered_members:
                fee_records = db.get_fee_records(member_id=m.id, limit=1)
                if fee_records:
                    latest = fee_records[0]
                    if hasattr(latest, 'period_end') and latest.period_end:
                        try:
                            if pd.to_datetime(latest.period_end).date() >= date.today():
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
                            if pd.to_datetime(latest.period_end).date() < date.today():
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
                            days_left = (pd.to_datetime(latest.period_end).date() - date.today()).days
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
                        if pd.to_datetime(latest.period_end).date() >= date.today():
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
                        period_end = pd.to_datetime(latest.period_end).date()
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
            
            if not fee_records:
                st.warning("⚠️ This member has no fee record yet. Collect fee to activate.")
            
            # 🔥 Quick Renew Button
            if sel_mem.expiry_date:
                try:
                    exp = pd.to_datetime(sel_mem.expiry_date).date()
                    if exp < date.today():
                        if st.button("🔄 Quick Renew", type="secondary", use_container_width=True):
                            st.session_state['renew_member'] = sel_mem.id
                            st.rerun()
                except:
                    pass

    with st.form("collect_fee_form", clear_on_submit=True):
        st.markdown("---")
        st.subheader("💳 Payment Details")
        
        f_c1, f_c2 = st.columns(2)

        with f_c1:
            if sel_mem and hasattr(sel_mem, 'fee_amount') and sel_mem.fee_amount and sel_mem.fee_amount > 0:
                default_amount = float(sel_mem.fee_amount)
            else:
                default_amount = 0.01
            
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
            
            expiry_info = ""
            if sel_mem and sel_mem.expiry_date:
                try:
                    current_expiry = pd.to_datetime(sel_mem.expiry_date).date()
                    if current_expiry > date.today():
                        expiry_info = f" (Current expiry: {current_expiry})"
                except:
                    pass
            
            period_end = st.date_input(
                f"📅 Period End{expiry_info}", 
                value=default_end, 
                key="cf_period_end",
                help="⏰ Default: 30 days from today. Manually change for 2 months, 3 months, etc."
            )

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
                    member_id=member_id, gym_id=sel_gym_id if sel_gym_id else sel_mem.gym_id, 
                    amount=amount,
                    payment_method=payment_method, payment_date=payment_date,
                    period_start=period_start, period_end=period_end,
                    collected_by=current_user, notes=notes
                )

                if ok:
                    db.update_member(member_id, expiry_date=str(period_end), status="Active")
                    try:
                        db.log_activity(
                            user=current_user, action="FEE_COLLECTED",
                            details=f"Member: {sel_mem.full_name} ({sel_mem.serial_number}) | Method: {payment_method} | Period: {period_start} → {period_end}",
                            gym_id=sel_gym_id if sel_gym_id else sel_mem.gym_id, 
                            amount=amount,
                            record_ref=generated_rcp,
                        )
                    except Exception:
                        pass

                    receipt_no = generated_rcp

                    receipt_data = {
                        'gym_name':     gym_sel_name if gym_sel_name else "Gym",
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
                                gym_id=sel_gym_id if sel_gym_id else sel_mem.gym_id,
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

                    st.success(f"✅ Payment recorded! Receipt: {receipt_no}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ============================================
# TAB 2: HISTORY & ADMIN - WITH ALL FEATURES
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
    
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        if user and user.role.lower() == "staff" and user.gym_id:
            staff_gym = db.get_gym(user.gym_id)
            sel_gid = user.gym_id
            st.text_input("🏋️ Gym", value=staff_gym.name if staff_gym else "Assigned Gym", disabled=True, key="fc_gym_display_staff")
        elif user and user.role.lower() in ["admin", "owner"]:
            gym_sel = st.selectbox(
                "🏋️ Select Gym",
                list(gym_opts.keys()),
                key="fc_gym_admin"
            )
            sel_gid = gym_opts[gym_sel]
        elif gym_id:
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

    # ── 🔥 Render Summary Cards ──────────────────────────────────────────────
    records = render_collection_summary(sel_gid, date_from, date_to, gyms)

    # ── 🔥 Staff Performance ──────────────────────────────────────────────────
    if user and user.role.lower() == "staff":
        render_staff_performance(records, current_user)

    # ── 🔥 Charts Row ────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns([2, 1])
    with chart_col1:
        render_collection_chart(records)
    with chart_col2:
        render_payment_method_chart(records)
    
    # ── 🔥 Gym-wise Comparison ──────────────────────────────────────────────
    if sel_gid is None and gyms and len(gyms) > 1:
        render_gym_comparison(gyms, date_from, date_to)
    
    # ── 🔥 Staff Ranking ────────────────────────────────────────────────────
    render_staff_ranking(records)
    
    # ── 🔥 Top Paying Members ────────────────────────────────────────────────
    render_top_paying_members(records)
    
    st.divider()

    # 🔥 Get members based on selection
    if sel_gid is None and gyms:
        all_members = []
        for g in gyms:
            all_members.extend(db.get_members(gym_id=g.id))
    else:
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

    # ── 🔥 RECENT PAYMENTS WITH DIFFERENCE CHECK ──────────────────────────────
    st.divider()
    st.subheader("🔄 Recent Payments & Difference Check")
    
    recent_records = records
    
    if recent_records:
        # ── 🔍 FIND DIFFERENCE ──────────────────────────────────────────────
        st.markdown("### 🔍 Amount Difference Check")
        
        paid_members_from_status = paid_members
        recent_member_ids = set()
        for r in recent_records:
            if r.member_id:
                recent_member_ids.add(r.member_id)
        
        missing_members = []
        for m in paid_members_from_status:
            if m.id not in recent_member_ids:
                missing_members.append(m)
        
        if missing_members:
            st.warning(f"⚠️ **{len(missing_members)} member(s)** PAID status mein hain lekin recent payments mein nahi:")
            
            missing_data = []
            total_missing = 0
            for m in missing_members:
                fee = m.fee_amount or 0
                total_missing += fee
                missing_data.append({
                    "Serial": m.serial_number,
                    "Name": m.full_name,
                    "Fee": f"PKR {fee:,.0f}",
                    "Expiry": m.expiry_date or "—",
                    "Status": "⚠️ No recent payment"
                })
            
            st.dataframe(
                pd.DataFrame(missing_data),
                use_container_width=True,
                hide_index=True,
            )
            
            st.markdown(f"""
            <div style="background:#1E293B;border:1px solid #F59E0B;border-radius:8px;
                        padding:0.8rem;text-align:center;margin-top:0.5rem;">
                <span style="color:#94A3B8;">Total Missing Amount: </span>
                <span style="color:#FBBF24;font-weight:700;font-size:1.1rem;">PKR {total_missing:,.0f}</span>
                <span style="color:#64748B;font-size:0.8rem;margin-left:0.5rem;">
                    ({len(missing_members)} members)
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background:#450A0A;border:2px solid #EF4444;border-radius:12px;
                        padding:1rem;text-align:center;margin-top:0.5rem;">
                <span style="color:#FCA5A5;font-weight:700;font-size:1.1rem;">
                    ⚠️ Difference: PKR {total_missing:,.0f}
                </span>
                <span style="color:#94A3B8;font-size:0.8rem;margin-left:1rem;">
                    ({len(missing_members)} members with no recent payment)
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("✅ All paid members have recent payment records!")
        
        st.divider()
        
        st.markdown("### 📋 Recent Payments List")
        
        recent_data = []
        for r in recent_records[:30]:
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
            <span style="color:#94A3B8;">Total Collection: </span>
            <span style="color:#FFC947;font-weight:700;font-size:1.3rem;">PKR {total_collected:,.2f}</span>
            <span style="color:#64748B;font-size:0.8rem;margin-left:1rem;">
                ({len(recent_records)} payments)
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No payments in this period")

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
                col_pic, col_info = st.columns([1.2, 4])
                
                with col_pic:
                    if selected_record['Member']:
                        show_member_photo(
                            selected_record['Member'].photo_path,
                            selected_record['Member'].serial_number,
                            width=180,
                            height=220
                        )
                    else:
                        st.markdown(
                            f"""
                            <div style="width:180px;height:220px;border-radius:16px;
                                        background:#334155;display:flex;align-items:center;
                                        justify-content:center;font-size:60px;color:white;">
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
                                        try:
                                            mem = selected_record.get('Member')
                                            mem_name = mem.full_name if mem else "Unknown"
                                            db.log_activity(
                                                user=current_user, action="FEE_EDITED",
                                                details=f"Receipt: {selected_record['Receipt']} | Member: {mem_name} | New Amount: PKR {new_amount:,.2f} | New End: {new_end}",
                                                gym_id=sel_gid, amount=new_amount,
                                                record_ref=selected_record['Receipt'],
                                            )
                                        except Exception:
                                            pass
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
                                mem = selected_record.get('Member')
                                mem_name = mem.full_name if mem else "Unknown"
                                ok, msg = db.delete_fee_record(selected_record['ID'])
                                if ok:
                                    try:
                                        db.log_activity(
                                            user=current_user, action="FEE_DELETED",
                                            details=f"Receipt: {selected_record['Receipt']} | Member: {mem_name} | Amount: PKR {selected_record['Amount']:,.2f}",
                                            gym_id=sel_gid, amount=selected_record['Amount'],
                                            record_ref=selected_record['Receipt'],
                                        )
                                    except Exception:
                                        pass
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
# SHIFT MANAGEMENT - FIXED for Staff
# ============================================

def render_shift_management(gym_id, role, current_user):
    """Staff opens/closes their cash shift. Admin sees all shifts."""

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
                        exp   = result["expected"]
                        diff  = result["discrepancy"]
                        stat  = result["status"]
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
                    sign  = "+" if s.discrepancy >= 0 else ""
                    diff_str = f'<span style="color:{color};font-weight:700;">{sign}PKR {s.discrepancy:,.0f}</span>'

                opened_str  = s.opened_at.strftime('%H:%M')  if s.opened_at  else "—"
                closed_str  = s.closed_at.strftime('%H:%M')  if s.closed_at  else "—"
                expected_str = f"PKR {s.expected_cash:,.0f}" if s.expected_cash is not None else "—"
                closing_str  = f"PKR {s.closing_cash:,.0f}"  if s.closing_cash  is not None else "—"

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
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role, current_user):
    """Main render function - called from app.py"""
    
    # Professional header
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
    
    tabs = ["📝 Collect Fee", "📋 History & Admin", "💼 Shift Management"]
    if role == 'admin':
        tabs.append("📊 Receipt Audit Log")
    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        render_collect_fee(gym_id, current_user)

    with tab_objs[1]:
        render_history_admin(gym_id, role, current_user)

    with tab_objs[2]:
        render_shift_management(gym_id, role, current_user)

    if role == 'admin' and len(tab_objs) > 3:
        with tab_objs[3]:
            render_receipt_audit(gym_id)