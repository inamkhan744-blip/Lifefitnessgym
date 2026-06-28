import streamlit as st
import pandas as pd
import os
import uuid
from PIL import Image
from datetime import date, timedelta
import database as db
import styles
from qr_utils import member_qr_png
import object_store
import id_card

GENDERS = ["Male", "Female", "Other", "Prefer not to say"]
STATUSES = ["Active", "Inactive", "Suspended", "Frozen"]


def save_photo(f, serial: str = "") -> str:
    """Photo save karo Object Storage mein. serial dene par key mein serial number hoga."""
    file_bytes = f.getbuffer()
    key = object_store.upload_photo(bytes(file_bytes), f.name, serial=serial)
    return key


def show_photo(photo_field, w=100):
    """Member photo dikhao — st.image() se (reliable, no base64 HTML)."""
    photo_bytes = object_store.get_photo_bytes(photo_field or "")

    size = f"{w}px"
    if photo_bytes:
        import io as _io
        st.image(_io.BytesIO(photo_bytes), width=w)
    else:
        st.markdown(
            f'<div style="width:{size};height:{size};border-radius:10px;'
            f'background:#1E293B;border:1px solid #334155;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:{w // 2}px;color:#94A3B8;">👤</div>',
            unsafe_allow_html=True,
        )


def render(gym_id, role):
    styles.page_header("👥", "Members", "Register, search and manage gym members")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym in **Gym Setup** first.")
        return

    # ============================================
    # STATS OVERVIEW - 4 Cards (Simple)
    # ============================================
    
    all_members = db.get_members()
    total_members = len(all_members)
    active_members = sum(1 for m in all_members if m.status == "Active")
    expiring_soon = len(db.get_expiring_members(days=7, gym_id=gym_id))
    
    all_fees = db.get_fee_records()
    total_collected = sum(f.amount for f in all_fees) if all_fees else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Members", total_members)
    with col2:
        st.metric("✅ Active Members", active_members)
    with col3:
        st.metric("⚠️ Expiring Soon", expiring_soon)
    with col4:
        st.metric("💰 Total Fees", f"PKR {total_collected:,.0f}")
    
    st.markdown("---")

    tab_add, tab_list = st.tabs(["➕ Register Member", "📋 Member List"])

    with tab_add:
        _register_form(gyms, gym_id, role)

    with tab_list:
        f1, f2, f3, f4 = st.columns([2, 2, 1, 1])
        gym_opts = {g.name: g.id for g in gyms}

        with f1:
            if gym_id:
                chosen_gym_name = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
                st.text_input("🏋️ Gym", value=chosen_gym_name, disabled=True, key="ml_gym_display")
                selected_gid = gym_id
            else:
                opts = {"All Gyms": None} | gym_opts
                chosen = st.selectbox("🏋️ Gym", list(opts.keys()), key="ml_gym")
                selected_gid = opts[chosen]
        with f2:
            search = st.text_input("🔍 Search", placeholder="Name, serial, phone…", key="ml_search")
        with f3:
            status_f = st.selectbox("📊 Status", ["All"] + STATUSES, key="ml_status")
        with f4:
            st.write("")
            st.write("")
            st.button("🔄 Refresh", use_container_width=True, key="ml_refresh")

        members = db.get_members(gym_id=selected_gid, status=status_f, search=search)

        # ============================================
        # STATS
        # ============================================
        
        active_c = sum(1 for m in members if m.status == "Active")
        inactive_c = sum(1 for m in members if m.status == "Inactive")
        suspended_c = sum(1 for m in members if m.status == "Suspended")
        frozen_c = sum(1 for m in members if m.status == "Frozen")
        
        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
        col_s1.metric("📊 Total", len(members))
        col_s2.metric("✅ Active", active_c)
        col_s3.metric("⛔ Inactive", inactive_c)
        col_s4.metric("⏸️ Suspended", suspended_c)
        col_s5.metric("❄️ Frozen", frozen_c)

        st.divider()

        if not members:
            st.info("📭 No members match your filters.")
        else:
            # ============================================
            # SIMPLE TABLE (Without Custom CSS)
            # ============================================
            
            rows = []
            for m in members:
                # Status badge
                status_badge = {
                    "Active": "🟢 Active",
                    "Inactive": "🔴 Inactive",
                    "Suspended": "🟡 Suspended",
                    "Frozen": "🔵 Frozen",
                }.get(m.status, m.status)
                
                # Expiry display
                expiry_display = m.expiry_date or "—"
                if m.expiry_date:
                    try:
                        exp = date.fromisoformat(m.expiry_date)
                        days = (exp - date.today()).days
                        if days < 0:
                            expiry_display = f"🚨 {m.expiry_date} (EXPIRED)"
                        elif days <= 3:
                            expiry_display = f"⚠️ {m.expiry_date} ({days}d)"
                        elif days <= 7:
                            expiry_display = f"⏳ {m.expiry_date} ({days}d)"
                        else:
                            expiry_display = f"✅ {m.expiry_date}"
                    except:
                        pass
                
                rows.append({
                    "Serial": m.serial_number,
                    "Name": m.full_name,
                    "Membership": m.membership_type,
                    "Phone": m.phone or "—",
                    "Fee": f"PKR {m.fee_amount:,.0f}",
                    "Expiry": expiry_display,
                    "Status": status_badge,
                })
            
            df = pd.DataFrame(rows)
            
            # Display simple dataframe
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "Serial": st.column_config.TextColumn("Serial", width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Membership": st.column_config.TextColumn("Membership", width="small"),
                    "Phone": st.column_config.TextColumn("Phone", width="small"),
                    "Fee": st.column_config.TextColumn("Fee", width="small"),
                    "Expiry": st.column_config.TextColumn("Expiry", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                }
            )
            
            st.caption(f"📋 Showing {len(members)} members")

            st.divider()
            st.markdown("### 👤 Member Details")
            
            # ============================================
            # MEMBER SELECTION
            # ============================================
            
            member_options = {m.serial_number: m for m in members}
            
            selected_serial = st.selectbox(
                "Select member to view/edit",
                list(member_options.keys()),
                format_func=lambda s: f"{s} — {member_options[s].full_name}",
                key="ml_select_member",
            )
            
            selected_m = member_options.get(selected_serial)
            if selected_m:
                _member_detail(selected_m, gyms, role)


def _member_detail(m, gyms, role):
    # ============================================
    # ENHANCED MEMBER DETAIL
    # ============================================
    
    col_photo, col_info = st.columns([1, 4])
    with col_photo:
        show_photo(m.photo_path, w=160)
    
    with col_info:
        gym_name = next((g.name for g in gyms if g.id == m.gym_id), "—")
        
        # Status badge
        status_emoji = {
            "Active": "🟢",
            "Inactive": "🔴",
            "Suspended": "🟡",
            "Frozen": "🔵",
        }.get(m.status, "⚪")
        
        st.markdown(f"### {status_emoji} {m.full_name}")
        st.caption(f"🆔 {m.serial_number} · 📍 {gym_name}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**📋 Membership**")
            st.write(f"Type: **{m.membership_type}**")
            st.write(f"Fee: **PKR {m.fee_amount:,.0f}**")
            st.write(f"Joined: **{m.join_date}**")
        
        with col2:
            st.markdown("**📞 Contact**")
            st.write(f"Phone: **{m.phone or '—'}**")
            st.write(f"Email: **{m.email or '—'}**")
            st.write(f"Gender: **{m.gender or '—'}**")
        
        with col3:
            st.markdown("**📅 Dates**")
            st.write(f"Expires: **{m.expiry_date or '—'}**")
            st.write(f"DOB: **{m.dob or '—'}**")
            if m.expiry_date:
                try:
                    exp = date.fromisoformat(m.expiry_date)
                    days = (exp - date.today()).days
                    if days >= 0:
                        st.write(f"Days Left: **{days} days**")
                    else:
                        st.write(f"Days Left: **{days} days (EXPIRED)**")
                except:
                    pass
        
        if m.notes:
            st.info(f"📝 Notes: {m.notes}")

    # ============================================
    # QUICK ACTION BUTTONS
    # ============================================
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    with col_q1:
        if st.button("📱 WhatsApp", use_container_width=True, key=f"wa_{m.id}"):
            if m.phone:
                wa_link = f"https://wa.me/{m.phone.replace(' ', '').replace('-', '')}"
                st.markdown(f'<a href="{wa_link}" target="_blank">Open WhatsApp</a>', unsafe_allow_html=True)
            else:
                st.warning("No phone number")
    
    with col_q2:
        if st.button("📋 Copy Serial", use_container_width=True, key=f"copy_{m.id}"):
            st.code(m.serial_number)
    
    with col_q3:
        renew_key = f"renew_active_{m.id}"
        if st.button("📅 Renew Membership", use_container_width=True, key=f"renew_btn_{m.id}"):
            st.session_state[renew_key] = not st.session_state.get(renew_key, False)
            st.rerun()
    
    with col_q4:
        if st.button("📊 View Progress", use_container_width=True, key=f"progress_{m.id}"):
            st.session_state["page"] = "Progress Tracker"
            st.rerun()
    
    # ============================================
    # RENEW POPUP
    # ============================================
    
    renew_key = f"renew_active_{m.id}"
    if st.session_state.get(renew_key, False):
        with st.container():
            st.markdown("---")
            st.markdown("#### 📅 Renew Membership")
            
            st.info(f"Current expiry: **{m.expiry_date or 'Not set'}**")
            
            new_expiry = st.date_input(
                "New Expiry Date",
                value=date.fromisoformat(m.expiry_date) + timedelta(days=30) if m.expiry_date else date.today() + timedelta(days=30),
                key=f"renew_date_{m.id}"
            )
            
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                if st.button("✅ Confirm Renewal", key=f"renew_confirm_{m.id}", type="primary"):
                    db.update_member(m.id, expiry_date=str(new_expiry), status="Active")
                    st.success(f"✅ Membership renewed until {new_expiry}!")
                    st.session_state[renew_key] = False
                    st.balloons()
                    st.rerun()
            with col_r2:
                if st.button("❌ Cancel", key=f"renew_cancel_{m.id}"):
                    st.session_state[renew_key] = False
                    st.rerun()
            with col_r3:
                if st.button("🗑️ Close", key=f"renew_close_{m.id}"):
                    st.session_state[renew_key] = False
                    st.rerun()

    # ============================================
    # QR CODE
    # ============================================
    
    with st.expander("🪪 ID Card & QR Code"):
        # ── ID Card preview ──────────────────────────────
        gyms = db.get_all_gyms()
        gym_name = next((g.name for g in gyms if g.id == m.gym_id), "GymPro")

        try:
            card_png = id_card.generate_id_card_png(m, gym_name)
            st.image(card_png, caption="Member ID Card Preview", use_container_width=True)

            dl1, dl2, dl3 = st.columns(3)

            with dl1:
                st.download_button(
                    "⬇️ Download PNG",
                    data=card_png,
                    file_name=f"{m.serial_number}_id_card.png",
                    mime="image/png",
                    key=f"card_png_{m.id}",
                    use_container_width=True,
                )

            with dl2:
                try:
                    card_pdf = id_card.generate_id_card_pdf(m, gym_name)
                    st.download_button(
                        "⬇️ Download PDF",
                        data=card_pdf,
                        file_name=f"{m.serial_number}_id_card.pdf",
                        mime="application/pdf",
                        key=f"card_pdf_{m.id}",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"PDF error: {e}")

            with dl3:
                qr_png = member_qr_png(m.serial_number, box_size=8, border=2)
                st.download_button(
                    "⬇️ QR Code Only",
                    data=qr_png,
                    file_name=f"{m.serial_number}_qr.png",
                    mime="image/png",
                    key=f"qr_dl_{m.id}",
                    use_container_width=True,
                )

        except Exception as e:
            st.error(f"ID card generation error: {e}")
            qr_png = member_qr_png(m.serial_number, box_size=8, border=2)
            st.image(qr_png, width=200, caption=m.serial_number)
            st.download_button("⬇️ QR PNG", data=qr_png,
                               file_name=f"{m.serial_number}_qr.png",
                               mime="image/png", key=f"qr_fb_{m.id}")

    # ============================================
    # FACE RECOGNITION
    # ============================================
    
    with st.expander("📸 Face Recognition Registration"):
        st.info("Register member's face for automatic check-in")
        
        try:
            import psycopg2
            import os as os_env
            DATABASE_URL = os_env.environ.get('DATABASE_URL')
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT face_encoding FROM members WHERE id = %s", (m.id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                st.success("✅ Face already registered for this member!")
                if st.button("🔄 Re-register Face", key=f"rereg_face_{m.id}"):
                    register_face_for_member(m.id)
            else:
                st.warning("⚠️ No face registered yet.")
                register_face_for_member(m.id)
        except Exception as e:
            st.error(f"Database error: {e}")
            register_face_for_member(m.id)

    # ============================================
    # EDIT SECTION
    # ============================================
    
    if role in ("admin", "staff"):
        with st.expander("✏️ Edit Member", expanded=False):
            _edit_form(m, gyms)
        if role == "admin":
            st.divider()
            col_del1, col_del2 = st.columns([1, 5])
            with col_del1:
                if st.button("🗑️ Delete Member", key=f"del_m_{m.id}", type="primary"):
                    st.session_state[f"confirm_del_m_{m.id}"] = True
            if st.session_state.get(f"confirm_del_m_{m.id}"):
                st.warning("⚠️ Permanently delete this member? This action cannot be undone!")
                col_del1, col_del2 = st.columns(2)
                if col_del1.button("✅ Yes, Delete", key=f"cdy_{m.id}", type="primary"):
                    if m.photo_path:
                        object_store.delete_photo(m.photo_path)
                    db.delete_member(m.id)
                    st.success("✅ Member deleted successfully.")
                    st.session_state.pop(f"confirm_del_m_{m.id}", None)
                    st.rerun()
                if col_del2.button("❌ Cancel", key=f"cdn_{m.id}"):
                    st.session_state.pop(f"confirm_del_m_{m.id}", None)
                    st.rerun()


def _register_form(gyms, gym_id, role):
    st.subheader("➕ Register New Member")
    st.caption("Fill in the details below to add a new member")
    
    gym_opts = {g.name: g.id for g in gyms}
    default_name = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)

    with st.form("reg_member_form", clear_on_submit=True):
        st.markdown("#### 📋 Personal Information")
        
        c1, c2 = st.columns(2)
        with c1:
            gym_sel = st.selectbox("🏋️ Gym *", list(gym_opts.keys()),
                                   index=list(gym_opts.keys()).index(default_name),
                                   key="reg_gym_sel")
            full_name = st.text_input("👤 Full Name *", key="reg_full_name", placeholder="e.g., Muhammad Ali")
            phone = st.text_input("📞 Phone", placeholder="+92 300-0000000", key="reg_phone")
            email = st.text_input("📧 Email", key="reg_email", placeholder="example@email.com")
            gender = st.selectbox("⚥ Gender", GENDERS, key="reg_gender")
            dob = st.date_input("🎂 Date of Birth", value=None,
                                min_value=date(1920, 1, 1), max_value=date.today(),
                                key="reg_dob")
        with c2:
            mem_type = st.selectbox("📋 Membership Type *", db.MEMBERSHIP_TYPES, key="reg_mem_type")
            fee_amount = st.number_input("💰 Monthly Fee (PKR)", min_value=0.0, step=5.0, format="%.2f", key="reg_fee")
            join_date = st.date_input("📅 Join Date *", value=date.today(), key="reg_join")
            expiry_date = st.date_input("📅 Expiry Date", value=date.today() + timedelta(days=30), key="reg_expiry")
            status = st.selectbox("📊 Status", STATUSES, key="reg_status")
            notes = st.text_area("📝 Notes", height=60, key="reg_notes", placeholder="Any remarks about this member...")
            photo = st.file_uploader("📷 Member Photo", type=["jpg", "jpeg", "png", "webp"],
                                     key="reg_photo")

        if photo:
            st.image(photo, width=120, caption="📸 Preview")

        st.markdown("---")
        if st.form_submit_button("✅ Register Member", type="primary", use_container_width=True):
            if not full_name.strip():
                st.error("❌ Full name is required!")
            else:
                photo_path = save_photo(photo) if photo else None
                ok, msg, serial = db.add_member(
                    gym_id=gym_opts[gym_sel],
                    full_name=full_name, phone=phone, email=email,
                    gender=gender, dob=str(dob) if dob else "",
                    membership_type=mem_type, fee_amount=fee_amount,
                    join_date=str(join_date),
                    expiry_date=str(expiry_date) if expiry_date else None,
                    photo_path=photo_path, status=status, notes=notes,
                )
                if ok:
                    # Photo key ko serial number se rename karo
                    if photo_path and serial:
                        new_key = f"member_photos/{serial}.jpg"
                        if object_store.rename_photo(photo_path, new_key):
                            member = db.get_member_by_serial(serial)
                            if member:
                                db.update_member_photo_path(member.id, new_key)
                    st.success(f"🎉 {msg}")
                    st.balloons()
                else:
                    st.error(f"❌ {msg}")


def _edit_form(m, gyms):
    gym_opts = {g.name: g.id for g in gyms}
    cur_gym = next((g.name for g in gyms if g.id == m.gym_id), gyms[0].name)

    with st.form(f"edit_member_form_{m.id}"):
        st.markdown("#### ✏️ Edit Member Details")
        
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("👤 Full Name *", value=m.full_name, key=f"ef_name_{m.id}")
            phone = st.text_input("📞 Phone", value=m.phone or "", key=f"ef_phone_{m.id}")
            email = st.text_input("📧 Email", value=m.email or "", key=f"ef_email_{m.id}")
            gender_i = GENDERS.index(m.gender) if m.gender in GENDERS else 0
            gender = st.selectbox("⚥ Gender", GENDERS, index=gender_i, key=f"ef_gender_{m.id}")
            dob_val = None
            if m.dob:
                try:
                    dob_val = date.fromisoformat(m.dob)
                except Exception:
                    pass
            dob = st.date_input("🎂 DOB", value=dob_val, min_value=date(1920, 1, 1),
                                max_value=date.today(), key=f"ef_dob_{m.id}")
        with c2:
            mi = db.MEMBERSHIP_TYPES.index(m.membership_type) if m.membership_type in db.MEMBERSHIP_TYPES else 0
            mem_type = st.selectbox("📋 Membership Type *", db.MEMBERSHIP_TYPES, index=mi, key=f"ef_mtype_{m.id}")
            fee_amount = st.number_input("💰 Fee (PKR)", value=float(m.fee_amount or 0),
                                         min_value=0.0, step=5.0, key=f"ef_fee_{m.id}")
            join_date = st.date_input("📅 Join Date *", value=date.fromisoformat(m.join_date),
                                      key=f"ef_join_{m.id}")
            exp_val = date.fromisoformat(m.expiry_date) if m.expiry_date else date.today() + timedelta(days=30)
            expiry_date = st.date_input("📅 Expiry Date", value=exp_val, key=f"ef_expiry_{m.id}")
            si = STATUSES.index(m.status) if m.status in STATUSES else 0
            status = st.selectbox("📊 Status", STATUSES, index=si, key=f"ef_status_{m.id}")
            notes = st.text_area("📝 Notes", value=m.notes or "", height=60, key=f"ef_notes_{m.id}")
            photo = st.file_uploader("📷 Replace Photo", type=["jpg", "jpeg", "png", "webp"],
                                     key=f"ef_photo_{m.id}")

        if photo:
            st.image(photo, width=100, caption="📸 New Photo Preview")

        st.markdown("---")
        col_s, col_c = st.columns(2)
        save = col_s.form_submit_button("💾 Save Changes", type="primary")
        cancel = col_c.form_submit_button("❌ Cancel")

        if cancel:
            st.rerun()
        if save:
            photo_path = m.photo_path
            if photo:
                new_key = f"member_photos/{m.serial_number}.jpg"
                photo_bytes = photo.getbuffer()
                object_store.upload_photo(bytes(photo_bytes), photo.name, serial=m.serial_number)
                if m.photo_path and m.photo_path != new_key:
                    try:
                        object_store.delete_photo(m.photo_path)
                    except Exception:
                        pass
                photo_path = new_key
            ok, msg = db.update_member(
                m.id, full_name=full_name, phone=phone, email=email,
                gender=gender, dob=str(dob) if dob else "",
                membership_type=mem_type, fee_amount=fee_amount,
                join_date=str(join_date), expiry_date=str(expiry_date),
                photo_path=photo_path, status=status, notes=notes,
            )
            if ok:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ========== FACE REGISTRATION FUNCTION ==========
def register_face_for_member(member_id):
    """Register face for existing member - PostgreSQL compatible"""
    import tempfile
    import os
    import pickle
    from deepface import DeepFace
    import cv2
    import psycopg2
    
    st.subheader("📸 Register Face")
    st.info("Make sure good lighting and face is clearly visible")
    
    picture = st.camera_input("📷 Take a photo of member", key=f"face_cam_{member_id}")
    
    if picture:
        temp_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
        with open(temp_path, 'wb') as f:
            f.write(picture.getbuffer())
        
        with st.spinner("🔄 Processing face..."):
            try:
                embedding = DeepFace.represent(
                    img_path=temp_path,
                    model_name='ArcFace',
                    detector_backend='retinaface',
                    enforce_detection=True
                )[0]['embedding']
                
                encoding_blob = pickle.dumps(embedding)
                
                import os as os_env
                DATABASE_URL = os_env.environ.get('DATABASE_URL')
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE members SET face_encoding = %s WHERE id = %s",
                    (encoding_blob, member_id)
                )
                conn.commit()
                cursor.close()
                conn.close()
                
                st.success("✅ Face registered successfully!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"❌ No face detected or error: {e}")
                st.info("Please take a clear photo with good lighting")
        
        os.unlink(temp_path)