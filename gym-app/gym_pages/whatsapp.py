import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io
import json
from datetime import date
import urllib.parse
import database as db
import styles


DEFAULT_TEMPLATE = (
    "Hello {name}, this is a reminder from {gym} that your membership expires on {expiry}. "
    "Please renew to continue enjoying our services. Thank you!"
)

URDU_TEMPLATE = (
    "السلام علیکم {name}! {gym} سے یاددہانی: آپ کی ممبرشپ {expiry} کو ختم ہو رہی ہے۔ "
    "براہ کرم جلد تجدید کریں۔ شکریہ! 🏋️"
)


def make_wa_link(phone: str, message: str) -> str:
    clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if clean.startswith("0"):
        clean = "+92" + clean[1:]
    return f"https://wa.me/{clean}?text={urllib.parse.quote(message)}"


def wa_button(link: str, label: str = "💬 Send WhatsApp") -> str:
    return (
        f'<a href="{link}" target="_blank" style="display:inline-block;'
        f'background:#25D366;color:white;padding:0.4rem 1rem;border-radius:8px;'
        f'font-weight:700;text-decoration:none;font-size:0.85rem;">{label}</a>'
    )


def _bulk_open_html(links: list[str], btn_label: str, btn_color: str = "#25D366") -> str:
    """Renders a single button that opens all WhatsApp links in new tabs."""
    links_json = json.dumps(links)
    count = len(links)
    return f"""
    <div style="margin:0.5rem 0;">
      <button onclick="gymproSendAll_{count}()"
        style="background:{btn_color};color:white;border:none;padding:0.6rem 1.4rem;
               border-radius:10px;font-weight:700;font-size:1rem;cursor:pointer;">
        {btn_label} ({count} contacts)
      </button>
    </div>
    <script>
    function gymproSendAll_{count}() {{
      var links = {links_json};
      if (links.length === 0) {{ alert('No contacts to message!'); return; }}
      if (!confirm('This will open ' + links.length + ' WhatsApp tabs.\\n\\nAllow popups if your browser blocks them.')) return;
      links.forEach(function(url, i) {{
        setTimeout(function() {{ window.open(url, '_blank'); }}, i * 400);
      }});
    }}
    </script>
    """


def render(gym_id, role):
    styles.page_header("💬", "WhatsApp Automation",
                       "Auto bulk send · Fee reminders · Absentee alerts · Birthdays")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    # ── Settings expander ──────────────────────────────────────────────────────
    with st.expander("⚙️ Message Settings", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            days_threshold = st.number_input(
                "Fee reminder — days ahead", min_value=1, max_value=60,
                value=5, step=1, key="wa_days_threshold",
            )
        with c2:
            absent_days = st.number_input(
                "Absentee alert after (days)", min_value=1, max_value=30,
                value=3, step=1, key="wa_absent_days",
            )
        with c3:
            lang = st.radio("Message language", ["English", "Urdu"], horizontal=True,
                            key="wa_lang")
        template = st.text_area(
            "Custom Fee Reminder Template",
            value=URDU_TEMPLATE if lang == "Urdu" else DEFAULT_TEMPLATE,
            height=80, key="wa_template",
            help="Placeholders: {name} {gym} {expiry} {days}",
        )
        st.caption("💡 WhatsApp links open WhatsApp Web / App — popups must be allowed in browser.")

    st.divider()

    # Shared gym selector
    def gym_selector(tab_key):
        if gym_id:
            return gym_id
        opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
        return opts[st.selectbox("Gym", list(opts.keys()), key=f"wa_gym_{tab_key}")]

    tab_auto, tab_expiry, tab_absent, tab_birthday, tab_streak = st.tabs([
        "🤖 Auto-Send Dashboard",
        "⏰ Fee Expiry",
        "🚶 Absentee Alerts",
        "🎂 Birthdays",
        "🔥 Streaks",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 0 — AUTO-SEND DASHBOARD (new)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_auto:
        st.markdown("### 🤖 One-Click Bulk WhatsApp Sender")
        st.info(
            "**How it works:** Click any 'Send All' button below → your browser opens "
            "each member's WhatsApp chat pre-filled with the message. "
            "Just tap **Send** in WhatsApp — done in seconds!"
        )

        sel_gid_auto = gym_selector("auto")

        # ── Gather all pending contacts ───────────────────────────────────────
        expiring = db.get_expiring_members(days=int(days_threshold), gym_id=sel_gid_auto)
        absent_list = db.get_absent_members(days=int(absent_days), gym_id=sel_gid_auto)
        bday_list = db.get_birthday_members(days_ahead=1, gym_id=sel_gid_auto)

        # Build link lists
        fee_links, fee_rows = [], []
        for m, days_left in expiring:
            if not m.phone:
                continue
            gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
            tip = db.get_health_tip(m.id)
            msg = template.format(name=m.full_name, gym=gym_name,
                                  expiry=m.expiry_date, days=days_left)
            full_msg = f"{msg}\n\n💪 Health Tip: {tip}"
            fee_links.append(make_wa_link(m.phone, full_msg))
            fee_rows.append({"Name": m.full_name, "Phone": m.phone,
                             "Days Left": days_left, "Gym": gym_name})

        abs_links, abs_rows = [], []
        for m in absent_list:
            if not m.phone:
                continue
            gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
            msg = (f"Hi {m.full_name}! 🌟 We miss you at {gym_name}!\n\n"
                   f"It's been a while — come back and keep your fitness journey going! 💪\n\n"
                   f"Your {gym_name} team is waiting for you. See you soon! 🏋️")
            abs_links.append(make_wa_link(m.phone, msg))
            abs_rows.append({"Name": m.full_name, "Phone": m.phone, "Gym": gym_name})

        bd_links, bd_rows = [], []
        for m, days_to_bday in bday_list:
            if not m.phone:
                continue
            gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
            msg = (f"🎂 Happy Birthday {m.full_name}! 🎉\n\n"
                   f"The entire {gym_name} family wishes you a wonderful birthday! "
                   f"Come in for a complimentary session today! 🎁\n\n"
                   f"Keep staying fit — you inspire us all! 💪")
            bd_links.append(make_wa_link(m.phone, msg))
            bd_rows.append({"Name": m.full_name, "Phone": m.phone, "Gym": gym_name,
                            "Birthday": "Today! 🎉" if days_to_bday == 0 else f"In {days_to_bday}d"})

        # ── Summary cards ─────────────────────────────────────────────────────
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("⏰ Fee Expiry", len(fee_links), f"{len(expiring)-len(fee_links)} no phone")
        mc2.metric("🚶 Absent Members", len(abs_links), f"{len(absent_list)-len(abs_links)} no phone")
        mc3.metric("🎂 Birthdays Today", len(bd_links))

        st.divider()

        # ── One-click bulk send buttons ───────────────────────────────────────
        all_links = fee_links + abs_links + bd_links

        if all_links:
            st.markdown("#### 📤 Send Everything at Once")
            components.html(
                _bulk_open_html(all_links, "🚀 Send ALL Pending Messages", "#7C3AED"),
                height=70,
            )
            st.caption(f"Total: {len(all_links)} WhatsApp messages ready to send")
            st.divider()

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown(f"**⏰ Fee Reminders — {len(fee_links)} contacts**")
            if fee_links:
                components.html(
                    _bulk_open_html(fee_links, "⏰ Send Fee Reminders", "#EF4444"),
                    height=70,
                )
                if fee_rows:
                    st.dataframe(pd.DataFrame(fee_rows), use_container_width=True,
                                 hide_index=True)
            else:
                st.success("✅ No fee reminders pending")

        with col_b:
            st.markdown(f"**🚶 Absentee Alerts — {len(abs_links)} contacts**")
            if abs_links:
                components.html(
                    _bulk_open_html(abs_links, "🚶 Send Absent Alerts", "#F59E0B"),
                    height=70,
                )
                if abs_rows:
                    st.dataframe(pd.DataFrame(abs_rows), use_container_width=True,
                                 hide_index=True)
            else:
                st.success("✅ No absentee alerts pending")

        with col_c:
            st.markdown(f"**🎂 Birthday Wishes — {len(bd_links)} contacts**")
            if bd_links:
                components.html(
                    _bulk_open_html(bd_links, "🎂 Send Birthday Wishes", "#25D366"),
                    height=70,
                )
                if bd_rows:
                    st.dataframe(pd.DataFrame(bd_rows), use_container_width=True,
                                 hide_index=True)
            else:
                st.success("✅ No birthdays today")

        # ── Daily auto-check summary ──────────────────────────────────────────
        st.divider()
        st.markdown("#### 📅 Daily Notification Summary")
        total_pending = len(all_links)
        if total_pending == 0:
            st.success("🎉 All caught up! No pending WhatsApp notifications for today.")
        else:
            st.warning(
                f"📬 **{total_pending} messages pending** for today. "
                f"Click the buttons above to send them all in one go!"
            )

        # Export all contacts
        if all_links:
            all_rows = (
                [{"Type": "Fee Expiry", **r} for r in fee_rows] +
                [{"Type": "Absent", **r} for r in abs_rows] +
                [{"Type": "Birthday", **r} for r in bd_rows]
            )
            buf = io.StringIO()
            pd.DataFrame(all_rows).to_csv(buf, index=False)
            st.download_button(
                "⬇️ Export All Pending Contacts",
                data=buf.getvalue().encode(),
                file_name=f"wa_pending_{date.today()}.csv",
                mime="text/csv",
                key="wa_auto_export",
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — FEE EXPIRY REMINDERS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_expiry:
        sel_gid_exp = gym_selector("expiry")
        expiring = db.get_expiring_members(days=int(days_threshold), gym_id=sel_gid_exp)

        if not expiring:
            st.success(f"✅ No members expiring within {int(days_threshold)} days!")
        else:
            urgent = sum(1 for _, d in expiring if d <= 2)
            ac1, ac2, ac3 = st.columns(3)
            ac1.metric("To Notify", len(expiring))
            ac2.metric("Urgent (≤ 2 days)", urgent)
            ac3.metric("Upcoming", len(expiring) - urgent)

            # Quick bulk-send at top of tab too
            tab_fee_links = []
            for m, days_left in expiring:
                if m.phone:
                    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                    tip = db.get_health_tip(m.id)
                    msg = template.format(name=m.full_name, gym=gym_name,
                                          expiry=m.expiry_date, days=days_left)
                    tab_fee_links.append(make_wa_link(m.phone, f"{msg}\n\n💪 {tip}"))
            if tab_fee_links:
                components.html(
                    _bulk_open_html(tab_fee_links, "⏰ Send All Fee Reminders", "#EF4444"),
                    height=70,
                )
            st.divider()

            rows = []
            for m, days_left in sorted(expiring, key=lambda x: x[1]):
                gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                tip = db.get_health_tip(m.id)
                msg = template.format(name=m.full_name, gym=gym_name,
                                      expiry=m.expiry_date, days=days_left)
                full_msg = f"{msg}\n\n💪 {tip}"
                phone = m.phone or ""
                urgency = "🔴" if days_left <= 2 else "🟡" if days_left <= 4 else "🟢"
                wa_link = make_wa_link(phone, full_msg) if phone else None

                with st.expander(
                    f"{urgency} {m.full_name} — {days_left} day(s) left | {gym_name}",
                    expanded=days_left <= 2,
                ):
                    e1, e2 = st.columns([3, 1])
                    with e1:
                        st.markdown(f"**Serial:** `{m.serial_number}` · **Phone:** {phone or '—'}")
                        st.markdown(f"**Membership:** {m.membership_type} · **Fee:** PKR {m.fee_amount:,.0f}")
                        st.info(full_msg)
                    with e2:
                        if wa_link:
                            st.markdown(wa_button(wa_link), unsafe_allow_html=True)
                        else:
                            st.warning("No phone")

                rows.append({"Urgency": urgency, "Name": m.full_name, "Phone": phone or "—",
                             "Gym": gym_name, "Expires": m.expiry_date, "Days Left": days_left})

            st.divider()
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            buf = io.StringIO(); df.to_csv(buf, index=False)
            st.download_button("⬇️ Export List", data=buf.getvalue().encode(),
                               file_name=f"fee_reminders_{date.today()}.csv",
                               mime="text/csv", key="wa_exp_export")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ABSENTEE ALERTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_absent:
        sel_gid_abs = gym_selector("absent")
        st.markdown(f"**Members absent for more than {int(absent_days)} consecutive days**")
        absent_members = db.get_absent_members(days=int(absent_days), gym_id=sel_gid_abs)

        if not absent_members:
            st.success(f"✅ All active members attended within the last {int(absent_days)} days!")
        else:
            st.warning(f"⚠️ {len(absent_members)} member(s) have not checked in recently")
            tab_abs_links = []
            for m in absent_members:
                if m.phone:
                    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                    msg = (f"Hi {m.full_name}! 🌟 We miss you at {gym_name}!\n\n"
                           f"It's been a few days — come back and keep the momentum going! 💪\n\n"
                           f"See you soon! 🏋️")
                    tab_abs_links.append(make_wa_link(m.phone, msg))
            if tab_abs_links:
                components.html(
                    _bulk_open_html(tab_abs_links, "🚶 Send All Absentee Alerts", "#F59E0B"),
                    height=70,
                )
            st.divider()
            for m in absent_members:
                gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                phone = m.phone or ""
                msg = (f"Hi {m.full_name}! 🌟 We miss you at {gym_name}!\n\n"
                       f"It's been a few days since we saw you — your fitness journey matters to us. "
                       f"Come back and keep up the great work! 💪\n\nSee you soon! 🏋️")
                wa_link = make_wa_link(phone, msg) if phone else None
                with st.expander(f"🚶 {m.full_name} — {gym_name} | {phone or 'No phone'}"):
                    ab1, ab2 = st.columns([3, 1])
                    with ab1:
                        st.markdown(f"**Serial:** `{m.serial_number}` · **Membership:** {m.membership_type}")
                        st.info(msg)
                    with ab2:
                        if wa_link:
                            st.markdown(wa_button(wa_link, "💬 Send Alert"), unsafe_allow_html=True)
                        else:
                            st.warning("No phone")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — BIRTHDAY WISHES
    # ══════════════════════════════════════════════════════════════════════════
    with tab_birthday:
        sel_gid_bday = gym_selector("birthday")
        bday_ahead = st.number_input("Show birthdays within (days)", min_value=1,
                                      max_value=30, value=7, step=1, key="wa_bday_days")
        birthday_members = db.get_birthday_members(days_ahead=int(bday_ahead),
                                                    gym_id=sel_gid_bday)

        if not birthday_members:
            st.info(f"No birthdays in the next {int(bday_ahead)} days.")
        else:
            st.success(f"🎂 {len(birthday_members)} birthday(s) upcoming!")
            tab_bd_links = []
            for m, _ in birthday_members:
                if m.phone:
                    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                    msg = (f"🎂 Happy Birthday {m.full_name}! 🎉\n\n"
                           f"The entire {gym_name} family wishes you a wonderful birthday! "
                           f"Come in for a complimentary session today! 🎁\n\n"
                           f"Keep staying fit — you inspire us all! 💪")
                    tab_bd_links.append(make_wa_link(m.phone, msg))
            if tab_bd_links:
                components.html(
                    _bulk_open_html(tab_bd_links, "🎂 Send All Birthday Wishes", "#25D366"),
                    height=70,
                )
            st.divider()
            for m, days_to_bday in birthday_members:
                gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                phone = m.phone or ""
                bday_label = "Today! 🎉" if days_to_bday == 0 else f"in {days_to_bday} day(s)"
                msg = (f"🎂 Happy Birthday {m.full_name}! 🎉\n\n"
                       f"The entire {gym_name} family wishes you a wonderful birthday! "
                       f"As a special gift, please come in for a complimentary session today.\n\n"
                       f"🎁 Special Offer: Show this message for your birthday discount!\n\n"
                       f"With love,\n{gym_name} Team 🏋️")
                wa_link = make_wa_link(phone, msg) if phone else None
                with st.expander(f"🎂 {m.full_name} — Birthday {bday_label} | DOB: {m.dob}",
                                 expanded=days_to_bday == 0):
                    bd1, bd2 = st.columns([3, 1])
                    with bd1:
                        st.markdown(f"**Serial:** `{m.serial_number}` · **Gym:** {gym_name}")
                        st.info(msg)
                    with bd2:
                        if wa_link:
                            st.markdown(wa_button(wa_link, "🎂 Send Wish"), unsafe_allow_html=True)
                        else:
                            st.warning("No phone")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — STREAK WARNINGS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_streak:
        sel_gid_str = gym_selector("streak")
        st.markdown("**Workout Streak Leaderboard & Streak Break Warnings**")

        leaderboard = db.get_attendance_leaderboard(gym_id=sel_gid_str, limit=20)

        if not leaderboard:
            st.info("No attendance data yet.")
        else:
            lb_rows = []
            for rank, entry in enumerate(leaderboard, 1):
                m = entry["member"]
                streak = entry["streak"]
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                lb_rows.append({"Rank": medal, "Name": m.full_name, "Serial": m.serial_number,
                                 "This Month": entry["count"],
                                 "Streak": f"🔥 {streak}" if streak >= 3 else streak,
                                 "Status": m.status})
            st.dataframe(pd.DataFrame(lb_rows), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("**🔥 Send Streak Message to Member**")
            members_all = db.get_members(gym_id=sel_gid_str, status="Active")
            if members_all:
                mem_opts = {f"{m.serial_number} — {m.full_name}": m for m in members_all}
                sel_label = st.selectbox("Select member", list(mem_opts.keys()), key="str_member_sel")
                sel_m = mem_opts[sel_label]
                streak_count = db.get_member_streak(sel_m.id)
                gym_name = next((g.name for g in gyms if g.id == sel_m.gym_id), "Gym")
                tip = db.get_health_tip(sel_m.id + 7)
                phone = sel_m.phone or ""

                if streak_count >= 7:
                    msg = (f"🔥 Amazing {sel_m.full_name}! You have a {streak_count}-day workout streak!\n\n"
                           f"You're crushing it at {gym_name}! Don't stop now! 🏆\n\n{tip}\n\n"
                           f"Keep going — your {gym_name} team is rooting for you! 💪")
                    label = "🔥 Send Streak Celebration"
                elif streak_count >= 3:
                    msg = (f"💪 Great work {sel_m.full_name}! You're on a {streak_count}-day streak!\n\n"
                           f"Consistency is the key to transformation! Keep going! 🎯\n\n{tip}\n\nSee you tomorrow! 🏋️")
                    label = "💪 Send Encouragement"
                else:
                    msg = (f"Hi {sel_m.full_name}! ⚠️ Your workout streak is at risk!\n\n"
                           f"Don't let your progress slip — come in today at {gym_name}! 🦁\n\n{tip}")
                    label = "⚠️ Send Streak Warning"

                st.markdown(styles.metric_card("Streak", f"🔥 {streak_count} days",
                                               sel_m.full_name, "purple"),
                            unsafe_allow_html=True)
                st.info(msg)
                if phone:
                    st.markdown(wa_button(make_wa_link(phone, msg), label), unsafe_allow_html=True)
                else:
                    st.warning("No phone number on file.")

        # Leaderboard broadcast
        if leaderboard and len(leaderboard) >= 3:
            st.divider()
            st.markdown("**📢 Share Weekly Leaderboard**")
            gym_name_lb = next((g.name for g in gyms if g.id == sel_gid_str), "GymPro")
            lb_text = f"🏆 *{gym_name_lb} — Monthly Attendance Leaderboard* 🏆\n\n"
            for rank, entry in enumerate(leaderboard[:5], 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                lb_text += (f"{medal} {entry['member'].full_name} — "
                            f"{entry['count']} sessions | 🔥 {entry['streak']} day streak\n")
            lb_text += f"\nKeep pushing! 💪 #{gym_name_lb.replace(' ', '')}"
            st.code(lb_text, language=None)
            st.caption("Copy the text above and paste into a WhatsApp group.")
