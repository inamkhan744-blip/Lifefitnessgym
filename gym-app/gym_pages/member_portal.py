"""
GymPro Member Portal — Professional Edition
Member apni serial number + phone se login karein.

Features:
 • Hero profile card with photo (Cloudinary / Object Storage / local)
 • Membership card (credit-card style)
 • Live fee countdown + payment history
 • Self check-in + daily code + 30-day attendance calendar
 • Progress charts (weight, measurements, BMI)
 • AI Diet Plan (7-day, personalized)
 • AI Exercise Coach (daily workout + chat)
 • Gym leaderboard rank
 • Daily motivational quote
"""

import streamlit as st
import database as db
import object_store
import os, io, base64, hashlib, requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# PHOTO HELPER  (mirrors fee_collection logic — supports all storage backends)
# ─────────────────────────────────────────────────────────────────────────────

def _get_member_photo_b64(photo_field: str, serial_number: str = "") -> str | None:
    """Return a data-URI for the member photo (Cloudinary → Object Storage → local)."""
    if not photo_field:
        return None
    photo_str = str(photo_field).strip()
    if "<div" in photo_str or "style=" in photo_str:
        return None

    # 1. Cloudinary URL — return directly
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
            return photo_str   # let browser fetch directly

    # 2. Object Storage / Cloudinary key
    try:
        b64, mime = object_store.get_photo_b64(photo_str)
        if b64:
            return f"data:image/{mime};base64,{b64}"
    except Exception:
        pass

    # 3. Local path
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

    # 4. Serial-number guess
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


# ─────────────────────────────────────────────────────────────────────────────
# AI HELPER  (Groq)
# ─────────────────────────────────────────────────────────────────────────────

def _groq(messages: list, max_tokens=2000) -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return "⚠️ GROQ_API_KEY set nahi — AI unavailable."
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama3-8b-8192", "messages": messages,
                  "temperature": 0.7, "max_tokens": max_tokens},
            timeout=30,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ AI error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _daily_code(member_id: int) -> str:
    h = hashlib.sha256(f"{member_id}-{date.today().isoformat()}-GYMPRO".encode()).hexdigest()
    return h[:6].upper()


_QUOTES = [
    ("Push yourself, because no one else is going to do it for you.", "Unknown"),
    ("Success starts with self-discipline.", "Unknown"),
    ("The body achieves what the mind believes.", "Unknown"),
    ("Wake up. Work out. Look hot. Kick ass.", "Unknown"),
    ("Your only limit is your mind.", "Unknown"),
    ("Don't stop when you're tired. Stop when you're done.", "Unknown"),
    ("Be stronger than your excuses.", "Unknown"),
    ("Train insane or remain the same.", "Unknown"),
    ("It never gets easier — you just get better.", "Unknown"),
    ("Sweat is just fat crying.", "Unknown"),
    ("Consistency > Perfection.", "Unknown"),
    ("Small steps every day lead to big results.", "Unknown"),
    ("The pain you feel today is the strength you'll feel tomorrow.", "Unknown"),
    ("Fitness is not a destination, it's a way of life.", "Unknown"),
]


def _daily_quote() -> tuple[str, str]:
    idx = date.today().toordinal() % len(_QUOTES)
    return _QUOTES[idx]


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

PORTAL_CSS = """
<style>
/* ── Reset / base ────────────────────────────────────────────── */
.mp-root { font-family: 'Inter', 'Segoe UI', sans-serif; }

/* ── Hero card ───────────────────────────────────────────────── */
.mp-hero {
    background: linear-gradient(135deg, #1a0533 0%, #0f172a 60%, #1e293b 100%);
    border: 1px solid #7c3aed44;
    border-radius: 24px;
    padding: 2rem 2rem 1.5rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
}
.mp-hero::before {
    content: '';
    position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, #7c3aed33 0%, transparent 70%);
    border-radius: 50%;
}

/* ── Profile photo ring ──────────────────────────────────────── */
.mp-photo-ring {
    width: 130px; height: 130px;
    border-radius: 50%;
    border: 4px solid #7c3aed;
    box-shadow: 0 0 0 4px #7c3aed33, 0 8px 32px rgba(124,58,237,0.5);
    overflow: hidden;
    background: linear-gradient(135deg,#7c3aed,#4f46e5);
    flex-shrink: 0;
    display: inline-block;
}
.mp-photo-ring img { width:100%; height:100%; object-fit:cover; display:block; }
.mp-photo-initials {
    width:100%; height:100%;
    display:flex; align-items:center; justify-content:center;
    font-size:2.8rem; font-weight:900; color:white;
}

/* ── Membership card (credit-card style) ─────────────────────── */
.mp-card-3d {
    background: linear-gradient(135deg, #7c3aed 0%, #4338ca 50%, #1d4ed8 100%);
    border-radius: 20px;
    padding: 1.6rem 1.8rem;
    color: white;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(124,58,237,0.45);
    min-height: 180px;
}
.mp-card-3d::before {
    content: '';
    position: absolute; top: -50px; right: -50px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}
.mp-card-3d::after {
    content: '';
    position: absolute; bottom: -70px; left: -30px;
    width: 250px; height: 250px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.mc-chip {
    width: 40px; height: 30px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    border-radius: 6px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

/* ── Stat tiles ──────────────────────────────────────────────── */
.mp-tile {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 1rem 0.8rem;
    text-align: center;
    height: 100%;
    transition: border-color 0.2s;
}
.mp-tile:hover { border-color: #7c3aed66; }
.mp-tile-val { font-size: 1.8rem; font-weight: 800; margin: 0; line-height: 1.1; }
.mp-tile-lbl { font-size: 0.7rem; color: #64748b; margin: 0.2rem 0 0;
               text-transform: uppercase; letter-spacing: 1px; }
.mp-tile-sub { font-size: 0.72rem; color: #94a3b8; margin: 0.15rem 0 0; }

/* ── Quote card ──────────────────────────────────────────────── */
.mp-quote {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    border-left: 4px solid #7c3aed;
    border-radius: 0 12px 12px 0;
    padding: 0.9rem 1.2rem;
    margin: 0.5rem 0 1rem;
}

/* ── Section header ──────────────────────────────────────────── */
.mp-sec {
    font-size: 1rem; font-weight: 700; color: #a78bfa;
    border-bottom: 1px solid #7c3aed22;
    padding-bottom: 0.35rem; margin: 1.2rem 0 0.8rem;
    display: flex; align-items: center; gap: 0.4rem;
}

/* ── Status badges ────────────────────────────────────────────── */
.badge { padding: 4px 14px; border-radius: 20px; font-size: 0.78rem;
         font-weight: 700; display: inline-block; }
.badge-active   { background:#064e3b33; color:#34d399; border:1px solid #34d39944; }
.badge-expired  { background:#450a0a33; color:#f87171; border:1px solid #f8717144; }
.badge-inactive { background:#1e1b4b33; color:#a78bfa; border:1px solid #a78bfa44; }
.badge-frozen   { background:#0c1a2e33; color:#60a5fa; border:1px solid #60a5fa44; }
.badge-suspended { background:#451a0333; color:#fb923c; border:1px solid #fb923c44; }

/* ── Progress bar ────────────────────────────────────────────── */
.mp-bar-bg {
    background: #1e293b; border-radius: 99px; height: 10px;
    overflow: hidden; margin-top: 0.3rem;
}
.mp-bar-fill {
    height: 100%; border-radius: 99px;
    transition: width 0.5s ease;
}

/* ── Attendance code ──────────────────────────────────────────── */
.att-code {
    font-size: 2.8rem; font-weight: 900; letter-spacing: 10px;
    text-align: center; color: #7c3aed;
    background: #0f172a; border: 2px dashed #7c3aed66;
    border-radius: 14px; padding: 1.1rem 0;
    font-family: 'Courier New', monospace;
}

/* ── AI Chat ──────────────────────────────────────────────────── */
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

/* ── Leaderboard ─────────────────────────────────────────────── */
.lb-row {
    display: flex; align-items: center; gap: 0.7rem;
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 10px; padding: 0.6rem 0.9rem;
    margin-bottom: 0.4rem;
}
.lb-rank { font-size: 1.2rem; font-weight: 900; min-width: 2rem; text-align: center; }
.lb-name { flex: 1; font-weight: 600; color: #e2e8f0; font-size: 0.9rem; }
.lb-count { color: #a78bfa; font-weight: 700; font-size: 0.85rem; }

/* ── Login ───────────────────────────────────────────────────── */
.mp-login-wrap {
    max-width: 440px; margin: 2rem auto;
    padding: 2.5rem 2rem;
    background: linear-gradient(135deg,#1a0533,#0f172a);
    border: 1px solid #7c3aed44; border-radius: 24px;
    box-shadow: 0 30px 80px rgba(124,58,237,0.25);
}

/* ── Notification banner ─────────────────────────────────────── */
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
            serial = st.text_input("🪪 Membership Serial Number",
                                   placeholder="e.g. PF-00001",
                                   help="Membership card ya receipt pe likha number")
            phone4 = st.text_input("📱 Phone number ke akhri 4 digits",
                                   placeholder="e.g. 5678", max_chars=4)
            login_btn = st.form_submit_button("🔓 Login", type="primary", use_container_width=True)

        if login_btn:
            if not serial.strip() or not phone4.strip():
                st.error("Dono fields zaruri hain.")
                return
            member = db.get_member_by_serial(serial.strip().upper())
            if not member:
                st.error("❌ Serial number nahi mila — dobara check karein.")
                return
            digits = "".join(c for c in (member.phone or "") if c.isdigit())
            if not digits.endswith(phone4.strip()):
                st.error("❌ Phone digits galat hain.")
                return
            st.session_state["portal_member_id"] = member.id
            if "mp_chat" not in st.session_state:
                st.session_state["mp_chat"] = []
            st.rerun()

        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem; color:#475569; font-size:0.78rem;">
            Serial number apni membership card ya fee receipt pe hoga.<br>
            Mushkil ho toh gym staff se rabta karein.
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HERO SECTION  (shown at top of every tab)
# ─────────────────────────────────────────────────────────────────────────────

def _render_hero(m, gym):
    today = date.today()

    # Days left / overdue
    days_left = None
    if m.expiry_date:
        try:
            days_left = (date.fromisoformat(str(m.expiry_date)) - today).days
        except Exception:
            pass

    # Attendance rate
    att_rate = db.get_member_attendance_rate(m.id, days=30)
    streak   = db.get_member_streak(m.id)

    # Photo
    photo_b64 = _get_member_photo_b64(m.photo_path, m.serial_number)
    initials  = "".join(p[0] for p in m.full_name.split()[:2]).upper()

    # Badge
    badge_cls = {
        "Active": "active", "Expired": "expired",
        "Inactive": "inactive", "Frozen": "frozen", "Suspended": "suspended"
    }.get(m.status, "inactive")

    # Expiry colour
    if days_left is None:
        exp_color, exp_txt = "#94a3b8", "—"
    elif days_left > 10:
        exp_color, exp_txt = "#34d399", f"{days_left} din bacha"
    elif days_left >= 0:
        exp_color, exp_txt = "#fbbf24", f"⚠️ {days_left} din"
    else:
        exp_color, exp_txt = "#f87171", f"🔴 {abs(days_left)} din overdue"

    # Notifications
    if days_left is not None:
        if days_left < 0:
            st.markdown(f'<div class="mp-notif-danger">🔴 Aap ki membership <b>{abs(days_left)} din pehle</b> expire ho gayi — fees jama karaein.</div>', unsafe_allow_html=True)
        elif days_left <= 5:
            st.markdown(f'<div class="mp-notif-warn">⚠️ Membership sirf <b>{days_left} din</b> mein expire hogi — jaldi renew karaein!</div>', unsafe_allow_html=True)

    # Birthday check
    if m.dob:
        try:
            dob = date.fromisoformat(str(m.dob))
            if dob.month == today.month and dob.day == today.day:
                st.markdown('<div class="mp-notif-ok">🎂 Happy Birthday! Aaj aap ka birthday hai — gym ki taraf se mubarak ho! 🎉</div>', unsafe_allow_html=True)
        except Exception:
            pass

    # Daily quote
    quote, _ = _daily_quote()

    # ── Hero HTML ─────────────────────────────────────────────────
    if photo_b64 and photo_b64.startswith("http"):
        photo_html = f'<img src="{photo_b64}" style="width:100%;height:100%;object-fit:cover;display:block;" />'
    elif photo_b64:
        photo_html = f'<img src="{photo_b64}" style="width:100%;height:100%;object-fit:cover;display:block;" />'
    else:
        photo_html = f'<div class="mp-photo-initials">{initials}</div>'

    st.markdown(f"""
    <div class="mp-hero">
      <div style="display:flex; align-items:center; gap:1.5rem; flex-wrap:wrap;">
        <div class="mp-photo-ring">{photo_html}</div>
        <div style="flex:1; min-width:180px;">
          <div style="font-size:1.6rem; font-weight:900; color:#f1f5f9; line-height:1.1;">{m.full_name}</div>
          <div style="font-size:0.8rem; color:#7c3aed; font-weight:700; letter-spacing:1.5px; margin:0.25rem 0;">
            #{m.serial_number}
          </div>
          <span class="badge badge-{badge_cls}">{m.status}</span>
          &nbsp;
          <span style="font-size:0.78rem; color:#94a3b8;">
            🏋️ {gym.name if gym else '—'} &nbsp;|&nbsp; 🎫 {m.membership_type}
          </span>
          <div style="margin-top:0.7rem; display:flex; gap:1.5rem; flex-wrap:wrap;">
            <div>
              <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Expiry</div>
              <div style="font-size:0.95rem;font-weight:700;color:{exp_color};">{exp_txt}</div>
            </div>
            <div>
              <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">🔥 Streak</div>
              <div style="font-size:0.95rem;font-weight:700;color:#f59e0b;">{streak} days</div>
            </div>
            <div>
              <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">30d Rate</div>
              <div style="font-size:0.95rem;font-weight:700;color:#a78bfa;">{att_rate:.0f}%</div>
            </div>
          </div>
        </div>
      </div>
      <div class="mp-quote" style="margin-top:1.2rem;">
        <div style="font-size:0.82rem;font-style:italic;color:#cbd5e1;">"{quote}"</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def _tab_home(m, gym):
    today = date.today()

    st.markdown('<div class="mp-sec">📊 Quick Stats</div>', unsafe_allow_html=True)

    fee_recs  = db.get_fee_records(member_id=m.id)
    total_paid = sum(r.amount for r in fee_recs) if fee_recs else 0
    att_rate   = db.get_member_attendance_rate(m.id, days=30)
    streak     = db.get_member_streak(m.id)

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
        (c2, f"🔥 {streak}", "#f59e0b", "Day Streak", "Keep going!"),
        (c3, f"{att_rate:.0f}%",
         "#34d399" if att_rate >= 70 else "#fbbf24" if att_rate >= 40 else "#f87171",
         "30d Attendance", ""),
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

    # ── Membership Card ───────────────────────────────────────────
    st.markdown('<div class="mp-sec">💳 Membership Card</div>', unsafe_allow_html=True)
    gym_name = gym.name if gym else "GymPro"
    join_yr  = str(m.join_date or "")[:4]
    exp_yr   = str(m.expiry_date or "")[:4]

    st.markdown(f"""
    <div class="mp-card-3d">
      <div class="mc-chip"></div>
      <div style="position:relative; z-index:1;">
        <div style="font-size:0.65rem;letter-spacing:3px;text-transform:uppercase;opacity:0.7;">
          GYMPRO MEMBER
        </div>
        <div style="font-size:1.4rem;font-weight:900;letter-spacing:1px;margin:0.3rem 0;">
          {m.full_name.upper()}
        </div>
        <div style="font-size:0.9rem;letter-spacing:4px;font-family:monospace;margin:0.6rem 0;opacity:0.85;">
          {m.serial_number}
        </div>
        <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:1rem;">
          <div>
            <div style="font-size:0.6rem;opacity:0.65;letter-spacing:1px;">MEMBERSHIP</div>
            <div style="font-size:0.88rem;font-weight:700;">{m.membership_type}</div>
          </div>
          <div>
            <div style="font-size:0.6rem;opacity:0.65;letter-spacing:1px;">VALID THRU</div>
            <div style="font-size:0.88rem;font-weight:700;">{str(m.expiry_date or '—')}</div>
          </div>
          <div style="font-size:1.5rem;opacity:0.3;font-weight:900;">🏋️</div>
        </div>
        <div style="font-size:0.75rem;opacity:0.5;margin-top:0.6rem;">{gym_name}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Attendance trend last 7 days ──────────────────────────────
    st.markdown('<div class="mp-sec">📅 Is Hafte ki Attendance</div>', unsafe_allow_html=True)
    days7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
    all_att = db.get_attendance(check_date=None)
    my_att  = {a.check_date: a.status for a in all_att if a.member_id == m.id}

    rows7 = []
    for d in days7:
        s = my_att.get(str(d), "Absent")
        rows7.append({"Day": d.strftime("%a"), "Val": 1 if s == "Present" else 0,
                      "Color": "#7c3aed" if s == "Present" else "#1e293b",
                      "Text": "✅" if s == "Present" else "❌"})

    fig = go.Figure(go.Bar(
        x=[r["Day"] for r in rows7], y=[r["Val"] for r in rows7],
        marker_color=[r["Color"] for r in rows7],
        text=[r["Text"] for r in rows7], textposition="outside",
    ))
    fig.update_layout(
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e2e8f0", height=180,
        margin=dict(t=10, b=10, l=10, r=10),
        yaxis=dict(showticklabels=False, range=[0, 1.6]),
        xaxis=dict(tickfont=dict(size=13)),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Gym leaderboard ───────────────────────────────────────────
    st.markdown('<div class="mp-sec">🏆 Gym Leaderboard (Is Mahine)</div>', unsafe_allow_html=True)
    board = db.get_attendance_leaderboard(gym_id=m.gym_id, limit=10)
    rank_icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    my_rank = None
    for i, row in enumerate(board):
        if row["member"].id == m.id:
            my_rank = i + 1
        icon = rank_icons[i] if i < len(rank_icons) else f"#{i+1}"
        is_me = row["member"].id == m.id
        highlight = "border-color:#7c3aed;" if is_me else ""
        st.markdown(f"""
        <div class="lb-row" style="{highlight}">
          <div class="lb-rank">{icon}</div>
          <div class="lb-name">{row['member'].full_name}{'&nbsp; <span style="color:#7c3aed;font-size:0.7rem;">(You)</span>' if is_me else ''}</div>
          <div class="lb-count">🔥 {row['streak']}d streak &nbsp; | &nbsp; 📅 {row['count']} days</div>
        </div>
        """, unsafe_allow_html=True)

    if my_rank:
        st.markdown(f'<div style="text-align:center;color:#a78bfa;font-size:0.85rem;margin-top:0.5rem;">Aap ki rank: <b>#{my_rank}</b> out of {len(board)}</div>', unsafe_allow_html=True)
    elif board:
        st.caption("Is mahine abhi tak leaderboard mein nahi — attendance mark karo!")


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
          <div style="font-size:0.72rem;color:#64748b;letter-spacing:1px;margin-bottom:0.4rem;text-transform:uppercase;">
            Aaj ka Daily Code — Staff ko dikhao
          </div>
          <div class="att-code">{code}</div>
          <div style="font-size:0.7rem;color:#475569;margin-top:0.4rem;">
            Yeh code sirf aaj valid hai (midnight pe change hoga)
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c_btn:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        if today_att:
            icon = "✅" if today_att.status == "Present" else "⚠️"
            st.success(f"{icon} Aaj ki attendance: **{today_att.status}**")
            st.caption(f"Marked by: {today_att.marked_by or 'staff'}")
        else:
            st.warning("⏰ Aaj ki attendance abhi mark nahi hui")
            if st.button("✅ Aaj Present Mark Karo", type="primary", use_container_width=True):
                ok, msg = db.mark_attendance(m.id, m.gym_id, today, "Present", "member-self")
                if ok:
                    st.success("✅ Attendance mark ho gayi!")
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()

    # ── Stats ──────────────────────────────────────────────────────
    st.markdown('<div class="mp-sec">📊 Attendance Stats</div>', unsafe_allow_html=True)
    streak  = db.get_member_streak(m.id)
    rate30  = db.get_member_attendance_rate(m.id, days=30)
    rate7   = db.get_member_attendance_rate(m.id, days=7)

    s1, s2, s3 = st.columns(3)
    for col, val, color, lbl in [
        (s1, f"🔥 {streak}", "#f59e0b", "Day Streak"),
        (s2, f"{rate30:.0f}%",
         "#34d399" if rate30 >= 70 else "#fbbf24" if rate30 >= 40 else "#f87171", "30-Day Rate"),
        (s3, f"{rate7:.0f}%",
         "#34d399" if rate7 >= 70 else "#fbbf24" if rate7 >= 40 else "#f87171", "7-Day Rate"),
    ]:
        with col:
            st.markdown(f"""
            <div class="mp-tile">
              <div class="mp-tile-val" style="color:{color};">{val}</div>
              <div class="mp-tile-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 30-day calendar ────────────────────────────────────────────
    st.markdown('<div class="mp-sec">📆 30 Din ki History</div>', unsafe_allow_html=True)
    days30  = [today - timedelta(days=i) for i in range(29, -1, -1)]
    all_att = db.get_attendance(check_date=None)
    my_att  = {a.check_date: a.status for a in all_att if a.member_id == m.id}

    cal = [{"Date": d.strftime("%d %b"), "Val": 1 if my_att.get(str(d)) == "Present" else 0,
            "Color": "#7c3aed" if my_att.get(str(d)) == "Present" else
                     "#fbbf24" if my_att.get(str(d)) == "Late" else "#1e293b",
            "Status": my_att.get(str(d), "Absent")} for d in days30]

    fig2 = go.Figure(go.Bar(
        x=[r["Date"] for r in cal], y=[r["Val"] for r in cal],
        marker_color=[r["Color"] for r in cal],
        hovertemplate="%{x} — %{customdata}<extra></extra>",
        customdata=[r["Status"] for r in cal],
    ))
    fig2.update_layout(
        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e2e8f0", height=200,
        yaxis=dict(showticklabels=False, range=[0, 1.3]),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("🟣 Present &nbsp;&nbsp; 🟡 Late &nbsp;&nbsp; ⬛ Absent")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PROGRESS
# ─────────────────────────────────────────────────────────────────────────────

def _tab_progress(m):
    records = db.get_body_measurements(m.id)

    with st.expander("➕ Naya Measurement Add Karo", expanded=not bool(records)):
        with st.form("mp_meas"):
            c1, c2, c3 = st.columns(3)
            with c1:
                weight = st.number_input("⚖️ Weight (kg)", 20.0, 300.0, 70.0, 0.5)
                chest  = st.number_input("Chest (cm)", 0.0, 200.0, 0.0, 0.5)
            with c2:
                waist  = st.number_input("Waist (cm)", 0.0, 200.0, 0.0, 0.5)
                hips   = st.number_input("Hips (cm)",  0.0, 200.0, 0.0, 0.5)
            with c3:
                bicep    = st.number_input("Bicep (cm)", 0.0, 100.0, 0.0, 0.5)
                body_fat = st.number_input("Body Fat %", 0.0, 60.0, 0.0, 0.5)
                height_cm = st.number_input("Height (cm)", 100, 250, 170)
            notes = st.text_input("Notes (optional)")
            if st.form_submit_button("💾 Save", type="primary"):
                ok, msg = db.add_body_measurement(
                    m.id, date.today(), weight,
                    chest or None, waist or None, hips or None, bicep or None,
                    body_fat or None, notes
                )
                if ok:
                    st.success("✅ Saved!")
                    st.rerun()
                else:
                    st.error(msg)

    if not records:
        st.info("Pehla measurement add karo upar se — progress track shuru hogi!")
        return

    latest = records[-1]
    first  = records[0]

    st.markdown('<div class="mp-sec">📋 Latest Snapshot</div>', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns(4)
    wc = latest.weight_kg - first.weight_kg
    wcolor = "#34d399" if wc <= 0 else "#f87171"
    for col, val, color, lbl in [
        (t1, f"{latest.weight_kg} kg", "#e2e8f0", "Current Weight"),
        (t2, f"{wc:+.1f} kg", wcolor, "Total Change"),
        (t3, f"{len(records)}", "#a78bfa", "Entries"),
        (t4, str(latest.recorded_date), "#64748b", "Last Record"),
    ]:
        with col:
            st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:{color};font-size:1.4rem;">{val}</div><div class="mp-tile-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    dates   = [str(r.recorded_date) for r in records]
    weights = [r.weight_kg for r in records]

    # Weight chart
    fig_w = go.Figure()
    fig_w.add_trace(go.Scatter(
        x=dates, y=weights, mode="lines+markers",
        line=dict(color="#7c3aed", width=3),
        marker=dict(size=8, color="#7c3aed",
                    line=dict(color="#a78bfa", width=2)),
        fill="tozeroy", fillcolor="rgba(124,58,237,0.08)",
        name="Weight (kg)"
    ))
    fig_w.update_layout(
        title="Weight Progress", plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
        font_color="#e2e8f0", title_x=0.5, height=280,
        yaxis_title="kg", margin=dict(t=40,b=20,l=40,r=10),
        yaxis=dict(gridcolor="#1e293b"), xaxis=dict(gridcolor="#1e293b"),
    )
    st.plotly_chart(fig_w, use_container_width=True)

    # Measurements chart
    meas = {}
    for field, lbl in [("chest_cm","Chest"),("waist_cm","Waist"),
                        ("hips_cm","Hips"),("bicep_cm","Bicep")]:
        vals = [getattr(r, field) for r in records]
        if any(v for v in vals):
            meas[lbl] = vals

    if meas:
        fig_m = go.Figure()
        for i, (lbl, vals) in enumerate(meas.items()):
            colors_m = ["#34d399","#f87171","#fbbf24","#60a5fa"]
            fig_m.add_trace(go.Scatter(
                x=dates, y=vals, mode="lines+markers",
                name=f"{lbl} (cm)",
                line=dict(color=colors_m[i%4], width=2),
                marker=dict(size=6),
            ))
        fig_m.update_layout(
            title="Body Measurements", plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
            font_color="#e2e8f0", title_x=0.5, height=280,
            yaxis_title="cm", margin=dict(t=40,b=20,l=40,r=10),
            yaxis=dict(gridcolor="#1e293b"), xaxis=dict(gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_m, use_container_width=True)

    # BMI
    if latest.weight_kg:
        h = st.number_input("Height (cm) — BMI ke liye", 100, 250, 170, key="bmi_h")
        if h:
            bmi = latest.weight_kg / ((h/100)**2)
            cat, bmi_color = (
                ("Underweight 🔵", "#60a5fa") if bmi < 18.5 else
                ("Normal ✅", "#34d399") if bmi < 25 else
                ("Overweight ⚠️", "#fbbf24") if bmi < 30 else
                ("Obese 🔴", "#f87171")
            )
            st.markdown(f"""
            <div class="mp-tile" style="text-align:left; padding:1.2rem; margin-top:0.5rem;">
              <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">BMI Calculator</div>
              <div style="font-size:2.5rem;font-weight:900;color:{bmi_color};">{bmi:.1f}</div>
              <div style="color:{bmi_color};font-weight:700;">{cat}</div>
              <div style="margin-top:0.5rem;">
                <div class="mp-bar-bg">
                  <div class="mp-bar-fill" style="width:{min(bmi/40*100,100):.0f}%;background:{bmi_color};"></div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — FEES
# ─────────────────────────────────────────────────────────────────────────────

def _tab_fees(m, gym):
    today = date.today()

    # Expiry countdown bar
    if m.expiry_date:
        try:
            exp = date.fromisoformat(str(m.expiry_date))
            join = date.fromisoformat(str(m.join_date)) if m.join_date else exp - timedelta(days=30)
            total_days = max((exp - join).days, 1)
            days_done  = (today - join).days
            pct = max(0, min(100, days_done / total_days * 100))
            days_left  = (exp - today).days
            bar_color  = "#34d399" if days_left > 10 else "#fbbf24" if days_left >= 0 else "#f87171"

            st.markdown(f"""
            <div class="mp-sec">⏳ Membership Timeline</div>
            <div class="mp-tile" style="text-align:left; padding:1.2rem; margin-bottom:1rem;">
              <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                <span style="color:#64748b;font-size:0.8rem;">Join: {m.join_date}</span>
                <span style="color:{bar_color};font-weight:700;font-size:0.9rem;">
                  {'✅ ' + str(days_left) + ' din bacha' if days_left >= 0 else '🔴 ' + str(abs(days_left)) + ' din overdue'}
                </span>
                <span style="color:#64748b;font-size:0.8rem;">Expiry: {m.expiry_date}</span>
              </div>
              <div class="mp-bar-bg">
                <div class="mp-bar-fill" style="width:{pct:.0f}%;background:{bar_color};"></div>
              </div>
              <div style="color:#94a3b8;font-size:0.75rem;margin-top:0.4rem;">{pct:.0f}% membership used</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            pass

    # Fee stats
    fee_recs = db.get_fee_records(member_id=m.id)
    total    = sum(r.amount for r in fee_recs) if fee_recs else 0
    last_fee = sorted(fee_recs, key=lambda r: r.payment_date, reverse=True)[0] if fee_recs else None

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#a78bfa;font-size:1.4rem;">PKR {total:,.0f}</div><div class="mp-tile-lbl">Total Paid</div></div>', unsafe_allow_html=True)
    with f2:
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#34d399;font-size:1.4rem;">{len(fee_recs)}</div><div class="mp-tile-lbl">Receipts</div></div>', unsafe_allow_html=True)
    with f3:
        lf = last_fee.payment_date if last_fee else "—"
        st.markdown(f'<div class="mp-tile"><div class="mp-tile-val" style="color:#e2e8f0;font-size:1.1rem;">{lf}</div><div class="mp-tile-lbl">Last Payment</div></div>', unsafe_allow_html=True)

    # Fee history table
    if fee_recs:
        st.markdown('<div class="mp-sec">🧾 Payment History</div>', unsafe_allow_html=True)
        rows = [{"Date": r.payment_date, "Amount": f"PKR {r.amount:,.0f}",
                 "Method": r.payment_method or "—",
                 "Period": f"{r.period_start or '—'} → {r.period_end or '—'}",
                 "Receipt": r.receipt_number or "—"}
                for r in sorted(fee_recs, key=lambda x: x.payment_date, reverse=True)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        # Monthly bar chart
        months = {}
        for r in fee_recs:
            mo = (r.payment_date or "")[:7]
            if mo:
                months[mo] = months.get(mo, 0) + (r.amount or 0)
        if months:
            df_m = pd.DataFrame({"Month": list(months.keys()), "Amount": list(months.values())}).sort_values("Month")
            fig_f = px.bar(df_m, x="Month", y="Amount",
                           color_discrete_sequence=["#7c3aed"],
                           title="Monthly Payments")
            fig_f.update_layout(
                plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
                font_color="#e2e8f0", title_x=0.5, height=260,
                yaxis=dict(gridcolor="#1e293b"), margin=dict(t=40,b=20,l=40,r=10)
            )
            st.plotly_chart(fig_f, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — AI COACH  (Diet + Exercise + Chat)
# ─────────────────────────────────────────────────────────────────────────────

def _tab_ai(m):
    records = db.get_body_measurements(m.id)
    latest  = records[-1] if records else None

    sub = st.tabs(["🥗 Diet Plan", "💪 Workout", "💬 AI Chat"])

    # ── Diet Plan ─────────────────────────────────────────────────
    with sub[0]:
        st.markdown('<div class="mp-sec">🥗 AI 7-Day Diet Plan</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            goal   = st.selectbox("🎯 Goal", ["Weight Loss","Muscle Gain","Maintenance","Endurance","Healthy Eating"])
            weight = st.number_input("⚖️ Weight (kg)", 30.0, 300.0,
                                     float(latest.weight_kg) if latest else 70.0, 0.5)
        with c2:
            height = st.number_input("📏 Height (cm)", 100, 250, 170)
            activity = st.selectbox("🏃 Activity", [
                "Sedentary","Lightly Active","Moderately Active (gym 3-4x)","Very Active (gym 5-6x)"])
        diet_pref = st.selectbox("🍽️ Diet", ["No restriction","Vegetarian","Halal","Low carb","High protein"])
        allergies = st.text_input("⚠️ Allergies (optional)")

        if st.button("🤖 Diet Plan Generate Karo", type="primary", use_container_width=True):
            with st.spinner("AI tayyar kar raha hai..."):
                plan = _groq([
                    {"role":"system","content":"You are a professional nutritionist. Respond in Roman Urdu + English."},
                    {"role":"user","content":
                     f"Create a detailed 7-day diet plan.\n"
                     f"Member: {m.full_name}, {m.gender or 'N/A'}\n"
                     f"Weight: {weight}kg, Height: {height}cm\n"
                     f"Goal: {goal}, Activity: {activity}\n"
                     f"Diet preference: {diet_pref}, Allergies: {allergies or 'None'}\n\n"
                     "Include: meal times, portion sizes, Pakistani foods, daily calories, 5 practical tips.\n"
                     "Format clearly with Day 1–7."}
                ], max_tokens=2500)
                st.session_state["mp_diet_plan"] = plan

        if st.session_state.get("mp_diet_plan"):
            st.divider()
            st.markdown(st.session_state["mp_diet_plan"])
            st.download_button("⬇️ Download Plan",
                               data=st.session_state["mp_diet_plan"],
                               file_name=f"diet_{m.serial_number}_{date.today()}.txt",
                               mime="text/plain")

    # ── Workout ───────────────────────────────────────────────────
    with sub[1]:
        st.markdown('<div class="mp-sec">💪 Aaj ka Workout</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            focus = st.selectbox("Focus", ["Full Body","Chest & Triceps","Back & Biceps",
                                           "Legs","Shoulders & Abs","Cardio & HIIT","Core & Stretch"])
        with c2:
            level = st.selectbox("Level", ["Beginner","Intermediate","Advanced"])
        with c3:
            dur = st.selectbox("Duration", ["30 mins","45 mins","60 mins","90 mins"])
        equip = st.multiselect("Equipment", ["Dumbbells","Barbell","Cable Machine","Bench",
                                              "Pull-up Bar","Resistance Bands","Treadmill","Bodyweight"],
                               default=["Dumbbells"])

        if st.button("⚡ Workout Generate Karo", type="primary", use_container_width=True):
            with st.spinner("AI plan bana raha hai..."):
                plan = _groq([
                    {"role":"system","content":"You are an expert personal trainer. Respond in Roman Urdu + English."},
                    {"role":"user","content":
                     f"Create a {dur} {focus} workout for {level} level.\n"
                     f"Member: {m.full_name}, Equipment: {', '.join(equip) or 'bodyweight'}\n\n"
                     "Include: warm-up, exercises (sets×reps, rest, tips), cool-down, motivation.\n"
                     "End with a table: Exercise | Sets | Reps | Rest | Muscle Group."}
                ], max_tokens=2000)
                st.session_state["mp_workout_plan"] = plan

        if st.session_state.get("mp_workout_plan"):
            st.divider()
            st.markdown(st.session_state["mp_workout_plan"])

            # Weekly training chart
            today2 = date.today()
            days7  = [today2 - timedelta(days=6-i) for i in range(7)]
            all_a  = db.get_attendance(check_date=None)
            my_a   = {a.check_date: a.status for a in all_a if a.member_id == m.id}
            vals7  = [1 if my_a.get(str(d)) == "Present" else 0 for d in days7]
            fig_wk = go.Figure(go.Bar(
                x=[d.strftime("%a %d") for d in days7], y=vals7,
                marker_color=["#7c3aed" if v else "#1e293b" for v in vals7],
                text=["✅" if v else "❌" for v in vals7], textposition="outside",
            ))
            fig_wk.update_layout(
                title="Is Hafte ki Training", plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
                font_color="#e2e8f0", height=220, title_x=0.5,
                yaxis=dict(showticklabels=False, range=[0,1.5]),
                margin=dict(t=40,b=10,l=10,r=10), showlegend=False,
            )
            st.plotly_chart(fig_wk, use_container_width=True)
            st.download_button("⬇️ Download Workout",
                               data=st.session_state["mp_workout_plan"],
                               file_name=f"workout_{m.serial_number}_{date.today()}.txt",
                               mime="text/plain")

    # ── Chat ──────────────────────────────────────────────────────
    with sub[2]:
        st.markdown('<div class="mp-sec">💬 AI se Kuch Bhi Pocho</div>', unsafe_allow_html=True)
        st.caption("Exercise, diet, fitness, motivation — kuch bhi pocho!")

        if "mp_chat" not in st.session_state:
            st.session_state["mp_chat"] = []

        for msg in st.session_state["mp_chat"]:
            cls = "chat-user" if msg["role"] == "user" else "chat-ai"
            icon = "🧑" if msg["role"] == "user" else "🤖"
            st.markdown(f'<div class="{cls}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)

        user_q = st.chat_input("Exercise ya diet ke bare mein pocho...")
        if user_q:
            st.session_state["mp_chat"].append({"role": "user", "content": user_q})
            sys_msg = {"role":"system","content":
                f"You are GymPro AI Coach for {m.full_name} "
                f"(membership: {m.membership_type}, gym: {db.get_gym(m.gym_id).name if db.get_gym(m.gym_id) else 'GymPro'}). "
                "Help with exercises, workout plans, nutrition, fitness tips. "
                "Respond in Roman Urdu + English. Be encouraging and specific."}
            with st.spinner("Soch raha hai..."):
                reply = _groq(
                    [sys_msg] + [{"role":x["role"],"content":x["content"]}
                                 for x in st.session_state["mp_chat"][-10:]],
                    max_tokens=1000
                )
            st.session_state["mp_chat"].append({"role":"assistant","content":reply})
            st.rerun()

        if st.session_state["mp_chat"]:
            if st.button("🗑️ Chat Clear"):
                st.session_state["mp_chat"] = []
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render():
    st.markdown(PORTAL_CSS, unsafe_allow_html=True)

    m = _mp_member()
    if not m:
        _login_page()
        return

    gym = db.get_gym(m.gym_id)

    # ── Top bar ───────────────────────────────────────────────────
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

    # ── Hero ──────────────────────────────────────────────────────
    _render_hero(m, gym)

    # ── Tabs ──────────────────────────────────────────────────────
    tabs = st.tabs(["🏠 Home", "📅 Attendance", "📈 Progress", "💰 Fees", "🤖 AI Coach", "🧠 Body Coach"])

    with tabs[0]: _tab_home(m, gym)
    with tabs[1]: _tab_attendance(m)
    with tabs[2]: _tab_progress(m)
    with tabs[3]: _tab_fees(m, gym)
    with tabs[4]: _tab_ai(m)
    with tabs[5]:
        from gym_pages import body_ai
        body_ai.render_body_coach(m, db.get_body_measurements(m.id))
