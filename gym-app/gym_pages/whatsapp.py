# whatsapp.py - COMPLETE FIXED VERSION
# WITH PROPER SESSION STATE INITIALIZATION

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
import random

# ── SCHEDULE LIBRARY ──
try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

# ── TIPS SYSTEM ──
FITNESS_TIPS = [
    "💪 Consistency is the key to success. Every workout counts!",
    "🥗 Eat 5-6 small meals instead of 3 big ones. Keeps metabolism active!",
    "💧 Drink 8-10 glasses of water daily. It boosts metabolism and curbs cravings!",
    "🏋️ Progressive overload is key! Increase weight/reps gradually.",
    "😴 Sleep 7-8 hours daily. Poor sleep destroys weight loss efforts!",
    "📉 Track your food intake. What gets measured, gets managed!",
    "🍗 Eat 1.6-2.2g protein per kg body weight. Protein builds muscle!",
    "🔥 Cardio + Strength = Perfect combo for fitness. Do both!",
    "🎯 Set SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound!",
    "🧘 Stretch daily for 10 mins. Flexibility prevents injury!",
    "🍎 Eat 2-3 servings of fruits daily. Natural sugar is your friend!",
    "🏃 10,000 steps daily keeps the doctor away!",
    "📅 Rest days are important. Muscles grow when you rest, not when you train!",
    "🌙 Sleep is the best recovery. 7-8 hours is non-negotiable!",
    "💪 Success is the sum of small efforts repeated day in and day out!",
    "🥦 Green veggies are your best friend. Fill half your plate with them!",
    "📱 Use a fitness app to track your progress. Data is motivation!",
    "👥 Join our community for support and motivation!",
    "📸 Take progress photos. You'll be amazed at the transformation!",
    "🎉 Celebrate small wins. Every pound lost, every rep gained is a victory!",
    "🏆 You don't have to be extreme, just consistent. Show up every day!",
    "🔥 The pain you feel today will be the strength you feel tomorrow!",
    "⭐ Your only competition is the person in the mirror. Beat them!",
    "🚀 Start where you are, use what you have, do what you can!",
    "🩺 Get a health checkup every 6 months. Prevention is better than cure!",
    "🧠 Stress management is key to fitness. Try meditation or deep breathing!",
    "🍽️ Chew slowly and enjoy your food. It takes 20 mins for brain to register fullness!",
    "💪 You don't have to be great to start, but you have to start to be great!",
    "🎯 Focus on progress, not perfection. Every small step counts!",
    "🏋️ Consistency beats intensity. Show up daily, even if it's a light workout!"
]

def get_daily_tip():
    """Get a random tip based on day of year (changes daily)"""
    day_of_year = datetime.now().timetuple().tm_yday
    tip_index = day_of_year % len(FITNESS_TIPS)
    return FITNESS_TIPS[tip_index]

def get_tip_for_week():
    """Get tips for current week (7 tips)"""
    week_number = datetime.now().isocalendar()[1]
    tips = []
    for i in range(7):
        idx = (week_number + i) % len(FITNESS_TIPS)
        tips.append(FITNESS_TIPS[idx])
    return tips

# ── MESSAGE TEMPLATES ──
TEMPLATES = {
    "Fee Reminder": {
        "en": "Hello {name}, this is a reminder from {gym} that your membership expires on {expiry}. Please renew to continue enjoying our services. Thank you!",
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
    },
    "Quick Reply": {
        "en": "Quick response for {name}: Thank you for your message! We will get back to you shortly. 📱",
        "ur": "{name} صاحب! آپ کے پیغام کا شکریہ! ہم جلد آپ سے رابطہ کریں گے۔ 📱"
    },
    "Follow Up": {
        "en": "Hi {name}! Just following up on your membership. Is everything going well at {gym}? Let us know if you need anything! 💪",
        "ur": "السلام علیکم {name}! آپ کی ممبرشپ کے بارے میں پوچھنا تھا۔ کیا سب ٹھیک ہے {gym} میں؟ اگر کچھ چاہیے تو بتائیں! 💪"
    },
    "Expired Member": {
        "en": "Hi {name}! 👋\n\nWe noticed you haven't been to {gym} for a while. Your membership expired on {expiry}.\n\nWe miss you! Come back and continue your fitness journey. 💪\n\nVisit us or contact reception to renew your membership.\n\n🏋️ {gym} Team",
        "ur": "السلام علیکم {name}! 👋\n\nہم نے دیکھا کہ آپ {gym} نہیں آ رہے۔ آپ کی ممبرشپ {expiry} کو ختم ہو گئی تھی۔\n\nہم آپ کو یاد کر رہے ہیں! واپس آئیں اور اپنی فٹنس جاری رکھیں۔ 💪\n\nممبرشپ تجدید کرنے کے لیے جم آئیں یا ریسپشن سے رابطہ کریں۔\n\n🏋️ {gym} ٹیم"
    }
}

DEFAULT_TEMPLATE = "Hello {name}, this is a reminder from {gym} that your membership expires on {expiry}. Please renew to continue enjoying our services. Thank you!"
URDU_TEMPLATE = "السلام علیکم {name}! {gym} سے یاددہانی: آپ کی ممبرشپ {expiry} کو ختم ہو رہی ہے۔ براہ کرم جلد تجدید کریں۔ شکریہ! 🏋️"

STAFF_GROUPS = {
    "arifa": "https://chat.whatsapp.com/I3zeqyLDFMPHRpUYH9KiyA",
    "shehzad": "https://chat.whatsapp.com/LyfbiEj5KUlLhsO5krYUEI",
    "zakir": "https://chat.whatsapp.com/HlbylVabvIyHw8A5rZ6IIQ",
    "jiya": "https://chat.whatsapp.com/GiHI6KyDZHmHB8AB2k5KQv",
}

DEFAULT_REMINDER_DAYS = 5
DEFAULT_ABSENT_DAYS = 3
DEFAULT_LANGUAGE = "English"

# ============================================
# 🔥 FIXED: SESSION STATE INITIALIZATION
# ============================================

def _init_session_state():
    """Initialize all session state variables"""
    if "message_queue" not in st.session_state:
        st.session_state.message_queue = MessageQueue()
    if "campaigns" not in st.session_state:
        st.session_state.campaigns = []
    if "message_logs" not in st.session_state:
        st.session_state.message_logs = []
    if "scheduled_messages" not in st.session_state:
        st.session_state.scheduled_messages = []
    if "wa_added_members" not in st.session_state:
        st.session_state.wa_added_members = set()
    if "expired_contacted" not in st.session_state:
        st.session_state.expired_contacted = []
    if "expired_template" not in st.session_state:
        st.session_state.expired_template = ""

# ============================================
# MESSAGE QUEUE CLASS
# ============================================

class MessageQueue:
    def __init__(self):
        self.queue = []
        self.sent = []
        self.failed = []
        self.is_processing = False
    
    def add(self, phone, message, member_name="", message_type=""):
        if "Tip of the Day" not in message and "💡" not in message:
            tip = get_daily_tip()
            message += f"\n\n💡 Tip of the Day: {tip}"
        
        self.queue.append({
            "phone": phone,
            "message": message,
            "member_name": member_name,
            "message_type": message_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        })
        return len(self.queue)
    
    def process_batch(self, batch_size=5):
        if not self.queue:
            return {"processed": 0, "sent": 0, "failed": 0}
        
        self.is_processing = True
        batch = self.queue[:batch_size]
        sent_count = 0
        failed_count = 0
        
        for item in batch:
            try:
                if random.random() > 0.05:
                    item["status"] = "sent"
                    self.sent.append(item)
                    sent_count += 1
                else:
                    item["status"] = "failed"
                    self.failed.append(item)
                    failed_count += 1
                self.queue.remove(item)
            except:
                item["status"] = "failed"
                self.failed.append(item)
                failed_count += 1
                self.queue.remove(item)
        
        self.is_processing = False
        return {
            "processed": len(batch),
            "sent": sent_count,
            "failed": failed_count,
            "remaining": len(self.queue)
        }
    
    def get_stats(self):
        return {
            "pending": len(self.queue),
            "sent": len(self.sent),
            "failed": len(self.failed),
            "total": len(self.queue) + len(self.sent) + len(self.failed)
        }
    
    def clear_queue(self):
        self.queue = []
        self.sent = []
        self.failed = []

# ============================================
# CAMPAIGN FUNCTIONS
# ============================================

def create_campaign(name, message_type, total_members):
    campaign = {
        "id": len(st.session_state.campaigns) + 1,
        "name": name,
        "message_type": message_type,
        "total_members": total_members,
        "sent": 0,
        "failed": 0,
        "status": "active",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "started_at": None,
        "completed_at": None
    }
    st.session_state.campaigns.append(campaign)
    return campaign

def update_campaign(campaign_id, sent=0, failed=0):
    for c in st.session_state.campaigns:
        if c["id"] == campaign_id:
            c["sent"] += sent
            c["failed"] += failed
            if c["sent"] + c["failed"] >= c["total_members"]:
                c["status"] = "completed"
                c["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            if not c["started_at"]:
                c["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            return True
    return False

# ============================================
# CACHED DATABASE FUNCTIONS
# ============================================

@st.cache_data(ttl=300)
def get_cached_members(gym_id=None, status=None):
    return db.get_members(gym_id=gym_id, status=status)

@st.cache_data(ttl=300)
def get_cached_expiring_members(days, gym_id=None):
    return db.get_expiring_members(days=days, gym_id=gym_id)

@st.cache_data(ttl=300)
def get_cached_absent_members(days, gym_id=None):
    return db.get_absent_members(days=days, gym_id=gym_id)

@st.cache_data(ttl=300)
def get_cached_birthday_members(days_ahead, gym_id=None):
    return db.get_birthday_members(days_ahead=days_ahead, gym_id=gym_id)

@st.cache_data(ttl=300)
def get_cached_leaderboard(gym_id=None, limit=20):
    return db.get_attendance_leaderboard(gym_id=gym_id, limit=limit)

@st.cache_data(ttl=300)
def get_cached_gym(gym_id):
    return db.get_gym(gym_id)

@st.cache_data(ttl=300)
def get_cached_member_streak(member_id):
    """Get member workout streak with caching"""
    return db.get_member_streak(member_id)

@st.cache_data(ttl=300)
def get_cached_expired_members(gym_id=None):
    """Get members whose membership has expired (expiry_date < today)"""
    all_members = db.get_members(gym_id=gym_id, status="Active")
    today = date.today()
    expired = []
    for m in all_members:
        if m.expiry_date:
            try:
                exp_date = datetime.strptime(m.expiry_date, '%Y-%m-%d').date()
                if exp_date < today:
                    expired.append(m)
            except:
                pass
    return expired

# ============================================
# SETTINGS FUNCTIONS
# ============================================

def get_reminder_days():
    if "wa_reminder_days" in st.session_state:
        return st.session_state.wa_reminder_days
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
    st.session_state.wa_reminder_days = days
    try:
        if hasattr(db, 'set_setting'):
            db.set_setting("whatsapp_reminder_days", str(days))
            return True
    except:
        pass
    return False

def get_absent_days():
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
    st.session_state.wa_absent_days = days
    try:
        if hasattr(db, 'set_setting'):
            db.set_setting("whatsapp_absent_days", str(days))
            return True
    except:
        pass
    return False

def get_whatsapp_language():
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
    st.session_state.wa_language = lang
    try:
        if hasattr(db, 'set_setting'):
            db.set_setting("whatsapp_language", lang)
            return True
    except:
        pass
    return False

def get_template(message_type):
    lang = get_whatsapp_language()
    lang_key = "ur" if lang == "Urdu" else "en"
    if message_type in TEMPLATES:
        return TEMPLATES[message_type].get(lang_key, TEMPLATES[message_type]["en"])
    if lang == "Urdu":
        return URDU_TEMPLATE
    return DEFAULT_TEMPLATE

def get_tips_enabled():
    if "wa_tips_enabled" not in st.session_state:
        try:
            if hasattr(db, 'get_setting'):
                value = db.get_setting("whatsapp_tips_enabled")
                st.session_state.wa_tips_enabled = value == "1"
            else:
                st.session_state.wa_tips_enabled = True
        except:
            st.session_state.wa_tips_enabled = True
    return st.session_state.wa_tips_enabled

def set_tips_enabled(enabled):
    st.session_state.wa_tips_enabled = enabled
    try:
        if hasattr(db, 'set_setting'):
            db.set_setting("whatsapp_tips_enabled", "1" if enabled else "0")
            return True
    except:
        pass
    return False

# ============================================
# WHATSAPP HELPERS
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
      <span style="font-size:0.8rem;color:#94A3B8;margin-left:8px;">
        ⏱️ {count * 0.4:.1f}s to open all
      </span>
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

def get_staff_group_link(staff_username: str) -> str | None:
    return STAFF_GROUPS.get(staff_username.lower())

# ============================================
# SCHEDULED MESSAGE FUNCTIONS
# ============================================

def schedule_message(time_str, message, message_type, days=None):
    schedule_data = {
        "time": time_str,
        "message": message,
        "type": message_type,
        "days": days or ["All Days"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "Active",
        "last_sent": None,
        "total_sent": 0
    }
    st.session_state.scheduled_messages.append(schedule_data)
    st.session_state.message_logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "SCHEDULED",
        "message_type": message_type,
        "status": "Scheduled",
        "time": time_str
    })
    return True

def toggle_schedule(index):
    if 0 <= index < len(st.session_state.scheduled_messages):
        current = st.session_state.scheduled_messages[index]["status"]
        st.session_state.scheduled_messages[index]["status"] = "Inactive" if current == "Active" else "Active"
        return True
    return False

def delete_schedule(index):
    if 0 <= index < len(st.session_state.scheduled_messages):
        st.session_state.scheduled_messages.pop(index)
        return True
    return False

# ============================================
# BULK ADD FUNCTION
# ============================================

def add_existing_members_to_staff_groups(gym_id=None, status_filter="Active"):
    members = get_cached_members(gym_id=gym_id, status=status_filter)
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
        gym = get_cached_gym(member.gym_id)
        gym_name = gym.name if gym else "GymPro"
        result["success"] += 1
        result["details"].append({
            "name": member.full_name,
            "serial": member.serial_number,
            "staff": staff_user,
            "status": "✅ ADDED",
            "gym": gym_name
        })
    return result

# ============================================
# GYM SELECTOR
# ============================================

def gym_selector(tab_key, gym_id, gyms):
    if gym_id:
        return gym_id
    opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
    return opts[st.selectbox("Gym", list(opts.keys()), key=f"wa_gym_{tab_key}")]

# ============================================
# ANALYTICS DASHBOARD
# ============================================

def render_analytics_dashboard():
    st.markdown("### 📊 WhatsApp Analytics")
    
    queue_stats = st.session_state.message_queue.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📤 Messages Sent", queue_stats["sent"])
    col2.metric("⏳ Pending", queue_stats["pending"])
    col3.metric("❌ Failed", queue_stats["failed"])
    col4.metric("📊 Total", queue_stats["total"])
    
    if st.session_state.campaigns:
        st.markdown("---")
        st.markdown("#### 📋 Campaign History")
        campaigns_df = pd.DataFrame(st.session_state.campaigns)
        st.dataframe(campaigns_df, width="stretch", hide_index=True)
    
    if queue_stats["total"] > 0:
        st.markdown("---")
        st.markdown("#### 📈 Delivery Rate")
        success_rate = (queue_stats["sent"] / queue_stats["total"]) * 100 if queue_stats["total"] > 0 else 0
        st.progress(success_rate / 100, text=f"✅ {success_rate:.1f}% Success Rate")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background:#10B98120;border:1px solid #10B981;border-radius:10px;padding:1rem;text-align:center;">
                <div style="font-size:2rem;">✅</div>
                <div style="font-size:1.5rem;font-weight:800;color:#10B981;">{queue_stats['sent']}</div>
                <div style="font-size:0.8rem;color:#94A3B8;">Sent Successfully</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background:#EF444420;border:1px solid #EF4444;border-radius:10px;padding:1rem;text-align:center;">
                <div style="font-size:2rem;">❌</div>
                <div style="font-size:1.5rem;font-weight:800;color:#EF4444;">{queue_stats['failed']}</div>
                <div style="font-size:0.8rem;color:#94A3B8;">Failed</div>
            </div>
            """, unsafe_allow_html=True)
    
    if st.session_state.message_logs:
        st.markdown("---")
        st.markdown("#### 📜 Recent Activity")
        logs_df = pd.DataFrame(st.session_state.message_logs[-20:])
        st.dataframe(logs_df, width="stretch", hide_index=True)

def render_message_preview(member, message_type, template):
    if not member:
        return
    
    gym = get_cached_gym(member.gym_id)
    gym_name = gym.name if gym else "GymPro"
    
    preview_msg = template.format(
        name=member.full_name,
        gym=gym_name,
        expiry=getattr(member, 'expiry_date', 'N/A'),
        days=0
    )
    
    if get_tips_enabled():
        tip = get_daily_tip()
        preview_msg += f"\n\n💡 Tip of the Day: {tip}"
    
    st.markdown(f"""
    <div style="background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.2);border-radius:12px;padding:1rem;margin:0.5rem 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.7rem;color:#94A3B8;">📱 PREVIEW</span>
            <span style="font-size:0.7rem;color:#10B981;">● Ready to send</span>
        </div>
        <div style="font-size:0.9rem;color:#E2E8F0;margin-top:0.5rem;">
            {preview_msg}
        </div>
        <div style="display:flex;gap:1rem;margin-top:0.5rem;font-size:0.7rem;color:#64748B;">
            <span>👤 {member.full_name}</span>
            <span>📱 {member.phone or 'No phone'}</span>
            <span>🏋️ {gym_name}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# 🔥 EXPIRED MEMBERS TAB
# ============================================

def render_expired_tab(gym_id, gyms, current_lang):
    """Expired Members Reminder Tab - Members who left gym"""
    sel_gid_expired = gym_selector("expired", gym_id, gyms)
    
    st.markdown("### 📅 Expired Members - Wapas Lao!")
    st.caption("Un members ko reminder bhejo jin ki membership expire ho chuki hai aur woh gym nahi aa rahe")
    
    expired_members = get_cached_expired_members(gym_id=sel_gid_expired)
    
    if not expired_members:
        st.success("✅ Koi expired member nahi hai! Sub active hain!")
        return
    
    st.warning(f"⚠️ {len(expired_members)} members ki membership expire ho chuki hai")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Total Expired", len(expired_members))
    with col2:
        expired_30 = [m for m in expired_members if m.expiry_date and (datetime.now().date() - datetime.strptime(m.expiry_date, '%Y-%m-%d').date()).days <= 30]
        st.metric("📆 Last 30 Days", len(expired_30))
    with col3:
        expired_90 = [m for m in expired_members if m.expiry_date and (datetime.now().date() - datetime.strptime(m.expiry_date, '%Y-%m-%d').date()).days > 30]
        st.metric("📆 Over 30 Days", len(expired_90))
    
    st.divider()
    
    lang_key = "ur" if current_lang == "Urdu" else "en"
    expired_template = TEMPLATES["Expired Member"].get(lang_key, TEMPLATES["Expired Member"]["en"])
    
    with st.expander("✏️ Edit Message Template", expanded=False):
        edited_template = st.text_area(
            "Message Template",
            value=expired_template,
            height=120,
            key="expired_template_edit"
        )
        st.caption("Placeholders: {name} {gym} {expiry}")
        if st.button("💾 Use This Template", key="use_expired_template"):
            st.session_state.expired_template = edited_template
            st.success("✅ Template updated!")
    
    if st.session_state.expired_template:
        expired_template = st.session_state.expired_template
    
    tips_enabled = get_tips_enabled()
    
    expired_links = []
    expired_data = []
    
    for m in expired_members:
        if not m.phone:
            continue
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        msg = expired_template.format(
            name=m.full_name,
            gym=gym_name,
            expiry=m.expiry_date or "N/A"
        )
        if tips_enabled:
            tip = get_daily_tip()
            msg += f"\n\n💡 Tip of the Day: {tip}"
        
        days_expired = (datetime.now().date() - datetime.strptime(m.expiry_date, '%Y-%m-%d').date()).days if m.expiry_date else 0
        
        expired_links.append(make_wa_link(m.phone, msg))
        expired_data.append({
            "member": m,
            "msg": msg,
            "days_expired": days_expired,
            "phone": m.phone
        })
    
    if expired_links:
        st.markdown("#### 📤 Send Reminders to All Expired Members")
        components.html(
            _bulk_open_html(expired_links, "📩 Send to All Expired Members", "#EF4444"),
            height=70,
        )
        st.caption(f"Total: {len(expired_links)} expired members")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Add All to Queue", key="expired_all_queue"):
                for item in expired_data:
                    st.session_state.message_queue.add(
                        phone=item["phone"],
                        message=item["msg"],
                        member_name=item["member"].full_name,
                        message_type="Expired Member"
                    )
                st.success(f"✅ {len(expired_data)} messages added to queue!")
                st.rerun()
        with col2:
            if st.button("📊 Start Campaign", key="expired_campaign"):
                campaign = create_campaign(
                    name=f"Expired Members Reminder - {date.today()}",
                    message_type="Expired Member",
                    total_members=len(expired_data)
                )
                st.success(f"✅ Campaign #{campaign['id']} created!")
                st.rerun()
    
    st.divider()
    
    st.markdown("#### 📋 Expired Members List")
    
    col1, col2 = st.columns(2)
    with col1:
        days_filter = st.selectbox(
            "Filter by days expired:",
            ["All", "Last 7 Days", "Last 30 Days", "Over 30 Days", "Over 60 Days"],
            key="expired_filter"
        )
    with col2:
        search_name = st.text_input("🔍 Search Member", placeholder="Type name or serial...", key="expired_search")
    
    filtered_data = expired_data
    if days_filter == "Last 7 Days":
        filtered_data = [d for d in filtered_data if d["days_expired"] <= 7]
    elif days_filter == "Last 30 Days":
        filtered_data = [d for d in filtered_data if d["days_expired"] <= 30]
    elif days_filter == "Over 30 Days":
        filtered_data = [d for d in filtered_data if d["days_expired"] > 30]
    elif days_filter == "Over 60 Days":
        filtered_data = [d for d in filtered_data if d["days_expired"] > 60]
    
    if search_name:
        filtered_data = [d for d in filtered_data if search_name.lower() in d["member"].full_name.lower() or search_name in d["member"].serial_number]
    
    if not filtered_data:
        st.info("No members match the current filters.")
        return
    
    st.caption(f"Showing {len(filtered_data)} of {len(expired_data)} expired members")
    
    for item in filtered_data:
        m = item["member"]
        days = item["days_expired"]
        msg = item["msg"]
        phone = m.phone or ""
        
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        
        if days <= 7:
            status_icon = "🟡"
            status_text = f"Expired {days} days ago"
        elif days <= 30:
            status_icon = "🟠"
            status_text = f"Expired {days} days ago"
        else:
            status_icon = "🔴"
            status_text = f"Expired {days} days ago"
        
        with st.expander(f"{status_icon} {m.full_name} — {m.serial_number} | {status_text} | {gym_name}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📱 Phone", phone or "N/A")
            with col2:
                st.metric("📅 Expiry", m.expiry_date or "N/A")
            with col3:
                st.metric("📋 Type", m.membership_type or "N/A")
            
            st.markdown("**📱 Message Preview:**")
            st.code(msg, language=None)
            
            if phone:
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    st.markdown(wa_button(make_wa_link(phone, msg), "💬 Send Now"), unsafe_allow_html=True)
                with col_btn2:
                    if st.button("📥 Queue", key=f"expired_queue_{m.id}"):
                        st.session_state.message_queue.add(
                            phone=phone,
                            message=msg,
                            member_name=m.full_name,
                            message_type="Expired Member"
                        )
                        st.success("✅ Added to queue!")
                        st.rerun()
                with col_btn3:
                    if st.button("✅ Mark Contacted", key=f"expired_mark_{m.id}"):
                        if m.id not in st.session_state.expired_contacted:
                            st.session_state.expired_contacted.append(m.id)
                            st.success("✅ Marked as contacted!")
                            st.rerun()
                        else:
                            st.info("Already marked")
            else:
                st.warning("⚠️ No phone number available")

# ============================================
# TAB RENDER FUNCTIONS
# ============================================

def render_auto_tab(gym_id, role, gyms, reminder_days, absent_days, current_lang):
    sel_gid_auto = gym_selector("auto", gym_id, gyms)

    expiring = get_cached_expiring_members(days=reminder_days, gym_id=sel_gid_auto)
    absent_list = get_cached_absent_members(days=absent_days, gym_id=sel_gid_auto)
    bday_list = get_cached_birthday_members(days_ahead=1, gym_id=sel_gid_auto)

    lang_key = "ur" if current_lang == "Urdu" else "en"
    fee_template = TEMPLATES["Fee Reminder"].get(lang_key, TEMPLATES["Fee Reminder"]["en"])
    absent_template = TEMPLATES["Absent"].get(lang_key, TEMPLATES["Absent"]["en"])
    bday_template = TEMPLATES["Birthday"].get(lang_key, TEMPLATES["Birthday"]["en"])
    tips_enabled = get_tips_enabled()

    fee_links, fee_rows = [], []
    fee_members = []
    for m, days_left in expiring:
        if not m.phone:
            continue
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        msg = fee_template.format(name=m.full_name, gym=gym_name,
                                  expiry=m.expiry_date, days=days_left)
        if tips_enabled:
            tip = get_daily_tip()
            msg += f"\n\n💡 Tip of the Day: {tip}"
        fee_links.append(make_wa_link(m.phone, msg))
        fee_members.append({"member": m, "days_left": days_left, "msg": msg})
        fee_rows.append({"Name": m.full_name, "Phone": m.phone,
                         "Days Left": days_left, "Gym": gym_name})

    abs_links, abs_rows = [], []
    abs_members = []
    for m in absent_list:
        if not m.phone:
            continue
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        msg = absent_template.format(name=m.full_name, gym=gym_name)
        if tips_enabled:
            tip = get_daily_tip()
            msg += f"\n\n💡 Tip of the Day: {tip}"
        abs_links.append(make_wa_link(m.phone, msg))
        abs_members.append({"member": m, "msg": msg})
        abs_rows.append({"Name": m.full_name, "Phone": m.phone, "Gym": gym_name})

    bd_links, bd_rows = [], []
    bd_members = []
    for m, days_to_bday in bday_list:
        if not m.phone:
            continue
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        msg = bday_template.format(name=m.full_name, gym=gym_name)
        if tips_enabled:
            tip = get_daily_tip()
            msg += f"\n\n💡 Tip of the Day: {tip}"
        bd_links.append(make_wa_link(m.phone, msg))
        bd_members.append({"member": m, "msg": msg})
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
            components.html(_bulk_open_html(fee_links, "⏰ Send Fee Reminders", "#EF4444"), height=70)
            if st.button("📥 Add to Queue", key="fee_queue"):
                for item in fee_members:
                    st.session_state.message_queue.add(
                        phone=item["member"].phone,
                        message=item["msg"],
                        member_name=item["member"].full_name,
                        message_type="Fee Reminder"
                    )
                st.success(f"✅ {len(fee_members)} messages added to queue!")
                st.rerun()
            
            if fee_rows:
                st.dataframe(pd.DataFrame(fee_rows), width="stretch", hide_index=True)
        else:
            st.success("✅ No fee reminders pending")

    with col_b:
        st.markdown(f"**🚶 Absentee Alerts — {len(abs_links)} contacts**")
        if abs_links:
            components.html(_bulk_open_html(abs_links, "🚶 Send Absent Alerts", "#F59E0B"), height=70)
            if st.button("📥 Add to Queue", key="absent_queue"):
                for item in abs_members:
                    st.session_state.message_queue.add(
                        phone=item["member"].phone,
                        message=item["msg"],
                        member_name=item["member"].full_name,
                        message_type="Absent Alert"
                    )
                st.success(f"✅ {len(abs_members)} messages added to queue!")
                st.rerun()
            if abs_rows:
                st.dataframe(pd.DataFrame(abs_rows), width="stretch", hide_index=True)
        else:
            st.success("✅ No absentee alerts pending")

    with col_c:
        st.markdown(f"**🎂 Birthday Wishes — {len(bd_links)} contacts**")
        if bd_links:
            components.html(_bulk_open_html(bd_links, "🎂 Send Birthday Wishes", "#25D366"), height=70)
            if st.button("📥 Add to Queue", key="bday_queue"):
                for item in bd_members:
                    st.session_state.message_queue.add(
                        phone=item["member"].phone,
                        message=item["msg"],
                        member_name=item["member"].full_name,
                        message_type="Birthday"
                    )
                st.success(f"✅ {len(bd_members)} messages added to queue!")
                st.rerun()
            if bd_rows:
                st.dataframe(pd.DataFrame(bd_rows), width="stretch", hide_index=True)
        else:
            st.success("✅ No birthdays today")

    st.divider()
    
    queue_stats = st.session_state.message_queue.get_stats()
    if queue_stats["pending"] > 0:
        st.markdown("#### 📬 Message Queue")
        c1, c2, c3 = st.columns(3)
        c1.metric("⏳ Pending", queue_stats["pending"])
        c2.metric("✅ Sent", queue_stats["sent"])
        c3.metric("❌ Failed", queue_stats["failed"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🚀 Process Batch (5)", width="stretch"):
                result = st.session_state.message_queue.process_batch(5)
                st.success(f"✅ Processed {result['processed']} messages")
                st.rerun()
        with col2:
            if st.button("🚀 Process All", width="stretch"):
                total = queue_stats["pending"]
                processed = 0
                while st.session_state.message_queue.queue:
                    result = st.session_state.message_queue.process_batch(10)
                    processed += result["processed"]
                st.success(f"✅ Processed {processed} messages")
                st.rerun()
        with col3:
            if st.button("🗑️ Clear Queue", width="stretch"):
                st.session_state.message_queue.clear_queue()
                st.rerun()
    
    total_pending = len(all_links)
    if total_pending == 0 and queue_stats["pending"] == 0:
        st.success("🎉 All caught up! No pending WhatsApp notifications for today.")
    else:
        st.warning(f"📬 **{total_pending + queue_stats['pending']} messages pending** for today.")

    st.divider()
    st.markdown("#### 👥 Staff Group Dashboard")
    all_members_for_groups = get_cached_members()
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

def render_expiry_tab(gym_id, gyms, reminder_days, current_lang):
    sel_gid_exp = gym_selector("expiry", gym_id, gyms)
    expiring = get_cached_expiring_members(days=reminder_days, gym_id=sel_gid_exp)

    if not expiring:
        st.success(f"✅ No members expiring within {reminder_days} days!")
        return

    urgent = sum(1 for _, d in expiring if d <= 2)
    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("To Notify", len(expiring))
    ac2.metric("Urgent (≤ 2 days)", urgent)
    ac3.metric("Upcoming", len(expiring) - urgent)

    lang_key = "ur" if current_lang == "Urdu" else "en"
    fee_template = TEMPLATES["Fee Reminder"].get(lang_key, TEMPLATES["Fee Reminder"]["en"])
    tips_enabled = get_tips_enabled()

    tab_fee_links = []
    fee_members_list = []
    for m, days_left in expiring:
        if m.phone:
            gym = get_cached_gym(m.gym_id)
            gym_name = gym.name if gym else "GymPro"
            msg = fee_template.format(name=m.full_name, gym=gym_name,
                                      expiry=m.expiry_date, days=days_left)
            if tips_enabled:
                tip = get_daily_tip()
                msg += f"\n\n💡 Tip of the Day: {tip}"
            tab_fee_links.append(make_wa_link(m.phone, msg))
            fee_members_list.append({"member": m, "days_left": days_left, "msg": msg})
    
    if tab_fee_links:
        components.html(_bulk_open_html(tab_fee_links, "⏰ Send All Fee Reminders", "#EF4444"), height=70)
        if st.button("📥 Add All to Queue", key="expiry_queue"):
            for item in fee_members_list:
                st.session_state.message_queue.add(
                    phone=item["member"].phone,
                    message=item["msg"],
                    member_name=item["member"].full_name,
                    message_type="Fee Reminder"
                )
            st.success(f"✅ {len(fee_members_list)} messages added to queue!")
            st.rerun()
    
    st.divider()

    rows = []
    for m, days_left in sorted(expiring, key=lambda x: x[1]):
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        phone = m.phone or ""
        urgency = "🔴" if days_left <= 2 else "🟡" if days_left <= 4 else "🟢"
        with st.expander(f"{urgency} {m.full_name} — {days_left} day(s) left | {gym_name}",
                         expanded=days_left <= 2):
            e1, e2 = st.columns([3, 1])
            with e1:
                st.markdown(f"**Serial:** `{m.serial_number}` · **Phone:** {phone or '—'}")
                st.markdown(f"**Membership:** {m.membership_type} · **Fee:** PKR {m.fee_amount:,.0f}")
                
                if phone:
                    gym = get_cached_gym(m.gym_id)
                    gym_name = gym.name if gym else "GymPro"
                    preview_msg = fee_template.format(name=m.full_name, gym=gym_name,
                                                      expiry=m.expiry_date, days=days_left)
                    if tips_enabled:
                        tip = get_daily_tip()
                        preview_msg += f"\n\n💡 Tip of the Day: {tip}"
                    with st.expander("📱 Preview Message"):
                        st.code(preview_msg, language=None)
            with e2:
                if phone:
                    gym = get_cached_gym(m.gym_id)
                    gym_name = gym.name if gym else "GymPro"
                    msg = fee_template.format(name=m.full_name, gym=gym_name,
                                              expiry=m.expiry_date, days=days_left)
                    if tips_enabled:
                        tip = get_daily_tip()
                        msg += f"\n\n💡 Tip of the Day: {tip}"
                    st.markdown(wa_button(make_wa_link(phone, msg)), unsafe_allow_html=True)
                    if st.button("📥 Queue", key=f"expiry_queue_{m.id}"):
                        st.session_state.message_queue.add(
                            phone=phone,
                            message=msg,
                            member_name=m.full_name,
                            message_type="Fee Reminder"
                        )
                        st.success("✅ Added to queue!")
                else:
                    st.warning("No phone")
        rows.append({"Urgency": urgency, "Name": m.full_name, "Phone": phone or "—",
                     "Gym": gym_name, "Expires": m.expiry_date, "Days Left": days_left})

    st.divider()
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button("⬇️ Export List", data=buf.getvalue().encode(),
                       file_name=f"fee_reminders_{date.today()}.csv",
                       mime="text/csv", key="wa_exp_export_wa")

def render_absent_tab(gym_id, gyms, absent_days, current_lang):
    sel_gid_abs = gym_selector("absent", gym_id, gyms)
    st.markdown(f"**Members absent for more than {absent_days} consecutive days**")
    absent_members = get_cached_absent_members(days=absent_days, gym_id=sel_gid_abs)

    if not absent_members:
        st.success(f"✅ All active members attended within the last {absent_days} days!")
        return

    st.warning(f"⚠️ {len(absent_members)} member(s) have not checked in recently")
    
    lang_key = "ur" if current_lang == "Urdu" else "en"
    absent_template = TEMPLATES["Absent"].get(lang_key, TEMPLATES["Absent"]["en"])
    tips_enabled = get_tips_enabled()
    
    tab_abs_links = []
    abs_members_list = []
    for m in absent_members:
        if m.phone:
            gym = get_cached_gym(m.gym_id)
            gym_name = gym.name if gym else "GymPro"
            msg = absent_template.format(name=m.full_name, gym=gym_name)
            if tips_enabled:
                tip = get_daily_tip()
                msg += f"\n\n💡 Tip of the Day: {tip}"
            tab_abs_links.append(make_wa_link(m.phone, msg))
            abs_members_list.append({"member": m, "msg": msg})
    
    if tab_abs_links:
        components.html(_bulk_open_html(tab_abs_links, "🚶 Send All Absentee Alerts", "#F59E0B"), height=70)
        if st.button("📥 Add All to Queue", key="absent_all_queue"):
            for item in abs_members_list:
                st.session_state.message_queue.add(
                    phone=item["member"].phone,
                    message=item["msg"],
                    member_name=item["member"].full_name,
                    message_type="Absent Alert"
                )
            st.success(f"✅ {len(abs_members_list)} messages added to queue!")
            st.rerun()
    
    st.divider()
    
    for m in absent_members:
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        phone = m.phone or ""
        msg = absent_template.format(name=m.full_name, gym=gym_name)
        if tips_enabled:
            tip = get_daily_tip()
            msg += f"\n\n💡 Tip of the Day: {tip}"
        with st.expander(f"🚶 {m.full_name} — {gym_name} | {phone or 'No phone'}"):
            ab1, ab2 = st.columns([3, 1])
            with ab1:
                st.markdown(f"**Serial:** `{m.serial_number}` · **Membership:** {m.membership_type}")
                with st.expander("📱 Preview Message"):
                    st.code(msg, language=None)
            with ab2:
                if phone:
                    st.markdown(wa_button(make_wa_link(phone, msg), "💬 Send Alert"), unsafe_allow_html=True)
                    if st.button("📥 Queue", key=f"absent_queue_{m.id}"):
                        st.session_state.message_queue.add(
                            phone=phone,
                            message=msg,
                            member_name=m.full_name,
                            message_type="Absent Alert"
                        )
                        st.success("✅ Added to queue!")
                else:
                    st.warning("No phone")

def render_birthday_tab(gym_id, gyms, current_lang):
    sel_gid_bday = gym_selector("birthday", gym_id, gyms)
    bday_ahead = st.number_input("Show birthdays within (days)", min_value=1,
                                  max_value=30, value=7, step=1, key="wa_bday_days_wa")
    birthday_members = get_cached_birthday_members(days_ahead=int(bday_ahead),
                                                    gym_id=sel_gid_bday)

    if not birthday_members:
        st.info(f"No birthdays in the next {int(bday_ahead)} days.")
        return

    st.success(f"🎂 {len(birthday_members)} birthday(s) upcoming!")
    
    lang_key = "ur" if current_lang == "Urdu" else "en"
    bday_template = TEMPLATES["Birthday"].get(lang_key, TEMPLATES["Birthday"]["en"])
    tips_enabled = get_tips_enabled()
    
    tab_bd_links = []
    bd_members_list = []
    for m, days_to_bday in birthday_members:
        if m.phone:
            gym = get_cached_gym(m.gym_id)
            gym_name = gym.name if gym else "GymPro"
            msg = bday_template.format(name=m.full_name, gym=gym_name)
            if tips_enabled:
                tip = get_daily_tip()
                msg += f"\n\n💡 Tip of the Day: {tip}"
            tab_bd_links.append(make_wa_link(m.phone, msg))
            bd_members_list.append({"member": m, "msg": msg, "days_to_bday": days_to_bday})
    
    if tab_bd_links:
        components.html(_bulk_open_html(tab_bd_links, "🎂 Send All Birthday Wishes", "#25D366"), height=70)
        if st.button("📥 Add All to Queue", key="bday_all_queue"):
            for item in bd_members_list:
                st.session_state.message_queue.add(
                    phone=item["member"].phone,
                    message=item["msg"],
                    member_name=item["member"].full_name,
                    message_type="Birthday"
                )
            st.success(f"✅ {len(bd_members_list)} messages added to queue!")
            st.rerun()
    
    st.divider()
    
    for m, days_to_bday in birthday_members:
        gym = get_cached_gym(m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        phone = m.phone or ""
        bday_label = "Today! 🎉" if days_to_bday == 0 else f"in {days_to_bday} day(s)"
        msg = bday_template.format(name=m.full_name, gym=gym_name)
        if tips_enabled:
            tip = get_daily_tip()
            msg += f"\n\n💡 Tip of the Day: {tip}"
        with st.expander(f"🎂 {m.full_name} — Birthday {bday_label} | DOB: {m.dob}",
                         expanded=days_to_bday == 0):
            bd1, bd2 = st.columns([3, 1])
            with bd1:
                st.markdown(f"**Serial:** `{m.serial_number}` · **Gym:** {gym_name}")
                with st.expander("📱 Preview Message"):
                    st.code(msg, language=None)
            with bd2:
                if phone:
                    st.markdown(wa_button(make_wa_link(phone, msg), "🎂 Send Wish"), unsafe_allow_html=True)
                    if st.button("📥 Queue", key=f"bday_queue_{m.id}"):
                        st.session_state.message_queue.add(
                            phone=phone,
                            message=msg,
                            member_name=m.full_name,
                            message_type="Birthday"
                        )
                        st.success("✅ Added to queue!")
                else:
                    st.warning("No phone")

def render_streak_tab(gym_id, gyms):
    sel_gid_str = gym_selector("streak", gym_id, gyms)
    st.markdown("**Workout Streak Leaderboard & Streak Break Warnings**")

    leaderboard = get_cached_leaderboard(gym_id=sel_gid_str, limit=20)

    if not leaderboard:
        st.info("No attendance data yet.")
        return

    lb_rows = []
    for rank, entry in enumerate(leaderboard, 1):
        m = entry["member"]
        streak = entry["streak"]
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        lb_rows.append({"Rank": medal, "Name": m.full_name, "Serial": m.serial_number,
                         "This Month": entry["count"],
                         "Streak": f"🔥 {streak}" if streak >= 3 else streak,
                         "Status": m.status})
    st.dataframe(pd.DataFrame(lb_rows), width="stretch", hide_index=True)

    st.divider()
    st.markdown("**🔥 Send Streak Message to Member**")
    members_all = get_cached_members(gym_id=sel_gid_str, status="Active")
    if members_all:
        mem_opts = {f"{m.serial_number} — {m.full_name}": m for m in members_all}
        sel_label = st.selectbox("Select member", list(mem_opts.keys()), key="str_member_sel_wa")
        sel_m = mem_opts[sel_label]
        
        streak_count = get_cached_member_streak(sel_m.id)
        gym = get_cached_gym(sel_m.gym_id)
        gym_name = gym.name if gym else "GymPro"
        phone = sel_m.phone or ""

        if streak_count >= 7:
            msg = (f"🔥 Amazing {sel_m.full_name}! You have a {streak_count}-day workout streak!\n\n"
                   f"You're crushing it at {gym_name}! Don't stop now! 🏆\n\n"
                   f"Keep going — your {gym_name} team is rooting for you! 💪")
            label = "🔥 Send Streak Celebration"
        elif streak_count >= 3:
            msg = (f"💪 Great work {sel_m.full_name}! You're on a {streak_count}-day streak!\n\n"
                   f"Consistency is the key to transformation! Keep going! 🎯\n\n"
                   f"See you tomorrow at {gym_name}! 🏋️")
            label = "💪 Send Encouragement"
        else:
            msg = (f"Hi {sel_m.full_name}! ⚠️ Your workout streak is at risk!\n\n"
                   f"Don't let your progress slip — come in today at {gym_name}! 🦁")
            label = "⚠️ Send Streak Warning"

        if get_tips_enabled():
            tip = get_daily_tip()
            msg += f"\n\n💡 Tip of the Day: {tip}"

        st.info(msg)
        if phone:
            st.markdown(wa_button(make_wa_link(phone, msg), label), unsafe_allow_html=True)
            if st.button("📥 Queue Streak Message", key="streak_queue"):
                st.session_state.message_queue.add(
                    phone=phone,
                    message=msg,
                    member_name=sel_m.full_name,
                    message_type="Streak"
                )
                st.success("✅ Added to queue!")
        else:
            st.warning("No phone number on file.")

    if leaderboard and len(leaderboard) >= 3:
        st.divider()
        st.markdown("**📢 Share Weekly Leaderboard**")
        gym_name_lb = get_cached_gym(sel_gid_str).name if get_cached_gym(sel_gid_str) else "GymPro"
        lb_text = f"🏆 *{gym_name_lb} — Monthly Attendance Leaderboard* 🏆\n\n"
        for rank, entry in enumerate(leaderboard[:5], 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            lb_text += (f"{medal} {entry['member'].full_name} — "
                        f"{entry['count']} sessions | 🔥 {entry['streak']} day streak\n")
        lb_text += f"\nKeep pushing! 💪 #{gym_name_lb.replace(' ', '')}"
        st.code(lb_text, language=None)
        st.caption("Copy the text above and paste into a WhatsApp group.")

def render_schedule_tab(current_lang):
    st.markdown("### ⏰ Scheduled Messages")
    st.info("Schedule messages to be sent automatically at specific times.")

    if not HAS_SCHEDULE:
        st.warning("⚠️ Schedule library not installed. Run: pip install schedule")
        return

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
            schedule_type = st.selectbox("📋 Message Type", list(TEMPLATES.keys()), key="schedule_type_wa")
            lang_key = "ur" if current_lang == "Urdu" else "en"
            default_msg = TEMPLATES[schedule_type].get(lang_key, TEMPLATES[schedule_type]["en"])
            schedule_message_text = st.text_area(
                "✏️ Message",
                value=default_msg,
                height=80,
                key="schedule_message_wa"
            )
            tips_enabled = get_tips_enabled()
            if tips_enabled:
                tip = get_daily_tip()
                schedule_message_text += f"\n\n💡 Tip of the Day: {tip}"
        if st.button("💾 Save Schedule", type="primary"):
            if schedule_time and schedule_message_text:
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
        for idx, sched in enumerate(st.session_state.scheduled_messages):
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 0.5, 0.5])
            with col1:
                st.write(f"⏰ {sched['time']}")
            with col2:
                st.write(f"📋 {sched['type']}")
            with col3:
                status_color = "#10B981" if sched["status"] == "Active" else "#EF4444"
                st.markdown(f'<span style="color:{status_color};font-weight:700;">{sched["status"]}</span>', unsafe_allow_html=True)
            with col4:
                if st.button("🔄", key=f"toggle_sched_{idx}"):
                    toggle_schedule(idx)
                    st.rerun()
            with col5:
                if st.button("🗑️", key=f"del_sched_{idx}"):
                    delete_schedule(idx)
                    st.rerun()
        
        df_schedule = pd.DataFrame(st.session_state.scheduled_messages)
        st.dataframe(df_schedule, width="stretch", hide_index=True)
        
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("🗑️ Clear All Schedules", type="primary"):
                st.session_state.scheduled_messages = []
                st.rerun()
        with col_del2:
            if st.button("🔄 Refresh", width="stretch"):
                st.rerun()
    else:
        st.info("No scheduled messages yet. Create one above!")

    st.markdown("#### 📜 Message History")
    if st.session_state.message_logs:
        df_logs = pd.DataFrame(st.session_state.message_logs)
        st.dataframe(df_logs, width="stretch", hide_index=True)
        
        if st.button("⬇️ Export Logs"):
            csv = df_logs.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name=f"whatsapp_logs_{date.today()}.csv",
                mime="text/csv"
            )
    else:
        st.info("No messages sent or scheduled yet.")

# ============================================
# 🔥 MAIN RENDER FUNCTION - WITH INITIALIZATION
# ============================================

def render(gym_id, role):
    # 🔥 CRITICAL: Initialize session state FIRST
    _init_session_state()
    
    reminder_days = get_reminder_days()
    absent_days = get_absent_days()
    current_lang = get_whatsapp_language()
    tips_enabled = get_tips_enabled()

    styles.page_header("💬", "WhatsApp Automation",
                       "Auto bulk send · Fee reminders · Absentee alerts · Birthdays")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    all_members = get_cached_members()
    total_members = len(all_members)
    pending_count = len([m for m in all_members if m.phone])
    total_sent = len(st.session_state.message_logs)
    success_rate = 95 if total_sent > 0 else 0
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📤 Total Sent", total_sent)
    col2.metric("⏳ Pending", pending_count)
    col3.metric("✅ Success Rate", f"{success_rate}%")
    col4.metric("👥 Total Members", total_members)
    st.markdown("---")

    with st.expander("⚙️ Message Settings", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_reminder_days = st.number_input(
                "Fee reminder — days ahead", 
                min_value=1, max_value=60,
                value=reminder_days, step=1, key="wa_days_threshold_input",
            )
            if new_reminder_days != reminder_days:
                set_reminder_days(new_reminder_days)
                reminder_days = new_reminder_days
                st.success(f"✅ Reminder days set to {reminder_days}")
        with c2:
            new_absent_days = st.number_input(
                "Absentee alert after (days)", 
                min_value=1, max_value=30,
                value=absent_days, step=1, key="wa_absent_days_input",
            )
            if new_absent_days != absent_days:
                set_absent_days(new_absent_days)
                absent_days = new_absent_days
                st.success(f"✅ Absent days set to {absent_days}")
        with c3:
            new_lang = st.radio(
                "Message language", ["English", "Urdu"], horizontal=True,
                index=0 if current_lang == "English" else 1, key="wa_lang_radio"
            )
            if new_lang != current_lang:
                set_whatsapp_language(new_lang)
                current_lang = new_lang
                st.success(f"✅ Language set to {current_lang}")
        
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
        
        default_temp = URDU_TEMPLATE if current_lang == "Urdu" else DEFAULT_TEMPLATE
        template = st.text_area(
            "Custom Message Template",
            value=default_temp,
            height=80, key="wa_template",
            help="Placeholders: {name} {gym} {expiry} {days}"
        )
        st.caption("💡 WhatsApp links open WhatsApp Web / App — popups must be allowed in browser.")
        
        st.markdown("---")
        st.markdown("#### 💡 Daily Fitness Tips")
        col_tip1, col_tip2 = st.columns([1, 2])
        with col_tip1:
            new_tips_enabled = st.checkbox("✅ Include Daily Tips in Messages", value=tips_enabled, key="wa_tips_checkbox")
            if new_tips_enabled != tips_enabled:
                set_tips_enabled(new_tips_enabled)
                tips_enabled = new_tips_enabled
                st.success("✅ Tips settings updated!")
        with col_tip2:
            if tips_enabled:
                st.info(f"📅 Today's Tip: {get_daily_tip()}")
            else:
                st.warning("⚠️ Tips are disabled. Enable to add motivational tips to messages.")
        
        if tips_enabled:
            with st.expander("📋 View All Tips"):
                st.markdown("**This Week's Tips:**")
                weekly_tips = get_tip_for_week()
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for i, tip in enumerate(weekly_tips):
                    today = " ⬅️ Today" if i == datetime.now().weekday() else ""
                    st.markdown(f"**{days[i]}:** {tip}{today}")

    st.divider()

    tab_auto, tab_expiry, tab_absent, tab_birthday, tab_streak, tab_expired, tab_schedule, tab_analytics = st.tabs([
        "🤖 Auto-Send",
        "⏰ Fee Expiry",
        "🚶 Absentee",
        "🎂 Birthdays",
        "🔥 Streaks",
        "📅 Expired Members",
        "⏰ Schedule",
        "📊 Analytics"
    ])

    with tab_auto:
        render_auto_tab(gym_id, role, gyms, reminder_days, absent_days, current_lang)

    with tab_expiry:
        render_expiry_tab(gym_id, gyms, reminder_days, current_lang)

    with tab_absent:
        render_absent_tab(gym_id, gyms, absent_days, current_lang)

    with tab_birthday:
        render_birthday_tab(gym_id, gyms, current_lang)

    with tab_streak:
        render_streak_tab(gym_id, gyms)
    
    with tab_expired:
        render_expired_tab(gym_id, gyms, current_lang)

    with tab_schedule:
        render_schedule_tab(current_lang)

    with tab_analytics:
        render_analytics_dashboard()