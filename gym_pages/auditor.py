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
    
    tab_headcount, tab_verify, tab_log, tab_summary, tab_present = st.tabs([
        "👥 Headcount Verification",
        "✍️ Cross-Verification Log",
        "📋 Audit Log",
        "⚠️ Dispute / Discrepancy",
        "✅ Present Members"
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