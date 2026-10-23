import streamlit as st
from datetime import date, datetime, timedelta
import io
import os
import re
import requests
import database as db

# ============================================
# YOUTUBE SEARCH FUNCTION
# ============================================

def _fmt_duration(secs) -> str:
    """Convert seconds to mm:ss or hh:mm:ss string."""
    try:
        s = int(secs)
        h, rem = divmod(s, 3600)
        m, sc  = divmod(rem, 60)
        return f"{h}:{m:02d}:{sc:02d}" if h else f"{m}:{sc:02d}"
    except Exception:
        return ""


# Simple in-process cache: {query_key: [results]}
_YT_CACHE: dict = {}


def search_youtube(query: str, max_results: int = 10) -> list:
    """
    Search YouTube using yt-dlp (handles bot detection automatically).
    Falls back to Invidious API, then to direct scraping if both fail.
    Returns list of {id, title, duration, thumb} dicts.
    """
    cache_key = f"{query.strip().lower()}|{max_results}"
    if cache_key in _YT_CACHE:
        return _YT_CACHE[cache_key]

    # ── Strategy 1: yt-dlp (most reliable, handles all bot checks) ─────────
    try:
        from yt_dlp import YoutubeDL
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "socket_timeout": 15,
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        results = []
        for e in (info or {}).get("entries", []):
            vid_id = e.get("id", "")
            if not vid_id:
                continue
            results.append({
                "id":       vid_id,
                "title":    e.get("title", "Unknown"),
                "duration": _fmt_duration(e.get("duration", 0)),
                "thumb":    f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg",
            })
        if results:
            _YT_CACHE[cache_key] = results
            return results
    except Exception as e:
        print(f"[yt-dlp] search failed: {e}")

    # ── Strategy 2: Invidious public API (no key needed) ───────────────────
    invidious_instances = [
        "https://invidious.io",
        "https://inv.riverside.rocks",
        "https://invidious.privacyredirect.com",
        "https://yt.cdaut.de",
    ]
    for base in invidious_instances:
        try:
            r = requests.get(
                f"{base}/api/v1/search",
                params={"q": query, "type": "video", "page": 1},
                timeout=8,
                headers={"User-Agent": "GymPro/1.0"},
            )
            if r.status_code == 200:
                data = r.json()
                results = []
                for item in data[:max_results]:
                    vid_id = item.get("videoId", "")
                    if not vid_id:
                        continue
                    thumbs = item.get("videoThumbnails", [])
                    thumb  = next((t["url"] for t in thumbs if "medium" in t.get("quality","").lower()),
                                  f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg")
                    results.append({
                        "id":       vid_id,
                        "title":    item.get("title", "Unknown"),
                        "duration": _fmt_duration(item.get("lengthSeconds", 0)),
                        "thumb":    thumb,
                    })
                if results:
                    _YT_CACHE[cache_key] = results
                    return results
        except Exception:
            continue

    # ── Strategy 3: Direct scraping (last resort) ──────────────────────────
    try:
        import json as _json
        url  = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        resp = requests.get(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }, timeout=12)
        m = re.search(r'var ytInitialData\s*=\s*(\{.*?\});\s*</script>', resp.text, re.DOTALL)
        if m:
            section = (_json.loads(m.group(1))
                       .get("contents", {})
                       .get("twoColumnSearchResultsRenderer", {})
                       .get("primaryContents", {})
                       .get("sectionListRenderer", {})
                       .get("contents", [{}])[0]
                       .get("itemSectionRenderer", {})
                       .get("contents", []))
            results = []
            for item in section:
                vr = item.get("videoRenderer", {})
                vid_id = vr.get("videoId", "")
                if not vid_id:
                    continue
                title_runs = vr.get("title", {}).get("runs", [])
                title = title_runs[0].get("text", "Unknown") if title_runs else "Unknown"
                dur   = (vr.get("lengthText", {}).get("simpleText", ""))
                results.append({"id": vid_id, "title": title, "duration": dur,
                                 "thumb": f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"})
            if results:
                _YT_CACHE[cache_key] = results[:max_results]
                return results[:max_results]

        ids = list(dict.fromkeys(re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', resp.text)))
        results = [{"id": v, "title": f"Track {i+1}", "duration": "",
                    "thumb": f"https://img.youtube.com/vi/{v}/mqdefault.jpg"}
                   for i, v in enumerate(ids[:max_results])]
        if results:
            _YT_CACHE[cache_key] = results
        return results
    except Exception as e:
        print(f"[scrape] YouTube search failed: {e}")
        return []

def extract_youtube_id(url_or_id: str) -> str:
    if not url_or_id:
        return ""
    url_or_id = url_or_id.strip()
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url_or_id)
    if match:
        return match.group(1)
    if len(url_or_id) == 11:
        return url_or_id
    return ""

# ============================================
# TEXT-TO-SPEECH (Google TTS)
# ============================================

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# ============================================
# SPEECH-TO-TEXT (SpeechRecognition)
# ============================================

try:
    import speech_recognition as sr
    HAS_SPEECH = True
except ImportError:
    HAS_SPEECH = False

# ============================================
# PAGE CONTEXT
# ============================================

PAGE_CONTEXT = {
    "Dashboard": "Showing gym overview: member counts, revenue, expenses, recent activity.",
    "Gym Setup": "Managing gym locations — add, edit, delete gyms with address and contact info.",
    "Members": "Managing members: registration, photo upload, serial numbers, edit/delete.",
    "Membership Cards": "Viewing and printing digital membership cards for members.",
    "Attendance": "Tracking daily attendance: marking present/absent, viewing history.",
    "Progress Tracker": "Logging member body measurements and fitness progress over time.",
    "Fee Collection": "Recording and tracking monthly fee payments from members.",
    "Expenses": "Logging gym expenses by category: equipment, maintenance, utilities, etc.",
    "Inventory": "Managing gym equipment and supply stock levels.",
    "Reports": "Generating financial and membership analytics reports.",
    "Message Center": "Sending announcements and messages to members.",
    "WhatsApp": "Sending WhatsApp messages to members via link/template.",
    "Complaints": "Logging and resolving member complaints and feedback.",
    "Audit": "Reviewing financial records and audit logs.",
    "User Management": "Managing staff user accounts, roles, and passwords.",
    "AI Assistant": "AI-powered assistant for gym management guidance.",
}

SYSTEM_PROMPT = (
    "You are GymPro AI — a highly intelligent, real-time gym management assistant embedded directly inside GymPro app. "
    "You have access to LIVE gym data including member counts, fees, overdue payments, staff activity, and fraud alerts.\n\n"
    "YOUR PERSONALITY:\n"
    "- Speak like a smart, caring senior colleague — not a robot\n"
    "- Roman Urdu mein baat karo jab user Roman Urdu mein likhe\n"
    "- Be direct, specific, and actionable — no vague answers\n"
    "- Give exact numbers from the live data provided\n\n"
    "FOR ADMIN: Give full business intelligence — revenue trends, fraud patterns, staff performance, overdue recovery\n"
    "FOR STAFF: Give step-by-step guidance — 'ab yeh karo, phir yeh karo' format\n\n"
    "Always use the LIVE DATA provided in context. Never say 'I don't have access to data' — you do."
)

# ============================================
# SESSION STATE INIT
# ============================================

def _init_state():
    defaults = {
        "ai_chat_history": [],
        "ai_input_counter": 0,
        "ai_last_question": "",
        "speak_trigger": None,
        "auto_speak": False,
        # Music
        "music_results": [],        # list of {id, title, duration, thumb}
        "music_search": "",
        "active_music": None,       # current video_id string
        "active_music_title": "",
        "music_queue": [],          # full result list for prev/next
        "music_queue_idx": 0,
        # Video
        "video_results": [],        # list of {id, title, duration, thumb}
        "video_search": "",
        "active_video": None,
        "active_video_title": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ============================================
# HELPER FUNCTIONS
# ============================================

def is_roman_urdu(text: str) -> bool:
    roman_urdu_words = ["hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "mai", "ho", "hum", "ap", "tum", "wo", "ye", "kya", "kyu", "kaise", "kahan", "kab", "kitna", "kitne", "aap", "mujhe", "tujhe", "usne", "unhon"]
    words = text.lower().split()
    if not words:
        return False
    urdu_count = sum(1 for w in words if w in roman_urdu_words)
    return urdu_count / len(words) > 0.2

def detect_language(text: str) -> str:
    if any(ord(char) in range(0x0600, 0x06FF) for char in text):
        return "urdu_script"
    if is_roman_urdu(text):
        return "roman_urdu"
    return "english"

def play_tts(text: str):
    if not HAS_GTTS:
        return
    try:
        lang_code = "ur" if detect_language(text) in ["urdu_script", "roman_urdu"] else "en"
        clean_text = re.sub(r'[*_`#\-\n]', ' ', text)[:500]
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3", autoplay=True)
    except:
        pass

def transcribe_mic(audio_bytes: bytes) -> str:
    if not HAS_SPEECH:
        return None
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio, language="ur-PK")
                return text
            except:
                try:
                    text = recognizer.recognize_google(audio, language="en-US")
                    return text
                except:
                    return None
    except:
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

# ============================================
# AI RESPONSE ENGINE
# ============================================

def _get_live_context(gym_id=None, role="staff", username=""):
    """Build rich real-time data string to inject into every AI call."""
    lines = []
    try:
        stats = db.get_stats(gym_id)
        lines.append(
            f"MEMBERS: total={stats.get('total_members',0)}, active={stats.get('active_members',0)}"
        )
        rev = stats.get('month_revenue', 0)
        exp = stats.get('month_expenses', 0)
        lines.append(
            f"FINANCIALS (this month): revenue=PKR {rev:,.0f}, expenses=PKR {exp:,.0f}, net=PKR {rev-exp:,.0f}"
        )
    except Exception:
        pass
    try:
        today_total, today_count, _ = db.get_daily_fee_summary(gym_id=gym_id)
        lines.append(f"TODAY'S FEE COLLECTIONS: PKR {today_total:,.0f} in {today_count} receipts")
    except Exception:
        pass
    try:
        alerts = db.check_fraud_alerts(gym_id=gym_id)
        if alerts:
            critical = [a for a in alerts if a["severity"] == "critical"]
            lines.append(
                f"FRAUD ALERTS TODAY: {len(alerts)} alerts, {len(critical)} critical. "
                + " | ".join(a["title"] for a in alerts[:3])
            )
        else:
            lines.append("FRAUD ALERTS TODAY: none — all clear")
    except Exception:
        pass
    try:
        shifts = db.get_today_shifts(gym_id=gym_id)
        open_s  = [s for s in shifts if s.status == "open"]
        flagged = [s for s in shifts if s.status == "flagged"]
        lines.append(f"SHIFTS TODAY: {len(shifts)} total, {len(open_s)} open, {len(flagged)} flagged")
    except Exception:
        pass
    try:
        from datetime import date as _date, timedelta
        overdue_logs = db.get_activity_logs(gym_id=gym_id, action="FEE_DELETED", limit=50,
                                            date_from=_date.today()-timedelta(days=7))
        if overdue_logs:
            lines.append(f"FEE DELETIONS (last 7 days): {len(overdue_logs)} records deleted")
    except Exception:
        pass
    lines.append(f"LOGGED IN USER: {username or 'unknown'}, ROLE: {role}")
    return "\n".join(lines)


def _build_system_content(page: str, gym_stats: dict, role="staff", username="", gym_id=None) -> str:
    page_ctx = PAGE_CONTEXT.get(page, "")
    live_ctx = _get_live_context(gym_id=gym_id, role=role, username=username)
    role_instr = (
        "This user is an ADMIN/OWNER — give full business intelligence, proactively mention risks, "
        "fraud alerts, overdue recovery, and staff performance. Be a trusted business advisor."
        if role in ["admin", "owner"] else
        "This user is STAFF — guide step by step in simple Roman Urdu. "
        "If they seem confused, break instructions into numbered steps like 1. pehle yeh karo 2. phir yeh."
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== LIVE GYM DATA ===\n{live_ctx}\n\n"
        f"=== CURRENT PAGE ===\n{page}: {page_ctx}\n\n"
        f"=== ROLE INSTRUCTION ===\n{role_instr}"
    )

def _rule_based_response(user_msg: str, page: str, gym_stats: dict) -> str:
    q = user_msg.lower()
    
    if any(w in q for w in ["salam", "hello", "hi", "hey", "assalam", "adaab"]):
        return "👋 **Assalam-u-Alaikum!** Main GymPro AI hoon. Aap **" + page + "** page par hain. Koi sawal poochiye! Members, fees, attendance, workout, diet — sab mein madad kar sakta hoon."
    
    if any(w in q for w in ["member", "register", "serial", "enroll", "new member"]):
        return "📝 **Member Register:** Members page par jao → 'Register Member' tab → form fill karo → photo upload karo. Serial number (PF-00001) automatically generate hoga."
    
    if any(w in q for w in ["fee", "payment", "collect", "paisa", "money", "charges"]):
        return f"💰 **Fees Collection:** Is mahine ka revenue: **PKR {gym_stats.get('month_revenue', 0):,.0f}**. Har member ki payment record karo."
    
    if any(w in q for w in ["expense", "cost", "spend", "kharch", "expenditure"]):
        return f"📊 **Expenses:** Is mahine total expenses: **PKR {gym_stats.get('month_expenses', 0):,.0f}**. Categories: Equipment, Maintenance, Utilities."
    
    if any(w in q for w in ["attendance", "present", "absent", "aaye", "haazri"]):
        return "📋 **Attendance:** Rozana haazri mark karo. 3+ din ghaib members alert hote hain."
    
    if any(w in q for w in ["diet", "khana", "protein", "nutrition", "food"]):
        return """🥗 **Diet Plan:**
• Subah: 2 ande + oats + milk + banana
• Dopahar: Chicken 200g + brown rice + salad
• Shaam: Protein shake + dry fruits
• Raat: Fish/Chicken 150g + vegetables
• Paani: 8-10 glass rozana
❌ Avoid: Junk food, sugar, soft drinks"""
    
    if any(w in q for w in ["workout", "exercise", "kasrat", "routine", "gym plan"]):
        return """🏋️ **Weekly Workout:**
• Mon: Chest + Triceps
• Tue: Back + Biceps
• Wed: Legs + Shoulders
• Thu: Rest / Cardio
• Fri: Full Body
• Sat: Abs + Core
• Sun: Active Rest
🔥 Warm-up 10 min mandatory!"""
    
    if any(w in q for w in ["inventory", "stock", "equipment"]):
        return "📦 **Inventory:** Equipment aur supplies track karo. Low-stock alerts sidebar mein aate hain."
    
    if any(w in q for w in ["report", "analytics", "chart", "statistics"]):
        total = gym_stats.get("total_members", "?")
        active = gym_stats.get("active_members", "?")
        return f"📈 **Reports:** Total: {total}, Active: {active}, Revenue: PKR {gym_stats.get('month_revenue', 0):,.0f}"
    
    if any(w in q for w in ["gym", "setup", "add gym", "branch"]):
        return "🏢 **Gym Setup:** Nayi gym add karo. Har gym ka alag member pool aur financials."
    
    if any(w in q for w in ["help", "madad", "support", "kya", "batao"]):
        return f"""🤖 **Main yeh topics mein help kar sakta hoon:**
📊 Members, Fees, Attendance, Expenses
📦 Inventory, Reports, Gym Setup
🏋️ Workout Plans, Diet Plans
💬 Complaints, Messages

Aap **{page}** page par hain. Poochiye!"""
    
    return f"🤔 Samajh nahi aaya. Aap **{page}** page par hain. Members, fees, attendance, workout, diet — kisi bhi topic par poochiye! 😊"

def get_ai_response(messages: list, page: str, gym_stats: dict,
                    role="staff", username="", gym_id=None) -> str:
    system_content = _build_system_content(page, gym_stats, role=role, username=username, gym_id=gym_id)
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            import requests as req
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_content}] + messages,
                "max_tokens": 800,
                "temperature": 0.5,
            }
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=25,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
    return _rule_based_response(messages[-1]["content"] if messages else "", page, gym_stats)


def _api_messages() -> list:
    return [
        {"role": "assistant" if m["role"] == "assistant" else "user", "content": m["content"]}
        for m in st.session_state.get("ai_chat_history", [])[-20:]
    ]


def _push_and_respond(user_text: str, page: str, gym_stats: dict,
                      role="staff", username="", gym_id=None):
    if st.session_state.get("ai_last_question", "") == user_text:
        st.warning("⚠️ Yeh sawaal already pooch chuke ho!")
        return
    st.session_state["ai_last_question"] = user_text
    st.session_state["ai_chat_history"].append({"role": "user", "content": user_text})
    with st.spinner("🤔 Soch raha hoon..."):
        reply = get_ai_response(_api_messages(), page, gym_stats,
                                role=role, username=username, gym_id=gym_id)
    st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
    
    if st.session_state.get("auto_speak", True):
        st.session_state["speak_trigger"] = reply
    
    st.session_state["ai_input_counter"] += 1
    st.rerun()

# ============================================
# SIDEBAR WIDGET
# ============================================

def render_sidebar_widget(current_page: str, gym_id=None, role="staff", username=""):
    _init_state()
    gym_stats = {}
    try:
        gym_stats = db.get_stats(gym_id)
    except Exception:
        pass

    role_label = {"admin": "👑 Admin", "owner": "👑 Owner", "staff": "👤 Staff", "auditor": "🔍 Auditor"}.get(role, role)
    role_color = "#FBBF24" if role in ["admin", "owner"] else "#60A5FA"

    with st.expander(f"🤖 AI Assistant — {role_label}", expanded=False):

        # Proactive snapshot for admin
        if role in ["admin", "owner"]:
            try:
                alerts = db.check_fraud_alerts(gym_id=gym_id)
                today_total, today_count, _ = db.get_daily_fee_summary(gym_id=gym_id)
                alert_badge = f"🚨 {len(alerts)} alert{'s' if len(alerts)!=1 else ''}" if alerts else "✅ Sab theek"
                st.markdown(f"""
                <div style="background:#0F172A;border:1px solid {role_color};border-radius:8px;
                            padding:0.5rem 0.75rem;margin-bottom:0.5rem;font-size:0.78rem;">
                    <span style="color:{role_color};font-weight:700;">{role_label}</span>
                    <span style="color:#94A3B8;"> · </span>
                    <span style="color:#34D399;">💰 PKR {today_total:,.0f} aaj</span>
                    <span style="color:#94A3B8;"> · </span>
                    <span style="color:{'#F87171' if alerts else '#34D399'};">{alert_badge}</span>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                pass

        # Quick chips — role specific
        if role in ["admin", "owner"]:
            chips = ["Aaj ka summary?", "Koi fraud alert?", "Overdue members?", "Staff performance?"]
        else:
            chips = ["Fee kaise collect karein?", "Member kaise register karein?", "Shift kaise kholein?"]

        chip_cols = st.columns(2)
        for i, chip in enumerate(chips[:4]):
            if chip_cols[i % 2].button(chip, key=f"sb_chip_{i}", use_container_width=True):
                _push_and_respond(chip, current_page, gym_stats, role=role, username=username, gym_id=gym_id)

        # Chat history preview
        history = st.session_state.get("ai_chat_history", [])
        if history:
            html = '<div style="max-height:180px;overflow-y:auto;font-size:0.78rem;margin:0.3rem 0;">'
            for msg in history[-6:]:
                bg  = "#1E3A5F" if msg["role"] == "user" else "#1a1a3a"
                ico = "👤" if msg["role"] == "user" else "🤖"
                txt = msg["content"][:100] + ("…" if len(msg["content"]) > 100 else "")
                html += f'<div style="background:{bg};padding:4px 8px;margin:2px 0;border-radius:5px;">{ico} {txt}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption(f"📍 {current_page} · Kuch bhi poochiye!")

        key = f"sb_chat_{st.session_state.get('ai_input_counter', 0)}"
        user_input = st.text_input("", placeholder="Roman Urdu mein likhein...", key=key,
                                   label_visibility="collapsed")
        col1, col2 = st.columns([3, 1])
        send  = col1.button("Send ➤", key="sb_send_btn",  type="primary", use_container_width=True)
        clear = col2.button("🗑",     key="sb_clear_btn", use_container_width=True)

        if clear:
            st.session_state["ai_chat_history"] = []
            st.session_state["ai_last_question"] = ""
            st.session_state["ai_input_counter"] += 1
            st.rerun()

        if send and user_input.strip():
            _push_and_respond(user_input.strip(), current_page, gym_stats,
                              role=role, username=username, gym_id=gym_id)

        auto = st.toggle("🔊 Voice", value=st.session_state.get("auto_speak", False), key="sb_voice_toggle")
        st.session_state["auto_speak"] = auto

        if st.session_state.get("speak_trigger") and st.session_state.get("auto_speak", False):
            play_tts(st.session_state["speak_trigger"])
            st.session_state["speak_trigger"] = None

# ============================================
# 🎵 MUSIC PLAYER - SEARCH ANY SONG
# ============================================

_MUSIC_GENRES = [
    ("🏋️ Workout", "gym workout motivation music"),
    ("🇵🇰 Pakistani", "Pakistani pop songs 2024"),
    ("🎬 Bollywood", "Bollywood hits 2024"),
    ("⚡ EDM", "EDM workout gym music"),
    ("☕ Lofi", "lofi hip hop study chill"),
    ("🎤 Hip-Hop", "hip hop rap workout"),
    ("🎸 Punjabi", "Punjabi songs 2024"),
    ("🕌 Naat", "naat sharif new 2024"),
]

def _music_player():
    _init_state()

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);border-radius:16px;
                padding:1.2rem 1.5rem;margin-bottom:1rem;">
        <h2 style="margin:0;font-size:1.5rem;">🎵 Music Player</h2>
        <p style="margin:0;color:#94A3B8;font-size:0.9rem;">
            Search any song • Queue navigation • Continues across pages
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Now playing bar (always visible at top if something is playing)
    vid   = st.session_state.get("active_music")
    title = st.session_state.get("active_music_title", "")
    queue = st.session_state.get("music_queue", [])
    idx   = st.session_state.get("music_queue_idx", 0)

    if vid:
        st.markdown(f"""
        <div style="background:linear-gradient(90deg,#1E3A5F,#1E1B4B);border:1px solid #3B82F6;
                    border-radius:12px;padding:0.8rem 1rem;margin-bottom:1rem;
                    display:flex;align-items:center;gap:0.6rem;">
            <span style="font-size:1.4rem;">🎵</span>
            <div>
                <div style="color:#60A5FA;font-weight:700;font-size:0.85rem;">NOW PLAYING</div>
                <div style="color:var(--gp-text);font-size:0.95rem;font-weight:600;">{title[:70]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Player embed — stays alive across page changes via persistent bar
        st.markdown(f"""
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;
                    border-radius:12px;background:#000;box-shadow:0 4px 20px rgba(0,0,0,0.5);">
            <iframe style="position:absolute;top:0;left:0;width:100%;height:100%;"
                src="https://www.youtube.com/embed/{vid}?autoplay=1&rel=0&modestbranding=1"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("⏮ Prev", key="music_prev", use_container_width=True):
                if queue and idx > 0:
                    new_idx = idx - 1
                    st.session_state["music_queue_idx"]   = new_idx
                    st.session_state["active_music"]      = queue[new_idx]["id"]
                    st.session_state["active_music_title"] = queue[new_idx]["title"]
                    st.rerun()
        with c2:
            if st.button("⏭ Next", key="music_next", use_container_width=True):
                if queue and idx < len(queue) - 1:
                    new_idx = idx + 1
                    st.session_state["music_queue_idx"]   = new_idx
                    st.session_state["active_music"]      = queue[new_idx]["id"]
                    st.session_state["active_music_title"] = queue[new_idx]["title"]
                    st.rerun()
        with c3:
            if queue:
                st.caption(f"Track {idx+1}/{len(queue)}")
        with c4:
            if st.button("⏹ Stop", key="music_stop", use_container_width=True):
                st.session_state["active_music"]      = None
                st.session_state["active_music_title"] = ""
                st.rerun()

        st.divider()

    # Genre presets
    st.markdown("#### 🎛️ Genre / Mood — Ek Click Mein")
    g_cols = st.columns(4)
    for i, (label, query) in enumerate(_MUSIC_GENRES):
        if g_cols[i % 4].button(label, key=f"genre_{i}", use_container_width=True):
            with st.spinner(f"🎵 {label} load ho raha hai..."):
                res = search_youtube(query, max_results=10)
            if res:
                st.session_state["music_results"]     = res
                st.session_state["music_search"]      = label
                st.session_state["music_queue"]       = res
                st.session_state["music_queue_idx"]   = 0
                st.session_state["active_music"]      = res[0]["id"]
                st.session_state["active_music_title"] = res[0]["title"]
                st.rerun()
            else:
                st.error("Nahi mila, dobara try karein")

    st.divider()

    # Custom search
    st.markdown("#### 🔍 Custom Search")
    s1, s2 = st.columns([4, 1])
    with s1:
        query_input = st.text_input("", placeholder="e.g. Atif Aslam, Nusrat Fateh Ali Khan, gym beats...",
                                    key="music_search_input", label_visibility="collapsed")
    with s2:
        do_search = st.button("Search 🔍", key="music_search_btn", type="primary", use_container_width=True)

    if do_search and query_input.strip():
        with st.spinner(f"Searching '{query_input}'..."):
            res = search_youtube(query_input.strip(), max_results=10)
        if res:
            st.session_state["music_results"] = res
            st.session_state["music_search"]  = query_input.strip()
            st.session_state["music_queue"]   = res
            st.session_state["music_queue_idx"] = 0
            st.rerun()
        else:
            st.error("❌ Koi result nahi mila. Aur kuch try karein.")

    # Results grid
    results = st.session_state.get("music_results", [])
    if results:
        search_label = st.session_state.get("music_search", "")
        st.success(f"🎵 **{len(results)} tracks** — *{search_label}*")
        cols = st.columns(2)
        for i, track in enumerate(results):
            with cols[i % 2]:
                is_active = (track["id"] == st.session_state.get("active_music"))
                border_color = "#3B82F6" if is_active else "#1E293B"
                st.markdown(f"""
                <div style="border:2px solid {border_color};border-radius:10px;overflow:hidden;
                            background:#0F172A;margin-bottom:0.5rem;">
                    <img src="{track['thumb']}" style="width:100%;height:120px;object-fit:cover;"
                         onerror="this.src='https://img.youtube.com/vi/{track['id']}/default.jpg'"/>
                    <div style="padding:0.4rem 0.6rem;">
                        <div style="font-size:0.78rem;color:#E2E8F0;font-weight:600;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
                             title="{track['title']}">{track['title'][:55]}</div>
                        <div style="font-size:0.7rem;color:#64748B;">{track.get('duration','')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                lbl = "▶️ Playing" if is_active else "▶️ Play"
                if st.button(lbl, key=f"mplay_{i}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state["active_music"]      = track["id"]
                    st.session_state["active_music_title"] = track["title"]
                    st.session_state["music_queue"]       = results
                    st.session_state["music_queue_idx"]   = i
                    st.rerun()

        if st.button("🗑️ Clear Results", key="music_clear", use_container_width=True):
            st.session_state["music_results"] = []
            st.session_state["music_search"]  = ""
            st.rerun()

# ============================================
# 🎬 VIDEO PLAYER - SEARCH ANY VIDEO
# ============================================

_VIDEO_CATEGORIES = [
    ("💪 Chest",         "best chest workout gym"),
    ("🦵 Legs",          "leg workout gym training"),
    ("🔙 Back",          "back workout gym training"),
    ("🏃 Cardio",        "cardio HIIT workout"),
    ("🧘 Yoga",          "yoga for beginners flexibility"),
    ("⚡ HIIT",          "HIIT fat burn workout"),
    ("🥗 Diet Tips",     "gym diet plan for muscle gain"),
    ("🏋️ Motivation",   "gym motivation bodybuilding"),
    ("💊 Supplements",   "best supplements for gym beginners"),
    ("🧠 Mind & Body",   "mindfulness meditation stress relief"),
    ("🇵🇰 Desi Fitness", "Pakistani fitness training urdu"),
    ("🤸 Flexibility",   "stretching flexibility full body"),
]

def _video_player():
    _init_state()

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0F172A,#1A1037);border-radius:16px;
                padding:1.2rem 1.5rem;margin-bottom:1rem;">
        <h2 style="margin:0;font-size:1.5rem;">🎬 Video Player</h2>
        <p style="margin:0;color:#94A3B8;font-size:0.9rem;">
            Workout tutorials • Exercise guides • Nutrition tips
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Active player — always at top when something is playing
    active_vid   = st.session_state.get("active_video")
    active_title = st.session_state.get("active_video_title", "")

    if active_vid:
        st.markdown(f"""
        <div style="background:linear-gradient(90deg,#1C1937,#0F172A);border:1px solid #8B5CF6;
                    border-radius:12px;padding:0.7rem 1rem;margin-bottom:0.8rem;">
            <span style="color:#A78BFA;font-weight:700;font-size:0.8rem;">▶ NOW PLAYING</span><br/>
            <span style="color:var(--gp-text);font-size:0.95rem;font-weight:600;">{active_title[:80]}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;
                    border-radius:14px;background:#000;box-shadow:0 8px 32px rgba(0,0,0,0.6);
                    margin-bottom:0.8rem;">
            <iframe style="position:absolute;top:0;left:0;width:100%;height:100%;"
                src="https://www.youtube.com/embed/{active_vid}?autoplay=1&rel=0&modestbranding=1"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
            </iframe>
        </div>
        """, unsafe_allow_html=True)

        cv1, cv2 = st.columns([4, 1])
        with cv2:
            if st.button("⏹ Stop", key="video_stop_top", use_container_width=True):
                st.session_state["active_video"]       = None
                st.session_state["active_video_title"] = ""
                st.rerun()
        st.divider()

    # Category presets
    st.markdown("#### 🏷️ Categories — Ek Click Mein")
    cat_cols = st.columns(4)
    for i, (label, query) in enumerate(_VIDEO_CATEGORIES):
        if cat_cols[i % 4].button(label, key=f"vcat_{i}", use_container_width=True):
            with st.spinner(f"🔍 {label} videos dhundh raha hoon..."):
                res = search_youtube(query, max_results=9)
            if res:
                st.session_state["video_results"]      = res
                st.session_state["video_search"]       = label
                st.rerun()
            else:
                st.error("Nahi mila, dobara try karein")

    st.divider()

    # Custom search
    st.markdown("#### 🔍 Custom Search")
    vs1, vs2 = st.columns([4, 1])
    with vs1:
        v_query = st.text_input("", placeholder="e.g. Shoulder workout, Weight loss tips, Protein diet...",
                                key="video_search_input", label_visibility="collapsed")
    with vs2:
        do_vsearch = st.button("Search 🔍", key="video_search_btn", type="primary", use_container_width=True)

    if do_vsearch and v_query.strip():
        with st.spinner(f"Searching '{v_query}'..."):
            res = search_youtube(v_query.strip(), max_results=9)
        if res:
            st.session_state["video_results"] = res
            st.session_state["video_search"]  = v_query.strip()
            st.rerun()
        else:
            st.error("❌ Koi video nahi mila. Kuch aur try karein.")

    # Results grid — 3 columns with titles
    results = st.session_state.get("video_results", [])
    if results:
        search_label = st.session_state.get("video_search", "")
        st.success(f"📹 **{len(results)} videos** — *{search_label}*")
        cols3 = st.columns(3)
        for i, track in enumerate(results):
            with cols3[i % 3]:
                is_active = (track["id"] == active_vid)
                border_col = "#8B5CF6" if is_active else "#1E293B"
                st.markdown(f"""
                <div style="border:2px solid {border_col};border-radius:10px;overflow:hidden;
                            background:#0F172A;margin-bottom:0.5rem;">
                    <img src="{track['thumb']}" style="width:100%;height:110px;object-fit:cover;"
                         onerror="this.src='https://img.youtube.com/vi/{track['id']}/default.jpg'"/>
                    <div style="padding:0.4rem 0.6rem;">
                        <div style="font-size:0.74rem;color:#E2E8F0;font-weight:600;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
                             title="{track['title']}">{track['title'][:50]}</div>
                        <div style="font-size:0.68rem;color:#64748B;">{track.get('duration','')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                lbl = "▶️ Playing" if is_active else "▶️ Play"
                if st.button(lbl, key=f"vplay_{i}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state["active_video"]       = track["id"]
                    st.session_state["active_video_title"] = track["title"]
                    st.rerun()

        if st.button("🗑️ Clear Results", key="video_clear", use_container_width=True):
            st.session_state["video_results"] = []
            st.session_state["video_search"]  = ""
            st.rerun()


# ============================================
# 🤖 STAFF AI COACH — Personal Dashboard Widget
# ============================================

def _score_staff(m: dict) -> tuple[int, str, str]:
    """
    Compute a 0-100 performance score and a grade.
    Returns (score, grade, color).
    """
    score = 50  # baseline

    # Shift opened today?
    if m["shift_open"]:
        score += 10
    elif m["shifts_today"] > 0:
        score += 5   # opened but already closed — still counts
    else:
        score -= 15  # no shift at all

    # Fees collected
    if m["fee_count"] >= 5:
        score += 15
    elif m["fee_count"] >= 2:
        score += 8
    elif m["fee_count"] == 1:
        score += 3

    # Attendance marking
    total = m["total_active_members"] or 1
    att_pct = m["att_count"] / total
    if att_pct >= 0.8:
        score += 20
    elif att_pct >= 0.4:
        score += 10
    elif att_pct > 0:
        score += 4

    # Deletions are bad
    score -= m["deletions_today"] * 10

    # New members registered
    score += m["new_members_today"] * 5

    score = max(0, min(100, score))

    if score >= 80:
        return score, "⭐ Excellent", "#22C55E"
    elif score >= 60:
        return score, "✅ Good",     "#3B82F6"
    elif score >= 40:
        return score, "⚠️ Average",  "#F59E0B"
    else:
        return score, "❌ Poor",     "#EF4444"


def _build_coach_prompt(username: str, m: dict, score: int, grade: str) -> str:
    now_hour = datetime.now().hour
    time_of_day = "subah" if now_hour < 12 else ("dopahar" if now_hour < 17 else "shaam")
    att_pct = int((m["att_count"] / max(m["total_active_members"], 1)) * 100)

    return f"""You are GymPro AI Coach. Write a SHORT (max 160 words), personal performance message for staff member "{username}" in Roman Urdu (with some English words fine).

TODAY'S METRICS ({time_of_day}):
- Performance Score: {score}/100 — {grade}
- Fees Collected: PKR {m['fee_total']:,.0f} ({m['fee_count']} receipts)
- Member Attendance Marked: {m['att_count']} out of {m['total_active_members']} ({att_pct}%)
- Shift: {"✅ OPEN since " + str(m['shift_opened_at']) if m['shift_open'] else ("✅ Completed today" if m['shifts_today'] > 0 else "❌ NOT STARTED — no shift opened!")}
- Fee Deletions Today: {m['deletions_today']} {"⚠️ SUSPICIOUS!" if m['deletions_today'] > 0 else "✅ none"}
- New Members Registered: {m['new_members_today']}
- Total Activities: {m['activity_count']}

TONE RULES — follow exactly:
- Score ≥ 80 → Start with STRONG shahbashi: "Shahbash {username}! Zabardast kaam!" — then praise specifically what was done well
- Score 60-79 → Positive but point out 1-2 things to improve
- Score 40-59 → Motivating but CLEAR about what's missing, give specific numbered steps
- Score < 40 → Firm, caring, clear about problems + exact steps to fix them RIGHT NOW
- If no shift → "Pehle SHIFT kholo: Fee Collection page → Shift Management tab → 'Open Shift'"
- If att_count == 0 and total_active > 0 → "ZARURI: Attendance page par jao, {m['total_active_members']} members ki attendance abhi mark karo!"
- If deletions > 0 → STERN warning about fee deletions — "har deletion record hota hai, admin dekhta hai"
- End with 2-3 numbered ACTION ITEMS for next 1 hour

Keep it punchy and real. Not corporate speak. Like a caring senior colleague."""


def render_staff_ai_coach(username: str, role: str = "staff", gym_id=None):
    """
    Personalized AI performance coach for staff — shown on their dashboard.
    Evaluates today's work, gives praise or advice, lists pending tasks.
    """
    _init_state()

    m = {}
    try:
        m = db.get_staff_today_metrics(username, gym_id=gym_id)
    except Exception:
        pass

    score, grade, grade_color = _score_staff(m)

    # ── Task checklist ──────────────────────────────────────────────────────
    tasks = []
    if not m.get("shift_open") and not m.get("shifts_today", 0):
        tasks.append(("❌", "Shift abhi tak nahi khuli", "Fee Collection → Shift Management", "critical"))
    else:
        tasks.append(("✅", "Shift khuli hai", f"Since {m.get('shift_opened_at','?')}", "ok"))

    att_pct = int((m.get("att_count", 0) / max(m.get("total_active_members", 1), 1)) * 100)
    if att_pct < 50 and m.get("total_active_members", 0) > 0:
        tasks.append(("⚠️", f"Attendance sirf {att_pct}% — {m.get('att_count',0)}/{m.get('total_active_members',0)} members",
                       "Attendance page → mark karo", "warn"))
    elif att_pct >= 80:
        tasks.append(("✅", f"Attendance {att_pct}% complete", f"{m.get('att_count',0)} members marked", "ok"))
    else:
        tasks.append(("🔶", f"Attendance {att_pct}% — thori aur baqi hai",
                       "Attendance page mein baki members", "warn"))

    if m.get("fee_count", 0) == 0:
        tasks.append(("❌", "Aaj abhi koi fee collect nahi hui", "Fee Collection → collect karo", "critical"))
    else:
        tasks.append(("✅", f"PKR {m.get('fee_total',0):,.0f} collect kiya ({m.get('fee_count',0)} receipts)", "", "ok"))

    if m.get("deletions_today", 0) > 0:
        tasks.append(("🚨", f"{m['deletions_today']} fee deletion(s) aaj! Admin ko pata hai.", "Explain karo agar mistake thi", "critical"))

    # ── Score ring HTML ─────────────────────────────────────────────────────
    ring_color = grade_color
    score_html = f"""
<div style="display:flex;align-items:center;gap:1.2rem;padding:1rem 1.25rem;
            background:linear-gradient(135deg,#0F172A,#1E1B4B);
            border:2px solid {ring_color};border-radius:14px;margin-bottom:0.8rem;">
  <div style="position:relative;width:72px;height:72px;flex-shrink:0;">
    <svg width="72" height="72" viewBox="0 0 72 72">
      <circle cx="36" cy="36" r="30" fill="none" stroke="#1E293B" stroke-width="8"/>
      <circle cx="36" cy="36" r="30" fill="none" stroke="{ring_color}" stroke-width="8"
        stroke-dasharray="{int(score*1.885)} 188.5"
        stroke-dashoffset="47" stroke-linecap="round" transform="rotate(-90 36 36)"/>
    </svg>
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                text-align:center;line-height:1;">
      <div style="font-size:1.1rem;font-weight:800;color:{ring_color};">{score}</div>
      <div style="font-size:0.5rem;color:#94A3B8;">/ 100</div>
    </div>
  </div>
  <div style="flex:1;">
    <div style="font-size:1rem;font-weight:700;color:{ring_color};">{grade}</div>
    <div style="font-size:0.85rem;color:var(--gp-text);font-weight:600;margin-top:0.2rem;">
      {username}'s Performance — Aaj
    </div>
    <div style="font-size:0.75rem;color:#94A3B8;margin-top:0.15rem;">
      💰 PKR {m.get('fee_total',0):,.0f} &nbsp;·&nbsp;
      👥 {m.get('att_count',0)}/{m.get('total_active_members',0)} att &nbsp;·&nbsp;
      {'🟢 Shift Open' if m.get('shift_open') else '🔴 No Shift'}
    </div>
  </div>
</div>"""
    st.markdown(score_html, unsafe_allow_html=True)

    # ── Task checklist ──────────────────────────────────────────────────────
    with st.expander("📋 Aaj ka Task Checklist", expanded=True):
        for icon, label, hint, sev in tasks:
            bg  = {"critical": "#450A0A", "warn": "#422006", "ok": "#052E16"}.get(sev, "#1E293B")
            bc  = {"critical": "#EF4444", "warn": "#F59E0B", "ok": "#22C55E"}.get(sev, "#475569")
            st.markdown(f"""
<div style="background:{bg};border-left:3px solid {bc};border-radius:8px;
            padding:0.5rem 0.75rem;margin-bottom:0.4rem;display:flex;
            justify-content:space-between;align-items:center;">
  <div>
    <span style="font-size:0.9rem;">{icon} <strong>{label}</strong></span>
    {"<div style='font-size:0.72rem;color:#94A3B8;margin-top:0.1rem;'>→ " + hint + "</div>" if hint else ""}
  </div>
</div>""", unsafe_allow_html=True)

    # ── AI coach message ─────────────────────────────────────────────────────
    coach_key = f"coach_msg_{username}"
    if coach_key not in st.session_state:
        st.session_state[coach_key] = None

    refresh_col, _ = st.columns([1, 3])
    do_refresh = refresh_col.button("🤖 AI Coach Message", key="staff_coach_btn",
                                     type="primary", use_container_width=True)

    if do_refresh or (st.session_state[coach_key] is None and score < 60):
        prompt = _build_coach_prompt(username, m, score, grade)
        groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        if groq_key:
            try:
                import requests as _r
                resp = _r.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}",
                             "Content-Type": "application/json"},
                    json={"model": "llama-3.3-70b-versatile",
                          "messages": [{"role": "user", "content": prompt}],
                          "max_tokens": 400, "temperature": 0.7},
                    timeout=20,
                )
                resp.raise_for_status()
                st.session_state[coach_key] = resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as ex:
                st.session_state[coach_key] = f"AI Coach abhi available nahi. Baad mein try karein. ({ex})"
        else:
            st.session_state[coach_key] = "⚠️ GROQ_API_KEY set nahi hai — AI coach unavailable."

    if st.session_state.get(coach_key):
        msg = st.session_state[coach_key]
        is_praise = score >= 70
        msg_bg    = "#052E16" if is_praise else "#1C1917"
        msg_bc    = "#22C55E" if is_praise else "#F59E0B"
        msg_ico   = "🎉" if score >= 80 else ("👍" if is_praise else ("⚠️" if score >= 40 else "🚨"))
        st.markdown(f"""
<div style="background:{msg_bg};border:1px solid {msg_bc};border-radius:12px;
            padding:1rem 1.25rem;margin-top:0.5rem;">
  <div style="color:{msg_bc};font-weight:700;font-size:0.8rem;margin-bottom:0.4rem;">
    {msg_ico} AI COACH — {grade}
  </div>
  <div style="color:var(--gp-text);font-size:0.9rem;line-height:1.6;white-space:pre-wrap;">{msg}</div>
</div>""", unsafe_allow_html=True)


# ============================================
# 🎵 PERSISTENT SIDEBAR MUSIC BAR
# ============================================

def render_persistent_music_bar():
    """
    Render a compact music mini-player in the sidebar.
    Uses st.components.v1.html so the YouTube iframe stays alive across page
    navigations — as long as the video_id doesn't change, Streamlit's React
    reconciler keeps the same iframe node and music keeps playing.
    """
    import streamlit.components.v1 as components

    _init_state()
    vid   = st.session_state.get("active_music")
    title = st.session_state.get("active_music_title", "")
    queue = st.session_state.get("music_queue", [])
    idx   = st.session_state.get("music_queue_idx", 0)

    if not vid:
        return  # nothing to show

    # Build the mini-player HTML — must be byte-for-byte identical across reruns
    # for the SAME song so React doesn't remount the iframe.
    html = f"""
<!DOCTYPE html><html><head>
<style>
  * {{ margin:0;padding:0;box-sizing:border-box; }}
  body {{ background:#0F172A;font-family:system-ui,sans-serif;overflow:hidden; }}
  .bar {{ display:flex;align-items:center;gap:8px;padding:8px 10px;
          background:linear-gradient(90deg,#1E3A5F,#1E1B4B);
          border-radius:10px;border:1px solid #3B82F6; }}
  .ico {{ font-size:20px;flex-shrink:0; }}
  .info {{ flex:1;min-width:0; }}
  .label {{ color:#60A5FA;font-size:9px;font-weight:700;text-transform:uppercase;
            letter-spacing:.05em; }}
  .song {{ color:var(--gp-text);font-size:11px;font-weight:600;
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }}
  iframe {{ width:100%;height:52px;border:none;border-radius:8px;margin-top:6px; }}
</style></head>
<body>
<div class="bar">
  <div class="ico">🎵</div>
  <div class="info">
    <div class="label">Now Playing</div>
    <div class="song" title="{title}">{title[:60]}</div>
  </div>
</div>
<iframe src="https://www.youtube.com/embed/{vid}?autoplay=1&rel=0&modestbranding=1"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen></iframe>
</body></html>
"""
    components.html(html, height=130, scrolling=False)

    # Controls below the component
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⏮", key="pmb_prev", use_container_width=True, help="Previous track"):
            if queue and idx > 0:
                ni = idx - 1
                st.session_state["music_queue_idx"]    = ni
                st.session_state["active_music"]       = queue[ni]["id"]
                st.session_state["active_music_title"] = queue[ni]["title"]
                st.rerun()
    with c2:
        if st.button("⏭", key="pmb_next", use_container_width=True, help="Next track"):
            if queue and idx < len(queue) - 1:
                ni = idx + 1
                st.session_state["music_queue_idx"]    = ni
                st.session_state["active_music"]       = queue[ni]["id"]
                st.session_state["active_music_title"] = queue[ni]["title"]
                st.rerun()
    with c3:
        if st.button("⏹", key="pmb_stop", use_container_width=True, help="Stop music"):
            st.session_state["active_music"]       = None
            st.session_state["active_music_title"] = ""
            st.rerun()
    if queue:
        st.caption(f"🎵 {idx+1}/{len(queue)} — go to **AI Assistant → Music** for more")

# ============================================
# 💬 CHAT TAB
# ============================================

def _chat_tab(page: str, gym_stats: dict, role="staff", username="", gym_id=None):
    role_label = {"admin": "👑 Admin", "owner": "👑 Owner", "staff": "👤 Staff", "auditor": "🔍 Auditor"}.get(role, role)

    st.markdown(f"### 💬 GymPro AI — {role_label}")
    st.caption("Real-time gym data ke saath AI — Roman Urdu mein poochiye, seedha jawab milega")

    # Role-specific quick action chips
    if role in ["admin", "owner"]:
        chips = [
            "Aaj ka mukammal summary do",
            "Koi fraud ya chori alert hai?",
            "Overdue members ki list aur total pending",
            "Is mahine ka profit/loss",
            "Staff mein se kaunsa sabse zyada collect kar raha hai?",
            "Kaunse members aaj expire ho rahe hain?",
        ]
    else:
        chips = [
            "Fee kaise collect karein?",
            "Naya member kaise register karein?",
            "Shift kaise shuru karein?",
            "Attendance kaise mark karein?",
            "Receipt print kaise karein?",
            "Member ki fee update kaise karein?",
        ]

    st.markdown("#### ⚡ Quick Questions — Ek Click Mein Jawab")
    cols = st.columns(3)
    for i, chip in enumerate(chips):
        if cols[i % 3].button(chip, key=f"chip_{i}", use_container_width=True):
            _push_and_respond(chip, page, gym_stats, role=role, username=username, gym_id=gym_id)

    st.divider()

    if hasattr(st, "audio_input"):
        st.markdown("### 🎤 Voice Input")
        voice_file = st.audio_input("🎙️ Press and speak (Roman Urdu/English)", key="mic_recorder_main")
        if voice_file is not None:
            audio_bytes = voice_file.read()
            with st.spinner("🎧 Sun raha hoon..."):
                transcribed = transcribe_mic(audio_bytes)
                if transcribed:
                    st.success(f"🗣️ Aapne kaha: **{transcribed}**")
                    _push_and_respond(transcribed, page, gym_stats, role=role, username=username, gym_id=gym_id)
                else:
                    st.error("❌ Samajh nahi aaya. Dobara bolein.")
        st.divider()

    history = st.session_state.get("ai_chat_history", [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if st.session_state.get("speak_trigger") and st.session_state.get("auto_speak", False):
        play_tts(st.session_state["speak_trigger"])
        st.session_state["speak_trigger"] = None

    st.divider()

    key = f"chat_input_{st.session_state.get('ai_input_counter', 0)}"
    col1, col2, col3 = st.columns([6, 1, 1])
    user_input = col1.text_input("", key=key, label_visibility="collapsed",
                                 placeholder="Roman Urdu mein likhein — e.g. Aaj kitna collect hua?")
    send  = col2.button("Send ➤",  key="send_chat_btn",  type="primary", use_container_width=True)
    clear = col3.button("🗑 Clear", key="clear_chat_btn", use_container_width=True)

    if clear:
        st.session_state["ai_chat_history"] = []
        st.session_state["ai_last_question"] = ""
        st.session_state["ai_input_counter"] += 1
        st.rerun()

    if send and user_input.strip():
        _push_and_respond(user_input.strip(), page, gym_stats, role=role, username=username, gym_id=gym_id)

# ============================================
# MAIN RENDER
# ============================================

def render(gym_id=None, role=None, username=""):
    _init_state()
    role = role or "staff"
    role_label = {"admin": "👑 Admin", "owner": "👑 Owner", "staff": "👤 Staff", "auditor": "🔍 Auditor"}.get(role, role)

    st.markdown(f"""
        <div style='text-align:center;padding:1rem;'>
            <h1>🤖 GymPro AI Assistant</h1>
            <p style='font-size:1.1rem;color:#94A3B8;'>Live gym data · Roman Urdu · Voice</p>
            <p style='font-size:0.9rem;color:#FBBF24;'>{role_label} — {username}</p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    current_page = st.session_state.get("page", "AI Assistant")
    gym_stats = {}
    try:
        gym_stats = db.get_stats(gym_id)
    except Exception:
        pass

    tab1, tab2, tab3 = st.tabs(["💬 AI Chat", "🎬 Video", "🎵 Music"])

    with tab1:
        _chat_tab(current_page, gym_stats, role=role, username=username, gym_id=gym_id)

    with tab2:
        _video_player()

    with tab3:
        _music_player()

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    render(None, "admin")