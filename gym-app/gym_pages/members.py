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


# ── Cached DB helpers (avoid repeated queries on every render) ────────────────
@st.cache_data(ttl=30, show_spinner=False)
def _cm(gym_id, status, search):
    return db.get_members(gym_id=gym_id, status=status, search=search)

@st.cache_data(ttl=60, show_spinner=False)
def _ce(gym_id):
    return db.get_expiring_members(days=7, gym_id=gym_id)

@st.cache_data(ttl=30, show_spinner=False)
def _cf(gym_id):
    return db.get_fee_records(gym_id=gym_id)

@st.cache_data(ttl=300, show_spinner=False)
def _photo_bytes_cached(key: str):
    return object_store.get_photo_bytes(key or "")


def save_photo(f, serial: str = "") -> str:
    """Photo save karo Object Storage mein. serial dene par key mein serial number hoga."""
    file_bytes = f.getbuffer()
    key = object_store.upload_photo(bytes(file_bytes), f.name, serial=serial)
    return key


def show_photo(photo_field, w=100):
    """Member photo dikhao — st.image() se (reliable, no base64 HTML)."""
    photo_bytes = _photo_bytes_cached(photo_field or "")

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

    # ── Staff gym restriction ─────────────────────────────────────────────────
    if role == "staff":
        user_gym_id = st.session_state.get("user_gym_id")
        if not gym_id and user_gym_id:
            gym_id = user_gym_id
        elif not gym_id:
            gym_id = gyms[0].id if gyms else None
        if not gym_id:
            st.warning("⚠️ Aapka account kisi gym se assign nahi hai. Admin se rabta karein.")
            return

    # ── STATS — single row, shown once ───────────────────────────────────────
    gym_members = _cm(gym_id, "All", "")
    today = date.today()
    total_members  = len(gym_members)
    active_members = sum(1 for m in gym_members if m.status == "Active")
    expired_count  = 0
    for m in gym_members:
        if m.expiry_date:
            try:
                if (date.fromisoformat(str(m.expiry_date)) - today).days < 0:
                    expired_count += 1
            except Exception:
                pass
    expiring_soon  = len(_ce(gym_id))
    gym_fees       = _cf(gym_id)
    total_collected = sum(f.amount for f in gym_fees) if gym_fees else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👥 Total Members",    total_members)
    c2.metric("✅ Active",           active_members)
    c3.metric("🚨 Expired",          expired_count)
    c4.metric("⏳ Expiring (7 days)", expiring_soon)
    c5.metric("💰 Fees Collected",   f"PKR {total_collected:,.0f}")

    st.markdown("---")

    # ── Tabs — Register first, Members second ────────────────────────────────
    tab_add, tab_list = st.tabs(["➕ Register New Member", "📋 Members"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — MEMBER LIST
    # ══════════════════════════════════════════════════════════════════════════
    with tab_list:
        gym_opts = {g.name: g.id for g in gyms}

        # ── Filters + Export row ──────────────────────────────────────────────
        f1, f2, f3, f4, f5 = st.columns([2, 2, 1, 1, 1])
        with f1:
            if gym_id or role == "staff":
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
            st.button("🔄 Refresh", use_container_width=True, key="ml_refresh",
                      on_click=lambda: _cm.clear())
        with f5:
            st.write("")
            st.write("")
            export_btn = st.button("⬇️ Export CSV", use_container_width=True, key="ml_export")

        members = _cm(selected_gid, status_f, search)

        # ── Export CSV ────────────────────────────────────────────────────────
        if export_btn and members:
            import io as _io2
            rows = []
            for m in members:
                rows.append({
                    "Serial #": m.serial_number,
                    "Full Name": m.full_name,
                    "Phone": m.phone or "",
                    "Email": m.email or "",
                    "Gender": m.gender or "",
                    "DOB": m.dob or "",
                    "Membership": m.membership_type or "",
                    "Fee (PKR)": m.fee_amount or 0,
                    "Join Date": m.join_date,
                    "Expiry Date": m.expiry_date or "",
                    "Status": m.status,
                    "Notes": m.notes or "",
                })
            csv_buf = _io2.StringIO()
            pd.DataFrame(rows).to_csv(csv_buf, index=False)
            st.download_button("📥 Download CSV", data=csv_buf.getvalue(),
                               file_name="members_export.csv", mime="text/csv",
                               key="ml_csv_dl")

        if not members:
            st.info("📭 No members match your filters.")
        else:
            # ── Member selector — at top so detail is immediately visible ─────
            st.markdown("#### 👤 Select Member")
            member_options = {m.serial_number: m for m in members}

            # colour-coded label for expired/expiring
            def _label(s):
                m = member_options[s]
                badge = ""
                if m.expiry_date:
                    try:
                        d = (date.fromisoformat(str(m.expiry_date)) - today).days
                        if d < 0:
                            badge = " 🔴 EXPIRED"
                        elif d <= 7:
                            badge = f" 🟡 {d}d left"
                    except Exception:
                        pass
                return f"{s} — {m.full_name}{badge}"

            selected_serial = st.selectbox(
                "Member",
                list(member_options.keys()),
                format_func=_label,
                key="ml_select_member",
                label_visibility="collapsed",
            )
            selected_m = member_options.get(selected_serial)
            if selected_m:
                _member_detail(selected_m, gyms, role)

            # ── Summary tables (collapsible) ──────────────────────────────────
            active_list   = []
            expired_list  = []
            upcoming_list = []
            unpaid_list   = []

            for m in members:
                expiry_str = str(m.expiry_date) if m.expiry_date else None
                is_expired  = False
                is_upcoming = False
                days_left   = None
                days_over   = None
                if expiry_str:
                    try:
                        exp       = date.fromisoformat(expiry_str)
                        days_left = (exp - today).days
                        if days_left < 0:
                            is_expired = True
                            days_over  = abs(days_left)
                        elif days_left <= 7:
                            is_upcoming = True
                    except Exception:
                        pass

                fee_str = f"PKR {m.fee_amount:,.0f}" if m.fee_amount else "—"
                phone   = m.phone or "—"

                if m.status == "Active" and not is_expired:
                    active_list.append({"#": len(active_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Type": m.membership_type or "—",
                        "Fee": fee_str, "Expiry": expiry_str or "—",
                        "Remaining": f"{days_left}d" if days_left is not None else "—"})
                if is_expired:
                    expired_list.append({"#": len(expired_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Type": m.membership_type or "—",
                        "Fee": fee_str, "Expired": expiry_str or "—", "Overdue": f"{days_over}d"})
                    unpaid_list.append({"#": len(unpaid_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Pending Fee": fee_str,
                        "Since": expiry_str or "—", "Days": f"{days_over}d",
                        "_fee": m.fee_amount or 0})
                if is_upcoming and not is_expired:
                    upcoming_list.append({"#": len(upcoming_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Type": m.membership_type or "—",
                        "Fee": fee_str, "Expiry": expiry_str or "—", "Days Left": f"{days_left}d"})
                if not expiry_str and m.status == "Active":
                    unpaid_list.append({"#": len(unpaid_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Pending Fee": fee_str,
                        "Since": "Not Set", "Days": "—", "_fee": m.fee_amount or 0})

            st.markdown("---")
            unpaid_total = sum(r["_fee"] for r in unpaid_list)

            # ── Inner tabs (no expander = no _arrow_right icon leak on mobile) ──
            tl1, tl2, tl3, tl4 = st.tabs([
                f"Fees ({len(unpaid_list)})",
                f"Active ({len(active_list)})",
                f"Expiring ({len(upcoming_list)})",
                f"Expired ({len(expired_list)})",
            ])

            with tl1:
                if unpaid_list:
                    st.markdown(f"**PKR {unpaid_total:,.0f} pending** — {len(unpaid_list)} members")
                    display = [{k: v for k, v in r.items() if k != "_fee"} for r in unpaid_list]
                    st.dataframe(
                        pd.DataFrame(display),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":           st.column_config.NumberColumn("#", width="small"),
                            "Serial":      st.column_config.TextColumn("Serial #", width="small"),
                            "Name":        st.column_config.TextColumn("Name", width="medium"),
                            "Phone":       st.column_config.TextColumn("Phone", width="small"),
                            "Pending Fee": st.column_config.TextColumn("Fee", width="small"),
                            "Since":       st.column_config.TextColumn("Since", width="small"),
                            "Days":        st.column_config.TextColumn("Days", width="small"),
                        },
                    )
                else:
                    st.success("All fees are up to date!")

            with tl2:
                if active_list:
                    st.dataframe(
                        pd.DataFrame(active_list),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":         st.column_config.NumberColumn("#", width="small"),
                            "Serial":    st.column_config.TextColumn("Serial #", width="small"),
                            "Name":      st.column_config.TextColumn("Name", width="medium"),
                            "Phone":     st.column_config.TextColumn("Phone", width="small"),
                            "Type":      st.column_config.TextColumn("Type", width="small"),
                            "Fee":       st.column_config.TextColumn("Fee", width="small"),
                            "Expiry":    st.column_config.TextColumn("Expiry", width="small"),
                            "Remaining": st.column_config.TextColumn("Left", width="small"),
                        },
                    )
                else:
                    st.info("No active members.")

            with tl3:
                if upcoming_list:
                    st.dataframe(
                        pd.DataFrame(upcoming_list),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":         st.column_config.NumberColumn("#", width="small"),
                            "Serial":    st.column_config.TextColumn("Serial #", width="small"),
                            "Name":      st.column_config.TextColumn("Name", width="medium"),
                            "Phone":     st.column_config.TextColumn("Phone", width="small"),
                            "Type":      st.column_config.TextColumn("Type", width="small"),
                            "Fee":       st.column_config.TextColumn("Fee", width="small"),
                            "Expiry":    st.column_config.TextColumn("Expiry", width="small"),
                            "Days Left": st.column_config.TextColumn("Days Left", width="small"),
                        },
                    )
                else:
                    st.info("No members expiring soon.")

            with tl4:
                if expired_list:
                    st.dataframe(
                        pd.DataFrame(expired_list),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":       st.column_config.NumberColumn("#", width="small"),
                            "Serial":  st.column_config.TextColumn("Serial #", width="small"),
                            "Name":    st.column_config.TextColumn("Name", width="medium"),
                            "Phone":   st.column_config.TextColumn("Phone", width="small"),
                            "Type":    st.column_config.TextColumn("Type", width="small"),
                            "Fee":     st.column_config.TextColumn("Fee", width="small"),
                            "Expired": st.column_config.TextColumn("Expired", width="small"),
                            "Overdue": st.column_config.TextColumn("Overdue", width="small"),
                        },
                    )
                else:
                    st.success("No expired members.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — REGISTER
    # ══════════════════════════════════════════════════════════════════════════
    with tab_add:
        _register_form(gyms, gym_id, role)


def _member_detail(m, gyms, role):
    today = date.today()
    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "—")

    # ── Status badge & days calculation ──────────────────────────────────────
    status_color = {"Active": "#10B981", "Inactive": "#EF4444",
                    "Suspended": "#F59E0B", "Frozen": "#3B82F6"}.get(m.status, "#94A3B8")
    status_emoji = {"Active": "🟢", "Inactive": "🔴",
                    "Suspended": "🟡", "Frozen": "🔵"}.get(m.status, "⚪")
    days_left = None
    is_expired = False
    if m.expiry_date:
        try:
            days_left  = (date.fromisoformat(str(m.expiry_date)) - today).days
            is_expired = days_left < 0
        except Exception:
            pass

    # birthday check
    birthday_today = False
    if m.dob:
        try:
            dob = date.fromisoformat(str(m.dob))
            birthday_today = (dob.month == today.month and dob.day == today.day)
        except Exception:
            pass

    st.markdown("---")

    # ── Top row: photo + info card ────────────────────────────────────────────
    col_photo, col_info = st.columns([1, 3])
    with col_photo:
        show_photo(m.photo_path, w=150)

    with col_info:
        birthday_banner = " 🎂 Birthday Today!" if birthday_today else ""
        st.markdown(
            f"<h3 style='margin:0;color:#F1F5F9'>{status_emoji} {m.full_name}{birthday_banner}</h3>"
            f"<p style='margin:2px 0;color:#A78BFA;font-weight:600'>🆔 {m.serial_number} &nbsp;·&nbsp; "
            f"<span style='color:#64748B'>📍 {gym_name}</span></p>",
            unsafe_allow_html=True,
        )

        # expiry alert
        if is_expired:
            st.error(f"🚨 Membership expired {abs(days_left)} days ago")
        elif days_left is not None and days_left <= 7:
            st.warning(f"⏳ Expires in {days_left} day(s) — {m.expiry_date}")
        elif days_left is not None:
            st.success(f"✅ Active — {days_left} days remaining (expires {m.expiry_date})")

        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown("**📋 Membership**")
            st.write(f"Type: **{m.membership_type or '—'}**")
            st.write(f"Fee: **PKR {m.fee_amount:,.0f}**")
            st.write(f"Joined: **{m.join_date}**")
        with d2:
            st.markdown("**📞 Contact**")
            st.write(f"Phone: **{m.phone or '—'}**")
            st.write(f"Email: **{m.email or '—'}**")
            st.write(f"Gender: **{m.gender or '—'}**")
        with d3:
            st.markdown("**📅 Info**")
            st.write(f"Expiry: **{m.expiry_date or '—'}**")
            st.write(f"DOB: **{m.dob or '—'}**")
            st.write(f"Status: **{m.status}**")

        if m.notes:
            st.info(f"📝 {m.notes}")

    # ── Quick Actions row ─────────────────────────────────────────────────────
    st.markdown("#### ⚡ Quick Actions")
    qa1, qa2, qa3, qa4, qa5 = st.columns(5)

    # WhatsApp — proper clickable link
    with qa1:
        if m.phone:
            clean_phone = m.phone.replace(" ", "").replace("-", "").replace("+", "")
            wa_url = f"https://wa.me/{clean_phone}"
            st.link_button("📱 WhatsApp", wa_url, use_container_width=True)
        else:
            st.button("📱 WhatsApp", disabled=True, use_container_width=True, key=f"wa_dis_{m.id}")

    # Copy serial
    with qa2:
        if st.button("📋 Serial #", use_container_width=True, key=f"copy_{m.id}"):
            st.code(m.serial_number)

    # Renew
    with qa3:
        renew_key = f"renew_active_{m.id}"
        if st.button("📅 Renew", use_container_width=True, key=f"renew_btn_{m.id}"):
            st.session_state[renew_key] = not st.session_state.get(renew_key, False)
            st.rerun()

    # Quick status change
    with qa4:
        qs_key = f"qs_toggle_{m.id}"
        if st.button("🔄 Change Status", use_container_width=True, key=f"qs_btn_{m.id}"):
            st.session_state[qs_key] = not st.session_state.get(qs_key, False)
            st.rerun()

    # Progress
    with qa5:
        if st.button("📊 Progress", use_container_width=True, key=f"progress_{m.id}"):
            st.session_state["page"] = "Progress Tracker"
            st.rerun()

    # ── Quick Status Change panel ─────────────────────────────────────────────
    qs_key = f"qs_toggle_{m.id}"
    if st.session_state.get(qs_key, False):
        with st.container():
            st.markdown("**🔄 Change Status**")
            new_status_cols = st.columns(4)
            for idx, s in enumerate(STATUSES):
                with new_status_cols[idx]:
                    is_cur = m.status == s
                    if st.button(
                        f"{'✅ ' if is_cur else ''}{s}",
                        key=f"qs_{m.id}_{s}",
                        type="primary" if is_cur else "secondary",
                        use_container_width=True,
                    ):
                        db.update_member(m.id, status=s)
                        st.session_state[qs_key] = False
                        _cm.clear()
                        st.success(f"Status updated to **{s}**")
                        st.rerun()

    # ── Renew panel ───────────────────────────────────────────────────────────
    renew_key = f"renew_active_{m.id}"
    if st.session_state.get(renew_key, False):
        with st.container():
            st.markdown("**📅 Renew Membership**")
            st.info(f"Current expiry: **{m.expiry_date or 'Not set'}**")
            try:
                base = date.fromisoformat(str(m.expiry_date)) if m.expiry_date else today
            except Exception:
                base = today

            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                if st.button("1 Month", use_container_width=True, key=f"ren1_{m.id}"):
                    new_exp = base + timedelta(days=30)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()
            with rc2:
                if st.button("3 Months", use_container_width=True, key=f"ren3_{m.id}"):
                    new_exp = base + timedelta(days=90)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()
            with rc3:
                if st.button("6 Months", use_container_width=True, key=f"ren6_{m.id}"):
                    new_exp = base + timedelta(days=180)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()
            with rc4:
                if st.button("1 Year", use_container_width=True, key=f"ren12_{m.id}"):
                    new_exp = base + timedelta(days=365)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()

            custom_exp = st.date_input("Or pick custom date",
                                       value=base + timedelta(days=30),
                                       key=f"renew_date_{m.id}")
            rcc1, rcc2 = st.columns(2)
            with rcc1:
                if st.button("✅ Confirm Custom", key=f"renew_confirm_{m.id}", type="primary"):
                    db.update_member(m.id, expiry_date=str(custom_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {custom_exp}")
                    st.rerun()
            with rcc2:
                if st.button("❌ Cancel", key=f"renew_cancel_{m.id}"):
                    st.session_state[renew_key] = False
                    st.rerun()

    # ── ID Card & QR ─────────────────────────────────────────────────────────
    with st.expander("🪪 ID Card & QR Code"):
        gyms_all = db.get_all_gyms()
        gname = next((g.name for g in gyms_all if g.id == m.gym_id), "GymPro")
        try:
            card_png = id_card.generate_id_card_png(m, gname)
            st.image(card_png, caption="Member ID Card Preview", use_container_width=True)
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("⬇️ Download PNG", data=card_png,
                                   file_name=f"{m.serial_number}_id_card.png", mime="image/png",
                                   key=f"card_png_{m.id}", use_container_width=True)
            with dl2:
                try:
                    card_pdf = id_card.generate_id_card_pdf(m, gname)
                    st.download_button("⬇️ Download PDF", data=card_pdf,
                                       file_name=f"{m.serial_number}_id_card.pdf",
                                       mime="application/pdf", key=f"card_pdf_{m.id}",
                                       use_container_width=True)
                except Exception as e:
                    st.warning(f"PDF: {e}")
            with dl3:
                qr_png = member_qr_png(m.serial_number, box_size=8, border=2)
                st.download_button("⬇️ QR Code", data=qr_png,
                                   file_name=f"{m.serial_number}_qr.png", mime="image/png",
                                   key=f"qr_dl_{m.id}", use_container_width=True)
        except Exception as e:
            st.error(f"ID card error: {e}")
            qr_png = member_qr_png(m.serial_number, box_size=8, border=2)
            st.image(qr_png, width=200, caption=m.serial_number)
            st.download_button("⬇️ QR PNG", data=qr_png,
                               file_name=f"{m.serial_number}_qr.png", mime="image/png",
                               key=f"qr_fb_{m.id}")

    # ── Face Recognition ──────────────────────────────────────────────────────
    with st.expander("📸 Face Recognition Registration"):
        st.info("Register member's face for automatic check-in")
        try:
            import psycopg2, os as os_env
            conn   = psycopg2.connect(os_env.environ.get("DATABASE_URL"))
            cursor = conn.cursor()
            cursor.execute("SELECT face_encoding FROM members WHERE id = %s", (m.id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result and result[0]:
                st.success("✅ Face already registered!")
                if st.button("🔄 Re-register Face", key=f"rereg_face_{m.id}"):
                    register_face_for_member(m.id)
            else:
                st.warning("⚠️ No face registered yet.")
                register_face_for_member(m.id)
        except Exception as e:
            st.error(f"Database error: {e}")
            register_face_for_member(m.id)

    # ── Edit & Delete (admin/staff only) ──────────────────────────────────────
    if role in ("admin", "staff"):
        with st.expander("✏️ Edit Member Details", expanded=False):
            _edit_form(m, gyms)

        if role == "admin":
            st.divider()
            col_del1, _ = st.columns([1, 5])
            with col_del1:
                if st.button("🗑️ Delete Member", key=f"del_m_{m.id}", type="primary"):
                    st.session_state[f"confirm_del_m_{m.id}"] = True
            if st.session_state.get(f"confirm_del_m_{m.id}"):
                st.warning("⚠️ Permanently delete this member? Cannot be undone!")
                cd1, cd2 = st.columns(2)
                if cd1.button("✅ Yes, Delete", key=f"cdy_{m.id}", type="primary"):
                    if m.photo_path:
                        object_store.delete_photo(m.photo_path)
                    db.delete_member(m.id)
                    st.success("✅ Member deleted.")
                    st.session_state.pop(f"confirm_del_m_{m.id}", None)
                    _cm.clear()
                    st.rerun()
                if cd2.button("❌ Cancel", key=f"cdn_{m.id}"):
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
            if role == "staff":
                gym_sel = default_name
                st.text_input("🏋️ Gym", value=default_name, disabled=True, key="reg_gym_display")
            else:
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
                    if photo_path and serial:
                        new_key = f"member_photos/{serial}.jpg"
                        if object_store.rename_photo(photo_path, new_key):
                            member = db.get_member_by_serial(serial)
                            if member and not photo_path.startswith("http"):
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
                photo_bytes = photo.getbuffer()
                uploaded_key = object_store.upload_photo(bytes(photo_bytes), photo.name, serial=m.serial_number)
                if m.photo_path and m.photo_path != uploaded_key:
                    try:
                        object_store.delete_photo(m.photo_path)
                    except Exception:
                        pass
                photo_path = uploaded_key
                object_store.get_photo_bytes.clear()
                st.session_state.photo_cache = {}
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
    import psycopg2

    try:
        from deepface import DeepFace
        import cv2
    except ImportError:
        st.warning("⚠️ Face registration feature is not available on this platform. Please use the Replit version for face recognition.")
        return
    
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