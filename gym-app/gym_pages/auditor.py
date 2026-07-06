import streamlit as st
import pandas as pd
import os
import base64
from datetime import date, datetime, timedelta
import database as db
import styles
import object_store
from PIL import Image, ImageOps
import io

# ============================================
# SESSION STATE INITIALIZATION - FIXED
# ============================================

def init_session_state():
    """Initialize all audit session state variables"""
    defaults = {
        'audit_photo_cache': {},
        'audit_selected_id': None,
        'audit_refresh': False,
        'audit_gallery_loaded': False,
        'audit_gallery_html': [],
        'audit_member_count': 0,
        'audit_members_data': [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Call initialization
init_session_state()


st.markdown("""
<style>
    .card-3d {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 
            0 10px 30px rgba(0,0,0,0.5),
            0 4px 10px rgba(0,0,0,0.3),
            inset 0 -2px 0 rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .card-3d:hover {
        transform: translateY(-5px);
        box-shadow: 
            0 20px 40px rgba(0,0,0,0.6),
            0 8px 20px rgba(0,0,0,0.4),
            inset 0 -2px 0 rgba(255,255,255,0.08);
    }
    
    .card-3d::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #7C3AED, #A78BFA, #7C3AED);
        box-shadow: 0 0 20px rgba(124,58,237,0.3);
    }
    
    .card-3d .icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .card-3d .value {
        font-size: 2rem;
        font-weight: 800;
        color: #F8FAFC;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .card-3d .label {
        font-size: 0.8rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }
    
    .card-3d.glow-purple {
        border-color: rgba(124,58,237,0.3);
    }
    
    .card-3d.glow-green {
        border-color: rgba(52,211,153,0.3);
    }
    
    .card-3d.glow-red {
        border-color: rgba(248,113,113,0.3);
    }
    
    .card-3d.glow-yellow {
        border-color: rgba(251,191,36,0.3);
    }
    
    .card-3d.glow-blue {
        border-color: rgba(96,165,250,0.3);
    }
    
    .status-verified {
        background: #10B981;
        color: white;
        padding: 2px 12px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .status-discrepancy {
        background: #EF4444;
        color: white;
        padding: 2px 12px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .status-pending {
        background: #F59E0B;
        color: #1E293B;
        padding: 2px 12px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .status-resolved {
        background: #3B82F6;
        color: white;
        padding: 2px 12px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# PHOTO HELPERS - FIXED
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

def get_audit_photo_b64(photo_path, serial_number: str = ""):
    """Get compressed photo with orientation fix - SAFE with session state check"""
    
    # 🔥 FIX: Ensure session state is initialized
    if 'audit_photo_cache' not in st.session_state:
        st.session_state.audit_photo_cache = {}
    
    if not photo_path and not serial_number:
        return None

    cache_key = f"audit_{photo_path}_{serial_number}"
    if cache_key in st.session_state.audit_photo_cache:
        return st.session_state.audit_photo_cache[cache_key]

    # 1. Object Storage — primary source
    for key in filter(None, [photo_path, f"member_photos/{serial_number}.jpg" if serial_number else None]):
        try:
            b64, _ = object_store.get_photo_b64(key)
            if b64:
                # Apply orientation fix
                try:
                    img_bytes = base64.b64decode(b64)
                    img = Image.open(io.BytesIO(img_bytes))
                    img = fix_image_orientation(img)
                    
                    output = io.BytesIO()
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(output, format='JPEG', quality=85, optimize=True)
                    fixed_b64 = base64.b64encode(output.getvalue()).decode()
                except:
                    fixed_b64 = b64
                
                st.session_state.audit_photo_cache[cache_key] = fixed_b64
                return fixed_b64
        except Exception:
            pass

    # 2. Local filesystem fallback
    if photo_path:
        paths_to_check = [
            photo_path,
            os.path.join("gym-app", "uploads", os.path.basename(photo_path)),
            os.path.join(os.getcwd(), "gym-app", "uploads", os.path.basename(photo_path)),
            os.path.join("uploads", os.path.basename(photo_path)),
        ]
        for path in paths_to_check:
            if os.path.exists(path) and os.path.isfile(path):
                try:
                    img = Image.open(path)
                    img = fix_image_orientation(img)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    if img.width > 300:
                        ratio = 300 / img.width
                        img = img.resize((300, int(img.height * ratio)), Image.Resampling.LANCZOS)
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=80, optimize=True)
                    b64 = base64.b64encode(output.getvalue()).decode()
                    st.session_state.audit_photo_cache[cache_key] = b64
                    return b64
                except Exception:
                    pass

    return None

def show_audit_photo(photo_path, width=120, height=180, serial_number=""):
    """Display member photo with orientation fix - SAFE with error handling"""
    
    # 🔥 FIX: Ensure session state is initialized
    if 'audit_photo_cache' not in st.session_state:
        st.session_state.audit_photo_cache = {}
    
    try:
        photo_b64 = get_audit_photo_b64(photo_path, serial_number)
        
        if photo_b64:
            st.markdown(f"""
            <div style="width:{width}px; height:{height}px; border-radius:12px;
                        border:3px solid #7C3AED; overflow:hidden;
                        background:#1E293B; box-shadow:0 4px 15px rgba(124,58,237,0.3);
                        flex-shrink:0;">
                <img src="data:image/jpeg;base64,{photo_b64}" 
                     style="width:100%; height:100%; object-fit:cover; display:block;
                            image-orientation:from-image;" />
            </div>
            """, unsafe_allow_html=True)
            return True
    except Exception as e:
        print(f"Photo display error: {e}")
    
    # Default placeholder
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

def get_member_from_reference(reference_id, gym_id=None):
    if not reference_id:
        return None
    
    try:
        ref_int = int(reference_id)
    except:
        return None
    
    member = db.get_member_by_id(ref_int)
    if member:
        return member
    
    try:
        fee_records = db.get_fee_records(gym_id=gym_id)
        for fr in fee_records:
            if fr.id == ref_int:
                return fr.member
    except:
        pass
    
    return None

# ============================================
# MAIN RENDER FUNCTION - FIXED
# ============================================

def render(gym_id, role, username):
    
    # 🔥 FIX: Ensure session state is initialized
    init_session_state()
    
    # Check if refresh needed
    if st.session_state.get('audit_refresh', False):
        st.session_state.audit_refresh = False
        st.rerun()
    
    styles.page_header("🔍", "Independent Audit Module",
                       "Cross-Verification Log — Staff aur Auditor ka Data Milana")
    
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    # ============================================
    # TABS
    # ============================================
    
    tab_headcount, tab_verify, tab_log, tab_summary, tab_present, tab_staff = st.tabs([
        "👥 Headcount Verification",
        "✍️ Cross-Verification Log",
        "📋 Audit Log",
        "⚠️ Dispute / Discrepancy",
        "✅ Present Members",
        "🛡️ Staff Monitor",
    ])

    # ============================================
    # TAB 1: HEADCOUNT VERIFICATION
    # ============================================
    
    with tab_headcount:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.markdown("**👥 Headcount Verification** — Physical headcount aur system records verify karein.")

        gym_opts = {g.name: g.id for g in gyms}
        if gym_id:
            hsel_gid = gym_id
        else:
            hsel_gid = gym_opts[st.selectbox("🏋️ Switch Gym Location", list(gym_opts.keys()), key="hc_gym")]

        st.divider()
        st.markdown("### 🤳 Active Members List")

        active_members = db.get_active_members(hsel_gid)

        total_members = len(active_members)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="card-3d glow-purple" style="text-align:center;padding:0.8rem;">
                <span class="icon">👥</span>
                <div class="value">{total_members}</div>
                <div class="label">Pending Verification</div>
            </div>
            """, unsafe_allow_html=True)

        if active_members:
            st.markdown("---")
            
            cols = st.columns(3)
            for idx, member in enumerate(active_members):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                                border:1px solid #334155;border-radius:12px;
                                padding:1rem;text-align:center;
                                box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                    """, unsafe_allow_html=True)
                    
                    show_audit_photo(member.photo_path, width=120, height=180, serial_number=member.serial_number)
                    
                    st.markdown(f"""
                    <div style="font-weight:700;color:#F8FAFC;margin-top:0.5rem;">{member.full_name}</div>
                    <div style="font-size:0.8rem;color:#94A3B8;">🆔 {member.serial_number}</div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("✅ Present", key=f"btn_{member.id}", use_container_width=True):
                        ok, msg = db.mark_member_present(member.id, hsel_gid, date.today())
                        db.update_audit_by_member(member.id, "Verified")
                        if ok:
                            st.toast(f"✅ {member.full_name} Marked Present!")
                            st.rerun()
                        else:
                            st.error(msg)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("🎉 Sab members verify ho chuke hain!")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 2: CROSS-VERIFICATION LOG
    # ============================================
    
    with tab_verify:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.markdown("**✍️ Cross-Verification Log** — Independent observation aur discrepancies check karein.")

        gym_opts2 = {g.name: g.id for g in gyms}
        sel_gid = gym_id if gym_id else gym_opts2[st.selectbox("🏋️ Switch Gym Location", list(gym_opts2.keys()), key="cv_gym")]

        entry_type = st.radio("📂 Entry Type", ["Fee Collection", "Expense"], horizontal=True, key="cv_entry_type")

        if entry_type == "Fee Collection":
            all_records = db.get_fee_records(gym_id=sel_gid)
            records = [r for r in all_records if not db.is_record_verified(r.id)]

            if not records:
                st.success("🎉 Sab fee records verify ho chuke hain!")
            else:
                selected_record = st.selectbox(
                    "Select Fee Record to Audit", 
                    records, 
                    format_func=lambda x: f"#{x.id} | {(x.member.full_name if x.member else 'Unknown')} | PKR {x.amount:,.2f}"
                )
                
                ref_id, expected, member = selected_record.id, selected_record.amount, selected_record.member
                
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown("### 📊 Comparison")
                    st.metric("💰 Staff Recorded Amount", f"PKR {expected:,.2f}")
                with c2:
                    if member and hasattr(member, 'photo_path'):
                        show_audit_photo(member.photo_path, width=120, height=180, serial_number=member.serial_number if hasattr(member, 'serial_number') else "")
                        st.caption(member.full_name)

                with st.form("cross_verification_form", clear_on_submit=True):
                    actual = st.number_input("💰 Actual Amount Observed (PKR)", min_value=0.0, format="%.2f")
                    description = st.text_input("📝 Description / Notes")
                    
                    if st.form_submit_button("✅ Submit Cross-Verification", type="primary", use_container_width=True):
                        status, msg = db.add_audit_entry(
                            gym_id=sel_gid, 
                            entry_type="fee", 
                            reference_id=ref_id,
                            expected_amount=expected, 
                            actual_amount=actual,
                            description=description, 
                            entry_date=str(date.today()),
                            verified_by=username
                        )
                        
                        if status:
                            if actual != expected:
                                st.error(f"⚠️ DISCREPANCY: Auditor observed {actual}, Staff recorded {expected}!")
                            else:
                                st.success("✅ MATCHED: Records are accurate.")
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")

        else:
            st.info("📝 Expense verification module under development.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 3: AUDIT LOG (FILTERED - RESOLVED HIDDEN)
    # ============================================
    
    with tab_log:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.markdown("**📋 Full Cross-Verification Log — Tamam Audit Entries**")

        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            opts2 = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen2 = st.selectbox("🏋️ Gym", list(opts2.keys()), key="log_gym")
            log_gid = opts2[chosen2]
        with f2:
            status_f = st.selectbox("📊 Audit Status", ["All", "Verified", "Discrepancy", "Pending", "Resolved"], key="log_status")
        with f3:
            df_from = st.date_input("📅 From", value=date.today().replace(day=1), key="log_from")
        with f4:
            df_to = st.date_input("📅 To", value=date.today(), key="log_to")

        entries = db.get_audit_entries(gym_id=log_gid, status=status_f, date_from=df_from, date_to=df_to)

        # Stats Cards
        v_count = sum(1 for e in entries if e.status == "Verified")
        d_count = sum(1 for e in entries if e.status == "Discrepancy")
        r_count = sum(1 for e in entries if e.status == "Resolved")
        p_count = len(entries) - v_count - d_count - r_count
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"""
            <div class="card-3d glow-purple" style="text-align:center;padding:0.8rem;">
                <div class="value">{len(entries)}</div>
                <div class="label">Total</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="card-3d glow-green" style="text-align:center;padding:0.8rem;">
                <div class="value">{v_count}</div>
                <div class="label">✅ Verified</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="card-3d glow-red" style="text-align:center;padding:0.8rem;">
                <div class="value">{d_count}</div>
                <div class="label">⚠️ Disputes</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="card-3d glow-yellow" style="text-align:center;padding:0.8rem;">
                <div class="value">{p_count}</div>
                <div class="label">🕐 Pending</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
            <div class="card-3d glow-blue" style="text-align:center;padding:0.8rem;">
                <div class="value">{r_count}</div>
                <div class="label">✅ Resolved</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # 🔥 FIXED: Filter out "Resolved" entries unless "All" or "Resolved" selected
        display_entries = entries
        if status_f not in ["All", "Resolved"]:
            display_entries = [e for e in entries if e.status != "Resolved"]
        
        if status_f == "All":
            display_entries = [e for e in entries if e.status != "Resolved"]

        # Display Logs with Member Details
        if display_entries:
            for e in display_entries:
                diff = (e.actual_amount or 0) - (e.expected_amount or 0)
                
                if e.status == "Verified":
                    status_color = "🟢"
                    status_class = "status-verified"
                elif e.status == "Discrepancy":
                    status_color = "🔴"
                    status_class = "status-discrepancy"
                elif e.status == "Resolved":
                    status_color = "✅"
                    status_class = "status-resolved"
                else:
                    status_color = "🟡"
                    status_class = "status-pending"

                member_info = get_member_from_reference(e.reference_id, log_gid)

                if member_info:
                    display_name = member_info.full_name
                    display_serial = member_info.serial_number
                    display_phone = member_info.phone or '—'
                    display_photo = member_info.photo_path
                    display_expiry = member_info.expiry_date or '—'
                    display_serial_num = member_info.serial_number if hasattr(member_info, 'serial_number') else ''
                else:
                    display_name = f"Ref: {e.reference_id}"
                    display_serial = '—'
                    display_phone = '—'
                    display_photo = None
                    display_expiry = '—'
                    display_serial_num = ''

                with st.expander(f"{status_color} {e.entry_date} | {display_name} | Diff: {diff:+.2f} PKR"):
                    
                    c_img, c_det = st.columns([1, 3])

                    with c_img:
                        show_audit_photo(display_photo, width=120, height=180, serial_number=display_serial_num)

                    with c_det:
                        if member_info:
                            st.markdown(f"""
                            <div style="margin-bottom:0.5rem;">
                                <div style="font-size:1.2rem;font-weight:700;color:#F8FAFC;">{member_info.full_name}</div>
                                <div style="font-size:0.85rem;color:#7C3AED;">🆔 {member_info.serial_number}</div>
                                <div style="font-size:0.8rem;color:#94A3B8;">📞 {member_info.phone or '—'}</div>
                                <div style="font-size:0.8rem;color:#94A3B8;">📅 {member_info.expiry_date or '—'}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.write(f"**Member:** Unknown Member")
                            st.write(f"**Reference ID:** {e.reference_id}")
                        
                        st.write(f"**Expected:** {e.expected_amount:,.2f} | **Actual:** {e.actual_amount:,.2f}")
                        st.write(f"**Verified By:** {e.verified_by} | **Status:** {e.status}")
                        st.info(f"📝 Notes: {e.description or 'No notes provided'}")

                        if e.status == "Discrepancy":
                            if st.button(f"✅ Mark as Resolved", key=f"res_{e.id}"):
                                db.update_audit_status(e.id, "Resolved")
                                st.success(f"✅ Record {e.id} marked as Resolved!")
                                st.session_state.audit_refresh = True
                                st.rerun()
                        elif e.status == "Resolved":
                            st.success("✅ This record has been resolved.")
        else:
            st.info("📭 No active audit entries found. All resolved!")

        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 4: DISPUTE / DISCREPANCY
    # ============================================
    
    with tab_summary:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.markdown("### ⚠️ Dispute / Discrepancy Control Center")

        st.subheader("💰 Financial Discrepancies")
        all_disc = [e for e in db.get_audit_entries(gym_id=gym_id, status="Discrepancy") if e.entry_type in ("fee", "expense")]

        if not all_disc:
            st.success("✅ Financial records clear!")
        else:
            total_var = sum(abs(e.actual_amount - e.expected_amount) for e in all_disc)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="card-3d glow-red" style="text-align:center;padding:0.8rem;">
                    <div class="value">PKR {total_var:,.2f}</div>
                    <div class="label">Total Financial Variance</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="card-3d glow-yellow" style="text-align:center;padding:0.8rem;">
                    <div class="value">{len(all_disc)}</div>
                    <div class="label">Open Issues</div>
                </div>
                """, unsafe_allow_html=True)

            for e in all_disc:
                diff = e.actual_amount - e.expected_amount
                color = "🔴" if diff < 0 else "🟢"
                
                member_info = get_member_from_reference(e.reference_id, gym_id)

                with st.expander(f"{color} {e.entry_date} | {e.entry_type.upper()} | Var: {diff:+,.2f} PKR"):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if member_info:
                            show_audit_photo(member_info.photo_path, width=120, height=180, serial_number=member_info.serial_number if hasattr(member_info, 'serial_number') else '')
                            st.write(f"**Member:** {member_info.full_name}")
                            st.write(f"**Serial:** {member_info.serial_number}")
                        else:
                            show_audit_photo(None, width=120, height=180)
                            st.write("**No Member Found**")
                        st.write(f"**Expected:** {e.expected_amount:,.2f}")
                        st.write(f"**Observed:** {e.actual_amount:,.2f}")
                    
                    with col2:
                        st.write(f"**Staff:** {e.verified_by}")
                        st.write(f"**Status:** {e.status}")
                        st.info(f"📝 Notes: {e.description or 'None'}")

                    c1, c2 = st.columns(2)
                    if c1.button(f"✅ Mark Resolved", key=f"dis_res_{e.id}"):
                        db.update_audit_status(e.id, "Resolved")
                        st.success(f"✅ Record {e.id} marked as Resolved!")
                        st.session_state.audit_refresh = True
                        st.rerun()
                    if c2.button(f"🚩 Flag to Manager", key=f"dis_flag_{e.id}"):
                        db.update_audit_status(e.id, "Manager Review")
                        st.success(f"🚩 Record {e.id} flagged to Manager!")
                        st.session_state.audit_refresh = True
                        st.rerun()

        st.divider()
        st.subheader("👥 Headcount Discrepancies")
        hc_disc = [e for e in db.get_audit_entries(gym_id=gym_id, status="Discrepancy") if "headcount" in e.entry_type]

        if not hc_disc:
            st.success("✅ Headcount is accurate!")
        else:
            for e in hc_disc:
                diff = int(e.actual_amount - e.expected_amount)
                st.warning(f"⚠️ **{e.entry_date}**: {e.entry_type.replace('_', ' ').title()} - Difference: {diff:+d}")
                
                if st.button(f"Resolve Headcount Issue", key=f"hc_res_{e.id}"):
                    db.update_audit_status(e.id, "Resolved")
                    st.success(f"✅ Headcount issue {e.id} resolved!")
                    st.session_state.audit_refresh = True
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 5: PRESENT MEMBERS
    # ============================================
    
    with tab_present:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.markdown("### ✅ Present Members Today")
        st.caption("Aaj jin members ko Present mark kiya gaya hai unki list")
        
        gym_opts_present = {g.name: g.id for g in gyms}
        if gym_id:
            psel_gid = gym_id
        else:
            psel_gid = gym_opts_present[st.selectbox("🏋️ Select Gym", list(gym_opts_present.keys()), key="present_gym")]
        
        today_str = date.today().isoformat()
        attendance_records = db.get_attendance(gym_id=psel_gid, check_date=today_str)
        present_records = [a for a in attendance_records if a.status == "Present"]
        
        if not present_records:
            st.info("📭 Aaj kisi member ko Present mark nahi kiya gaya.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="card-3d glow-green" style="text-align:center;padding:0.8rem;">
                    <span class="icon">✅</span>
                    <div class="value">{len(present_records)}</div>
                    <div class="label">Present Today</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            cols = st.columns(3)
            for idx, record in enumerate(present_records):
                member = db.get_member(record.member_id)
                if member:
                    with cols[idx % 3]:
                        st.markdown(f"""
                        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                                    border:2px solid #10B981;border-radius:12px;
                                    padding:1rem;text-align:center;
                                    box-shadow:0 4px 15px rgba(16,185,129,0.2);">
                        """, unsafe_allow_html=True)
                        
                        show_audit_photo(member.photo_path, width=120, height=180, serial_number=member.serial_number if hasattr(member, 'serial_number') else '')
                        
                        st.markdown(f"""
                        <div style="font-weight:700;color:#F8FAFC;margin-top:0.5rem;">{member.full_name}</div>
                        <div style="font-size:0.8rem;color:#7C3AED;">🆔 {member.serial_number}</div>
                        <div style="font-size:0.75rem;color:#94A3B8;">📞 {member.phone or '—'}</div>
                        <div style="font-size:0.7rem;color:#34D399;margin-top:0.2rem;">
                            ✅ Marked at {record.created_at.strftime('%H:%M') if record.created_at else '—'}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 6: STAFF MONITOR (Anti-Theft)
    # ============================================

    with tab_staff:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;border-radius:12px;
                    padding:1.5rem;box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)

        st.markdown("### 🛡️ Staff Monitor — Anti-Theft Dashboard")
        st.caption("Har staff action yahan record hoti hai — fee collection, edit, aur delete. Koi chori chhupi nahi rahegi.")

        # ── Fraud Alerts (Today) ───────────────────────────────────────────
        try:
            sm_alerts = db.check_fraud_alerts(gym_id=gym_id)
            if sm_alerts:
                critical_sm = [a for a in sm_alerts if a["severity"] == "critical"]
                hcolor = "#7F1D1D" if critical_sm else "#78350F"
                bcolor = "#EF4444" if critical_sm else "#F59E0B"
                tcolor = "#FCA5A5" if critical_sm else "#FCD34D"
                alert_rows = ""
                for a in sm_alerts:
                    bg2 = "#450A0A" if a["severity"] == "critical" else "#422006"
                    bc2 = "#EF4444" if a["severity"] == "critical" else "#F59E0B"
                    alert_rows += f"""
                    <div style="background:{bg2};border-left:4px solid {bc2};border-radius:8px;padding:0.65rem 1rem;margin-bottom:0.4rem;">
                        <div style="font-weight:700;color:#F8FAFC;">{a['icon']} {a['title']}</div>
                        <div style="color:#CBD5E1;font-size:0.82rem;">{a['detail']}</div>
                    </div>"""
                st.markdown(f"""
                <div style="background:{hcolor};border:2px solid {bcolor};border-radius:12px;padding:1rem;margin-bottom:1rem;">
                    <div style="font-size:1rem;font-weight:800;color:{tcolor};margin-bottom:0.6rem;">
                        {'🚨 CRITICAL: Fori Jaanch Zaroor!' if critical_sm else '⚠️ Suspicious Activity Detected Today'}
                    </div>
                    {alert_rows}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:#052e16;border:1px solid #16a34a;border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;">
                    <span style="color:#4ade80;font-weight:700;">✅ Aaj koi suspicious activity nahi mili — Sab theek hai!</span>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

        # ── Today's Shifts Summary ─────────────────────────────────────────
        st.markdown("#### 💼 Aaj Ki Shifts")
        try:
            today_shifts = db.get_today_shifts(gym_id=gym_id)
            if today_shifts:
                shift_rows = ""
                for s in today_shifts:
                    sm = {"open": ("#34D399","#065F46","🟢 Open"), "closed": ("#60A5FA","#1E3A5F","✅ Closed"), "flagged": ("#F87171","#7F1D1D","🚨 Flagged")}
                    sc2, sbg2, slbl = sm.get(s.status, ("#94A3B8","#1E293B", s.status))
                    diff_html = ""
                    if s.discrepancy is not None and s.status != "open":
                        dc = "#34D399" if s.discrepancy >= 0 else "#F87171"
                        sign = "+" if s.discrepancy >= 0 else ""
                        diff_html = f'<span style="color:{dc};font-weight:700;">{sign}PKR {s.discrepancy:,.0f}</span>'
                    shift_rows += f"""
                    <tr style="border-bottom:1px solid #1E293B;">
                        <td style="padding:0.45rem 0.7rem;color:#F8FAFC;font-weight:600;">{s.staff_user}</td>
                        <td style="padding:0.45rem 0.7rem;color:#94A3B8;">{s.opened_at.strftime('%H:%M') if s.opened_at else '—'}</td>
                        <td style="padding:0.45rem 0.7rem;color:#34D399;">PKR {s.opening_cash:,.0f}</td>
                        <td style="padding:0.45rem 0.7rem;color:#FBBF24;">{'PKR ' + f'{s.expected_cash:,.0f}' if s.expected_cash is not None else '—'}</td>
                        <td style="padding:0.45rem 0.7rem;color:#F8FAFC;">{'PKR ' + f'{s.closing_cash:,.0f}' if s.closing_cash is not None else '—'}</td>
                        <td style="padding:0.45rem 0.7rem;">{diff_html}</td>
                        <td style="padding:0.45rem 0.7rem;"><span style="background:{sbg2};color:{sc2};padding:0.15rem 0.45rem;border-radius:5px;font-size:0.75rem;font-weight:700;">{slbl}</span></td>
                    </tr>"""
                st.markdown(f"""
                <div style="overflow-x:auto;margin-bottom:1rem;">
                <table style="width:100%;border-collapse:collapse;background:#0F172A;border-radius:8px;overflow:hidden;">
                    <thead><tr style="background:#1E3A5F;">
                        <th style="padding:0.55rem 0.7rem;color:#60A5FA;text-align:left;">Staff</th>
                        <th style="padding:0.55rem 0.7rem;color:#60A5FA;">Opened</th>
                        <th style="padding:0.55rem 0.7rem;color:#60A5FA;">Opening</th>
                        <th style="padding:0.55rem 0.7rem;color:#60A5FA;">Expected</th>
                        <th style="padding:0.55rem 0.7rem;color:#60A5FA;">Submitted</th>
                        <th style="padding:0.55rem 0.7rem;color:#60A5FA;">Diff</th>
                        <th style="padding:0.55rem 0.7rem;color:#60A5FA;">Status</th>
                    </tr></thead>
                    <tbody>{shift_rows}</tbody>
                </table></div>
                """, unsafe_allow_html=True)
            else:
                st.info("Aaj koi shift record nahi. Staff ko Fee Collection → 💼 Shift Management se shift shuru karni chahiye.")
        except Exception as e:
            st.warning(f"Shifts load nahi ho sake: {e}")

        st.divider()

        # ── Gym + Date selectors ───────────────────────────────────────────
        gym_opts_sm = {g.name: g.id for g in gyms}
        sm_col1, sm_col2, sm_col3 = st.columns([2, 1, 1])
        with sm_col1:
            if gym_id:
                sm_gid = gym_id
                st.text_input("🏋️ Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True, key="sm_gym")
            else:
                sm_chosen = st.selectbox("🏋️ Select Gym", ["All Gyms"] + list(gym_opts_sm.keys()), key="sm_gym")
                sm_gid = gym_opts_sm.get(sm_chosen)
        with sm_col2:
            sm_from = st.date_input("📅 From", value=date.today().replace(day=1), key="sm_from")
        with sm_col3:
            sm_to = st.date_input("📅 To", value=date.today(), key="sm_to")

        # ── Cash Reconciliation (Today) ────────────────────────────────────
        st.markdown("#### 💵 Today's Cash Reconciliation")
        try:
            today_total, today_count, today_records = db.get_daily_fee_summary(
                gym_id=sm_gid, target_date=date.today()
            )

            # Group by collected_by
            staff_totals = {}
            for r in today_records:
                who = getattr(r, 'collected_by', None) or "Unknown"
                staff_totals[who] = staff_totals.get(who, {"count": 0, "amount": 0.0})
                staff_totals[who]["count"] += 1
                staff_totals[who]["amount"] += (r.amount or 0)

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("💰 Total Collected Today", f"PKR {today_total:,.0f}")
            mc2.metric("🧾 Receipts Issued", str(today_count))
            mc3.metric("👤 Staff Members Active", str(len(staff_totals)))

            if staff_totals:
                rows_html = ""
                for who, info in sorted(staff_totals.items(), key=lambda x: -x[1]["amount"]):
                    rows_html += f"""
                    <tr>
                        <td style="padding:0.5rem 0.75rem;color:#F8FAFC;font-weight:600;">{who}</td>
                        <td style="padding:0.5rem 0.75rem;color:#34D399;font-weight:700;text-align:right;">PKR {info['amount']:,.0f}</td>
                        <td style="padding:0.5rem 0.75rem;color:#94A3B8;text-align:center;">{info['count']}</td>
                    </tr>"""
                st.markdown(f"""
                <table style="width:100%;border-collapse:collapse;background:#0F172A;border-radius:8px;overflow:hidden;margin-top:0.5rem;">
                    <thead>
                        <tr style="background:#1E3A5F;">
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:left;">Staff Member</th>
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:right;">Amount Collected</th>
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:center;">Receipts</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """, unsafe_allow_html=True)
            else:
                st.info("Aaj koi fee collect nahi hui.")
        except Exception as e:
            st.warning(f"Reconciliation data load nahi ho saki: {e}")

        st.divider()

        # ── Activity Log ───────────────────────────────────────────────────
        st.markdown("#### 📋 Staff Activity Log")

        act_col1, act_col2 = st.columns([2, 1])
        with act_col1:
            act_filter_action = st.selectbox(
                "Filter by Action",
                ["All Actions", "FEE_COLLECTED", "FEE_EDITED", "FEE_DELETED"],
                key="sm_action_filter"
            )
        with act_col2:
            act_filter_user = st.text_input("Filter by Staff Name", placeholder="e.g. admin", key="sm_user_filter")

        try:
            logs = db.get_activity_logs(
                gym_id=sm_gid,
                limit=300,
                date_from=sm_from,
                date_to=sm_to,
                user=act_filter_user.strip() if act_filter_user.strip() else None,
                action=act_filter_action if act_filter_action != "All Actions" else None,
            )

            if logs:
                # Colour codes per action
                action_colors = {
                    "FEE_COLLECTED": "#34D399",
                    "FEE_EDITED":    "#FBBF24",
                    "FEE_DELETED":   "#F87171",
                }

                rows_html = ""
                for entry in logs:
                    color = action_colors.get(entry.action, "#94A3B8")
                    ts = entry.created_at.strftime("%d %b %Y  %H:%M") if entry.created_at else "—"
                    amt = f"PKR {entry.amount:,.0f}" if entry.amount is not None else "—"
                    badge_bg = {"FEE_COLLECTED": "#065F46", "FEE_EDITED": "#78350F", "FEE_DELETED": "#7F1D1D"}.get(entry.action, "#1E293B")
                    rows_html += f"""
                    <tr style="border-bottom:1px solid #1E293B;">
                        <td style="padding:0.5rem 0.75rem;color:#94A3B8;font-size:0.8rem;white-space:nowrap;">{ts}</td>
                        <td style="padding:0.5rem 0.75rem;font-weight:700;color:#F8FAFC;">{entry.user}</td>
                        <td style="padding:0.4rem 0.75rem;">
                            <span style="background:{badge_bg};color:{color};padding:0.2rem 0.5rem;border-radius:6px;font-size:0.75rem;font-weight:700;">{entry.action}</span>
                        </td>
                        <td style="padding:0.5rem 0.75rem;color:{color};font-weight:700;text-align:right;">{amt}</td>
                        <td style="padding:0.5rem 0.75rem;color:#CBD5E1;font-size:0.8rem;max-width:300px;overflow:hidden;text-overflow:ellipsis;">{entry.details or '—'}</td>
                        <td style="padding:0.5rem 0.75rem;color:#60A5FA;font-size:0.75rem;">{entry.record_ref or '—'}</td>
                    </tr>"""

                st.markdown(f"""
                <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;background:#0F172A;border-radius:8px;overflow:hidden;font-family:monospace;">
                    <thead>
                        <tr style="background:#1E3A5F;">
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:left;white-space:nowrap;">Time</th>
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:left;">Staff</th>
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:left;">Action</th>
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:right;">Amount</th>
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:left;">Details</th>
                            <th style="padding:0.6rem 0.75rem;color:#60A5FA;text-align:left;">Receipt</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                </div>
                """, unsafe_allow_html=True)

                # Download CSV
                log_data = [{
                    "Time":    e.created_at.strftime("%Y-%m-%d %H:%M") if e.created_at else "",
                    "Staff":   e.user,
                    "Role":    e.role,
                    "Action":  e.action,
                    "Amount":  e.amount,
                    "Details": e.details,
                    "Receipt": e.record_ref,
                } for e in logs]
                import io as _io
                df_log = pd.DataFrame(log_data)
                csv_buf = _io.StringIO()
                df_log.to_csv(csv_buf, index=False)
                st.download_button(
                    "⬇️ Download Log CSV",
                    data=csv_buf.getvalue(),
                    file_name=f"staff_activity_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="sm_csv_download",
                )
            else:
                st.info("Is period mein koi activity record nahi mili. (Fees collect karne ke baad yahan entries aayengi.)")

        except Exception as e:
            st.warning(f"Activity log load nahi ho saki: {e}")

        st.divider()

        # ── AI Fraud Risk Analyzer ─────────────────────────────────────────
        st.markdown("#### 🤖 AI Fraud Risk Analyzer")
        st.caption("AI 30 din ka pura data analyze karke har staff ka risk level aur chori ke patterns batayega.")

        if st.button("🔍 AI Se Analyze Karwao", type="primary", use_container_width=True, key="ai_fraud_btn"):
            with st.spinner("🤖 AI data analyze kar raha hai — please wait..."):
                try:
                    from datetime import timedelta
                    import os, requests as _req

                    thirty_days_ago = datetime.now().date() - timedelta(days=30)

                    # Collect all activity logs for 30 days
                    all_logs = db.get_activity_logs(
                        gym_id=sm_gid, limit=1000,
                        date_from=thirty_days_ago, date_to=datetime.now().date()
                    )

                    # Build per-staff stats
                    from collections import defaultdict
                    staff_stats = defaultdict(lambda: {
                        "collected": 0, "collected_amount": 0.0,
                        "deleted": 0, "deleted_amount": 0.0,
                        "edited": 0,
                        "shift_opened": 0, "shift_closed": 0,
                        "off_hours": 0,
                        "flagged_shifts": 0,
                    })

                    for lg in all_logs:
                        s = staff_stats[lg.user]
                        h = lg.created_at.hour if lg.created_at else 12
                        if lg.action == "FEE_COLLECTED":
                            s["collected"] += 1
                            s["collected_amount"] += (lg.amount or 0)
                            if h < 7 or h >= 22:
                                s["off_hours"] += 1
                        elif lg.action == "FEE_DELETED":
                            s["deleted"] += 1
                            s["deleted_amount"] += (lg.amount or 0)
                        elif lg.action == "FEE_EDITED":
                            s["edited"] += 1
                        elif lg.action == "SHIFT_OPENED":
                            s["shift_opened"] += 1
                        elif lg.action == "SHIFT_CLOSED":
                            s["shift_closed"] += 1
                            if lg.record_ref == "FLAGGED":
                                s["flagged_shifts"] += 1

                    # Build prompt
                    staff_lines = []
                    for name, s in staff_stats.items():
                        del_ratio = round(s["deleted"] / max(s["collected"], 1) * 100, 1)
                        staff_lines.append(
                            f"- {name}: collected {s['collected']} fees (PKR {s['collected_amount']:,.0f}), "
                            f"deleted {s['deleted']} records (PKR {s['deleted_amount']:,.0f}, {del_ratio}% of collected), "
                            f"edited {s['edited']} times, off-hours transactions: {s['off_hours']}, "
                            f"shifts opened: {s['shift_opened']}, shifts closed: {s['shift_closed']}, "
                            f"flagged shifts (cash short): {s['flagged_shifts']}"
                        )

                    if not staff_lines:
                        st.warning("30 din ka koi activity data nahi mila. Pehle fees collect karein taake AI analyze kar sake.")
                    else:
                        prompt = f"""You are an expert financial fraud investigator analyzing gym staff activity data for the past 30 days.

STAFF ACTIVITY DATA (last 30 days):
{chr(10).join(staff_lines)}

Analyze each staff member for theft/fraud risk. For each person provide:
1. Risk Level: CRITICAL / HIGH / MEDIUM / LOW
2. Risk Score: 0-100 (100 = most suspicious)
3. Key red flags found (be specific with numbers)
4. What action the gym owner should take

Important red flags to look for:
- High deletion ratio (>10% of collections deleted = suspicious, >20% = very suspicious)
- Large deleted amounts relative to collected amounts
- Off-hours transactions
- Flagged shifts (cash short)
- Many edits (could be changing amounts after collection)
- Shift opened but not closed (running without accountability)

Respond in Urdu/Roman Urdu. Be direct and specific. Format as:

**[Staff Name]** — Risk Level: [LEVEL] (Score: X/100)
🔴 Red Flags: [specific issues]
✅ Action: [what to do]

End with a 2-line overall summary for the gym owner."""

                        groq_key = os.environ.get("GROQ_API_KEY", "").strip()
                        if not groq_key:
                            st.error("❌ GROQ_API_KEY set nahi hai. AI analysis ke liye key chahiye.")
                        else:
                            resp = _req.post(
                                "https://api.groq.com/openai/v1/chat/completions",
                                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                                json={
                                    "model": "llama-3.3-70b-versatile",
                                    "messages": [{"role": "user", "content": prompt}],
                                    "max_tokens": 1200,
                                    "temperature": 0.3,
                                },
                                timeout=30,
                            )
                            resp.raise_for_status()
                            ai_text = resp.json()["choices"][0]["message"]["content"].strip()

                            st.markdown(f"""
                            <div style="background:#0F172A;border:2px solid #7C3AED;border-radius:12px;padding:1.25rem;margin-top:0.5rem;">
                                <div style="color:#A78BFA;font-weight:800;font-size:1rem;margin-bottom:0.75rem;">
                                    🤖 AI Analysis — Last 30 Days
                                </div>
                                <div style="color:#E2E8F0;font-size:0.9rem;line-height:1.7;white-space:pre-wrap;">{ai_text}</div>
                                <div style="color:#64748B;font-size:0.72rem;margin-top:0.75rem;">
                                    Powered by LLaMA 3.3 70B via Groq · {datetime.now().strftime('%d %b %Y %H:%M')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Save to session for re-read
                            st.session_state["ai_fraud_last_result"] = ai_text

                except Exception as e:
                    st.error(f"❌ AI analysis fail ho gayi: {e}")

        elif st.session_state.get("ai_fraud_last_result"):
            st.markdown(f"""
            <div style="background:#0F172A;border:1px solid #334155;border-radius:12px;padding:1.25rem;margin-top:0.5rem;">
                <div style="color:#94A3B8;font-size:0.75rem;margin-bottom:0.5rem;">Last analysis result (re-run karne ke liye button dabayein):</div>
                <div style="color:#E2E8F0;font-size:0.9rem;line-height:1.7;white-space:pre-wrap;">{st.session_state['ai_fraud_last_result']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)