import streamlit as st
from datetime import date, datetime, timedelta
import io, os, re, requests, database as db, sqlite3
import shutil, json, ast, time, subprocess, zipfile, difflib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from database import (
    get_db, get_gym, get_all_gyms, get_members, get_member, get_member_by_serial,
    add_member, update_member, delete_member, get_fee_records, add_fee_record,
    get_expenses, add_expense, get_attendance, mark_attendance,
    get_stock_items, add_stock_item, get_complaints, add_complaint,
    get_body_measurements, add_body_measurement, get_staff_targets,
    get_staff_progress, get_active_announcement, get_all_announcements,
    get_gym_plans, get_gym_photos, get_recent_scans, get_stats,
    get_monthly_revenue, get_expiring_members, get_absent_members,
    get_birthday_members, get_attendance_leaderboard, get_activity_logs,
    get_daily_fee_summary, get_staff_attendance_summary, get_my_attendance_summary,
    get_staff_timing, get_all_staff_timings, get_unknown_captures,
    get_face_encodings, get_receipt_logs, get_audit_entries,
    MEMBERSHIP_TYPES, PAYMENT_METHODS, EXPENSE_CATEGORIES, STOCK_CATEGORIES,
    COMPLAINT_PRIORITIES, COMPLAINT_STATUSES, get_health_tip,
    get_setting, set_setting, hash_password, verify_password,
    SessionLocal, Base, engine, IS_POSTGRES, DB_MODE, UPLOAD_FOLDER,
    get_member_count, get_active_member_count, get_expenses_by_category,
    get_all_users
)

# ═══════════════════════════════════════════════════════════
# 🤖 IMPORT V12 ENGINE
# ═══════════════════════════════════════════════════════════
try:
    from gym_pages.ai_coder_v12 import (
        v12_execute, v12_auto_fix, v12_self_test, v12_get_commits,
        v12_time_travel, v12_scan_project, v12_load_index, v12_index_summary,
        v12_cleanup_backups, v12_is_protected, v12_validate_syntax,
        v12_validate_imports, v12_validate_safety, v12_build_context,
        PROTECTED_FILES, PROTECTED_EXTENSIONS, PROTECTED_DIRS,
        V12_BACKUP_ROOT,
    )
    V12_AVAILABLE = True
except Exception as _e:
    V12_AVAILABLE = False
    _V12_IMPORT_ERROR = str(_e)


# ============================================
# CONFIG
# ============================================

CODER_COMMITS_FILE = ".ai_coder_commits.json"
CODER_MEMORY_FILE = ".ai_coder_memory.json"
CODER_SCHEDULE_FILE = ".ai_coder_schedule.json"
CODER_MAX_CHARS = 32000
CODER_MAX_TOKENS = 16000
CODER_MAX_RETRIES = 3
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".streamlit", "backups",
             "uploads", "member_photos", "docs", "logs", ".backups"}


# ============================================
# YOUTUBE
# ============================================

_YT_CACHE = {}
_YT_CACHE_TIMEOUT = 300


def _fmt_duration(secs):
    try:
        s = int(secs)
        h, rem = divmod(s, 3600)
        m, sc = divmod(rem, 60)
        return f"{h}:{m:02d}:{sc:02d}" if h else f"{m}:{sc:02d}"
    except Exception:
        return ""


def search_youtube(query, max_results=10):
    cache_key = f"{query.strip().lower()}|{max_results}"
    if cache_key in _YT_CACHE:
        cached, ts = _YT_CACHE[cache_key]
        if (datetime.now() - ts).seconds < _YT_CACHE_TIMEOUT:
            return cached
    try:
        from yt_dlp import YoutubeDL
        opts = {"quiet": True, "no_warnings": True, "extract_flat": True,
                "skip_download": True, "socket_timeout": 15}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        results = []
        for e in (info or {}).get("entries", []):
            vid_id = e.get("id", "")
            if vid_id:
                results.append({
                    "id": vid_id,
                    "title": e.get("title", "Unknown"),
                    "duration": _fmt_duration(e.get("duration", 0)),
                    "thumb": f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg",
                })
        if results:
            _YT_CACHE[cache_key] = (results, datetime.now())
            return results
    except Exception:
        pass
    return []


# ============================================
# SESSION STATE
# ============================================

def _init_state():
    defaults = {
        "ai_chat_history": [], "ai_input_counter": 0, "ai_last_question": "",
        "speak_trigger": None, "auto_speak": False,
        "music_results": [], "music_search": "", "active_music": None,
        "active_music_title": "", "music_queue": [], "music_queue_idx": 0,
        "video_results": [], "video_search": "", "active_video": None,
        "active_video_title": "", "ai_coder_result": None,
        "coder_undo_stack": [], "coder_last_error": None,
        "coder_memory": [], "coder_search_results": [],
        "music_playing": False, "music_volume": 0.5, "auto_speak": False,
        # V12 state
        "v12_last_result": None, "v12_last_preview": None,
        "v12_action": None, "v12_command": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def play_tts(text):
    try:
        from gtts import gTTS
        lang = "ur" if any(ord(c) in range(0x0600, 0x06FF) for c in text) else "en"
        clean = re.sub(r'[*_`#\-\n]', ' ', text)[:500]
        tts = gTTS(text=clean, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3", autoplay=True)
    except Exception:
        pass


# ============================================
# MUSIC BAR
# ============================================

def render_persistent_music_bar():
    _init_state()
    vid = st.session_state.get("active_music")
    title = st.session_state.get("active_music_title", "")
    queue = st.session_state.get("music_queue", [])
    idx = st.session_state.get("music_queue_idx", 0)
    if "music_playing" not in st.session_state:
        st.session_state["music_playing"] = bool(vid)
    if "music_volume" not in st.session_state:
        st.session_state["music_volume"] = 0.5
    if not vid:
        return
    html = (
        '<div style="background:linear-gradient(90deg,#1E3A5F,#1E1B4B);border:1px solid #3B82F6;'
        'border-radius:10px;padding:0.6rem 0.8rem;margin-bottom:0.5rem;">'
        '<span style="color:#60A5FA;font-weight:700;font-size:0.7rem;">NOW PLAYING</span><br>'
        f'<span style="color:var(--gp-text);font-size:0.8rem;">{title[:50]}</span></div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    with c1:
        if st.button("⏮", key="pmb_prev", use_container_width=True):
            if queue and idx > 0:
                ni = idx - 1
                st.session_state["music_queue_idx"] = ni
                st.session_state["active_music"] = queue[ni]["id"]
                st.session_state["active_music_title"] = queue[ni]["title"]
                st.session_state["music_playing"] = True
                st.rerun()
    with c2:
        if st.session_state["music_playing"]:
            if st.button("⏸", key="pmb_pause", use_container_width=True):
                st.session_state["music_playing"] = False
                st.rerun()
        else:
            if st.button("▶️", key="pmb_play", use_container_width=True):
                st.session_state["music_playing"] = True
                st.rerun()
    with c3:
        if st.button("⏹", key="pmb_stop", use_container_width=True):
            st.session_state["active_music"] = None
            st.session_state["active_music_title"] = ""
            st.session_state["music_playing"] = False
            st.rerun()
    with c4:
        vol = st.slider("Volume", 0.0, 1.0, st.session_state["music_volume"], key="music_vol_slider")
        st.session_state["music_volume"] = vol
    if st.session_state["music_playing"]:
        embed_url = f"https://www.youtube.com/embed/{vid}?autoplay=1&mute=0"
        audio_html = (
            f'<iframe id="ytplayer" type="text/html" width="0" height="0" '
            f'src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" '
            f'allowfullscreen></iframe>'
        )
        st.components.v1.html(audio_html, height=0)


def render_sidebar_widget(current_page, gym_id=None, role="staff", username=""):
    _init_state()
    gym_stats = {}
    try:
        gym_stats = db.get_stats(gym_id)
    except Exception:
        pass
    role_label = {"admin": "👑 Admin", "owner": "👑 Owner",
                  "staff": "👤 Staff", "auditor": "🔍 Auditor"}.get(role, role)
    with st.expander(f"🤖 AI Assistant — {role_label}", expanded=False):
        chips = ["Aaj ka summary?", "Fee collection?"] if role in ["admin", "owner"] else ["Fee kaise?", "Member kaise?"]
        chip_cols = st.columns(2)
        for i, chip in enumerate(chips):
            if chip_cols[i % 2].button(chip, key=f"sb_chip_{i}", use_container_width=True):
                _push_and_respond(chip, current_page, gym_stats, role=role, username=username, gym_id=gym_id)
        key = f"sb_chat_{st.session_state.get('ai_input_counter', 0)}"
        user_input = st.text_input("", placeholder="Roman Urdu...", key=key, label_visibility="collapsed")
        col1, col2 = st.columns([3, 1])
        send = col1.button("Send ➤", key="sb_send_btn", type="primary", use_container_width=True)
        clear = col2.button("🗑", key="sb_clear_btn", use_container_width=True)
        # Auto Speak toggle
        auto_speak_chk = st.checkbox("Auto Speak (Voice Output)", value=st.session_state.get("auto_speak", False), key="auto_speak_chk")
        if auto_speak_chk != st.session_state.get("auto_speak", False):
            st.session_state["auto_speak"] = auto_speak_chk
        # Mic input placeholder
        if st.button("🎤 Speak (Mic)", key="mic_btn"):
            st.session_state["speak_trigger"] = True
        if clear:
            st.session_state["ai_chat_history"] = []
            st.session_state["ai_input_counter"] += 1
            st.rerun()
        if send and user_input.strip():
            _push_and_respond(user_input.strip(), current_page, gym_stats, role=role, username=username, gym_id=gym_id)


# ============================================
# AI CHAT
# ============================================

def _handle_app_check():
    try:
        members = db.get_members()
        today = date.today()
        fees = db.get_fee_records(date_from=today, date_to=today)
        return "🔍 DB: OK\n👥 Members: " + str(len(members) if members else 0) + "\n💰 Today: " + str(len(fees) if fees else 0)
    except Exception as e:
        return "❌ " + str(e)


def _create_backup(backup_name=None):
    try:
        if not backup_name:
            backup_name = "backup_" + datetime.now().strftime('%Y%m%d_%H%M%S')
        bdir = "backups/" + backup_name
        os.makedirs(bdir, exist_ok=True)
        for f in ["app.py", "database.py", "auth.py"]:
            if os.path.exists(f):
                shutil.copy2(f, bdir + "/" + f)
        return "✅ Backup: " + bdir
    except Exception as e:
        return "❌ " + str(e)


def _run_tests():
    tests = []
    try:
        db.get_stats()
        tests.append("✅ DB")
    except Exception:
        tests.append("❌ DB")
    try:
        members = db.get_members()
        tests.append("✅ Members: " + str(len(members)))
    except Exception:
        tests.append("❌ Members")
    return "🧪 " + ", ".join(tests)


def _get_reminders():
    rem = []
    try:
        exp = db.get_expiring_members(days=3)
        if exp:
            rem.append(str(len(exp)) + " expiring")
    except Exception:
        pass
    return rem


def _get_live_context(gym_id=None, role="staff", username=""):
    lines = []
    try:
        stats = db.get_stats(gym_id)
        lines.append("Members: " + str(stats.get('total_members', 0)) +
                     ", Active: " + str(stats.get('active_members', 0)))
    except Exception:
        pass
    lines.append("User: " + str(username) + ", Role: " + str(role))
    return "\n".join(lines)


def get_ai_response(messages, page, gym_stats, role="staff", username="", gym_id=None):
    user_msg = messages[-1]["content"] if messages else ""
    q = user_msg.lower()
    if "backup" in q and role in ["admin", "owner"]:
        return _create_backup()
    if "test" in q and role in ["admin", "owner"]:
        return _run_tests()
    if "app check" in q and role in ["admin", "owner"]:
        return _handle_app_check()
    if "reminder" in q:
        r = _get_reminders()
        return "🔔 " + ", ".join(r) if r else "✅ No reminders!"
    if "help" in q:
        return "🤖 Commands: backup, test, app check, summary, workout, diet"
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            sys_c = _get_live_context(gym_id, role, username)
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": "Bearer " + groq_key, "Content-Type": "application/json"},
                json={"model": "openai/gpt-oss-120b",
                      "messages": [
                          {"role": "system", "content": "You are GymPro AI. " + sys_c + ". Reply in Roman Urdu."},
                          {"role": "user", "content": user_msg}],
                      "max_tokens": 500, "temperature": 0.7},
                timeout=15,
            )
            if resp.status_code == 200:
                msg = resp.json()["choices"][0]["message"]
                out = (msg.get("content") or "").strip()
                if not out:
                    out = (msg.get("reasoning") or "").strip()
                if out:
                    return out
        except Exception:
            pass
    if "summary" in q:
        return "📊 Members: " + str(gym_stats.get('total_members', 0))
    if "fee" in q:
        try:
            t, c, _ = db.get_daily_fee_summary()
            return "💰 Today: PKR " + str(f"{t:,.0f}")
        except Exception:
            return "💰"
    if "workout" in q:
        return "🏋️ Mon-Chest, Tue-Back, Wed-Legs..."
    if "diet" in q:
        return "🥗 Subah: Eggs, Dopahar: Chicken"
    return "🤔 " + page + " par poochiye"


def _push_and_respond(user_text, page, gym_stats, role="staff", username="", gym_id=None):
    if st.session_state.get("ai_last_question") == user_text:
        st.warning("⚠️ Already pooch chuke ho!")
        return
    st.session_state["ai_last_question"] = user_text
    st.session_state["ai_chat_history"].append({"role": "user", "content": user_text})
    with st.spinner("🤔..."):
        reply = get_ai_response(st.session_state["ai_chat_history"][-20:], page, gym_stats, role=role, username=username, gym_id=gym_id)
    st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
    if st.session_state.get("auto_speak", True):
        st.session_state["speak_trigger"] = reply
    st.session_state["ai_input_counter"] += 1
    st.rerun()


# ============================================
# MUSIC / VIDEO
# ============================================

_MUSIC_GENRES = [
    ("🏋️ Workout", "gym workout motivation"),
    ("🇵🇰 Pakistani", "Pakistani pop songs 2024"),
    ("🎬 Bollywood", "Bollywood hits 2024"),
    ("⚡ EDM", "EDM gym music"),
    ("☕ Lofi", "lofi hip hop"),
    ("🎤 Hip-Hop", "hip hop rap"),
    ("🎸 Punjabi", "Punjabi songs 2024"),
    ("🕌 Naat", "naat sharif new 2024"),
]


def _music_player():
    _init_state()
    st.markdown("### 🎵 Music")
    vid = st.session_state.get("active_music")
    if vid:
        st.markdown("**NOW PLAYING:** " + st.session_state.get('active_music_title', '')[:70])
        iframe = '<iframe width="100%" height="315" src="https://www.youtube.com/embed/' + vid + '?autoplay=1" frameborder="0" allow="autoplay" allowfullscreen></iframe>'
        st.markdown(iframe, unsafe_allow_html=True)
        if st.button("⏹ Stop", key="music_stop2", use_container_width=True):
            st.session_state["active_music"] = None
            st.rerun()
        st.divider()
    g_cols = st.columns(4)
    for i, (label, query) in enumerate(_MUSIC_GENRES):
        if g_cols[i % 4].button(label, key=f"genre_{i}", use_container_width=True):
            with st.spinner(label + "..."):
                res = search_youtube(query, max_results=10)
            if res:
                st.session_state["music_results"] = res
                st.session_state["music_queue"] = res
                st.session_state["music_queue_idx"] = 0
                st.session_state["active_music"] = res[0]["id"]
                st.session_state["active_music_title"] = res[0]["title"]
                st.rerun()
    results = st.session_state.get("music_results", [])
    if results:
        cols = st.columns(2)
        for i, track in enumerate(results):
            with cols[i % 2]:
                st.markdown("**" + track['title'][:55] + "**")
                if st.button("▶️ Play", key=f"mplay_{i}", use_container_width=True):
                    st.session_state["active_music"] = track["id"]
                    st.session_state["active_music_title"] = track["title"]
                    st.session_state["music_queue"] = results
                    st.session_state["music_queue_idx"] = i
                    st.rerun()


_VIDEO_CATEGORIES = [
    ("💪 Chest", "best chest workout"), ("🦵 Legs", "leg workout"),
    ("🔙 Back", "back workout"), ("🏃 Cardio", "cardio HIIT"),
    ("🧘 Yoga", "yoga for beginners"), ("⚡ HIIT", "HIIT fat burn"),
    ("🥗 Diet", "gym diet plan"), ("🏋️ Motivation", "gym motivation"),
]


def _video_player():
    _init_state()
    st.markdown("### 🎬 Video")
    vid = st.session_state.get("active_video")
    if vid:
        st.markdown("**NOW PLAYING:** " + st.session_state.get('active_video_title', '')[:80])
        iframe = '<iframe width="100%" height="400" src="https://www.youtube.com/embed/' + vid + '?autoplay=1" frameborder="0" allow="autoplay" allowfullscreen></iframe>'
        st.markdown(iframe, unsafe_allow_html=True)
        if st.button("⏹ Stop", key="vstop", use_container_width=True):
            st.session_state["active_video"] = None
            st.rerun()
        st.divider()
    cat_cols = st.columns(4)
    for i, (label, query) in enumerate(_VIDEO_CATEGORIES):
        if cat_cols[i % 4].button(label, key=f"vcat_{i}", use_container_width=True):
            with st.spinner(label + "..."):
                res = search_youtube(query, max_results=9)
            if res:
                st.session_state["video_results"] = res
                st.rerun()
    results = st.session_state.get("video_results", [])
    if results:
        cols3 = st.columns(3)
        for i, track in enumerate(results):
            with cols3[i % 3]:
                st.markdown("**" + track['title'][:45] + "**")
                if st.button("▶️ Play", key=f"vplay_{i}", use_container_width=True):
                    st.session_state["active_video"] = track["id"]
                    st.session_state["active_video_title"] = track["title"]
                    st.rerun()


# ============================================
# 🎯 V12 CODER TAB (Replit-style UI)
# ============================================

def _render_preview_changes(changes):
    """Preview mein changes dikhao"""
    for i, ch in enumerate(changes):
        fp = ch.get("file", "")
        act = ch.get("action", "modify")
        with st.expander(f"#{i+1} — **{act.upper()}**: `{fp}`", expanded=True):
            if act == "create":
                st.markdown("**🆕 Naya file:**")
                st.code(ch.get("new_content", "")[:3000], language="python")
            elif act == "modify":
                st.markdown("**🔴 Search (ye milega):**")
                st.code(ch.get("search_for", ""), language="python")
                st.markdown("**🟢 Replace (ye hoga):**")
                st.code(ch.get("replace_with", ""), language="python")


def _render_result(res):
    """Execution result dikhao"""
    if res.get("success"):
        st.success(res["message"])
    else:
        st.warning(res["message"])

    if res.get("plan"):
        with st.expander("📋 Plan", expanded=False):
            for i, s in enumerate(res["plan"], 1):
                st.markdown(f"{i}. {s}")

    if res.get("changes_applied"):
        st.markdown("### ✅ Applied")
        for ch in res["changes_applied"]:
            st.success(f"**{ch['file']}** — {ch['message']}")

    if res.get("verification"):
        with st.expander("🧪 Verification", expanded=False):
            for fp, v in res["verification"].items():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{fp}**")
                c2.metric("Syntax", "✅" if v.get("syntax") else "❌")
                c3.metric("Imports", "✅" if v.get("imports_ok") else "⚠️")
                if v.get("missing"):
                    st.caption(f"⚠️ Missing imports: {', '.join(v['missing'])}")

    if res.get("backup_dir"):
        st.caption(f"💾 Backup: `{res['backup_dir']}`")


def _v12_coder_tab(role, username, gym_id=None):
    if role not in ("admin", "owner"):
        st.error("🔒 Sirf Admin")
        return

    if not V12_AVAILABLE:
        st.error("❌ V12 engine load nahi hua")
        st.code(f"Error: {_V12_IMPORT_ERROR if '_V12_IMPORT_ERROR' in globals() else 'unknown'}")
        return

    # Header
    st.markdown("""
    <div style="text-align:center;padding:1rem;background:linear-gradient(135deg,#0f172a,#1e1b4b);
    border-radius:16px;border:2px solid #10b981;margin-bottom:1rem;">
        <h2 style="margin:0;color:#10b981;">🤖 AI Coder V12 — SUPER MODE</h2>
        <p style="margin:0.5rem 0 0;color:#94a3b8;font-size:0.9rem;">
        Chat · Preview · Multi-file · Auto-Verify · Database Safe</p>
    </div>
    """, unsafe_allow_html=True)

    # Project index summary
    try:
        summary = v12_index_summary()
        st.caption(summary)
    except Exception:
        pass

    # ═══ 4 BIG BUTTONS ═══
    if "v12_action" not in st.session_state:
        st.session_state["v12_action"] = None

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("🎯 Kuch Banao", use_container_width=True, type="primary", key="v12_btn_create"):
            st.session_state["v12_action"] = "create"
    with b2:
        if st.button("🔧 Error Fix", use_container_width=True, type="primary", key="v12_btn_fix"):
            st.session_state["v12_action"] = "fix"
    with b3:
        if st.button("📜 History", use_container_width=True, type="primary", key="v12_btn_hist"):
            st.session_state["v12_action"] = "history"
    with b4:
        if st.button("🧪 System", use_container_width=True, type="primary", key="v12_btn_sys"):
            st.session_state["v12_action"] = "system"

    st.divider()
    action = st.session_state.get("v12_action")

    # ═══ ACTION: CREATE ═══
    if action == "create":
        st.markdown("### 🎯 Bolo Kya Karna Hai")
        st.caption("Roman Urdu mein likho — AI samjhega aur karega")

        cmd = st.text_area(
            "Command:",
            value=st.session_state.get("v12_command", ""),
            height=140,
            key="v12_cmd_input",
            placeholder="Jaise: Members page mein ek search bar add karo jo naam aur phone se search kare...",
        )

        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            preview_btn = st.button("👁️ Pehle Dikhao", use_container_width=True, key="v12_preview_btn")
        with c2:
            apply_btn = st.button("🚀 Seedha Karo", use_container_width=True, type="primary", key="v12_apply_btn")
        with c3:
            if st.button("❌", use_container_width=True, key="v12_cancel_btn"):
                st.session_state["v12_action"] = None
                st.session_state["v12_last_result"] = None
                st.session_state["v12_last_preview"] = None
                st.rerun()

        # Show recent conversation (memory)
        try:
            from gym_pages.ai_coder_v12 import v12_get_conversation
            recent = v12_get_conversation(limit=3)
            if recent:
                with st.expander("🧠 Pichhli Baatein (AI yaad rakhta hai)", expanded=False):
                    for turn in reversed(recent):
                        st.markdown(f"**Tum:** {turn.get('user', '')[:150]}")
                        if turn.get('topic'):
                            st.caption(f"📌 Topic: {turn['topic']}")
                        if turn.get('ai_explanation'):
                            st.markdown(f"**AI:** {turn.get('ai_explanation', '')[:200]}")
                        st.divider()
        except Exception:
            pass
        
        if preview_btn and cmd.strip():
            with st.spinner("👁️ Preview bana raha hoon..."):
                res = v12_execute(cmd, preview_only=True)
            st.session_state["v12_last_preview"] = res
            st.session_state["v12_command"] = cmd

        if apply_btn and cmd.strip():
            with st.spinner("🚀 Verify + Apply..."):
                res = v12_execute(cmd, preview_only=False)
            st.session_state["v12_last_result"] = res
            st.session_state["v12_command"] = cmd
            # Refresh index
            try:
                v12_scan_project()
            except Exception:
                pass

        # Show preview — ALWAYS show, even if empty
        prev = st.session_state.get("v12_last_preview")
        if prev is not None:
            st.divider()
            st.markdown("### 👁️ Preview")
            if prev.get("included_files"):
                st.caption("📂 AI ne ye files padhe: " + ", ".join(prev["included_files"][:5]))
            preview_changes = prev.get("changes_preview", [])
            if preview_changes:
                st.success(f"✅ {len(preview_changes)} changes ready hain")
                _render_preview_changes(preview_changes)
            else:
                # Show why no changes
                msg = prev.get("message", "Koi change nahi mila")
                st.warning(msg)
                if prev.get("explanation"):
                    st.info("🤖 AI ka explanation: " + prev["explanation"])
                if prev.get("blocked"):
                    st.error("🛡️ Ye files protected hain:\n- " + "\n- ".join(prev["blocked"]))

        # Show result — ALWAYS
        res = st.session_state.get("v12_last_result")
        if res is not None:
            st.divider()
            st.markdown("### 📊 Result")
            _render_result(res)
            # Show explanation if no changes
            if res.get("explanation") and not res.get("changes_applied"):
                st.info("🤖 AI: " + res["explanation"])

    # ═══ ACTION: FIX ═══
    elif action == "fix":
        st.markdown("### 🔧 Error Fix Karo")
        st.caption("Error paste karo — AI khud diagnose karega aur fix karega")

        # File selector
        files_list = []
        try:
            idx = v12_load_index()
            files_list = [f for f in idx.get("files", {}).keys() if not v12_is_protected(f)[0]]
        except Exception:
            pass

        ef = st.selectbox("File (optional)", [""] + sorted(files_list), key="v12_fix_file")

        err = st.text_area(
            "Error message:",
            height=150,
            key="v12_fix_err",
            placeholder='Traceback (most recent call last):\n  File "app.py", line 42...',
        )

        c1, c2 = st.columns([3, 1])
        with c1:
            fix_btn = st.button("🩹 Fix Karo", use_container_width=True, type="primary", key="v12_fix_btn")
        with c2:
            if st.button("❌ Cancel", use_container_width=True, key="v12_fix_cancel"):
                st.session_state["v12_action"] = None
                st.rerun()

        if fix_btn and err.strip():
            with st.spinner("🔍 Diagnose + Fix..."):
                res = v12_auto_fix(err, ef or None)
            if res.get("diagnosis"):
                st.info(f"🔍 **Diagnosis:** {res['diagnosis']}")
            for ch in res.get("applied", []):
                st.success(ch["message"])
            for ch in res.get("failed", []):
                st.error(ch["message"])
            if res.get("backup_dir"):
                st.caption(f"💾 Backup: `{res['backup_dir']}`")
            try:
                v12_scan_project()
            except Exception:
                pass

    # ═══ ACTION: HISTORY ═══
    elif action == "history":
        st.markdown("### 📜 History — Kya Kya Hua")

        commits = v12_get_commits()
        if not commits:
            st.info("Abhi tak kuch nahi hua")
        else:
            st.caption(f"Total: {len(commits)} commits")
            for c in reversed(commits[-30:]):
                with st.expander(f"#{c['id']} — {c['description'][:70]}"):
                    st.caption(f"⏰ {c['time']}")
                    st.markdown("**Changes:**")
                    for ch in c.get("changes", []):
                        st.markdown(f"- `{ch.get('action', 'modify')}` — `{ch.get('file', '')}`")
                    if st.button(f"🕰️ Wapas Jao #{c['id']}", key=f"v12_tt_{c['id']}"):
                        ok, msg = v12_time_travel(c["id"])
                        if ok:
                            st.success(msg)
                            try:
                                v12_scan_project()
                            except Exception:
                                pass
                        else:
                            st.error(msg)

    # ═══ ACTION: SYSTEM ═══
    elif action == "system":
        st.markdown("### 🧪 System Health")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧪 Full Test Chalao", use_container_width=True, type="primary", key="v12_test_btn"):
                with st.spinner("Testing..."):
                    results = v12_self_test()
                st.markdown("**Results:**")
                for k, v in results.items():
                    st.markdown(f"{'✅' if v else '❌'} **{k.replace('_', ' ').title()}**")
                if all(results.values()):
                    st.success("🎉 Sab theek hai!")
                else:
                    st.warning("⚠️ Kuch fail")
        with col2:
            if st.button("🔄 Project Rescan", use_container_width=True, key="v12_rescan_btn"):
                with st.spinner("Scanning..."):
                    idx = v12_scan_project()
                st.success(f"✅ Scan complete: {idx['stats']['total_files']} files, {idx['stats']['total_lines']} lines")

        st.divider()

        # Cleanup
        st.markdown("#### 🧹 Cleanup")
        if st.button("Purane backups delete (7 din se purane)", key="v12_cleanup_btn"):
            deleted, msg = v12_cleanup_backups(days=7)
            st.success(msg)

        st.divider()

        # Protected files info
        st.markdown("#### 🛡️ Protected Files (AI kabhi touch nahi karega)")
        with st.expander("Dekho"):
            st.markdown("**Files:**")
            for f in sorted(PROTECTED_FILES):
                st.markdown(f"- 🛡️ `{f}`")
            st.markdown("**Extensions:**")
            for e in sorted(PROTECTED_EXTENSIONS):
                st.markdown(f"- 🛡️ `*{e}`")
            st.markdown("**Folders:**")
            for d in sorted(PROTECTED_DIRS):
                st.markdown(f"- 🛡️ `{d}/`")

        st.divider()

        # Project index details
        st.markdown("#### 📊 Project Index")
        try:
            idx = v12_load_index()
            s = idx.get("stats", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("Files", s.get("total_files", 0))
            c2.metric("Lines", s.get("total_lines", 0))
            c3.metric("Pages", s.get("pages", 0))
            st.caption(f"Last scan: {idx.get('scanned_at', 'N/A')}")
        except Exception as e:
            st.warning(f"Index load fail: {e}")

    # ═══ DEFAULT ═══
    else:
        st.info("👆 Upar 4 buttons mein se ek dabao — kaam shuru karne ke liye")


# ============================================
# CHAT TAB
# ============================================

def _chat_tab(page, gym_stats, role="staff", username="", gym_id=None):
    _init_state()
    role_label = {"admin": "👑 Admin", "owner": "👑 Owner",
                  "staff": "👤 Staff", "auditor": "🔍 Auditor"}.get(role, role)
    st.markdown("### 💬 GymPro AI — " + role_label)

    if role in ["admin", "owner"]:
        chips = ["Aaj ka summary", "Backup karo", "Test karo", "App check", "Reminders"]
    else:
        chips = ["Fee kaise?", "Member kaise?", "Workout plan", "Diet plan"]

    cols = st.columns(4)
    for i, chip in enumerate(chips):
        if cols[i % 4].button(chip, key="chip_" + str(i), use_container_width=True):
            _push_and_respond(chip, page, gym_stats, role=role, username=username, gym_id=gym_id)

    st.divider()
    for msg in st.session_state.get("ai_chat_history", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if st.session_state.get("speak_trigger") and st.session_state.get("auto_speak", False):
        play_tts(st.session_state["speak_trigger"])
        st.session_state["speak_trigger"] = None

    st.divider()
    key = "chat_input_" + str(st.session_state.get('ai_input_counter', 0))
    col1, col2, col3 = st.columns([6, 1, 1])
    user_input = col1.text_input("", key=key, label_visibility="collapsed",
                                 placeholder="Roman Urdu mein likhein...")
    send = col2.button("Send ➤", key="send_chat_btn", type="primary", use_container_width=True)
    clear = col3.button("🗑", key="clear_chat_btn", use_container_width=True)
    if clear:
        st.session_state["ai_chat_history"] = []
        st.session_state["ai_input_counter"] += 1
        st.rerun()
    if send and user_input.strip():
        _push_and_respond(user_input.strip(), page, gym_stats, role=role, username=username, gym_id=gym_id)


# ============================================
# RENDER
# ============================================

def render_staff_ai_coach(username, role="staff", gym_id=None):
    _init_state()
    try:
        from database import get_staff_today_metrics
        m = get_staff_today_metrics(username, gym_id=gym_id)
    except Exception:
        m = {}
    st.markdown("### 📊 " + username + "'s Performance")
    st.metric("Fee Today", "PKR " + str(f"{m.get('fee_total', 0):,.0f}"))


def render(gym_id=None, role=None, username=""):
    _init_state()
    role = role or "staff"
    role_label = {"admin": "👑 Admin", "owner": "👑 Owner",
                  "staff": "👤 Staff", "auditor": "🔍 Auditor"}.get(role, role)

    st.markdown("# 🤖 Super AI Assistant V12 — ULTIMATE")
    st.caption(role_label + " — " + username + " · V12 Super Coder")
    st.divider()

    current_page = st.session_state.get("page", "AI Assistant")
    gym_stats = {}
    try:
        gym_stats = db.get_stats(gym_id)
    except Exception:
        pass

    if role in ("admin", "owner"):
        tabs = st.tabs(["💬 Chat", "🤖 AI Coder V12", "🎬 Video", "🎵 Music"])
        with tabs[0]:
            _chat_tab(current_page, gym_stats, role=role, username=username, gym_id=gym_id)
        with tabs[1]:
            _v12_coder_tab(role, username, gym_id=gym_id)
        with tabs[2]:
            _video_player()
        with tabs[3]:
            _music_player()
    else:
        tabs = st.tabs(["💬 Chat", "🎬 Video", "🎵 Music"])
        with tabs[0]:
            _chat_tab(current_page, gym_stats, role=role, username=username, gym_id=gym_id)
        with tabs[1]:
            _video_player()
        with tabs[2]:
            _music_player()


if __name__ == "__main__":
    render(None, "admin")
