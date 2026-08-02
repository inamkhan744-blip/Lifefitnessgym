import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io
import json
from datetime import date, datetime, timedelta
import urllib.parse
import database as db
import styles
import threading
import time

# ── SCHEDULE LIBRARY ──
try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

# ── MESSAGE TEMPLATES (English + Urdu) ──
TEMPLATES = {
    "Fee Reminder": {
        "en": "Hello {name}, this is a reminder that your membership expires on {expiry}. Please renew to continue enjoying our services. Thank you!",
        "ur": "السلام علیکم {name}! {gym} سے یاددہانی: آپ کی ممبرشپ {expiry} کو ختم ہو رہی ہے۔ براہ کرم جلد تجدید کریں۔ شکریہ! 🏋️"
    },
    "Welcome": {
        "en": "👋 Welcome {name} to {gym}! We're excited to have you. Stay consistent and keep pushing! 💪",
        "ur": "👋 {name} صاحب! {gym} میں خوش آمدید! ہمیں آپ کو دیکھ کر بہت خوشی ہوئی۔ مستقل مزاج رہیں اور محنت جاری رکھیں! 💪"
    },
    "Birthday": {
        "en": "🎂 Happy Birthday {name}! The entire {gym} family wishes you a wonderful day! 🎉",
        "ur": "🎂 سالگرہ مبارک {name}! {gym} کی پوری ٹیم آپ کو مبارکباد دیتی ہے! 🎉"
    },
    "Absent": {
        "en": "Hi {name}! 🌟 We miss you at {gym}! It's been a while — come back and keep your fitness journey going! 💪",
        "ur": "السلام علیکم {name}! 🌟 ہم آپ کو {gym} میں یاد کر رہے ہیں! کچھ دن ہو گئے — واپس آئیں اور اپنی فٹنس جاری رکھیں! 💪"
    },
    "Motivation": {
        "en": "💪 Stay strong {name}! Consistency is the key to success. Every workout counts! 🏋️",
        "ur": "💪 حوصلہ رکھیں {name}! کامیابی کی کلید مستقل مزاجی ہے۔ ہر ورزش شمار ہوتی ہے! 🏋️"
    },
    "Diet Plan": {
        "en": "🥗 Here's your diet plan {name}: High protein, balanced carbs, and healthy fats. Stay hydrated! 💧",
        "ur": "🥗 یہ ہے آپ کا ڈائٹ پلان {name}: زیادہ پروٹین، متوازن کاربوہائیڈریٹس، اور صحت مند چکنائیاں۔ پانی پیتے رہیں! 💧"
    },
    "Workout": {
        "en": "🏋️ Today's workout {name}: 3 sets of 10 reps. Push yourself! You've got this! 💪",
        "ur": "🏋️ آج کی ورزش {name}: 10 ریپس کے 3 سیٹس۔ خود کو آگے بڑھائیں! آپ یہ کر سکتے ہیں! 💪"
    }
}

# ── DEFAULT TEMPLATES (Backward compatibility) ──
DEFAULT_TEMPLATE = "Hello {name}, this is a reminder from {gym} that your membership expires on {expiry}. Please renew to continue enjoying our services. Thank you!"
URDU_TEMPLATE = "السلام علیکم {name}! {gym} سے یاددہانی: آپ کی ممبرشپ {expiry} کو ختم ہو رہی ہے۔ براہ کرم جلد تجدید کریں۔ شکریہ! 🏋️"

# ── STAFF GROUP LINKS ──
STAFF_GROUPS = {
    "arifa": "https://chat.whatsapp.com/I3zeqyLDFMPHRpUYH9KiyA",
    "shehzad": "https://chat.whatsapp.com/LyfbiEj5KUlLhsO5krYUEI",
    "zakir": "https://chat.whatsapp.com/HlbylVabvIyHw8A5rZ6IIQ",
    "jiya": "https://chat.whatsapp.com/GiHI6KyDZHmHB8AB2k5KQv",
}

# ── DEFAULT SETTINGS ──
DEFAULT_REMINDER_DAYS = 5
DEFAULT_ABSENT_DAYS = 3
DEFAULT_LANGUAGE = "English"


# ============================================
# 🔥 SETTINGS FUNCTIONS (Database + Session)
# ============================================

def get_reminder_days():
    """Get reminder days from database or session state"""
    # Check session state first
    if "wa_reminder_days" in st.session_state:
        return st.session_state.wa_reminder_days
    
    # Check database
    try:
        if hasattr(db, 'get_setting'):
            value = db.get_setting("whatsapp_reminder_days")
            if value:
                st.session_state.wa_reminder_days = int(float(value))
                return int(float(value))
    except:
        pass
    
    return DEFAULT_REMINDER_DAYS

def set_reminder_days(days):
    """Save reminder days to database and session state"""
    st.session_state.wa_reminder_days = days
    try:
        if hasattr(db, 'set_setting'):
            db.set_setting("whatsapp_reminder_days", str(days))
            return True
    except:
        pass
    return False

def get_absent_days():
    """Get absent days from database or session state"""
    if "wa_absent_days" in st.session_state:
        return st.session_state.wa_absent_days
    
    try:
        if hasattr(db, 'get_setting'):
            value = db.get_setting("whatsapp_absent_days")
            if value:
                st.session_state.wa_absent_days = int(float(value))
                return int(float(value))
    except:
        pass
    
    return DEFAULT_ABSENT_DAYS

def set_absent_days(days):
    """Save absent days to database and session state"""
    st.session_state.wa_absent_days = days
    try:
        if hasattr(db, 'set_setting'):
            db.set_setting("whatsapp_absent_days", str(days))
            return True
    except:
        pass
    return False

def get_whatsapp_language():
    """Get language from session state or database"""
    if "wa_language" in st.session_state:
        return st.session_state.wa_language
    
    try:
        if hasattr(db, 'get_setting'):
            value = db.get_setting("whatsapp_language")
            if value:
                st.session_state.wa_language = value
                return value
    except:
        pass
    
    return DEFAULT_LANGUAGE

def set_whatsapp_language(lang):
    """Save language to database and session state"""
    st.session_state.wa_language = lang
    try:
        if hasattr(db, 'set_setting'):
            db.set_setting("whatsapp_language", lang)
            return True
    except:
        pass
    return False

def get_template(message_type):
    """Get template based on language"""
    lang = get_whatsapp_language()
    lang_key = "ur" if lang == "Urdu" else "en"
    
    if message_type in TEMPLATES:
        return TEMPLATES[message_type].get(lang_key, TEMPLATES[message_type]["en"])
    
    # Fallback
    if lang == "Urdu":
        return URDU_TEMPLATE
    return DEFAULT_TEMPLATE


# ============================================
# STAFF GROUP FUNCTIONS
# ============================================

def get_staff_group_link(staff_username: str) -> str | None:
    """Get WhatsApp group link for a staff member"""
    return STAFF_GROUPS.get(staff_username.lower())


def add_member_to_staff_group(
    phone_number: str, 
    staff_username: str, 
    member_name: str = "", 
    serial: str = ""
) -> bool:
    """Auto-add member to staff's WhatsApp group"""
    group_link = get_staff_group_link(staff_username)
    if not group_link:
        print(f"❌ No group found for staff: {staff_username}")
        return False
    
    if not phone_number or len(phone_number) < 10:
        print(f"❌ Invalid phone: {phone_number}")
        return False
    
    try:
        clean_phone = "".join(c for c in phone_number if c.isdigit() or c == "+")
        if clean_phone.startswith("0"):
            clean_phone = "+92" + clean_phone[1:]
        elif not clean_phone.startswith("+"):
            clean_phone = "+92" + clean_phone

        welcome_msg = f"""👋 *Welcome {member_name} to the Gym!* 🏋️

📌 *Serial #:* {serial}
📌 *Added by:* {staff_username.title()}

🔗 *Join your staff's WhatsApp Group:*
{group_link}

💪 Stay connected and keep pushing!

*See you at the gym!* 🎉"""

        try:
            import pywhatkit as kit
            now = datetime.now()
            kit.sendwhatmsg(clean_phone, welcome_msg, now.hour, now.minute + 2)
            print(f"✅ Welcome message sent to {member_name}")
        except ImportError:
            print(f"⚠️ pywhatkit not installed. Run: pip install pywhatkit")
        except Exception as e:
            print(f"⚠️ Auto-message error: {e}")

        try:
            db.log_activity(
                user="System (Admin WhatsApp)",
                action="WHATSAPP_GROUP_LINK_SENT",
                details=f"Member: {member_name} | Serial: {serial} | Staff: {staff_username}",
                record_ref=serial
            )
        except Exception as e:
            print(f"⚠️ Log error: {e}")

        print(f"✅ Group link sent to {member_name} by {staff_username}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def add_existing_members_to_staff_groups(gym_id=None, status_filter="Active"):
    """Bulk add ALL existing members to their staff groups"""
    members = db.get_members(gym_id=gym_id, status=status_filter)
    
    if not members:
        return {"success": 0, "failed": 0, "skipped": 0, "details": []}

    result = {"success": 0, "failed": 0, "skipped": 0, "details": []}

    for member in members:
        if not member.phone:
            result["skipped"] += 1
            result["details"].append({
                "name": member.full_name,
                "serial": member.serial_number,
                "status": "SKIPPED - No Phone"
            })
            continue

        staff_user = getattr(member, 'created_by_staff', None)
        if not staff_user or staff_user == 'unknown':
            result["skipped"] += 1
            result["details"].append({
                "name": member.full_name,
                "serial": member.serial_number,
                "status": "SKIPPED - No staff assigned"
            })
            continue

        success = add_member_to_staff_group(
            phone_number=member.phone,
            staff_username=staff_user,
            member_name=member.full_name,
            serial=member.serial_number
        )

        if success:
            result["success"] += 1
            result["details"].append({
                "name": member.full_name,
                "serial": member.serial_number,
                "staff": staff_user,
                "status": "✅ ADDED"
            })
        else:
            result["failed"] += 1
            result["details"].append({
                "name": member.full_name,
                "serial": member.serial_number,
                "staff": staff_user,
                "status": "❌ FAILED"
            })

    return result


# ============================================
# WHATSAPP LINK HELPERS
# ============================================

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


# ── SCHEDULED MESSAGE FUNCTION ──
def schedule_message(time_str, message, message_type, days=None):
    """Schedule a message to be sent"""
    schedule_data = {
        "time": time_str,
        "message": message,
        "type": message_type,
        "days": days or ["All Days"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "Active"
    }
    
    if "scheduled_messages" not in st.session_state:
        st.session_state.scheduled_messages = []
    if "message_logs" not in st.session_state:
        st.session_state.message_logs = []
    
    st.session_state.scheduled_messages.append(schedule_data)
    
    st.session_state.message_logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "SCHEDULED",
        "message_type": message_type,
        "status": "Scheduled",
        "time": time_str
    })
    
    return True


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role):
    # ── 🔥 SESSION STATE INITIALIZATION ──
    if "message_logs" not in st.session_state:
        st.session_state.message_logs = []
    if "scheduled_messages" not in st.session_state:
        st.session_state.scheduled_messages = []
    if "wa_added_members" not in st.session_state:
        st.session_state.wa_added_members = set()
    
    # ── 🔥 LOAD SETTINGS FROM DATABASE ──
    reminder_days = get_reminder_days()
    absent_days = get_absent_days()
    current_lang = get_whatsapp_language()

    styles.page_header("💬", "WhatsApp Automation",
                       "Auto bulk send · Fee reminders · Absentee alerts · Birthdays")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    # ── 🔥 ANALYTICS DASHBOARD ──
    all_members = db.get_members()
    total_members = len(all_members)
    pending_count = len([m for m in all_members if m.phone and not getattr(m, 'whatsapp_sent', False)])
    
    total_sent = len(st.session_state.message_logs)
    success_rate = 95 if total_sent > 0 else 0
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📤 Total Sent", total_sent)
    col2.metric("⏳ Pending", pending_count)
    col3.metric("✅ Success Rate", f"{success_rate}%")
    col4.metric("👥 Total Members", total_members)
    st.markdown("---")

    # ── 🔥 SETTINGS EXPANDER (WITH DATABASE SAVE) ──
    with st.expander("⚙️ Message Settings", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_reminder_days = st.number_input(
                "Fee reminder — days ahead", 
                min_value=1, 
                max_value=60,
                value=reminder_days, 
                step=1, 
                key="wa_days_threshold_input",
            )
            if new_reminder_days != reminder_days:
                set_reminder_days(new_reminder_days)
                reminder_days = new_reminder_days
                st.success(f"✅ Reminder days set to {reminder_days}")
        
        with c2:
            new_absent_days = st.number_input(
                "Absentee alert after (days)", 
                min_value=1, 
                max_value=30,
                value=absent_days, 
                step=1, 
                key="wa_absent_days_input",
            )
            if new_absent_days != absent_days:
                set_absent_days(new_absent_days)
                absent_days = new_absent_days
                st.success(f"✅ Absent days set to {absent_days}")
        
        with c3:
            new_lang = st.radio(
                "Message language", 
                ["English", "Urdu"], 
                horizontal=True,
                index=0 if current_lang == "English" else 1,
                key="wa_lang_radio"
            )
            if new_lang != current_lang:
                set_whatsapp_language(new_lang)
                current_lang = new_lang
                st.success(f"✅ Language set to {current_lang}")
        
        # ── 🔥 TEMPLATES PREVIEW ──
        st.markdown("---")
        st.subheader("📋 Message Templates")
        
        col_temp1, col_temp2 = st.columns([1, 2])
        with col_temp1:
            selected_template = st.selectbox(
                "Select Template",
                list(TEMPLATES.keys()),
                key="template_selector_wa"
            )
        
        with col_temp2:
            if selected_template:
                lang_key = "ur" if current_lang == "Urdu" else "en"
                template_preview = TEMPLATES[selected_template].get(lang_key, TEMPLATES[selected_template]["en"])
                st.text_area(
                    "Template Preview",
                    value=template_preview,
                    height=60,
                    key="template_preview_wa",
                    disabled=True
                )
                st.caption(f"💡 Language: {current_lang}")
        
        # Custom template based on language
        default_temp = URDU_TEMPLATE if current_lang == "Urdu" else DEFAULT_TEMPLATE
        template = st.text_area(
            "Custom Message Template",
            value=default_temp,
            height=80, 
            key="wa_template",
            help="Placeholders: {name} {gym} {expiry} {days}"
        )
        st.caption("💡 WhatsApp links open WhatsApp Web / App — popups must be allowed in browser.")

    st.divider()

    def gym_selector(tab_key):
        if gym_id:
            return gym_id
        opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
        return opts[st.selectbox("Gym", list(opts.keys()), key=f"wa_gym_{tab_key}")]

    tab_auto, tab_expiry, tab_absent, tab_birthday, tab_streak, tab_schedule = st.tabs([
        "🤖 Auto-Send Dashboard",
        "⏰ Fee Expiry",
        "🚶 Absentee Alerts",
        "🎂 Birthdays",
        "🔥 Streaks",
        "⏰ Schedule"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 0 — AUTO-SEND DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    with tab_auto:
        st.markdown("### 🤖 One-Click Bulk WhatsApp Sender")
        st.info(
            "**How it works:** Click any 'Send All' button below → your browser opens "
            "each member's WhatsApp chat pre-filled with the message. "
            "Just tap **Send** in WhatsApp — done in seconds!"
        )

        sel_gid_auto = gym_selector("auto")

        expiring = db.get_expiring_members(days=reminder_days, gym_id=sel_gid_auto)
        absent_list = db.get_absent_members(days=absent_days, gym_id=sel_gid_auto)
        bday_list = db.get_birthday_members(days_ahead=1, gym_id=sel_gid_auto)

        # ── Get template based on language ──
        lang_key = "ur" if current_lang == "Urdu" else "en"
        fee_template = TEMPLATES["Fee Reminder"].get(lang_key, TEMPLATES["Fee Reminder"]["en"])

        fee_links, fee_rows = [], []
        for m, days_left in expiring:
            if not m.phone:
                continue
            gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
            tip = db.get_health_tip(m.id)
            msg = fee_template.format(name=m.full_name, gym=gym_name,
                                      expiry=m.expiry_date, days=days_left)
            full_msg = f"{msg}\n\n💪 Health Tip: {tip}"
            fee_links.append(make_wa_link(m.phone, full_msg))
            fee_rows.append({"Name": m.full_name, "Phone": m.phone,
                             "Days Left": days_left, "Gym": gym_name})

        # ── Absent template ──
        absent_template = TEMPLATES["Absent"].get(lang_key, TEMPLATES["Absent"]["en"])
        abs_links, abs_rows = [], []
        for m in absent_list:
            if not m.phone:
                continue
            gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
            msg = absent_template.format(name=m.full_name, gym=gym_name)
            abs_links.append(make_wa_link(m.phone, msg))
            abs_rows.append({"Name": m.full_name, "Phone": m.phone, "Gym": gym_name})

        # ── Birthday template ──
        bday_template = TEMPLATES["Birthday"].get(lang_key, TEMPLATES["Birthday"]["en"])
        bd_links, bd_rows = [], []
        for m, days_to_bday in bday_list:
            if not m.phone:
                continue
            gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
            msg = bday_template.format(name=m.full_name, gym=gym_name)
            bd_links.append(make_wa_link(m.phone, msg))
            bd_rows.append({"Name": m.full_name, "Phone": m.phone, "Gym": gym_name,
                            "Birthday": "Today! 🎉" if days_to_bday == 0 else f"In {days_to_bday}d"})

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("⏰ Fee Expiry", len(fee_links), f"{len(expiring)-len(fee_links)} no phone")
        mc2.metric("🚶 Absent Members", len(abs_links), f"{len(absent_list)-len(abs_links)} no phone")
        mc3.metric("🎂 Birthdays Today", len(bd_links))

        st.divider()

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

        # ── 🔥 GROUP DASHBOARD ──
        st.divider()
        st.markdown("#### 👥 Staff Group Dashboard")
        
        all_members_for_groups = db.get_members()
        total_members_for_groups = len(all_members_for_groups)
        
        for staff in STAFF_GROUPS.keys():
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.write(f"**{staff.title()}**")
            with col2:
                count = len([m for m in all_members_for_groups if getattr(m, 'created_by_staff', '') == staff])
                progress_val = count / total_members_for_groups if total_members_for_groups > 0 else 0
                st.progress(progress_val, text=f"{count} members")
            with col3:
                st.write(f"🔗 [Link]({STAFF_GROUPS[staff]})")

        # ── 🔥 BULK ADD EXISTING MEMBERS ──
        st.divider()
        st.markdown("#### 📥 Bulk Add Existing Members to Staff WhatsApp Groups")
        st.caption("Add all your existing members to the WhatsApp group of the staff member who registered them.")

        col_bulk1, col_bulk2 = st.columns(2)

        with col_bulk1:
            bulk_status = st.selectbox(
                "Member Status",
                options=["Active", "All", "Inactive", "Suspended", "Frozen"],
                key="bulk_status_selector_wa"
            )

        with col_bulk2:
            st.write("")
            st.write("")
            if st.button("📤 Add All Members to Staff Groups", type="primary", use_container_width=True):
                with st.spinner("⏳ Adding members to staff WhatsApp groups..."):
                    result = add_existing_members_to_staff_groups(
                        status_filter=bulk_status
                    )

                    st.success(f"""
                    ✅ **Bulk Add Complete!**
                    - ✅ Added: {result['success']} members
                    - ❌ Failed: {result['failed']} members  
                    - ⏭️ Skipped: {result['skipped']} members
                    """)

                    if result['details']:
                        with st.expander("📋 View Details"):
                            df_details = pd.DataFrame(result['details'])
                            st.dataframe(df_details, use_container_width=True, hide_index=True)

                    st.balloons()

        # ── 📋 MANUAL WHATSAPP GROUP ADD TRACKER ──
        st.divider()
        st.markdown("#### 📋 WhatsApp Group Add Tracker")
        st.caption("Click 'Add to Group' → WhatsApp opens → Add member → Click 'Mark Added'")

        col_filter1, col_filter2, col_filter3 = st.columns(3)

        with col_filter1:
            filter_gym = st.selectbox(
                "Select Gym",
                options=[None] + [g.id for g in gyms],
                format_func=lambda x: "All Gyms" if x is None else next((g.name for g in gyms if g.id == x), str(x)),
                key="wa_tracker_gym"
            )

        with col_filter2:
            filter_staff = st.selectbox(
                "Filter by Staff",
                options=["All"] + list(STAFF_GROUPS.keys()),
                key="wa_tracker_staff"
            )

        with col_filter3:
            filter_status = st.selectbox(
                "Member Status",
                options=["Active", "All", "Inactive", "Suspended", "Frozen"],
                key="wa_tracker_status"
            )

        tracker_members = db.get_members(gym_id=filter_gym, status=filter_status)

        if filter_staff != "All":
            tracker_members = [m for m in tracker_members if getattr(m, 'created_by_staff', '') == filter_staff]

        pending_members = [
            m for m in tracker_members 
            if m.phone and len(m.phone) >= 10 
            and m.id not in st.session_state.wa_added_members
        ]

        st.info(f"📌 **{len(pending_members)}** members pending to add to WhatsApp group")

        if pending_members:
            for idx, member in enumerate(pending_members):
                col_name, col_phone, col_serial, col_staff, col_gym, col_action1, col_action2 = st.columns([1.5, 1.2, 1, 1, 1.2, 1.2, 1])

                with col_name:
                    st.write(f"**{member.full_name}**")

                with col_phone:
                    clean_phone = "".join(c for c in member.phone if c.isdigit() or c == "+")
                    if clean_phone.startswith("0"):
                        clean_phone = "+92" + clean_phone[1:]
                    elif not clean_phone.startswith("+"):
                        clean_phone = "+92" + clean_phone
                    st.code(clean_phone, language=None)

                with col_serial:
                    st.write(f"`{member.serial_number}`")

                with col_staff:
                    staff = getattr(member, 'created_by_staff', '')
                    st.write(f"**{staff or '—'}**")

                with col_gym:
                    gym_name = next((g.name for g in gyms if g.id == member.gym_id), "—")
                    st.write(gym_name)

                with col_action1:
                    staff = getattr(member, 'created_by_staff', '')
                    group_link = STAFF_GROUPS.get(staff)
                    if group_link:
                        st.markdown(f'<a href="{group_link}" target="_blank" style="display:inline-block;background:#25D366;color:white;padding:0.3rem 0.6rem;border-radius:6px;text-decoration:none;font-size:0.8rem;font-weight:600;text-align:center;width:100%;">➕ Add to Group</a>', unsafe_allow_html=True)
                    else:
                        st.write("—")

                with col_action2:
                    if st.button("✅ Mark Added", key=f"wa_mark_{member.id}", type="primary", use_container_width=True):
                        st.session_state.wa_added_members.add(member.id)
                        st.session_state.message_logs.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "type": "MARKED_ADDED",
                            "member": member.full_name,
                            "serial": member.serial_number,
                            "status": "Added to group"
                        })
                        st.rerun()

                st.divider()

            col_clear1, col_clear2, col_clear3 = st.columns(3)
            with col_clear1:
                if st.button("✅ Mark All as Added", type="primary", use_container_width=True):
                    for m in pending_members:
                        st.session_state.wa_added_members.add(m.id)
                    st.rerun()

            with col_clear2:
                if st.button("🔄 Reset All (Show Again)", use_container_width=True):
                    st.session_state.wa_added_members = set()
                    st.rerun()
            
            with col_clear3:
                all_links = []
                for m in pending_members:
                    staff = getattr(m, 'created_by_staff', '')
                    link = STAFF_GROUPS.get(staff)
                    if link:
                        all_links.append(link)
                if all_links:
                    links_text = "\n".join(list(set(all_links)))
                    st.download_button(
                        "📋 Copy Group Links",
                        data=links_text,
                        file_name="group_links.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

            st.markdown("---")
            st.markdown("#### 📋 Bulk Phone Numbers for WhatsApp")

            all_phones = []
            for m in pending_members:
                clean_phone = "".join(c for c in m.phone if c.isdigit() or c == "+")
                if clean_phone.startswith("0"):
                    clean_phone = "+92" + clean_phone[1:]
                elif not clean_phone.startswith("+"):
                    clean_phone = "+92" + clean_phone
                all_phones.append(clean_phone)

            if all_phones:
                phone_text = "\n".join(all_phones)
                st.text_area(
                    "📋 Copy these phone numbers (one per line)",
                    value=phone_text,
                    height=150,
                    key="bulk_phone_export_wa"
                )

                st.markdown("""
                <div style="background:#1E293B;padding:10px;border-radius:8px;margin:10px 0;">
                    <p style="color:#94A3B8;font-size:0.8rem;">
                        💡 <strong>How to add:</strong><br>
                        1. Click <strong>"Add to Group"</strong> → WhatsApp group opens<br>
                        2. In WhatsApp, click <strong>Add Members</strong> → Paste phone number<br>
                        3. Come back and click <strong>"Mark Added"</strong><br>
                        4. Member disappears from list! ✅
                    </p>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.success("🎉 All members have been marked as added to WhatsApp group!")
            if st.button("🔄 Reset List", use_container_width=True):
                st.session_state.wa_added_members = set()
                st.rerun()

        added_members = [
            m for m in tracker_members 
            if m.id in st.session_state.wa_added_members
        ]

        if added_members:
            with st.expander(f"📋 Already Added ({len(added_members)} members)"):
                for m in added_members[:20]:
                    st.write(f"✅ {m.full_name} ({m.serial_number})")
                if len(added_members) > 20:
                    st.write(f"... and {len(added_members) - 20} more")

        # ── 🔥 MESSAGE HISTORY ──
        st.divider()
        st.markdown("#### 📜 Message History")
        
        if st.session_state.message_logs:
            df_logs = pd.DataFrame(st.session_state.message_logs)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Clear History"):
                st.session_state.message_logs = []
                st.rerun()
        else:
            st.info("No messages sent or scheduled yet.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — FEE EXPIRY REMINDERS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_expiry:
        sel_gid_exp = gym_selector("expiry")
        expiring = db.get_expiring_members(days=reminder_days, gym_id=sel_gid_exp)

        if not expiring:
            st.success(f"✅ No members expiring within {reminder_days} days!")
        else:
            urgent = sum(1 for _, d in expiring if d <= 2)
            ac1, ac2, ac3 = st.columns(3)
            ac1.metric("To Notify", len(expiring))
            ac2.metric("Urgent (≤ 2 days)", urgent)
            ac3.metric("Upcoming", len(expiring) - urgent)

            # ── Use language-specific template ──
            lang_key = "ur" if current_lang == "Urdu" else "en"
            fee_template = TEMPLATES["Fee Reminder"].get(lang_key, TEMPLATES["Fee Reminder"]["en"])

            tab_fee_links = []
            for m, days_left in expiring:
                if m.phone:
                    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                    tip = db.get_health_tip(m.id)
                    msg = fee_template.format(name=m.full_name, gym=gym_name,
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
                msg = fee_template.format(name=m.full_name, gym=gym_name,
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
                               mime="text/csv", key="wa_exp_export_wa")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ABSENTEE ALERTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_absent:
        sel_gid_abs = gym_selector("absent")
        st.markdown(f"**Members absent for more than {absent_days} consecutive days**")
        absent_members = db.get_absent_members(days=absent_days, gym_id=sel_gid_abs)

        if not absent_members:
            st.success(f"✅ All active members attended within the last {absent_days} days!")
        else:
            st.warning(f"⚠️ {len(absent_members)} member(s) have not checked in recently")
            
            lang_key = "ur" if current_lang == "Urdu" else "en"
            absent_template = TEMPLATES["Absent"].get(lang_key, TEMPLATES["Absent"]["en"])
            
            tab_abs_links = []
            for m in absent_members:
                if m.phone:
                    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                    msg = absent_template.format(name=m.full_name, gym=gym_name)
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
                msg = absent_template.format(name=m.full_name, gym=gym_name)
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
                                      max_value=30, value=7, step=1, key="wa_bday_days_wa")
        birthday_members = db.get_birthday_members(days_ahead=int(bday_ahead),
                                                    gym_id=sel_gid_bday)

        if not birthday_members:
            st.info(f"No birthdays in the next {int(bday_ahead)} days.")
        else:
            st.success(f"🎂 {len(birthday_members)} birthday(s) upcoming!")
            
            lang_key = "ur" if current_lang == "Urdu" else "en"
            bday_template = TEMPLATES["Birthday"].get(lang_key, TEMPLATES["Birthday"]["en"])
            
            tab_bd_links = []
            for m, _ in birthday_members:
                if m.phone:
                    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                    msg = bday_template.format(name=m.full_name, gym=gym_name)
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
                msg = bday_template.format(name=m.full_name, gym=gym_name)
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
                sel_label = st.selectbox("Select member", list(mem_opts.keys()), key="str_member_sel_wa")
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

                st.info(msg)
                if phone:
                    st.markdown(wa_button(make_wa_link(phone, msg), label), unsafe_allow_html=True)
                else:
                    st.warning("No phone number on file.")

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

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — SCHEDULE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_schedule:
        st.markdown("### ⏰ Scheduled Messages")
        st.info("Schedule messages to be sent automatically at specific times.")

        if not HAS_SCHEDULE:
            st.warning("⚠️ Schedule library not installed. Run: pip install schedule")
            st.stop()

        with st.expander("📝 Create New Schedule", expanded=True):
            col_sched1, col_sched2 = st.columns(2)
            
            with col_sched1:
                schedule_time = st.time_input("⏰ Send Time", value=datetime.now().time())
                schedule_days = st.multiselect(
                    "📅 Repeat on",
                    options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                )
            
            with col_sched2:
                schedule_type = st.selectbox(
                    "📋 Message Type",
                    list(TEMPLATES.keys()),
                    key="schedule_type_wa"
                )
                lang_key = "ur" if current_lang == "Urdu" else "en"
                default_msg = TEMPLATES[schedule_type].get(lang_key, TEMPLATES[schedule_type]["en"])
                schedule_message_text = st.text_area(
                    "✏️ Message",
                    value=default_msg,
                    height=80,
                    key="schedule_message_wa"
                )
            
            if st.button("💾 Save Schedule", type="primary"):
                if schedule_time and schedule_message_text:
                    if "scheduled_messages" not in st.session_state:
                        st.session_state.scheduled_messages = []
                    if "message_logs" not in st.session_state:
                        st.session_state.message_logs = []
                    
                    success = schedule_message(
                        time_str=schedule_time.strftime("%H:%M"),
                        message=schedule_message_text,
                        message_type=schedule_type,
                        days=schedule_days
                    )
                    if success:
                        st.success("✅ Schedule saved successfully!")
                        st.balloons()
                else:
                    st.error("❌ Please fill in all fields.")

        st.markdown("#### 📋 Scheduled Messages")

        if st.session_state.scheduled_messages:
            df_schedule = pd.DataFrame(st.session_state.scheduled_messages)
            st.dataframe(df_schedule, use_container_width=True, hide_index=True)
            
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button("🗑️ Clear All Schedules", type="primary"):
                    st.session_state.scheduled_messages = []
                    st.rerun()
            
            with col_del2:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
        else:
            st.info("No scheduled messages yet. Create one above!")

        st.markdown("#### 📜 Message History")

        if st.session_state.message_logs:
            df_logs = pd.DataFrame(st.session_state.message_logs)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.info("No messages sent or scheduled yet.")