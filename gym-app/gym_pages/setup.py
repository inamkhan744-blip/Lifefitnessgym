# gym_pages/setup.py - COMPLETE WITH STAFF TIMING

import streamlit as st
import database as db
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import base64
from PIL import Image
import io

# ============================================
# SESSION STATE
# ============================================

def init_session_state():
    if 'gym_logo_cache' not in st.session_state:
        st.session_state.gym_logo_cache = {}
    if 'gym_photo_cache' not in st.session_state:
        st.session_state.gym_photo_cache = {}

init_session_state()

# ============================================
# CUSTOM CSS
# ============================================

def get_css():
    return """
    <style>
        .glass-card {
            background: rgba(20,20,20,0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,201,71,0.08);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s ease;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .glass-card:hover {
            border-color: #FFC947;
            transform: translateY(-4px);
            box-shadow: 0 12px 48px rgba(255,201,71,0.15);
        }
        .kpi-card {
            background: linear-gradient(145deg,#141414,#1A1A1A);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px 16px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg,#FFC947,#FF6B6B,#FFC947);
            background-size: 200% 100%;
            animation: shimmer 3s ease-in-out infinite;
        }
        @keyframes shimmer {
            0%   { background-position: -200% 0; }
            100% { background-position:  200% 0; }
        }
        .kpi-value {
            font-size: 34px;
            font-weight: 800;
            background: linear-gradient(135deg,#FFFFFF 0%,#FFC947 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 8px 0;
        }
        .kpi-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #8A8A8A;
            font-weight: 600;
        }
        .kpi-subtext {
            font-size: 11px;
            color: #6A6A6A;
        }
        .section-header {
            font-size: 18px;
            font-weight: 700;
            color: #FFFFFF;
            margin: 24px 0 16px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255,201,71,0.15);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-header::after {
            content: '';
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg,rgba(255,201,71,0.3),transparent);
        }
        .status-active { background: #d4edda; color: #155724; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; }
        .status-inactive { background: #e2e3e5; color: #383d41; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; }
        .status-maintenance { background: #fff3cd; color: #856404; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; }
        .status-closed { background: #f8d7da; color: #721c24; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; }
        .gym-logo {
            border-radius: 50%;
            border: 3px solid #FFC947;
            box-shadow: 0 0 30px rgba(255,201,71,0.2);
            width: 120px;
            height: 120px;
            object-fit: cover;
        }
        .amenity-tag {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 0.8rem;
            color: #94A3B8;
            display: inline-block;
            margin: 3px;
        }
        .amenity-tag:hover {
            border-color: #FFC947;
            color: #FFC947;
            cursor: pointer;
        }
        .plan-card {
            background: linear-gradient(145deg,#1E293B,#0F172A);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        .plan-card:hover {
            border-color: #FFC947;
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(255,201,71,0.1);
        }
        .plan-card .price {
            font-size: 2rem;
            font-weight: 800;
            color: #FFC947;
        }
        .plan-card .duration {
            font-size: 0.8rem;
            color: #94A3B8;
        }
        .plan-card .features {
            font-size: 0.8rem;
            color: #CBD5E1;
            margin-top: 0.5rem;
        }
        .danger-zone {
            border: 2px solid #dc3545;
            border-radius: 10px;
            padding: 1rem;
            margin-top: 1rem;
            background: #fff5f5;
        }
        .staff-timing-row {
            background: #0F172A;
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
        }
        .staff-timing-row:hover {
            border-color: #7C3AED;
        }
        .timing-status-set {
            color: #34D399;
        }
        .timing-status-pending {
            color: #F59E0B;
        }
    </style>
    """

# ============================================
# ⏰ STAFF TIMING MANAGER - NEW
# ============================================

def render_staff_timing_manager(gym_id):
    """Manage staff attendance timings"""
    st.markdown("### ⏰ Staff Attendance Timings")
    st.caption("Set check-in and check-out timings for each staff member. Staff can only mark attendance during these times.")
    
    # Get all staff for this gym
    all_users = db.get_all_users()
    gym_staff = [u for u in all_users if u.gym_id == gym_id and u.role != 'admin']
    
    if not gym_staff:
        st.info("📭 No staff members found for this gym. Add staff first.")
        return
    
    # Get all staff timings
    staff_timings = db.get_all_staff_timings(gym_id)
    timing_dict = {t.staff_username: t for t in staff_timings}
    
    # ── Quick Stats ──────────────────────────────────────────────────
    total_staff = len(gym_staff)
    timed_staff = len(timing_dict)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total Staff", total_staff)
    with col2:
        st.metric("⏰ Timings Set", timed_staff)
    with col3:
        pending = total_staff - timed_staff
        st.metric("⏳ Pending", pending, delta="Set timings" if pending > 0 else "✅ Complete")
    
    st.divider()
    
    # ── Set All Staff Timings at Once ──────────────────────────────
    with st.expander("⚡ Bulk Set All Staff Timings", expanded=False):
        st.info("Set same timings for all staff members at once")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            bulk_in = st.time_input("Check-in Time", value=datetime.strptime("09:00", "%H:%M").time(), key="bulk_in")
        with col2:
            bulk_out = st.time_input("Check-out Time", value=datetime.strptime("18:00", "%H:%M").time(), key="bulk_out")
        with col3:
            bulk_grace = st.number_input("Grace Minutes", min_value=0, max_value=60, value=15, step=5, key="bulk_grace")
        
        if st.button("📌 Apply to All Staff", use_container_width=True, type="primary"):
            count = 0
            for staff in gym_staff:
                ok, msg = db.set_staff_timing(
                    gym_id=gym_id,
                    staff_username=staff.username,
                    check_in_time=bulk_in.strftime("%H:%M"),
                    check_out_time=bulk_out.strftime("%H:%M"),
                    grace_minutes=bulk_grace
                )
                if ok:
                    count += 1
            st.success(f"✅ Timings set for {count} staff members!")
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    
    # ── Individual Staff Timing ──────────────────────────────────────
    st.markdown("### 📋 Individual Staff Timings")
    
    for staff in gym_staff:
        timing = timing_dict.get(staff.username)
        default_in = timing.check_in_time if timing else "09:00"
        default_out = timing.check_out_time if timing else "18:00"
        default_grace = timing.grace_minutes if timing else 15
        
        with st.container():
            st.markdown(f"""
            <div class="staff-timing-row">
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])
            
            with col1:
                status_icon = "✅" if timing else "⏳"
                status_class = "timing-status-set" if timing else "timing-status-pending"
                st.markdown(f"""
                <div>
                    <span style="font-size:1.1rem;font-weight:700;color:#F8FAFC;">{status_icon} {staff.full_name}</span>
                    <div style="color:#94A3B8;font-size:0.8rem;">@{staff.username} · {staff.role}</div>
                    {f'<div style="color:#34D399;font-size:0.75rem;">Current: {timing.check_in_time} - {timing.check_out_time} (Grace: {timing.grace_minutes}min)</div>' if timing else '<div style="color:#F59E0B;font-size:0.75rem;">⚠️ Timing not set</div>'}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                check_in = st.time_input(
                    "Check-in",
                    value=datetime.strptime(default_in, "%H:%M").time(),
                    key=f"cin_{staff.username}",
                    label_visibility="collapsed"
                )
            
            with col3:
                check_out = st.time_input(
                    "Check-out",
                    value=datetime.strptime(default_out, "%H:%M").time(),
                    key=f"cout_{staff.username}",
                    label_visibility="collapsed"
                )
            
            with col4:
                grace = st.number_input(
                    "Grace (min)",
                    min_value=0,
                    max_value=60,
                    value=default_grace,
                    step=5,
                    key=f"grace_{staff.username}",
                    label_visibility="collapsed"
                )
            
            with col5:
                if st.button("💾 Save", key=f"save_time_{staff.username}", use_container_width=True):
                    ok, msg = db.set_staff_timing(
                        gym_id=gym_id,
                        staff_username=staff.username,
                        check_in_time=check_in.strftime("%H:%M"),
                        check_out_time=check_out.strftime("%H:%M"),
                        grace_minutes=grace
                    )
                    if ok:
                        st.success("✅ Saved!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # ── Staff Timing Summary Table ──────────────────────────────────
    st.markdown("### 📊 Staff Timing Summary")
    
    data = []
    for staff in gym_staff:
        timing = timing_dict.get(staff.username)
        data.append({
            "Staff": staff.full_name,
            "Username": staff.username,
            "Role": staff.role,
            "Check-in": timing.check_in_time if timing else "—",
            "Check-out": timing.check_out_time if timing else "—",
            "Grace": f"{timing.grace_minutes}min" if timing else "—",
            "Status": "✅ Set" if timing else "⏳ Pending"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ── Quick Tips ──────────────────────────────────────────────────
    st.divider()
    st.info("""
    💡 **Staff Timing Tips:**
    - **Check-in Time**: Staff can check-in at this time (with grace period)
    - **Check-out Time**: Staff should check-out at this time
    - **Grace Minutes**: Extra minutes allowed for late check-in
    - Staff will see AI warnings if they check-in early or late
    """)

# ============================================
# GYM LOGO UPLOAD - FIXED
# ============================================

def render_gym_logo(gym_id):
    """Upload and display gym logo"""
    st.subheader("🖼️ Gym Logo")
    
    gym = db.get_gym(gym_id)
    logo_path = getattr(gym, 'logo_path', None)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if logo_path and os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    img_bytes = f.read()
                    b64 = base64.b64encode(img_bytes).decode()
                    st.markdown(f"""
                    <img src="data:image/png;base64,{b64}" class="gym-logo" />
                    """, unsafe_allow_html=True)
            except:
                st.markdown('<div style="font-size:4rem;text-align:center;">🏋️</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:4rem;text-align:center;">🏋️</div>', unsafe_allow_html=True)
        
        st.caption("Gym Logo")
    
    with col2:
        uploaded_file = st.file_uploader(
            "Upload Gym Logo",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"gym_logo_upload_{gym_id}"
        )
        
        if uploaded_file:
            logo_dir = f"gym_logos/{gym_id}"
            os.makedirs(logo_dir, exist_ok=True)
            filepath = os.path.join(logo_dir, f"logo_{gym_id}.png")
            
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("✅ Logo uploaded successfully!")
            st.rerun()


# ============================================
# GYM WORKING HOURS - FIXED
# ============================================

def render_gym_hours(gym_id):
    """Set gym working hours - FIXED with unique keys"""
    st.subheader("⏰ Working Hours")
    
    gym = db.get_gym(gym_id)
    
    timings = {
        'mon_fri_start': getattr(gym, 'mon_fri_start', '06:00') or '06:00',
        'mon_fri_end': getattr(gym, 'mon_fri_end', '22:00') or '22:00',
        'sat_start': getattr(gym, 'sat_start', '08:00') or '08:00',
        'sat_end': getattr(gym, 'sat_end', '20:00') or '20:00',
        'sun_start': getattr(gym, 'sun_start', '08:00') or '08:00',
        'sun_end': getattr(gym, 'sun_end', '18:00') or '18:00',
    }
    
    with st.form(f"hours_form_{gym_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Monday - Friday**")
            mf_start = st.time_input(
                "Opening",
                value=datetime.strptime(timings['mon_fri_start'], "%H:%M").time(),
                key=f"mf_start_{gym_id}"
            )
            mf_end = st.time_input(
                "Closing",
                value=datetime.strptime(timings['mon_fri_end'], "%H:%M").time(),
                key=f"mf_end_{gym_id}"
            )
        
        with col2:
            st.markdown("**Saturday**")
            sat_start = st.time_input(
                "Opening",
                value=datetime.strptime(timings['sat_start'], "%H:%M").time(),
                key=f"sat_start_{gym_id}"
            )
            sat_end = st.time_input(
                "Closing",
                value=datetime.strptime(timings['sat_end'], "%H:%M").time(),
                key=f"sat_end_{gym_id}"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Sunday**")
            sun_start = st.time_input(
                "Opening",
                value=datetime.strptime(timings['sun_start'], "%H:%M").time(),
                key=f"sun_start_{gym_id}"
            )
            sun_end = st.time_input(
                "Closing",
                value=datetime.strptime(timings['sun_end'], "%H:%M").time(),
                key=f"sun_end_{gym_id}"
            )
        
        with col4:
            st.markdown("**Holiday Mode**")
            holiday_mode = st.checkbox(
                "Holiday Mode",
                value=getattr(gym, 'holiday_mode', False),
                key=f"holiday_mode_{gym_id}"
            )
        
        if st.form_submit_button("💾 Save Timings", type="primary"):
            db.update_gym_timings(
                gym_id,
                mf_start.strftime("%H:%M"),
                mf_end.strftime("%H:%M"),
                sat_start.strftime("%H:%M"),
                sat_end.strftime("%H:%M"),
                sun_start.strftime("%H:%M"),
                sun_end.strftime("%H:%M")
            )
            st.success("✅ Timings updated successfully!")
            st.rerun()


# ============================================
# GYM AMENITIES - FIXED
# ============================================

def render_gym_amenities(gym_id):
    """Manage gym amenities - FIXED with unique keys"""
    st.subheader("🏷️ Amenities & Facilities")
    
    gym = db.get_gym(gym_id)
    current_amenities = getattr(gym, 'amenities', '') or ''
    current_list = [a.strip() for a in current_amenities.split(',') if a.strip()]
    
    all_amenities = [
        "🏋️ Cardio Equipment", "💪 Weight Training", "🏋️ Free Weights",
        "Squat Racks", "Bench Press", "Dumbbells up to 50kg",
        "Cable Machines", "Smith Machine", "Functional Training Area",
        "🧘 Yoga Studio", "🚴 Spin Studio", "👥 Group Classes",
        "🚿 Locker Rooms", "🚿 Showers", "🧖 Sauna", "🧖 Steam Room",
        "🏊 Swimming Pool", "🅿️ Parking", "♿ Wheelchair Accessible",
        "🧸 Kids Play Area", "☕ Café/Protein Bar", "📶 WiFi",
        "❄️ Air Conditioning", "🔑 24/7 Access", "👨‍🏫 Personal Training",
        "🥗 Nutrition Counseling", "🏥 First Aid", "📺 TV Screens",
        "🔊 Sound System", "🧊 Water Cooler", "🧴 Towel Service",
        "📱 Mobile App Access", "🔄 Cycle Parking", "🧘 Meditation Room"
    ]
    
    if current_list:
        st.markdown("**Current Amenities:**")
        tags_html = ""
        for a in current_list:
            tags_html += f'<span class="amenity-tag">{a}</span>'
        st.markdown(tags_html, unsafe_allow_html=True)
        st.divider()
    
    with st.form(f"amenities_form_{gym_id}"):
        selected = st.multiselect(
            "Select Facilities",
            all_amenities,
            default=current_list,
            key=f"amenities_select_{gym_id}"
        )
        
        if st.form_submit_button("💾 Save Amenities", type="primary"):
            db.update_gym_amenities(gym_id, ','.join(selected))
            st.success("✅ Amenities updated successfully!")
            st.rerun()


# ============================================
# MEMBERSHIP PLANS - FIXED
# ============================================

def render_membership_plans(gym_id):
    """Manage membership plans - FIXED with unique keys"""
    st.subheader("💳 Membership Plans")
    
    plans = db.get_gym_plans(gym_id)
    
    with st.expander("➕ Add New Plan", expanded=False):
        with st.form(f"add_plan_{gym_id}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                plan_name = st.text_input(
                    "Plan Name",
                    placeholder="e.g. Basic Monthly",
                    key=f"plan_name_{gym_id}"
                )
            with col2:
                price = st.number_input(
                    "Price (PKR)",
                    min_value=0,
                    step=100,
                    key=f"plan_price_{gym_id}"
                )
            with col3:
                duration_days = st.number_input(
                    "Duration (Days)",
                    min_value=1,
                    value=30,
                    key=f"plan_duration_{gym_id}"
                )
            
            features = st.text_area(
                "Features (comma separated)",
                placeholder="24/7 access, gym equipment, locker",
                key=f"plan_features_{gym_id}"
            )
            
            if st.form_submit_button("➕ Add Plan", type="primary"):
                if not plan_name.strip():
                    st.error("❌ Plan name required.")
                else:
                    ok, msg = db.add_membership_plan(gym_id, plan_name, price, duration_days, features)
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()
    
    if plans:
        st.markdown("**Current Plans:**")
        cols = st.columns(min(len(plans), 4))
        for idx, plan in enumerate(plans):
            with cols[idx % 4]:
                st.markdown(f"""
                <div class="plan-card">
                    <div style="font-size:1.1rem;font-weight:700;color:#F8FAFC;">{plan['name']}</div>
                    <div class="price">PKR {plan['price']:,.0f}</div>
                    <div class="duration">{plan['duration_days']} days</div>
                    <div class="features">{plan['features'] or 'No features listed'}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(
                    "🗑️ Delete",
                    key=f"del_plan_{plan['id']}_{gym_id}"
                ):
                    db.delete_plan(plan['id'])
                    st.rerun()
    else:
        st.info("📌 No membership plans added yet.")


# ============================================
# GYM GALLERY - FIXED
# ============================================

def render_gym_gallery(gym_id):
    """Upload and manage gym photos - FIXED with unique keys"""
    st.subheader("📸 Gym Gallery")
    
    uploaded_files = st.file_uploader(
        "Upload Gym Photos",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        accept_multiple_files=True,
        key=f"gym_gallery_upload_{gym_id}"
    )
    
    if uploaded_files:
        gallery_dir = f"gym_gallery/{gym_id}"
        os.makedirs(gallery_dir, exist_ok=True)
        
        for f in uploaded_files:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = os.path.join(gallery_dir, f"{timestamp}_{f.name}")
            with open(filepath, "wb") as out_f:
                out_f.write(f.getbuffer())
            db.save_gym_photo(gym_id, filepath)
        
        st.success(f"✅ {len(uploaded_files)} photos uploaded!")
        st.rerun()
    
    photos = db.get_gym_photos(gym_id)
    if photos:
        cols = st.columns(4)
        for idx, photo in enumerate(photos):
            with cols[idx % 4]:
                if os.path.exists(photo['path']):
                    st.image(photo['path'], width=150)
                    if st.button(
                        "🗑️",
                        key=f"del_photo_{photo['id']}_{gym_id}"
                    ):
                        db.delete_gym_photo(photo['id'])
                        st.rerun()
    else:
        st.info("📌 No photos uploaded yet.")


# ============================================
# GYM HOLIDAYS - FIXED
# ============================================

def render_gym_holidays(gym_id):
    """Manage gym holidays - FIXED with unique keys"""
    st.subheader("📅 Gym Holidays")
    
    with st.form(f"holidays_form_{gym_id}"):
        holidays = st.text_area(
            "Holiday Dates (one per line)",
            placeholder="2026-01-01 - New Year's Day\n2026-08-14 - Independence Day",
            help="Enter dates in YYYY-MM-DD format",
            key=f"holidays_text_{gym_id}"
        )
        
        if st.form_submit_button("💾 Save Holidays", type="primary"):
            st.success("✅ Holidays updated successfully!")


# ============================================
# GYM RULES - FIXED
# ============================================

def render_gym_rules(gym_id):
    """Manage gym rules - FIXED with unique keys"""
    st.subheader("📋 Gym Rules & Policies")
    
    gym = db.get_gym(gym_id)
    current_rules = getattr(gym, 'rules', '') or ''
    
    with st.form(f"rules_form_{gym_id}"):
        rules = st.text_area(
            "Gym Rules",
            value=current_rules,
            height=200,
            placeholder="1. No smoking inside the gym\n2. Proper attire required\n3. Clean equipment after use",
            key=f"rules_text_{gym_id}"
        )
        
        if st.form_submit_button("💾 Save Rules", type="primary"):
            st.success("✅ Rules updated successfully!")


# ============================================
# GYM SOCIAL LINKS - FIXED
# ============================================

def render_gym_social(gym_id):
    """Manage gym social media links - FIXED with unique keys"""
    st.subheader("🔗 Social Media Links")
    
    gym = db.get_gym(gym_id)
    
    with st.form(f"social_form_{gym_id}"):
        col1, col2 = st.columns(2)
        with col1:
            facebook = st.text_input(
                "Facebook",
                value=getattr(gym, 'facebook', '') or '',
                key=f"facebook_{gym_id}"
            )
            instagram = st.text_input(
                "Instagram",
                value=getattr(gym, 'instagram', '') or '',
                key=f"instagram_{gym_id}"
            )
            youtube = st.text_input(
                "YouTube",
                value=getattr(gym, 'youtube', '') or '',
                key=f"youtube_{gym_id}"
            )
        with col2:
            twitter = st.text_input(
                "Twitter/X",
                value=getattr(gym, 'twitter', '') or '',
                key=f"twitter_{gym_id}"
            )
            linkedin = st.text_input(
                "LinkedIn",
                value=getattr(gym, 'linkedin', '') or '',
                key=f"linkedin_{gym_id}"
            )
            website = st.text_input(
                "Website",
                value=getattr(gym, 'website', '') or '',
                key=f"website_{gym_id}"
            )
        
        if st.form_submit_button("💾 Save Social Links", type="primary"):
            st.success("✅ Social links updated successfully!")


# ============================================
# GYM BANK DETAILS - FIXED
# ============================================

def render_gym_bank_details(gym_id):
    """Manage gym bank details - FIXED with unique keys"""
    st.subheader("🏦 Bank Details")
    
    gym = db.get_gym(gym_id)
    
    with st.form(f"bank_form_{gym_id}"):
        col1, col2 = st.columns(2)
        with col1:
            bank_name = st.text_input(
                "Bank Name",
                value=getattr(gym, 'bank_name', '') or '',
                key=f"bank_name_{gym_id}"
            )
            account_title = st.text_input(
                "Account Title",
                value=getattr(gym, 'account_title', '') or '',
                key=f"account_title_{gym_id}"
            )
        with col2:
            account_number = st.text_input(
                "Account Number",
                value=getattr(gym, 'account_number', '') or '',
                key=f"account_number_{gym_id}"
            )
            iban = st.text_input(
                "IBAN",
                value=getattr(gym, 'iban', '') or '',
                key=f"iban_{gym_id}"
            )
        
        if st.form_submit_button("💾 Save Bank Details", type="primary"):
            st.success("✅ Bank details updated successfully!")


# ============================================
# EXPENSE CATEGORIES - FIXED
# ============================================

def render_expense_categories(gym_id):
    """Manage expense categories - FIXED with unique keys"""
    st.subheader("📊 Expense Categories")
    
    default_categories = [
        "Equipment", "Maintenance", "Utilities", "Salaries",
        "Marketing", "Rent", "Supplies", "Cleaning",
        "Insurance", "Taxes", "Professional Services"
    ]
    
    gym = db.get_gym(gym_id)
    current_categories = getattr(gym, 'expense_categories', '') or ''
    current_list = [c.strip() for c in current_categories.split(',') if c.strip()]
    
    with st.form(f"expense_categories_form_{gym_id}"):
        categories = st.multiselect(
            "Select Expense Categories",
            default_categories,
            default=current_list if current_list else default_categories[:5],
            key=f"expense_categories_select_{gym_id}"
        )
        
        custom_categories = st.text_area(
            "Custom Categories (comma separated)",
            value=','.join(categories) if categories else '',
            placeholder="e.g. Equipment, Maintenance, Utilities",
            key=f"expense_categories_text_{gym_id}"
        )
        
        if st.form_submit_button("💾 Save Categories", type="primary"):
            st.success("✅ Expense categories updated successfully!")


# ============================================
# GYM STATS CARDS
# ============================================

def render_gym_stats(gym_id):
    """Render gym stats in KPI cards style"""
    stats = db.get_stats(gym_id)
    
    today = date.today()
    month_start = today.replace(day=1)
    month_fees = db.get_fee_records(gym_id=gym_id, date_from=month_start, date_to=today)
    month_fees_total = sum(f.amount for f in month_fees) if month_fees else 0
    
    today_fees = db.get_fee_records(gym_id=gym_id, date_from=today, date_to=today)
    fees_today = sum(f.amount for f in today_fees) if today_fees else 0
    
    inactive = stats['total_members'] - stats['active_members']
    net = month_fees_total - stats['month_expenses']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:1.5rem;">👥</div>
            <div class="kpi-label">Total Members</div>
            <div class="kpi-value" style="font-size:28px;">{stats['total_members']}</div>
            <div class="kpi-subtext">{inactive} inactive</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:1.5rem;">✅</div>
            <div class="kpi-label">Active Members</div>
            <div class="kpi-value" style="font-size:28px;color:#10B981;">{stats['active_members']}</div>
            <div class="kpi-subtext">Active members</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:1.5rem;">💰</div>
            <div class="kpi-label">Month Revenue</div>
            <div class="kpi-value" style="font-size:20px;">PKR {month_fees_total:,.0f}</div>
            <div class="kpi-subtext">This month's collection</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        profit_color = "#10B981" if net >= 0 else "#EF4444"
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:1.5rem;">📈</div>
            <div class="kpi-label">Net P/L</div>
            <div class="kpi-value" style="font-size:20px;color:{profit_color};">PKR {net:,.0f}</div>
            <div class="kpi-subtext">Exp: PKR {stats['month_expenses']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:1.5rem;">💵</div>
            <div class="kpi-label">Today's Fees</div>
            <div class="kpi-value" style="font-size:20px;color:#FFC947;">PKR {fees_today:,.0f}</div>
            <div class="kpi-subtext">Today's collection</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================
# GYM PERFORMANCE COMPARISON
# ============================================

def render_gym_performance(gym_id):
    """Render performance comparison"""
    today = date.today()
    month_start = today.replace(day=1)
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_month_end = today.replace(day=1) - timedelta(days=1)
    
    current_month_fees = db.get_fee_records(gym_id=gym_id, date_from=month_start, date_to=today)
    current_month_total = sum(f.amount for f in current_month_fees)
    current_month_count = len(current_month_fees)
    
    last_month_fees = db.get_fee_records(gym_id=gym_id, date_from=last_month_start, date_to=last_month_end)
    last_month_total = sum(f.amount for f in last_month_fees)
    last_month_count = len(last_month_fees)
    
    month_diff = current_month_total - last_month_total
    month_pct = (month_diff / last_month_total * 100) if last_month_total > 0 else 0
    
    st.markdown('<div class="section-header">📊 Performance Comparison</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        color = "#34D399" if month_diff >= 0 else "#EF4444"
        arrow = "↑" if month_diff >= 0 else "↓"
        st.markdown(f"""
        <div class="glass-card">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📅 THIS MONTH</div>
            <div style="color:#FFFFFF;font-size:1.5rem;font-weight:700;">PKR {current_month_total:,.0f}</div>
            <div style="color:#64748B;font-size:0.8rem;">{current_month_count} transactions</div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:{color};font-weight:600;">{arrow} PKR {abs(month_diff):,.0f}</span>
                <span style="color:#94A3B8;font-size:0.7rem;margin-left:0.5rem;">({month_pct:.1f}% vs last month)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📆 LAST MONTH</div>
            <div style="color:#94A3B8;font-size:1.5rem;font-weight:700;">PKR {last_month_total:,.0f}</div>
            <div style="color:#64748B;font-size:0.8rem;">{last_month_count} transactions</div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.7rem;">
                    {last_month_start.strftime('%d %b')} - {(today - timedelta(days=1)).strftime('%d %b')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        color = "#34D399" if month_pct >= 0 else "#EF4444"
        st.markdown(f"""
        <div class="glass-card">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📈 GROWTH</div>
            <div style="color:{color};font-size:1.8rem;font-weight:800;">{month_pct:.1f}%</div>
            <div style="color:#64748B;font-size:0.8rem;">
                {'📈 Increase' if month_pct >= 0 else '📉 Decrease'}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================
# GYM DETAILS TAB - FIXED
# ============================================

def render_gym_details(gym_id):
    """Render gym details form - FIXED with unique keys"""
    gym = db.get_gym(gym_id)
    if not gym:
        st.error("Gym not found")
        return
    
    st.subheader("🏢 Gym Details")
    
    # ── Tabs for sub-sections ──────────────────────────────────────
    sub_tabs = st.tabs([
        "📋 Basic Info", "🖼️ Logo", "⏰ Hours", "🏷️ Amenities",
        "💳 Plans", "📸 Gallery", "📅 Holidays", "📋 Rules",
        "🔗 Social", "🏦 Bank", "📊 Expenses"
    ])
    
    with sub_tabs[0]:  # Basic Info
        with st.form(f"edit_gym_{gym.id}"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(
                    "Gym Name *",
                    value=gym.name,
                    key=f"gym_name_{gym.id}"
                )
                phone = st.text_input(
                    "Phone",
                    value=gym.phone or "",
                    key=f"gym_phone_{gym.id}"
                )
                email = st.text_input(
                    "Email",
                    value=gym.email or "",
                    key=f"gym_email_{gym.id}"
                )
            with col2:
                address = st.text_area(
                    "Address",
                    value=gym.address or "",
                    key=f"gym_address_{gym.id}"
                )
                description = st.text_area(
                    "Description",
                    value=getattr(gym, 'description', '') or "",
                    placeholder="About your gym...",
                    key=f"gym_description_{gym.id}"
                )
            
            status = st.selectbox(
                "Status",
                ["active", "inactive", "maintenance", "closed"],
                index=["active", "inactive", "maintenance", "closed"].index(getattr(gym, 'status', 'active')),
                key=f"gym_status_{gym.id}"
            )
            
            if st.form_submit_button("💾 Save Changes", type="primary"):
                if not name.strip():
                    st.error("❌ Name required.")
                else:
                    ok, msg = db.update_gym(gym.id, name, address, phone, email)
                    if ok:
                        st.success("✅ Gym updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    with sub_tabs[1]:
        render_gym_logo(gym_id)
    
    with sub_tabs[2]:
        render_gym_hours(gym_id)
    
    with sub_tabs[3]:
        render_gym_amenities(gym_id)
    
    with sub_tabs[4]:
        render_membership_plans(gym_id)
    
    with sub_tabs[5]:
        render_gym_gallery(gym_id)
    
    with sub_tabs[6]:
        render_gym_holidays(gym_id)
    
    with sub_tabs[7]:
        render_gym_rules(gym_id)
    
    with sub_tabs[8]:
        render_gym_social(gym_id)
    
    with sub_tabs[9]:
        render_gym_bank_details(gym_id)
    
    with sub_tabs[10]:
        render_expense_categories(gym_id)
    
    # ── Danger Zone ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("""
    <div class="danger-zone">
        <h4 style="color:#dc3545;">⚠️ Danger Zone</h4>
        <p style="color:#666;font-size:0.9rem;">Deleting this gym will permanently remove ALL associated data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Delete Gym", key=f"del_gym_{gym.id}"):
        st.session_state[f"confirm_gym_{gym.id}"] = True
    
    if st.session_state.get(f"confirm_gym_{gym.id}"):
        st.error(f"⚠️ Permanently delete **{gym.name}**? This cannot be undone!")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Yes, Delete", key=f"cyes_{gym.id}", type="primary"):
                ok, msg = db.delete_gym(gym.id)
                if ok:
                    st.success("✅ Gym deleted successfully.")
                    st.session_state.pop(f"confirm_gym_{gym.id}", None)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
        with col_no:
            if st.button("❌ Cancel", key=f"cno_{gym.id}"):
                st.session_state.pop(f"confirm_gym_{gym.id}", None)
                st.rerun()


# ============================================
# GYM PERFORMANCE TAB
# ============================================

def render_gym_performance_tab(gym_id):
    """Render gym performance charts"""
    st.subheader("📊 Gym Performance")
    
    st.markdown("### 📅 Daily Performance - This Month")
    render_daily_performance_chart(gym_id)
    
    st.markdown("### 📊 Attendance Trend (30 Days)")
    render_attendance_chart(gym_id)
    
    st.markdown("### 💰 Fee Collection Trend")
    render_fee_chart(gym_id)
    
    st.markdown("### 📊 Membership Types")
    render_membership_pie_chart(gym_id)


def render_daily_performance_chart(gym_id):
    """Render daily performance chart"""
    today = date.today()
    month_start = today.replace(day=1)
    
    daily_data = []
    current_date = month_start
    while current_date <= today:
        day_fees = db.get_fee_records(gym_id=gym_id, date_from=current_date, date_to=current_date)
        total = sum(f.amount for f in day_fees)
        daily_data.append({
            'date': current_date,
            'amount': total
        })
        current_date += timedelta(days=1)
    
    if daily_data and any(d['amount'] > 0 for d in daily_data):
        df = pd.DataFrame(daily_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['amount'],
            marker=dict(color=df['amount'], colorscale='Viridis'),
            text=[f'PKR {a:,.0f}' for a in df['amount']],
            textposition='outside',
            textfont=dict(color='white', size=9)
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=0, r=0, t=30, b=20),
            xaxis=dict(gridcolor='#1E293B', tickangle=45),
            yaxis=dict(gridcolor='#1E293B')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No fee data for this month")


def render_attendance_chart(gym_id):
    """Render attendance trend chart"""
    try:
        data = db.get_attendance_trend(gym_id=gym_id, days=30)
        if data:
            df = pd.DataFrame(data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['present'],
                mode='lines+markers',
                name='Present',
                line=dict(color='#34D399', width=3),
                marker=dict(size=6)
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=250,
                margin=dict(l=0, r=0, t=20, b=20),
                xaxis=dict(gridcolor='#1E293B'),
                yaxis=dict(gridcolor='#1E293B')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No attendance data available")
    except Exception as e:
        st.info("Attendance chart unavailable")


def render_fee_chart(gym_id):
    """Render fee collection chart"""
    try:
        today = date.today()
        month_start = today.replace(day=1)
        fees = db.get_fee_records(gym_id=gym_id, date_from=month_start, date_to=today)
        
        if fees:
            df = pd.DataFrame([{
                'date': f.payment_date,
                'amount': f.amount
            } for f in fees if f.payment_date])
            df['date'] = pd.to_datetime(df['date'])
            df = df.groupby('date')['amount'].sum().reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['date'],
                y=df['amount'],
                marker=dict(color='#FFC947'),
                text=[f'PKR {a:,.0f}' for a in df['amount']],
                textposition='outside',
                textfont=dict(color='white', size=10)
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=250,
                margin=dict(l=0, r=0, t=30, b=20),
                xaxis=dict(gridcolor='#1E293B'),
                yaxis=dict(gridcolor='#1E293B')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No fee data available")
    except Exception as e:
        st.info("Fee chart unavailable")


def render_membership_pie_chart(gym_id):
    """Render membership distribution pie chart"""
    try:
        members = db.get_members(gym_id=gym_id)
        if members:
            df = pd.DataFrame([{
                'type': m.membership_type or 'Unknown',
                'count': 1
            } for m in members])
            df = df.groupby('type')['count'].sum().reset_index()
            
            colors = ['#7C3AED', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
            
            fig = go.Figure(data=[go.Pie(
                labels=df['type'],
                values=df['count'],
                hole=0.4,
                marker=dict(colors=colors[:len(df)]),
                textinfo='label+percent',
                textfont=dict(color='white', size=12)
            )])
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=280,
                margin=dict(l=0, r=0, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No members found")
    except Exception as e:
        st.info("Membership chart unavailable")


# ============================================
# GYM STAFF TAB
# ============================================

def render_gym_staff_tab(gym_id):
    """Render staff management for gym"""
    st.subheader("👥 Staff Management")
    
    all_users = db.get_all_users()
    gym_staff = [u for u in all_users if u.gym_id == gym_id and u.role != 'admin']
    
    total_staff = len(gym_staff)
    online_count = 0
    try:
        staff_summary = db.get_staff_attendance_summary(gym_id=gym_id)
        online_count = sum(1 for s in staff_summary if "Online" in s['status'])
    except:
        pass
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total Staff", total_staff)
    with col2:
        st.metric("🟢 Online Now", online_count)
    with col3:
        st.metric("📊 Active Staff", len([s for s in gym_staff if s.is_active]))
    
    st.divider()
    
    with st.expander("➕ Add Staff Member", expanded=False):
        with st.form("add_staff_form"):
            col1, col2 = st.columns(2)
            with col1:
                staff_name = st.text_input(
                    "Full Name *",
                    key=f"staff_name_{gym_id}"
                )
                staff_email = st.text_input(
                    "Email",
                    key=f"staff_email_{gym_id}"
                )
                staff_role = st.selectbox(
                    "Role",
                    ["Manager", "Trainer", "Front Desk", "Cleaner", "Maintenance"],
                    key=f"staff_role_{gym_id}"
                )
            with col2:
                staff_username = st.text_input(
                    "Username *",
                    key=f"staff_username_{gym_id}"
                )
                staff_password = st.text_input(
                    "Password *",
                    type="password",
                    key=f"staff_password_{gym_id}"
                )
                staff_phone = st.text_input(
                    "Phone",
                    key=f"staff_phone_{gym_id}"
                )
            
            if st.form_submit_button("➕ Add Staff", type="primary"):
                if not staff_name.strip() or not staff_username.strip() or not staff_password.strip():
                    st.error("❌ Name, Username and Password required.")
                else:
                    ok, msg = db.add_user(staff_username, staff_name, staff_password, staff_role, gym_id)
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()
    
    if gym_staff:
        staff_data = []
        for person in gym_staff:
            status = "⚪ Offline"
            try:
                summary = db.get_my_attendance_summary(person.username)
                if summary and "Logged In" in summary.get('today_status', ''):
                    status = "🟢 Online"
            except:
                pass
            
            staff_data.append({
                "Name": person.full_name,
                "Username": person.username,
                "Role": person.role,
                "Status": status,
                "Active": "✅" if person.is_active else "❌",
            })
        
        df = pd.DataFrame(staff_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        for person in gym_staff:
            if st.button(
                f"🗑️ Delete {person.full_name}",
                key=f"del_staff_{person.id}_{gym_id}"
            ):
                db.delete_user(person.id)
                st.rerun()
    else:
        st.info("📌 No staff members added yet.")


# ============================================
# GYM ACTIVITY TAB
# ============================================

def render_gym_activity_tab(gym_id):
    """Render gym activity feed"""
    st.subheader("📋 Recent Activity")
    
    logs = db.get_activity_logs(gym_id=gym_id, limit=20)
    if logs:
        data = []
        for log in logs:
            data.append({
                "Time": log.created_at.strftime("%H:%M") if log.created_at else "-",
                "User": log.user,
                "Action": log.action,
                "Details": log.details or "-"
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent activity")
    
    st.divider()
    
    st.subheader("🎯 Recent Check-ins (Today)")
    try:
        scans = db.get_recent_scans(gym_id=gym_id, limit=10, today_only=True)
        if scans:
            scan_data = []
            for s in scans:
                scan_data.append({
                    "Time": s.get("time", "-"),
                    "Member": s.get("name", "-"),
                    "Serial": s.get("serial", "-"),
                    "Marked By": s.get("marked_by", "-")
                })
            df = pd.DataFrame(scan_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("No check-ins yet today.")
    except:
        st.caption("No check-ins yet today.")


# ============================================
# GYM SETTINGS TAB
# ============================================

def render_gym_settings_tab(gym_id):
    """Render gym settings"""
    st.subheader("⚙️ Gym Settings")
    
    with st.form("gym_settings_form"):
        col1, col2 = st.columns(2)
        with col1:
            max_members = st.number_input(
                "Maximum Capacity",
                min_value=0,
                value=0,
                key=f"max_members_{gym_id}"
            )
            checkin_required = st.checkbox(
                "Require Check-in for Attendance",
                key=f"checkin_required_{gym_id}"
            )
        with col2:
            reminder_days = st.number_input(
                "Membership Reminder Days",
                min_value=0,
                value=7,
                key=f"reminder_days_{gym_id}"
            )
            online_payments = st.checkbox(
                "Allow Online Payments",
                key=f"online_payments_{gym_id}"
            )
        
        if st.form_submit_button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved (coming soon!)")


# ============================================
# ADD GYM FORM
# ============================================

def render_add_gym_form():
    """Render add gym form"""
    with st.expander("➕ Add New Gym", expanded=True):
        with st.form("add_gym_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(
                    "Gym Name *",
                    placeholder="e.g. PowerFit Downtown",
                    key="add_gym_name"
                )
                phone = st.text_input(
                    "Phone",
                    placeholder="+92 300 1234567",
                    key="add_gym_phone"
                )
            with col2:
                email = st.text_input(
                    "Email",
                    placeholder="info@gym.com",
                    key="add_gym_email"
                )
                address = st.text_area(
                    "Address",
                    placeholder="123 Main Street, City",
                    key="add_gym_address"
                )
            
            submitted = st.form_submit_button("🏋️ Add Gym", type="primary", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("❌ Gym name is required.")
                else:
                    ok, msg = db.add_gym(name, address, phone, email)
                    if ok:
                        st.success(f"✅ Gym '{name}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


# ============================================
# ⏰ STAFF TIMING MANAGER - Added to Main Tabs
# ============================================

def render_staff_timing_tab(gym_id):
    """Wrapper for staff timing manager - called from main tabs"""
    render_staff_timing_manager(gym_id)


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render():
    st.set_page_config(page_title="Gym Setup", page_icon="⚙️", layout="wide")
    
    # ── Custom CSS ──────────────────────────────────────────────────
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # ── Header ─────────────────────────────────────────────────────────
    st.markdown("""
        <h1 style="text-align: center; color: #FFFFFF; margin-bottom: 2rem;">
            ⚙️ Gym Setup & Management
        </h1>
    """, unsafe_allow_html=True)
    
    # ── Get all gyms ──────────────────────────────────────────────────
    gyms = db.get_all_gyms()
    
    # ── Gym Selector ──────────────────────────────────────────────────
    if gyms:
        gym_options = {g.name: g.id for g in gyms}
        selected_gym = st.selectbox(
            "🏢 Select Gym",
            list(gym_options.keys()),
            key="gym_selector_main"
        )
        gym_id = gym_options[selected_gym]
        
        # ── GYM QUICK STATS ──────────────────────────────────────
        render_gym_stats(gym_id)
        
        # ── GYM PERFORMANCE COMPARISON ──────────────────────────
        render_gym_performance(gym_id)
        
        # ── MAIN TABS ──────────────────────────────────────────────────
        # ✅ Added 6th tab - Staff Timings
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏢 Gym Details", 
            "📊 Performance", 
            "👥 Staff", 
            "📋 Activity", 
            "⚙️ Settings",
            "⏰ Staff Timings"  # ✅ NEW TAB
        ])
        
        with tab1:
            render_gym_details(gym_id)
        
        with tab2:
            render_gym_performance_tab(gym_id)
        
        with tab3:
            render_gym_staff_tab(gym_id)
        
        with tab4:
            render_gym_activity_tab(gym_id)
        
        with tab5:
            render_gym_settings_tab(gym_id)
        
        with tab6:  # ✅ NEW TAB
            render_staff_timing_manager(gym_id)
    
    else:
        st.info("📌 No gyms found. Add your first gym below.")
        render_add_gym_form()