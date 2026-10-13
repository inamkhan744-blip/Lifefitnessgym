"""
GymPro Member Portal — COMPLETE VERSION with AI Voice Trainer
Member apni serial number + phone se login karein.

Features:
 • Hero profile card with photo
 • Membership card (credit-card style)
 • Live fee countdown + payment history
 • Self check-in + daily code + 30-day attendance calendar
 • Progress charts (weight, measurements, BMI)
 • AI Diet Plan (7-day, personalized)
 • AI Exercise Coach (daily workout + chat)
 • 🏋️ AI VOICE TRAINER (NEW!) — Urdu voice feedback
 • Gym leaderboard rank
 • Daily motivational quote
 • Workout Timer
 • Water Tracker
 • Fasting Tracker
 • Share via WhatsApp
"""

import streamlit as st
import database as db
import object_store
import os, io, base64, hashlib, requests, time, json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# PHOTO HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _get_member_photo_b64(photo_field: str, serial_number: str = "") -> str | None:
    """Return a data-URI for the member photo."""
    if not photo_field:
        return None
    photo_str = str(photo_field).strip()
    if "<div" in photo_str or "style=" in photo_str:
        return None

    if photo_str.startswith("http"):
        try:
            resp = requests.get(photo_str, timeout=8)
            if resp.status_code == 200:
                ext = "jpeg"
                ct = resp.headers.get("Content-Type", "")
                if "png" in ct:
                    ext = "png"
                b64 = base64.b64encode(resp.content).decode()
                return f"data:image/{ext};base64,{b64}"
        except Exception:
            return photo_str

    try:
        b64, mime = object_store.get_photo_b64(photo_str)
        if b64:
            return f"data:image/{mime};base64,{b64}"
    except Exception:
        pass

    for path_candidate in [
        photo_str,
        os.path.join(os.path.dirname(__file__), "..", photo_str),
        os.path.join(os.path.dirname(__file__), "..", "uploads", os.path.basename(photo_str)),
    ]:
        if os.path.exists(path_candidate):
            try:
                with open(path_candidate, "rb") as f:
                    raw = f.read()
                b64 = base64.b64encode(raw).decode()
                return f"data:image/jpeg;base64,{b64}"
            except Exception:
                pass

    if serial_number:
        for ext in [".jpg", ".jpeg", ".png"]:
            p = os.path.join(os.path.dirname(__file__), "..", "member_photos", f"{serial_number}{ext}")
            if os.path.exists(p):
                try:
                    with open(p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    return f"data:image/jpeg;base64,{b64}"
                except Exception:
                    pass

    return None


# ─────────────────────────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _mp_member():
    mid = st.session_state.get("portal_member_id")
    return db.get_member(mid) if mid else None


def _mp_logout():
    for k in ["portal_member_id", "portal_member_serial", "mp_chat",
              "mp_diet_plan", "mp_workout_plan", "mp_diet_goal"]:
        st.session_state.pop(k, None)
    st.rerun()


def _record_portal_activity(member, event="MEMBER_PORTAL_ACTIVE"):
    now = time.time()
    last_logged = st.session_state.get("mp_last_activity_log", 0.0)
    if event == "MEMBER_PORTAL_LOGIN" or now - last_logged >= 300:
        db.log_activity(
            user=member.serial_number,
            action=event,
            details=f"Member: {member.full_name} | Portal activity",
            gym_id=member.gym_id,
            role="member",
            record_ref=str(member.id),
        )
        st.session_state["mp_last_activity_log"] = now


def _staff_usage_panel():
    gym_id = st.session_state.get("selected_gym_id")
    gyms = {g.id: g.name for g in db.get_all_gyms()}

    st.markdown(
        "<div style='font-size:1.6rem;font-weight:900;color:#A78BFA;'>"
        "📱 Member Portal Usage</div>"
        "<div style='color:#94A3B8;margin-bottom:1rem;'>"
        "Yahan aap dekh sakte hain kaun se members portal use kar rahe hain.</div>",
        unsafe_allow_html=True,
    )
    if st.button("🔄 Refresh Usage", key="mp_usage_refresh"):
        st.rerun()

    usage = db.get_member_portal_usage(gym_id=gym_id)
    today = date.today()
    active_now = [u for u in usage if u["is_active"]]
    used_today = [u for u in usage if u["last_seen"] and u["last_seen"].date() == today]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🟢 Active Now", len(active_now), "last 15 minutes")
    with c2:
        st.metric("📅 Used Today", len(used_today))
    with c3:
        st.metric("👥 Total Members Used", len(usage))

    if not usage:
        st.info("Abhi kisi member ne Member Portal login nahi kiya.")
        return

    rows = []
    for item in usage:
        rows.append({
            "Status": "🟢 Online" if item["is_active"] else "⚪ Not active",
            "Member": item["name"] or "Unknown",
            "Serial": item["serial"],
            "Gym": gyms.get(item["gym_id"], "—"),
            "Last Active": item["last_seen_text"],
            "Visits": item["visits"],
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ─────────────────────────────────────────────────────────────────────────────
# AI HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _groq(messages: list, max_tokens=2000) -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return "⚠️ GROQ_API_KEY set nahi — AI unavailable."
    
    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
    last_error = None
    for model in models_to_try:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": max_tokens},
                timeout=30,
            )
            if r.status_code == 200:
                data = r.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
            else:
                last_error = f"Model {model} failed: {r.status_code}"
        except Exception as e:
            last_error = str(e)
    return f"⚠️ AI error: {last_error}"


# ─────────────────────────────────────────────────────────────────────────────
# TTS — VOICE FEEDBACK
# ─────────────────────────────────────────────────────────────────────────────

def _play_tts_urdu(text: str, key_suffix: str = ""):
    """Play Urdu/English text as voice using gTTS."""
    try:
        from gtts import gTTS
        # Detect Urdu characters
        is_urdu = any(ord(c) in range(0x0600, 0x06FF) for c in text)
        lang_code = "ur" if is_urdu else "en"
        
        clean_text = text[:300]  # Limit length
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.warning(f"🔊 Voice error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _daily_code(member_id: int) -> str:
    h = hashlib.sha256(f"{member_id}-{date.today().isoformat()}-GYMPRO".encode()).hexdigest()
    return h[:6].upper()


_QUOTES = [
    "Push yourself, because no one else is going to do it for you.",
    "Success starts with self-discipline.",
    "The body achieves what the mind believes.",
    "Your only limit is your mind.",
    "Don't stop when you're tired. Stop when you're done.",
    "Be stronger than your excuses.",
    "It never gets easier — you just get better.",
    "Consistency > Perfection.",
    "Small steps every day lead to big results.",
    "Fitness is not a destination, it's a way of life.",
]


def _daily_quote() -> str:
    idx = date.today().toordinal() % len(_QUOTES)
    return _QUOTES[idx]


# ─────────────────────────────────────────────────────────────────────────────
# SHARE BUTTON
# ─────────────────────────────────────────────────────────────────────────────

def _render_share_button(text: str):
    col1, col2 = st.columns(2)
    with col1:
        encoded = text.replace("\n", "%0A").replace(" ", "%20")[:500]
        whatsapp_url = f"https://wa.me/?text={encoded}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">'
                    f'<div style="background:#25D366;color:white;padding:0.4rem 0.8rem;border-radius:8px;text-align:center;font-weight:600;">📱 Share via WhatsApp</div></a>',
                    unsafe_allow_html=True)
    with col2:
        if st.button("📋 Copy", key=f"copy_{time.time()}", use_container_width=True):
            st.info("✅ Content ready to copy")


# ─────────────────────────────────────────────────────────────────────────────
# WORKOUT TIMER
# ─────────────────────────────────────────────────────────────────────────────

def _render_timer():
    st.markdown("### ⏱️ Workout Timer")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        minutes = st.number_input("Minutes", min_value=1, max_value=60, value=5, key="mp_timer_minutes")
    with col2:
        if st.button("▶️ Start", key="mp_timer_start", use_container_width=True):
            st.session_state["mp_timer_running"] = True
            st.session_state["mp_timer_end"] = time.time() + (minutes * 60)
    with col3:
        if st.button("⏹ Stop", key="mp_timer_stop", use_container_width=True):
            st.session_state["mp_timer_running"] = False

    if st.session_state.get("mp_timer_running", False):
        remaining = st.session_state["mp_timer_end"] - time.time()
        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #7c3aed;border-radius:12px;
                        padding:0.8rem;text-align:center;margin:0.5rem 0;">
                <div style="font-size:2.5rem;font-weight:900;color:#a78bfa;">{mins:02d}:{secs:02d}</div>
                <div style="color:#64748b;font-size:0.8rem;">Time Remaining</div>
            </div>
            """, unsafe_allow_html=True)
            st.rerun()
        else:
            st.success("⏰ Timer finished! 🎉")
            st.session_state["mp_timer_running"] = False


# ─────────────────────────────────────────────────────────────────────────────
# WATER TRACKER
# ─────────────────────────────────────────────────────────────────────────────

def _render_water_tracker(suffix: str = "home"):
    st.markdown("### 💧 Water Tracker")
    
    if "mp_water" not in st.session_state:
        st.session_state["mp_water"] = 0
        st.session_state["mp_water_date"] = date.today().isoformat()
    
    if st.session_state["mp_water_date"] != date.today().isoformat():
        st.session_state["mp_water"] = 0
        st.session_state["mp_water_date"] = date.today().isoformat()
    
    target = 8
    current = st.session_state["mp_water"]
    pct = min(current / target * 100, 100)
    color = "#34d399" if pct >= 80 else "#fbbf24" if pct >= 50 else "#f87171"
    
    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1rem;margin:0.5rem 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
            <span style="color:#64748b;font-size:0.8rem;">Today's Water</span>
            <span style="color:{color};font-weight:800;font-size:1.2rem;">{current}/{target} glasses</span>
        </div>
        <div style="background:#1e293b;border-radius:99px;height:12px;overflow:hidden;">
            <div style="height:100%;width:{pct:.0f}%;background:linear-gradient(90deg,#34d399,{color});border-radius:99px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Add", key=f"mp_water_add_{suffix}", use_container_width=True):
            st.session_state["mp_water"] += 1
            st.rerun()
    with col2:
        if st.button("➖ Remove", key=f"mp_water_remove_{suffix}", use_container_width=True):
            if st.session_state["mp_water"] > 0:
                st.session_state["mp_water"] -= 1
                st.rerun()
    with col3:
        if st.button("🔄 Reset", key=f"mp_water_reset_{suffix}", use_container_width=True):
            st.session_state["mp_water"] = 0
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# FASTING TRACKER
# ─────────────────────────────────────────────────────────────────────────────

def _render_fasting_tracker():
    st.markdown("### ⏰ Fasting Tracker")
    
    if "mp_fasting_start" not in st.session_state:
        st.session_state["mp_fasting_start"] = None
    if "mp_fasting_active" not in st.session_state:
        st.session_state["mp_fasting_active"] = False
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Fast", key="mp_fast_start", use_container_width=True, type="primary"):
            st.session_state["mp_fasting_start"] = time.time()
            st.session_state["mp_fasting_active"] = True
            st.rerun()
    with col2:
        if st.button("⏹ End Fast", key="mp_fast_end", use_container_width=True):
            if st.session_state["mp_fasting_active"]:
                duration = (time.time() - st.session_state["mp_fasting_start"]) / 3600
                st.success(f"✅ Fast ended! Duration: {duration:.1f} hours")
                st.session_state["mp_fasting_active"] = False
            st.rerun()
    
    if st.session_state.get("mp_fasting_active") and st.session_state.get("mp_fasting_start"):
        elapsed = (time.time() - st.session_state["mp_fasting_start"]) / 3600
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #a78bfa;border-radius:12px;
                    padding:0.8rem;text-align:center;margin:0.5rem 0;">
            <div style="font-size:2rem;font-weight:900;color:#a78bfa;">{elapsed:.1f}h</div>
            <div style="color:#64748b;font-size:0.8rem;">Fasting in progress 🕐</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption("16:8 intermittent fasting — 16 hours fast, 8 hours eating window")


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

PORTAL_CSS = """
<style>
.mp-hero {
    background: linear-gradient(135deg, #1a0533 0%, #0f172a 60%, #1e293b 100%);
    border: 1px solid #7c3aed44; border-radius: 24px;
    padding: 2rem 2rem 1.5rem; margin-bottom: 1.2rem;
    position: relative; overflow: hidden;
}
.mp-hero::before {
    content: ''; position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, #7c3aed33 0%, transparent 70%);
    border-radius: 50%;
}
.mp-photo-ring {
    width: 130px; height: 130px; border-radius: 50%;
    border: 4px solid #7c3aed;
    box-shadow: 0 0 0 4px #7c3aed33, 0 8px 32px rgba(124,58,237,0.5);
    overflow: hidden;
    background: linear-gradient(135deg,#7c3aed,#4f46e5);
    flex-shrink: 0; display: inline-block;
}
.mp-photo-ring img { width:100%; height:100%; object-fit:cover; display:block; }
.mp-photo-initials {
    width:100%; height:100%; display:flex; align-items:center; justify-content:center;
    font-size:2.8rem; font-weight:900; color:white;
}
.mp-card-3d {
    background: linear-gradient(135deg, #7c3aed 0%, #4338ca 50%, #1d4ed8 100%);
    border-radius: 20px; padding: 1.6rem 1.8rem; color: white;
    position: relative; overflow: hidden;
    box-shadow: 0 20px 60px rgba(124,58,237,0.45); min-height: 180px;
}
.mp-card-3d::before {
    content: ''; position: absolute; top: -50px; right: -50px;
    width: 200px; height: 200px; background: rgba(255,255,255,0.08); border-radius: 50%;
}
.mp-card-3d::after {
    content: ''; position: absolute; bottom: -70px; left: -30px;
    width: 250px; height: 250px; background: rgba(255,255,255,0.05); border-radius: 50%;
}
.mc-chip {
    width: 40px; height: 30px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    border-radius: 6px; margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.mp-tile {
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 16px; padding: 1rem 0.8rem;
    text-align: center; height: 100%; transition: border-color 0.2s;
}
.mp-tile:hover { border-color: #7c3aed66; }
.mp-tile-val { font-size: 1.8rem; font-weight: 800; margin: 0; line-height: 1.1; }
.mp-tile-lbl { font-size: 0.7rem; color: #64748b; margin: 0.2rem 0 0; text-transform: uppercase; letter-spacing: 1px; }
.mp-tile-sub { font-size: 0.72rem; color: #94a3b8; margin: 0.15rem 0 0; }
.mp-quote {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    border-left: 4px solid #7c3aed; border-radius: 0 12px 12px 0;
    padding: 0.9rem 1.2rem; margin: 0.5rem 0 1rem;
}
.mp-sec {
    font-size: 1rem; font-weight: 700; color: #a78bfa;
    border-bottom: 1px solid #7c3aed22;
    padding-bottom: 0.35rem; margin: 1.2rem 0 0.8rem;
    display: flex; align-items: center; gap: 0.4rem;
}
.badge { padding: 4px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; display: inline-block; }
.badge-active   { background:#064e3b33; color:#34d399; border:1px solid #34d39944; }
.badge-expired  { background:#450a0a33; color:#f87171; border:1px solid #f8717144; }
.badge-inactive { background:#1e1b4b33; color:#a78bfa; border:1px solid #a78bfa44; }
.badge-frozen   { background:#0c1a2e33; color:#60a5fa; border:1px solid #60a5fa44; }
.badge-suspended { background:#451a0333; color:#fb923c; border:1px solid #fb923c44; }
.mp-bar-bg { background: #1e293b; border-radius: 99px; height: 10px; overflow: hidden; margin-top: 0.3rem; }
.mp-bar-fill { height: 100%; border-radius: 99px; transition: width 0.5s ease; }
.att-code {
    font-size: 2.8rem; font-weight: 900; letter-spacing: 10px;
    text-align: center; color: #7c3aed;
    background: #0f172a; border: 2px dashed #7c3aed66;
    border-radius: 14px; padding: 1.1rem 0;
    font-family: 'Courier New', monospace;
}
.chat-user {
    background: linear-gradient(135deg,#4c1d95,#312e81);
    border-radius: 18px 18px 4px 18px;
    padding: 0.7rem 1rem; margin: 0.4rem 0;
    color: #e0e7ff; font-size: 0.9rem; text-align: right;
}
.chat-ai {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 18px 18px 18px 4px;
    padding: 0.7rem 1rem; margin: 0.4rem 0;
    color: #e2e8f0; font-size: 0.9rem;
}
.lb-row {
    display: flex; align-items: center; gap: 0.7rem;
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 10px; padding: 0.6rem 0.9rem; margin-bottom: 0.4rem;
}
.lb-rank { font-size: 1.2rem; font-weight: 900; min-width: 2rem; text-align: center; }
.lb-name { flex: 1; font-weight: 600; color: #e2e8f0; font-size: 0.9rem; }
.lb-count { color: #a78bfa; font-weight: 700; font-size: 0.85rem; }
.mp-notif-warn {
    background: #451a0322; border: 1px solid #fb923c55;
    border-radius: 10px; padding: 0.7rem 1rem;
    color: #fb923c; font-size: 0.85rem; margin-bottom: 0.5rem;
}
.mp-notif-danger {
    background: #450a0a22; border: 1px solid #f8717155;
    border-radius: 10px; padding: 0.7rem 1rem;
    color: #f87171; font-size: 0.85rem; margin-bottom: 0.5rem;
}
.mp-notif-ok {
    background: #064e3b22; border: 1px solid #34d39955;
    border-radius: 10px; padding: 0.7rem 1rem;
    color: #34d399; font-size: 0.85rem; margin-bottom: 0.5rem;
}
.qa-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 10px; margin: 0.5rem 0 1.2rem 0;
}
.qa-item {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #7c3aed33; border-radius: 14px;
    padding: 14px 8px; text-align: center;
}
.qa-item .icon { font-size: 2rem; display: block; margin-bottom: 2px; }
.qa-item .label { font-size: 0.85rem; font-weight: 700; color: #e2e8f0; }
.qa-item .sub { font-size: 0.65rem; color: #64748b; }
.vt-voice-card {
    background: linear-gradient(135deg, #1a0533, #0f172a);
    border: 2px solid #7c3aed;
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}
.vt-voice-btn {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 1rem;
    font-weight: 700;
    width: 100%;
    cursor: pointer;
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

def _login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:3.5rem; margin-bottom:0.3rem;">🏋️</div>
            <div style="font-size:2rem; font-weight:900; background:linear-gradient(135deg,#a78bfa,#7c3aed);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                Member Portal
            </div>
            <div style="color:#64748b; font-size:0.88rem; margin-top:0.3rem;">
                Apna profile, attendance, progress & AI coach
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("mp_login", clear_on_submit=False):
            serial = st.text_input("🪪 Membership Serial Number", placeholder="e.g. PF-00001")
            phone4 = st.text_input("📱 Phone ke akhri 4 digits", placeholder="e.g. 5678", max_chars=4)
            login_btn = st.form_submit_button("🔓 Login", type="primary", use_container_width=True)

        if login_btn:
            if not serial.strip() or not phone4.strip():
                st.error("Dono fields zaruri hain.")
                return
            member = db.get_member_by_serial(serial.strip().upper())
            if not member:
                st.error("❌ Serial number nahi mila.")
                return
            digits = "".join(c for c in (member.phone or "") if c.isdigit())
            if not digits.endswith(phone4.strip()):
                st.error("❌ Phone digits galat hain.")
                return
            st.session_state["portal_member_id"] = member.id
            _record_portal_activity(member, "MEMBER_PORTAL_LOGIN")
            if "mp_chat" not in st.session_state:
                st.session_state["mp_chat"] = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────

def _render_hero(m, gym):
    today = date.today()
    days_left = None
    if m.expiry_date:
        try:
            days_left = (date.fromisoformat(str(m.expiry_date)) - today).days
        except Exception:
            pass

    att_rate = db.get_member_attendance_rate(m.id, days=30)
    streak = db.get_member_streak(m.id)
    photo_b64 = _get_member_photo_b64(m.photo_path, m.serial_number)
    initials = "".join(p[0] for p in m.full_name.split()[:2]).upper()
    badge_cls = {"Active": "active", "Expired": "expired", "Inactive": "inactive",
                 "Frozen": "frozen", "Suspended": "suspended"}.get(m.status, "inactive")

    if days_left is None:
        exp_color, exp_txt = "#94a3b8", "—"
    elif days_left > 10:
        exp_color, exp_txt = "#34d399", f"{days_left} din bacha"
    elif days_left >= 0:
        exp_color, exp_txt = "#fbbf24", f"⚠️ {days_left} din"
    else:
        exp_color, exp_txt = "#f87171", f"🔴 {abs(days_left)} din overdue"

    if days_left is not None and days_left < 0:
        st.markdown(f'<div class="mp-notif-danger">🔴 Membership <b>{abs(days_left)} din pehle</b> expire ho gayi.</div>', unsafe_allow_html=True)
    elif days_left is not None and days_left <= 5:
        st.markdown(f'<div class="mp-notif-warn">⚠️ Sirf <b>{days_left} din</b> bache hain — renew karaein!</div>', unsafe_allow_html=True)

    if m.dob:
        try:
            dob = date.fromisoformat(str(m.dob))
            if dob.month == today.month and dob.day == today.day:
                st.markdown('<div class="mp-notif-ok">🎂 Happy Birthday! 🎉</div>', unsafe_allow_html=True)
        except Exception:
            pass

    quote = _daily_quote()
    photo_html = f'<img src="{photo_b64}" style="width:100%;height:100%;object-fit:cover;" />' if photo_b64 else f'<div class="mp-photo-initials">{initials}</div>'

    st.markdown(f"""
    <div class="mp-hero">
      <div style="display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;">
        <div class="mp-photo-ring">{photo_html}</div>
        <div style="flex:1; min-width:180px;">
          <div style="font-size:1.6rem; font-weight:900; color:#f1f5f9;">{m.full_name}</div>
          <div style="font-size:0.8rem; color:#7c3aed; font-weight:700; letter-spacing:1.5px;">#{m.serial_number}</div>
          <span class="badge badge-{badge_cls}">{m.status}</span>
          <span style="font-size:0.78rem; color:#94a3b8;">🏋️ {gym.name if gym else '—'} | 🎫 {m.membership_type}</span>
          <div style="margin-top:0.7rem; display:flex; gap:1.5rem; flex-wrap:wrap;">
            <div><div style="font-size:0.68rem;color:#64748b;">EXPIRY</div><div style="color:{exp_color};font-weight:700;">{exp_txt}</div></div>
            <div><div style="font-size:0.68rem;color:#64748b;">STREAK</div><div style="color:#f59e0b;font-weight:700;">🔥 {streak} days</div></div>
            <div><div style="font-size:0.68rem;color:#64748b;">30d RATE</div><div style="color:#a78bfa;font-weight:700;">{att_rate:.0f}%</div></div>
          </div>
        </div>
      </div>
      <div class="mp-quote" style="margin-top:1.2rem;">
        <div style="font-size:0.82rem;font-style:italic;color:#cbd5e1;">"{quote}"</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — HOME
# ─────────────────────────────────────────────────────────────────────────────

def _tab_home(m, gym):
    today = date.today()
    st.markdown('<div class="mp-sec">📊 Quick Stats</div>', unsafe_allow_html=True)

    fee_recs = db.get_fee_records(member_id=m.id)
    total_paid = sum(r.amount for r in fee_recs) if fee_recs else 0
    att_rate = db.get_member_attendance_rate(m.id, days=30)
    streak = db.get_member_streak(m.id)

    days_left = None
    if m.expiry_date:
        try:
            days_left = (date.fromisoformat(str(m.expiry_date)) - today).days
        except Exception:
            pass

    c1, c2, c3, c4 = st.columns(4)
    tiles = [
        (c1, str(days_left) if days_left is not None else "—",
         "#34d399" if (days_left or 0) > 7 else "#fbbf24" if (days_left or 0) >= 0 else "#f87171",
         "Days Left", m.expiry_date or "—"),
        (c2, f"🔥 {streak}", "#f59e0b", "Day Streak", ""),
        (c3, f"{att_rate:.0f}%", "#34d399" if att_rate >= 70 else "#fbbf24", "30d Rate", ""),
        (c4, f"PKR {total_paid:,.0f}", "#a78bfa", "Total Paid", f"{len(fee_recs)} receipts"),
    ]
    for col, val, color, lbl, sub in tiles:
        with col:
            st.markdown(f"""
            <div class="mp-tile">
              <div class="mp-tile-val" style="color:{color};">{val}</div>
              <div class="mp-tile-lbl">{lbl}</div>
              {'<div class="mp-tile-sub">' + sub + '</div>' if sub else ''}
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="mp-sec">💳 Membership Card</div>', unsafe_allow_html=True)
    gym_name = gym.name if gym else "GymPro"
    st.markdown(f"""
    <div class="mp-card-3d">
      <div class="mc-chip"></div>
      <div style="position:relative; z-index:1;">
        <div style="font-size:0.65rem;letter-spacing:3px;opacity:0.7;">GYMPRO MEMBER</div>
        <div style="font-size:1.4rem;font-weight:900;margin:0.3rem 0;">{m.full_name.upper()}</div>
        <div style="font-size:0.9rem;letter-spacing:4px;font-family:monospace;opacity:0.85;">{m.serial_number}</div>
        <div style="display:flex;justify-content:space-between;margin-top:1rem;">
          <div><div style="font-size:0.6rem;opacity:0.65;">MEMBERSHIP</div><div style="font-weight:700;">{m.membership_type}</div></div>
          <div><div style="font-size:0.6rem;opacity:0.65;">VALID THRU</div><div style="font-weight:700;">{str(m.expiry_date or '—')}</div></div>
          <div style="font-size:1.5rem;opacity:0.3;">🏋️</div>
        </div>
        <div style="font-size:0.75rem;opacity:0.5;">{gym_name}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="mp-sec">💧 Daily Hydration</div>', unsafe_allow_html=True)
    _render_water_tracker(suffix="home")

    st.markdown('<div class="mp-sec">🏆 Gym Leaderboard</div>', unsafe_allow_html=True)
    board = db.get_attendance_leaderboard(gym_id=m.gym_id, limit=10)
    rank_icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, row in enumerate(board):
        icon = rank_icons[i] if i < len(rank_icons) else f"#{i+1}"
        is_me = row["member"].id == m.id
        highlight = "border-color:#7c3aed;" if is_me else ""
        st.markdown(f"""
        <div class="lb-row" style="{highlight}">
          <div class="lb-rank">{icon}</div>
          <div class="lb-name">{row['member'].full_name}{' (You)' if is_me else ''}</div>
          <div class="lb-count">🔥 {row['streak']}d | 📅 {row['count']} days</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — ATTENDANCE
# ─────────────────────────────────────────────────────────────────────────────

def _tab_attendance(m):
    today = date.today()
    st.markdown('<div class="mp-sec">📲 Aaj ka Check-In</div>', unsafe_allow_html=True)

    all_today = db.get_attendance(check_date=str(today))
    today_att = next((a for a in all_today if a.member_id == m.id), None)

    c_code, c_btn = st.columns([1, 1])
    with c_code:
        code = _daily_code(m.id)
        st.markdown(f"""
        <div style="text-align:center;">
          <div style="font-size:0.72rem;color:#64748b;margin-bottom:0.4rem;">AAJ KA CODE</div>
          <div class="att-code">{code}</div>
        </div>
        """, unsafe_allow_html=True)

    with c_btn:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        if today_att:
            st.success(f"✅ Aaj ki attendance: **{today_att.status}**")
        else:
            st.warning("⏰ Abhi mark nahi hui")
            if st.button("✅ Present Mark Karo", type="primary", use_container_width=True):
                ok, msg = db.mark_attendance(m.id, m.gym_id, today, "Present", "member-self")
                if ok:
                    st.success("✅ Mark ho gayi!")
                    st.rerun()

    st.divider()
    streak = db.get_member_streak(m.id)
    rate30 = db.get_member_attendance_rate(m.id, days=30)
    rate7 = db.get_member_attendance_rate(m.id, days=7)

    s1, s2, s3 = st.columns(3)
    for col, val, color, lbl in [
        (s1, f"🔥 {streak}", "#f59e0b", "Day Streak"),
        (s2, f"{rate30:.0f}%", "#34d399", "30-Day"),
        (s3, f"{rate7:.0f}%", "#a78bfa", "7-Day"),
    ]:
        with col:
            st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:{color};">{val}</div><div class="mp-tile-lbl">{lbl}</div></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PROGRESS
# ─────────────────────────────────────────────────────────────────────────────

def _tab_progress(m):
    records = db.get_body_measurements(m.id)

    with st.expander("➕ Naya Measurement", expanded=not bool(records)):
        with st.form("mp_meas"):
            c1, c2, c3 = st.columns(3)
            with c1:
                weight = st.number_input("⚖️ Weight (kg)", 20.0, 300.0, 70.0, 0.5)
                chest = st.number_input("Chest (cm)", 0.0, 200.0, 0.0, 0.5)
            with c2:
                waist = st.number_input("Waist (cm)", 0.0, 200.0, 0.0, 0.5)
                hips = st.number_input("Hips (cm)", 0.0, 200.0, 0.0, 0.5)
            with c3:
                bicep = st.number_input("Bicep (cm)", 0.0, 100.0, 0.0, 0.5)
                body_fat = st.number_input("Body Fat %", 0.0, 60.0, 0.0, 0.5)
            notes = st.text_input("Notes")
            if st.form_submit_button("💾 Save", type="primary"):
                ok, msg = db.add_body_measurement(m.id, date.today(), weight,
                    chest or None, waist or None, hips or None, bicep or None, body_fat or None, notes)
                if ok:
                    st.success("✅ Saved!")
                    st.rerun()

    if not records:
        st.info("Pehla measurement add karo!")
        return

    latest = records[-1]
    first = records[0]
    wc = latest.weight_kg - first.weight_kg

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#e2e8f0;font-size:1.4rem;">{latest.weight_kg} kg</div><div class="mp-tile-lbl">Current</div></div>', unsafe_allow_html=True)
    with t2:
        color = "#34d399" if wc <= 0 else "#f87171"
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:{color};font-size:1.4rem;">{wc:+.1f} kg</div><div class="mp-tile-lbl">Change</div></div>', unsafe_allow_html=True)
    with t3:
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#a78bfa;font-size:1.4rem;">{len(records)}</div><div class="mp-tile-lbl">Entries</div></div>', unsafe_allow_html=True)

    dates = [str(r.recorded_date) for r in records]
    weights = [r.weight_kg for r in records]

    fig_w = go.Figure()
    fig_w.add_trace(go.Scatter(x=dates, y=weights, mode="lines+markers",
        line=dict(color="#7c3aed", width=3),
        marker=dict(size=8, color="#7c3aed"), fill="tozeroy",
        fillcolor="rgba(124,58,237,0.08)"))
    fig_w.update_layout(title="Weight Progress", plot_bgcolor="#0a0a0f",
        paper_bgcolor="#0a0a0f", font_color="#e2e8f0", title_x=0.5, height=280)
    st.plotly_chart(fig_w, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — FEES
# ─────────────────────────────────────────────────────────────────────────────

def _tab_fees(m, gym):
    fee_recs = db.get_fee_records(member_id=m.id)
    total = sum(r.amount for r in fee_recs) if fee_recs else 0

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#a78bfa;font-size:1.4rem;">PKR {total:,.0f}</div><div class="mp-tile-lbl">Total Paid</div></div>', unsafe_allow_html=True)
    with f2:
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#34d399;font-size:1.4rem;">{len(fee_recs)}</div><div class="mp-tile-lbl">Receipts</div></div>', unsafe_allow_html=True)
    with f3:
        lf = sorted(fee_recs, key=lambda r: r.payment_date, reverse=True)[0].payment_date if fee_recs else "—"
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#e2e8f0;font-size:1rem;">{lf}</div><div class="mp-tile-lbl">Last Payment</div></div>', unsafe_allow_html=True)

    if fee_recs:
        st.markdown('<div class="mp-sec">🧾 Payment History</div>', unsafe_allow_html=True)
        rows = [{"Date": r.payment_date, "Amount": f"PKR {r.amount:,.0f}",
                 "Method": r.payment_method or "—", "Receipt": r.receipt_number or "—"}
                for r in sorted(fee_recs, key=lambda x: x.payment_date, reverse=True)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — AI COACH
# ─────────────────────────────────────────────────────────────────────────────

def _tab_ai(m):
    records = db.get_body_measurements(m.id)
    latest = records[-1] if records else None

    sub = st.tabs(["🥗 Diet Plan", "💪 Workout", "💬 AI Chat", "⏱️ Tools"])

    # ── Diet Plan ──
    with sub[0]:
        st.markdown('<div class="mp-sec">🥗 AI Diet Plan</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            goal = st.selectbox("🎯 Goal", ["Weight Loss","Muscle Gain","Maintenance","Endurance"])
            weight = st.number_input("⚖️ Weight (kg)", 30.0, 300.0, float(latest.weight_kg) if latest else 70.0, 0.5)
        with c2:
            height = st.number_input("📏 Height (cm)", 100, 250, 170)
            activity = st.selectbox("🏃 Activity", ["Sedentary","Lightly Active","Moderate","Very Active"])

        if st.button("🤖 Diet Plan Generate Karo", type="primary", use_container_width=True):
            with st.spinner("AI tayyar kar raha hai..."):
                plan = _groq([
                    {"role":"system","content":"You are a nutritionist. Respond in Roman Urdu + English."},
                    {"role":"user","content":f"7-day diet plan for {m.full_name}, weight {weight}kg, goal {goal}, activity {activity}. Include Pakistani foods, calories, times."}
                ], max_tokens=2500)
                st.session_state["mp_diet_plan"] = plan

        if st.session_state.get("mp_diet_plan"):
            st.divider()
            st.markdown(st.session_state["mp_diet_plan"])
            st.download_button("⬇️ Download", data=st.session_state["mp_diet_plan"],
                               file_name=f"diet_{m.serial_number}.txt", mime="text/plain")

    # ── Workout ──
    with sub[1]:
        st.markdown('<div class="mp-sec">💪 AI Workout</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            focus = st.selectbox("Focus", ["Full Body","Chest","Back","Legs","Shoulders","Cardio","Core"])
        with c2:
            level = st.selectbox("Level", ["Beginner","Intermediate","Advanced"])
        with c3:
            dur = st.selectbox("Duration", ["30 mins","45 mins","60 mins"])

        if st.button("⚡ Workout Generate Karo", type="primary", use_container_width=True):
            with st.spinner("AI plan bana raha hai..."):
                plan = _groq([
                    {"role":"system","content":"You are a personal trainer. Respond in Roman Urdu + English."},
                    {"role":"user","content":f"{dur} {focus} workout for {level}. Include sets×reps, rest, tips."}
                ], max_tokens=2000)
                st.session_state["mp_workout_plan"] = plan

        if st.session_state.get("mp_workout_plan"):
            st.divider()
            st.markdown(st.session_state["mp_workout_plan"])

    # ── Chat ──
    with sub[2]:
        st.markdown('<div class="mp-sec">💬 AI Coach</div>', unsafe_allow_html=True)
        if "mp_chat" not in st.session_state:
            st.session_state["mp_chat"] = []
        for msg in st.session_state["mp_chat"]:
            cls = "chat-user" if msg["role"] == "user" else "chat-ai"
            icon = "🧑" if msg["role"] == "user" else "🤖"
            st.markdown(f'<div class="{cls}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)

        user_q = st.chat_input("Kuch bhi pocho...")
        if user_q:
            st.session_state["mp_chat"].append({"role": "user", "content": user_q})
            with st.spinner("Soch raha hai..."):
                reply = _groq([{"role":"system","content":f"You are GymPro Coach for {m.full_name}. Roman Urdu + English."}] +
                              [{"role":x["role"],"content":x["content"]} for x in st.session_state["mp_chat"][-10:]], max_tokens=1000)
            st.session_state["mp_chat"].append({"role":"assistant","content":reply})
            st.rerun()

    # ── Tools ──
    with sub[3]:
        st.markdown('<div class="mp-sec">⏱️ Tools</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            _render_timer()
        with c2:
            _render_fasting_tracker()


# ─────────────────────────────────────────────────────────────────────────────
# ⭐ TAB 6 — VOICE TRAINER (NEW)
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# VOICE TRAINER — AI COACH SECTION
# ─────────────────────────────────────────────────────────────────────────────

def _render_ai_voice_coach(m):
    """AI se koi bhi exercise ya fitness sawal poocho"""
    st.markdown('<div class="mp-sec">🤖 AI Voice Coach</div>', unsafe_allow_html=True)
    st.caption("Koi bhi exercise, diet, ya form ka sawal poocho — AI Urdu mein jawab dega")
    
    st.markdown("#### 🎯 Exercise Ka Naam Likho — AI Guide Banayega")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        exercise_input = st.text_input(
            "Exercise ka naam",
            placeholder="e.g. Bicep Curls, Shoulder Press, Lat Pulldown, Deadlift...",
            key="ai_exercise_input",
            label_visibility="collapsed"
        )
    with col2:
        generate_btn = st.button("🤖 Guide Banao", type="primary", use_container_width=True, key="ai_gen_btn")
    
    if generate_btn and exercise_input.strip():
        with st.spinner(f"🤖 AI '{exercise_input}' ka guide bana raha hai..."):
            member_info = {
                "full_name": m.full_name,
                "gender": m.gender,
            }
            
            guide_json = db.ai_generate_exercise_guide(exercise_input.strip(), member_info)
            
            try:
                import json as _json
                clean = guide_json.strip()
                if "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                    if clean.startswith("json"):
                        clean = clean[4:].strip()
                guide = _json.loads(clean)
                st.session_state["ai_generated_guide"] = guide
            except Exception as e:
                st.error(f"❌ AI guide parse nahi hua: {e}")
                st.code(guide_json[:500])
    
    if st.session_state.get("ai_generated_guide"):
        guide = st.session_state["ai_generated_guide"]
        
        st.markdown("---")
        st.markdown(f"""
        <div class="vt-voice-card">
            <div style="font-size:1.4rem;font-weight:900;color:#a78bfa;">{guide.get('name', 'Exercise')}</div>
            <div style="font-size:1.1rem;color:#e2e8f0;margin-bottom:0.5rem;">{guide.get('name_urdu', '')}</div>
            <div style="display:flex;gap:1rem;font-size:0.8rem;color:#94a3b8;flex-wrap:wrap;">
                <span>📂 {guide.get('category', '—')}</span>
                <span>⭐ {guide.get('difficulty', '—')}</span>
                <span>🏋️ {guide.get('equipment', '—')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 Instructions (Steps)", expanded=True):
            for i, step in enumerate(guide.get("instructions", []), 1):
                st.markdown(f"**{i}.** {step}")
        
        if guide.get("common_mistakes"):
            with st.expander("⚠️ Common Mistakes"):
                for mistake in guide["common_mistakes"]:
                    st.markdown(f"❌ {mistake}")
        
        voice_guide = guide.get("voice_guide", {})
        
        st.markdown("---")
        st.markdown("### 🎤 AI Voice Feedback")
        
        wc1, wc2, wc3 = st.columns(3)
        with wc1:
            sets = st.number_input("Sets", 1, 10, 3, key="ai_vt_sets")
        with wc2:
            reps = st.number_input("Reps", 1, 50, 10, key="ai_vt_reps")
        with wc3:
            weight = st.number_input("Weight (kg)", 0.0, 500.0, 0.0, step=2.5, key="ai_vt_weight")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶️ Start", type="primary", use_container_width=True, key="ai_vt_start"):
                msg = voice_guide.get("start", "Exercise shuru karein.")
                st.success(f"🔊 {msg}")
                _play_tts_urdu(msg, "start")
        with col2:
            if st.button("✅ Good Rep", use_container_width=True, key="ai_vt_good"):
                msg = voice_guide.get("good_rep", "Shabash!")
                st.success(f"🔊 {msg}")
                _play_tts_urdu(msg, "good")
        with col3:
            if st.button("⚠️ Bad Form", use_container_width=True, key="ai_vt_bad"):
                msg = voice_guide.get("bad_form", "Form sahi karo.")
                st.warning(f"🔊 {msg}")
                _play_tts_urdu(msg, "bad")
        
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("⏸️ Rest", use_container_width=True, key="ai_vt_rest"):
                msg = voice_guide.get("rest", "Rest lo.")
                st.info(f"🔊 {msg}")
                _play_tts_urdu(msg, "rest")
        with col5:
            if st.button("🏁 Finish", type="primary", use_container_width=True, key="ai_vt_finish"):
                msg = voice_guide.get("finish", "Set complete!")
                st.success(f"🔊 {msg}")
                _play_tts_urdu(msg, "finish")
        with col6:
            if st.button("🔄 Naya", use_container_width=True, key="ai_vt_reset"):
                st.session_state.pop("ai_generated_guide", None)
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 💬 AI se Kuch Bhi Poocho")
    
    if "ai_voice_chat" not in st.session_state:
        st.session_state["ai_voice_chat"] = []
    
    for msg in st.session_state["ai_voice_chat"][-5:]:
        cls = "chat-user" if msg["role"] == "user" else "chat-ai"
        icon = "🧑" if msg["role"] == "user" else "🤖"
        st.markdown(f'<div class="{cls}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)
    
    ai_question = st.chat_input("Exercise ya fitness ke bare mein poocho...", key="ai_voice_chat_input")
    
    if ai_question:
        st.session_state["ai_voice_chat"].append({"role": "user", "content": ai_question})
        
        with st.spinner("🤖 Soch raha hoon..."):
            reply = _groq([
                {"role": "system", "content": f"You are GymPro AI Voice Coach for {m.full_name}. Help with exercises, workouts, form, diet. Respond in Roman Urdu + English. Be specific and encouraging. Keep answers under 150 words."},
                *[{"role": x["role"], "content": x["content"]} for x in st.session_state["ai_voice_chat"][-5:]]
            ], max_tokens=500)
        
        st.session_state["ai_voice_chat"].append({"role": "assistant", "content": reply})
        _play_tts_urdu(reply[:200], "chat")
        st.rerun()
    
    if st.session_state["ai_voice_chat"]:
        if st.button("🗑️ Chat Clear", use_container_width=True, key="ai_voice_chat_clear"):
            st.session_state["ai_voice_chat"] = []
            st.rerun()



def _tab_voice_trainer(m):
    """AI Voice Trainer — Urdu voice feedback for exercises."""
    st.markdown('<div class="mp-sec">🏋️ AI Voice Trainer</div>', unsafe_allow_html=True)
    st.caption("Exercise chuno, AI Urdu mein guide karega")
    
    # ── Gender filter ──
    member_gender = (m.gender or "both").lower()
    gender_filter = "female" if member_gender == "female" else "male" if member_gender == "male" else "both"
    
    # ── Exercise Filters ──
    st.markdown("### 🎯 Apna Exercise Chuno")
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("📂 Category",
            ["All", "Chest", "Back", "Legs", "Arms", "Shoulders", "Core", "Cardio"],
            key="vt_category")
    with col2:
        difficulty = st.selectbox("⭐ Difficulty",
            ["All", "Beginner", "Intermediate", "Advanced"],
            key="vt_difficulty")
    
    # ── Fetch Exercises ──
    try:
        if category == "All":
            exercises = db.get_exercises_by_category(gender=gender_filter)
        else:
            exercises = db.get_exercises_by_category(category=category, gender=gender_filter)
        
        if difficulty != "All":
            exercises = [e for e in exercises if e.difficulty == difficulty]
    except Exception as e:
        st.error(f"❌ Exercises load nahi ho sake: {e}")
        st.info("💡 Staff se kahein ke database mein exercises add karein")
        return
    
    if not exercises:
        st.info("📭 Is category mein koi exercise nahi. Doosri try karo.")
        return
    
    # ── Exercise Dropdown ──
    ex_options = {f"{e.name} ({e.name_urdu or ''})": e.id for e in exercises}
    selected_ex_name = st.selectbox("🏋️ Exercise", list(ex_options.keys()), key="vt_exercise_select")
    ex_id = ex_options[selected_ex_name]
    exercise = db.get_exercise(ex_id)
    
    if not exercise:
        st.error("Exercise not found")
        return
    
    # ── Parse JSON ──
    try:
        instructions = json.loads(exercise.instructions) if exercise.instructions else []
        voice_guide = json.loads(exercise.voice_guide) if exercise.voice_guide else {}
        common_mistakes = json.loads(exercise.common_mistakes) if exercise.common_mistakes else []
    except Exception:
        instructions = []
        voice_guide = {}
        common_mistakes = []
    
    st.markdown("---")
    
    # ── Exercise Info Card ──
    st.markdown(f"""
    <div class="vt-voice-card">
        <div style="font-size:1.4rem;font-weight:900;color:#a78bfa;">{exercise.name}</div>
        <div style="font-size:1.1rem;color:#e2e8f0;margin-bottom:0.5rem;">{exercise.name_urdu or ''}</div>
        <div style="display:flex;gap:1rem;font-size:0.8rem;color:#94a3b8;flex-wrap:wrap;">
            <span>📂 {exercise.category}</span>
            <span>⭐ {exercise.difficulty}</span>
            <span>🏋️ {exercise.equipment}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Instructions ──
    if instructions:
        with st.expander("📋 Instructions (Steps)", expanded=True):
            for i, step in enumerate(instructions, 1):
                st.markdown(f"**{i}.** {step}")
    
    if common_mistakes:
        with st.expander("⚠️ Common Mistakes"):
            for mistake in common_mistakes:
                st.markdown(f"❌ {mistake}")
    
    st.markdown("---")
    
    # ── Workout Setup ──
    st.markdown("### ⚙️ Workout Setup")
    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        sets = st.number_input("Sets", 1, 10, 3, key="vt_sets")
    with wc2:
        reps = st.number_input("Reps", 1, 50, 10, key="vt_reps")
    with wc3:
        weight = st.number_input("Weight (kg)", 0.0, 500.0, 0.0, step=2.5, key="vt_weight")
    
    st.markdown("---")
    
    # ── Voice Feedback Buttons ──
    st.markdown("### 🎤 AI Voice Feedback")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start", type="primary", use_container_width=True, key="vt_btn_start"):
            msg = voice_guide.get("start", f"{exercise.name} shuru karein. {reps} reps karenge.")
            st.success(f"🔊 {msg}")
            _play_tts_urdu(msg, "start")
    
    with col2:
        if st.button("✅ Good Rep", use_container_width=True, key="vt_btn_good"):
            msg = voice_guide.get("good_rep", "Shabash! Acha rep tha.")
            st.success(f"🔊 {msg}")
            _play_tts_urdu(msg, "good")
    
    with col3:
        if st.button("⚠️ Bad Form", use_container_width=True, key="vt_btn_bad"):
            msg = voice_guide.get("bad_form", "Form sahi karo.")
            st.warning(f"🔊 {msg}")
            _play_tts_urdu(msg, "bad")
    
    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button("⏸️ Rest", use_container_width=True, key="vt_btn_rest"):
            msg = voice_guide.get("rest", "Ek minute ka rest lo.")
            st.info(f"🔊 {msg}")
            _play_tts_urdu(msg, "rest")
    
    with col5:
        if st.button("🏁 Finish", type="primary", use_container_width=True, key="vt_btn_finish"):
            msg = voice_guide.get("finish", "Set complete! Shabash.")
            st.success(f"🔊 {msg}")
            _play_tts_urdu(msg, "finish")
    
    with col6:
        if st.button("📖 Instructions", use_container_width=True, key="vt_btn_read"):
            if instructions:
                full_text = ". ".join(instructions)
                _play_tts_urdu(full_text[:250], "instr")
    
    st.markdown("---")
    
    # ── Save Workout ──
    if st.button("💾 Workout Save Karo", type="primary", use_container_width=True, key="vt_btn_save"):
        try:
            ok, msg = db.log_workout_session(
                member_id=m.id,
                gym_id=m.gym_id,
                exercise_id=ex_id,
                sets=sets,
                reps=reps,
                weight=weight,
                voice_feedback=voice_guide.get("finish", "")
            )
            if ok:
                st.success("✅ Workout save ho gaya!")
                st.balloons()
            else:
                st.error(f"❌ {msg}")
        except Exception as e:
            st.error(f"❌ Save error: {e}")
    
    # ── Workout History ──
    st.markdown("---")
    st.markdown("### 📊 Workout History")
    try:
        history = db.get_member_workout_history(m.id, limit=10)
        if history:
            rows = []
            for h in history:
                ex = db.get_exercise(h.exercise_id) if h.exercise_id else None
                rows.append({
                    "Date": h.started_at.strftime("%d %b %Y") if h.started_at else "—",
                    "Exercise": ex.name if ex else "—",
                    "Sets": h.sets_completed,
                    "Reps": h.reps_completed,
                    "Weight (kg)": h.weight_used_kg
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.info("📭 Abhi koi workout history nahi. Pehla workout karo!")
    except Exception as e:
        st.warning(f"History load nahi hui: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 7 — BODY COACH
# ─────────────────────────────────────────────────────────────────────────────

def _tab_body_coach(m):
    try:
        from gym_pages import body_ai
        body_ai.render_body_coach(m, db.get_body_measurements(m.id))
    except ImportError:
        st.info("🧠 Body Coach feature available soon!")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render():
    st.markdown(PORTAL_CSS, unsafe_allow_html=True)

    m = _mp_member()
    if not m:
        staff_view = (
            st.query_params.get("portal") != "1"
            and st.session_state.get("user_id")
            and st.session_state.get("role") in ("admin", "staff")
        )
        if staff_view:
            _staff_usage_panel()
        else:
            _login_page()
        return

    _record_portal_activity(m)
    gym = db.get_gym(m.gym_id)

    hdr, logout_col = st.columns([5, 1])
    with hdr:
        st.markdown(
            '<div style="font-size:1.3rem;font-weight:900;background:linear-gradient(135deg,#a78bfa,#7c3aed);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🏋️ GymPro Member Portal</div>',
            unsafe_allow_html=True
        )
    with logout_col:
        if st.button("🚪 Logout", use_container_width=True):
            _mp_logout()

    _render_hero(m, gym)

    # ⭐ 7 TABS (Voice Trainer added)
    tabs = st.tabs([
        "🏠 Home",
        "📅 Attendance",
        "📈 Progress",
        "💰 Fees",
        "🤖 AI Coach",
        "🏋️ Voice Trainer",  # ⭐ NAYA
        "🧠 Body Coach"
    ])

    with tabs[0]: _tab_home(m, gym)
    with tabs[1]: _tab_attendance(m)
    with tabs[2]: _tab_progress(m)
    with tabs[3]: _tab_fees(m, gym)
    with tabs[4]: _tab_ai(m)
    with tabs[5]: _tab_voice_trainer(m)  # ⭐ NAYA
    with tabs[6]: _tab_body_coach(m)