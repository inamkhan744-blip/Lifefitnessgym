import streamlit as st
import sys
import os
import base64
from datetime import datetime, timedelta

os.environ['TZ'] = 'Asia/Karachi'
import time
time.tzset()
sys.path.insert(0, os.path.dirname(__file__))

import database as db
import auth
import styles
import themes

# ── Session timeout (24 h) ─────────────────────────────────────────────────────
if "last_activity" not in st.session_state:
    st.session_state.last_activity = datetime.now()
else:
    if datetime.now() - st.session_state.last_activity > timedelta(hours=24):
        st.session_state.clear()
        st.warning("⏰ Session expired. Please login again.")
        st.rerun()
        st.stop()
    else:
        st.session_state.last_activity = datetime.now()

st.set_page_config(page_title="GymPro", page_icon="🏋️", layout="wide")

# ── Init DB once per server lifetime (not on every render) ────────────────────
@st.cache_resource
def _init_db_once():
    db.init_db()
    return True

_init_db_once()
styles.inject_css()

# ── Music player: encode MP3 once, reuse forever ──────────────────────────────
@st.cache_data(show_spinner=False)
def _get_music_b64() -> str | None:
    music_file = os.path.join(os.path.dirname(__file__), "gym_music.mp3")
    if not os.path.exists(music_file):
        return None
    try:
        with open(music_file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

def add_floating_music_player():
    _b64 = _get_music_b64()
    if _b64:
        st.markdown(f"""
        <style>
        .floating-music {{
            position: fixed; bottom: 20px; right: 20px;
            background: #1E293B; border-radius: 50px; padding: 8px 16px;
            border: 1px solid #334155; z-index: 999;
        }}
        .floating-music audio {{ height: 35px; width: 200px; }}
        @media (max-width: 600px) {{ .floating-music audio {{ width: 140px; }} }}
        </style>
        <div class="floating-music">
            <audio controls loop>
                <source src="data:audio/mp3;base64,{_b64}" type="audio/mp3">
            </audio>
        </div>
        """, unsafe_allow_html=True)

add_floating_music_player()

# ── Member Portal route (no staff login needed) ───────────────────────────────
if st.query_params.get("portal") == "1":
    from gym_pages import member_portal
    member_portal.render()
    st.stop()

# ── Auth gate ──────────────────────────────────────────────────────────────────
if not auth.require_login():
    auth.login_page()
    st.stop()

# ── Public profile route ───────────────────────────────────────────────────────
_profile_param = st.query_params.get("profile")
if _profile_param:
    from gym_pages import public_profile
    from profile_token import parse_token
    _mid = parse_token(_profile_param)
    public_profile.render(_mid if _mid is not None else -1)
    st.stop()

# ── Cached data helpers (avoid repeated DB hits every render) ─────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _cached_gyms():
    return db.get_all_gyms()

@st.cache_data(ttl=30, show_spinner=False)
def _cached_stats(gym_id):
    return db.get_stats(gym_id)

@st.cache_data(ttl=60, show_spinner=False)
def _cached_sidebar_alerts(gym_id):
    try:
        bdays = db.get_birthday_members(days_ahead=1, gym_id=gym_id)
    except Exception:
        bdays = []
    try:
        absent = db.get_absent_members(days=3, gym_id=gym_id)
    except Exception:
        absent = []
    try:
        low_s = db.get_stock_items(gym_id=gym_id, low_stock_only=True)
    except Exception:
        low_s = []
    return bdays, absent, low_s

@st.cache_data(ttl=300, show_spinner=False)
def _cached_theme_settings():
    return db.get_setting("theme_auto", "0"), db.get_setting("theme_key", "design_1")

# ── Session vars ───────────────────────────────────────────────────────────────
role        = st.session_state.get("role", "staff")
full_name   = st.session_state.get("full_name", "User")
username    = st.session_state.get("username", "")
user_id     = st.session_state.get("user_id")
gym_id      = st.session_state.get("selected_gym_id")
user_gym_id = st.session_state.get("user_gym_id")

gyms = _cached_gyms()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    _mode        = db.DB_MODE
    _badge_color = "#22c55e" if _mode == "online" else "#f59e0b"
    _badge_icon  = "🟢" if _mode == "online" else "🟡"
    _badge_label = "Online (Cloud DB)" if _mode == "online" else "Offline (Local DB)"
    st.markdown(
        f'<div style="text-align:center;padding:0.4rem 0.5rem 0;">'
        f'<span style="background:{_badge_color}22;color:{_badge_color};'
        f'border:1px solid {_badge_color}55;border-radius:20px;'
        f'font-size:0.72rem;padding:2px 10px;">{_badge_icon} {_badge_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div style="padding:1rem 0.5rem 0.5rem;text-align:center;">
        <div style="font-size:2rem;">🏋️</div>
        <div style="font-size:1.2rem;font-weight:800;color:#A78BFA;letter-spacing:0.05em;">GymPro</div>
        <div style="font-size:0.7rem;color:#475569;letter-spacing:0.1em;text-transform:uppercase;">Multi-Gym Control Panel</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    role_icon  = auth.ROLE_ICONS.get(role, "👤")
    role_label = {"admin": "Administrator", "staff": "Staff Member",
                  "auditor": "Independent Auditor"}.get(role, role.upper())
    st.markdown(f"""
    <div style="background:#1E293B;border-radius:10px;padding:0.75rem;margin-bottom:0.75rem;">
        <div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;">Signed in as</div>
        <div style="font-weight:700;color:#E2E8F0;">{role_icon} {full_name}</div>
        <div style="font-size:0.72rem;color:#7C3AED;font-weight:600;">{role_label}</div>
    </div>
    """, unsafe_allow_html=True)

    # Gym selector
    if role == "admin" and gyms:
        st.markdown("""<div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;
            letter-spacing:0.08em;margin-bottom:0.3rem;">Switch Gym Location</div>""",
                    unsafe_allow_html=True)
        gym_options = {"🌐 All Gyms": None} | {f"🏋️ {g.name}": g.id for g in gyms}
        cur_gym_key = next((f"🏋️ {g.name}" for g in gyms if g.id == gym_id), "🌐 All Gyms")
        chosen_gym  = st.selectbox(
            "Switch Gym Location",
            list(gym_options.keys()),
            index=list(gym_options.keys()).index(cur_gym_key),
            label_visibility="collapsed",
            key="main_gym_selector",
        )
        st.session_state["selected_gym_id"] = gym_options[chosen_gym]
        gym_id = st.session_state["selected_gym_id"]
        st.markdown(f"""<div style="font-size:0.7rem;color:#64748B;text-align:right;
            margin-top:-0.3rem;margin-bottom:0.3rem;">{len(gyms)} gym(s) registered</div>""",
                    unsafe_allow_html=True)
    elif user_gym_id and gyms:
        gym_name = next((g.name for g in gyms if g.id == user_gym_id), "Your Gym")
        st.markdown(f"""<div style="background:#1E293B;border-radius:8px;padding:0.5rem 0.75rem;
            margin-bottom:0.5rem;font-size:0.85rem;">🏋️ <strong>{gym_name}</strong><br>
            <span style="font-size:0.65rem;color:#64748B;">Assigned Gym</span></div>""",
                    unsafe_allow_html=True)
        st.session_state["selected_gym_id"] = user_gym_id
        gym_id = user_gym_id

    # Theme selector (admin only)
    if role == "admin":
        st.divider()
        st.markdown(
            '<div style="font-size:0.6rem;color:#475569;text-transform:uppercase;'
            'letter-spacing:0.1em;margin-bottom:0.4rem;">🎨 App Theme</div>',
            unsafe_allow_html=True,
        )
        _theme_auto_str, _theme_key_str = _cached_theme_settings()
        _auto_on   = _theme_auto_str == "1"
        _cur_key   = themes.get_daily_theme() if _auto_on else _theme_key_str
        _cur_label = themes.THEME_NAMES.get(_cur_key, "🪨 Dark Slate")

        _auto_toggle = st.checkbox("Auto (daily)", value=_auto_on, key="theme_auto_chk")
        if _auto_toggle != _auto_on:
            db.set_setting("theme_auto", "1" if _auto_toggle else "0")
            _cached_theme_settings.clear()
            st.rerun()

        if not _auto_toggle:
            _all_labels = list(themes.THEME_NAMES.values())
            _all_keys   = list(themes.THEME_NAMES.keys())
            _sel_idx    = _all_keys.index(_cur_key) if _cur_key in _all_keys else 0
            _picked     = st.selectbox(
                "Select Theme",
                _all_labels,
                index=_sel_idx,
                key="theme_picker",
                label_visibility="collapsed",
            )
            _picked_key = _all_keys[_all_labels.index(_picked)]
            if _picked_key != _cur_key:
                db.set_setting("theme_key", _picked_key)
                _cached_theme_settings.clear()
                st.rerun()
        else:
            st.caption(f"Today: **{_cur_label}**")

    st.divider()

    # ── SIDEBAR NAVIGATION BUTTONS FIX - Theme-aware ──────────────────────────
    st.markdown("""
    <style>
        /* Sidebar Navigation Buttons - Force visibility in ALL themes */
        section[data-testid="stSidebar"] .stButton > button {
            background: rgba(255, 255, 255, 0.08) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.10) !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 8px 14px !important;
            min-height: 42px !important;
            width: 100% !important;
            border-radius: 10px !important;
            text-align: left !important;
            transition: all 0.2s ease !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(124, 58, 237, 0.25) !important;
            border-color: #7C3AED !important;
            transform: translateX(4px) !important;
        }
        section[data-testid="stSidebar"] .stButton > button:focus,
        section[data-testid="stSidebar"] .stButton > button:active {
            background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
            border-color: #7C3AED !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
        }
        /* Force ALL text white in sidebar buttons */
        section[data-testid="stSidebar"] .stButton > button span,
        section[data-testid="stSidebar"] .stButton > button p,
        section[data-testid="stSidebar"] .stButton > button div,
        section[data-testid="stSidebar"] .stButton > button label,
        section[data-testid="stSidebar"] .stButton > button .st-emotion-cache-1wbqy5l {
            color: #FFFFFF !important;
        }
        /* Fix for active/selected state */
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
            border-color: #7C3AED !important;
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] span,
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] p {
            color: #FFFFFF !important;
        }
        /* Fix for nav-btn class */
        .nav-btn button, .nav-btn-active button {
            background: rgba(255, 255, 255, 0.08) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.10) !important;
        }
        .nav-btn-active button {
            background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
            border-color: #7C3AED !important;
            color: #FFFFFF !important;
        }
        .nav-btn button:hover {
            background: rgba(124, 58, 237, 0.25) !important;
            border-color: #7C3AED !important;
        }
        .nav-btn-active button span,
        .nav-btn-active button p {
            color: #FFFFFF !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Navigation
    allowed = auth.allowed_pages()
    nav_sections = {
        "AI & Support": {
            "AI Assistant":      ("🤖", "AI Assistant"),
        },
        "General Management": {
            "Dashboard":         ("📊", "Dashboard"),
         "Gym Setup":         ("⚙️", "Gym Setup"),
         "Settings":          ("🧩", "Settings"),
        },
        "Member & Identity": {
            "Members":           ("👥", "Members"),
            "Membership Cards":  ("🪪", "Membership Cards"),
            "Bulk ID Cards":     ("🖨️", "Bulk ID Cards"),
            "Attendance":        ("📅", "Attendance"),
            "Progress Tracker":  ("📏", "Progress Tracker"),
        },
        "Fees & Finance": {
            "Fee Collection":    ("💰", "Fee Collection"),
            "Expenses":          ("📉", "Expenses"),
            "Inventory":         ("📦", "Inventory"),
            "Reports":           ("📈", "Reports"),
        },
        "Staff Management": {
            "Staff Targets":     ("🎯", "Staff Targets"),
        },
        "Communication": {
            "Message Center":    ("📨", "Message Center"),
            "WhatsApp":          ("💬", "WhatsApp"),
            "Complaints":        ("📣", "Complaints"),
        },
        "Audit & Access": {
            "Audit":             ("🔍", "Audit"),
            "User Management":   ("🔐", "User Management"),
        },
        "Member Portal": {
            "Member Portal":     ("📱", "Member Portal"),
        },
    }

    current_page = st.session_state.get("page", "Dashboard")
    for section_label, pages in nav_sections.items():
        visible = [k for k in pages if k in allowed]
        if not visible:
            continue
        st.markdown(
            f'<div style="font-size:0.6rem;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.1em;padding:0.4rem 0 0.2rem;">{section_label}</div>',
            unsafe_allow_html=True,
        )
        for page_key in visible:
            icon, label = pages[page_key]
            is_active   = current_page == page_key
            btn_style   = "nav-btn-active" if is_active else "nav-btn"
            st.markdown(f'<div class="{btn_style}">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state["page"] = page_key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Alert badges — cached, not re-queried every render
    _bdays, _absent, _low_s = _cached_sidebar_alerts(gym_id)
    if _bdays:
        st.markdown(f'<div style="background:#1E3A1E;border-radius:6px;padding:0.4rem 0.6rem;'
                    f'font-size:0.75rem;color:#34D399;margin-bottom:0.3rem;">🎂 {len(_bdays)} birthday today</div>',
                    unsafe_allow_html=True)
    if _absent:
        st.markdown(f'<div style="background:#3A1E1E;border-radius:6px;padding:0.4rem 0.6rem;'
                    f'font-size:0.75rem;color:#F87171;margin-bottom:0.3rem;">🚶 {len(_absent)} absent 3+ days</div>',
                    unsafe_allow_html=True)
    if _low_s:
        st.markdown(f'<div style="background:#3A2A1E;border-radius:6px;padding:0.4rem 0.6rem;'
                    f'font-size:0.75rem;color:#FBBF24;margin-bottom:0.3rem;">📦 {len(_low_s)} low stock items</div>',
                    unsafe_allow_html=True)

    # Sidebar stats — cached
    stats = _cached_stats(gym_id)
    st.markdown("""<div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;
        letter-spacing:0.08em;margin:0.5rem 0 0.3rem;">Revenue Analytics</div>""",
                unsafe_allow_html=True)
    st.markdown(styles.metric_card("Members", stats["total_members"],
                                   f"{stats['active_members']} active", "purple"),
                unsafe_allow_html=True)
    st.markdown(styles.metric_card("Month Revenue", f"PKR {stats['month_revenue']:,.0f}",
                                   "", "green"), unsafe_allow_html=True)
    st.markdown(styles.metric_card("Month Expenses", f"PKR {stats['month_expenses']:,.0f}",
                                   "", "red"), unsafe_allow_html=True)

    st.divider()

    from gym_pages import ai_assistant as _ai
    _ai.render_persistent_music_bar()

    st.divider()

    _ai.render_sidebar_widget(
        current_page=st.session_state.get("page", "Dashboard"),
        gym_id=gym_id,
        role=role,
        username=username,
    )

    st.divider()
    if st.button("🚪 Sign Out", use_container_width=True):
        auth.logout()

# ── Page router — lazy imports (each module loaded only when first visited) ────
page = st.session_state.get("page", "Dashboard")

if not auth.can_access(page):
    st.error("🚫 You don't have permission to access this page.")
    st.stop()

gid = st.session_state.get("selected_gym_id")

# ── Import all pages ──────────────────────────────────────────────────────────
# Dashboard
if page == "Dashboard":
    from gym_pages import design_dashboard
    design_dashboard.render(gid, role, username)

# General Management
elif page == "Gym Setup":
    from gym_pages import setup
    setup.render()

elif page == "Settings":
    from gym_pages import settings
    settings.render()

# Member & Identity
elif page == "Members":
    from gym_pages import members
    members.render(gid, role)

elif page == "Membership Cards":
    from gym_pages import membership_card
    membership_card.render(gid, role)

elif page == "Bulk ID Cards":
    from gym_pages import bulk_id_cards
    bulk_id_cards.render(gid, role)

elif page == "Attendance":
    from gym_pages import attendance
    attendance.render(gid, role, username)

elif page == "Progress Tracker":
    from gym_pages import progress
    progress.render(gid, role)

# Fees & Finance
elif page == "Fee Collection":
    from gym_pages import fee_collection
    fee_collection.render(gid, role, username)

elif page == "Expenses":
    from gym_pages import expenses
    expenses.render(gid, role, username)

elif page == "Inventory":
    from gym_pages import inventory
    inventory.render(gid, role)

elif page == "Reports":
    from gym_pages import reports
    reports.render(gid, role, username)

# Communication
elif page == "Message Center":
    from gym_pages import message_center
    message_center.render(gid, role)

elif page == "WhatsApp":
    from gym_pages import whatsapp
    whatsapp.render(gid, role)

elif page == "Complaints":
    from gym_pages import complaints
    complaints.render(gid, role)

# Staff Management
elif page == "Staff Targets":
    from gym_pages import staff_targets
    staff_targets.render(gid, role, username)

# Audit & Access
elif page == "Audit":
    from gym_pages import auditor
    auditor.render(gid, role, username)

elif page == "User Management":
    from gym_pages import user_management
    user_management.render(user_id)

# AI
elif page == "AI Assistant":
    from gym_pages import ai_assistant
    ai_assistant.render(gid, role, username)

# Member Portal (staff/admin view)
elif page == "Member Portal":
    from gym_pages import member_portal
    member_portal.render()

# ── Unknown page fallback ──────────────────────────────────────────────────────
else:
    st.error(f"❌ Page '{page}' not found.")
    st.info("Please select a page from the sidebar.")