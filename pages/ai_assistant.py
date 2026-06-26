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

def search_youtube(query: str, max_results: int = 8) -> list:
    """Search YouTube and return video IDs"""
    try:
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        
        response = requests.get(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=10)
        
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', response.text)
        video_ids = list(dict.fromkeys(video_ids))  # Remove duplicates
        
        return video_ids[:max_results]
    except Exception as e:
        print(f"Search error: {e}")
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
    "You are GymPro AI, an expert assistant embedded in GymPro — a professional multi-gym management system. "
    "You help gym managers, admins, staff, and auditors with: member management, fee collection, "
    "attendance tracking, financial analysis, expense management, inventory control, membership operations, "
    "and best practices for gym management.\n"
    "Be concise, practical, and friendly. Respond in Roman Urdu if the user asks in Roman Urdu. "
    "If asked something unrelated to gym management, politely redirect to gym topics."
)

# ============================================
# SESSION STATE INIT
# ============================================

def _init_state():
    if "ai_chat_history" not in st.session_state:
        st.session_state["ai_chat_history"] = []
    if "ai_input_counter" not in st.session_state:
        st.session_state["ai_input_counter"] = 0
    if "ai_last_question" not in st.session_state:
        st.session_state["ai_last_question"] = ""
    if "speak_trigger" not in st.session_state:
        st.session_state["speak_trigger"] = None
    if "auto_speak" not in st.session_state:
        st.session_state["auto_speak"] = True
    
    # Music Player
    if "music_results" not in st.session_state:
        st.session_state["music_results"] = []
    if "music_search" not in st.session_state:
        st.session_state["music_search"] = ""
    if "active_music" not in st.session_state:
        st.session_state["active_music"] = None
    
    # Video Player
    if "video_results" not in st.session_state:
        st.session_state["video_results"] = []
    if "video_search" not in st.session_state:
        st.session_state["video_search"] = ""
    if "active_video" not in st.session_state:
        st.session_state["active_video"] = None

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

def _build_system_content(page: str, gym_stats: dict) -> str:
    page_ctx = PAGE_CONTEXT.get(page, "")
    stats_ctx = (
        f"Live gym stats — Total members: {gym_stats.get('total_members', '?')}, "
        f"Active: {gym_stats.get('active_members', '?')}, "
        f"Month revenue: PKR {gym_stats.get('month_revenue', 0):,.0f}, "
        f"Month expenses: PKR {gym_stats.get('month_expenses', 0):,.0f}."
    )
    return f"{SYSTEM_PROMPT}\n\nCurrent page: {page}. {page_ctx}\n{stats_ctx}"

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

def get_ai_response(messages: list, page: str, gym_stats: dict) -> str:
    system_content = _build_system_content(page, gym_stats)
    
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            import requests as req
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_content}] + messages,
                "max_tokens": 600,
                "temperature": 0.7,
            }
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            pass
    
    return _rule_based_response(messages[-1]["content"] if messages else "", page, gym_stats)

def _api_messages() -> list:
    return [
        {"role": "assistant" if m["role"] == "assistant" else "user", "content": m["content"]}
        for m in st.session_state.get("ai_chat_history", [])[-20:]
    ]

def _push_and_respond(user_text: str, page: str, gym_stats: dict):
    if st.session_state.get("ai_last_question", "") == user_text:
        st.warning("⚠️ Yeh sawaal already pooch chuke ho!")
        return
    
    st.session_state["ai_last_question"] = user_text
    st.session_state["ai_chat_history"].append({"role": "user", "content": user_text})
    
    with st.spinner("🤔 Soch raha hoon..."):
        reply = get_ai_response(_api_messages(), page, gym_stats)
    
    st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
    
    if st.session_state.get("auto_speak", True):
        st.session_state["speak_trigger"] = reply
    
    st.session_state["ai_input_counter"] += 1
    st.rerun()

# ============================================
# SIDEBAR WIDGET
# ============================================

def render_sidebar_widget(current_page: str, gym_id=None):
    _init_state()
    
    gym_stats = {}
    try:
        gym_stats = db.get_stats(gym_id)
    except:
        pass
    
    with st.expander("🤖 AI Assistant", expanded=False):
        history = st.session_state.get("ai_chat_history", [])
        
        if history:
            html = '<div style="max-height:150px;overflow-y:auto;font-size:0.8rem;">'
            for msg in history[-5:]:
                if msg["role"] == "user":
                    html += f'<div style="background:#1E3A5F;padding:4px 8px;margin:2px 0;border-radius:5px;">👤 {msg["content"][:80]}...</div>'
                else:
                    html += f'<div style="background:#1E1E3A;padding:4px 8px;margin:2px 0;border-radius:5px;">🤖 {msg["content"][:80]}...</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption(f"Page: {current_page}. Kuch poochiye!")
        
        key = f"sb_chat_{st.session_state.get('ai_input_counter', 0)}"
        user_input = st.text_input("Message", placeholder="Roman Urdu mein likhein...", key=key, label_visibility="collapsed")
        
        col1, col2 = st.columns([3, 1])
        send = col1.button("Send", key="sb_send_btn", type="primary", use_container_width=True)
        clear = col2.button("🗑", key="sb_clear_btn", use_container_width=True)
        
        if clear:
            st.session_state["ai_chat_history"] = []
            st.session_state["ai_last_question"] = ""
            st.session_state["ai_input_counter"] += 1
            st.rerun()
        
        if send and user_input.strip():
            _push_and_respond(user_input.strip(), current_page, gym_stats)
        
        auto = st.toggle("🔊 Voice Reply", value=st.session_state.get("auto_speak", True))
        st.session_state["auto_speak"] = auto
        
        if st.session_state.get("speak_trigger") and st.session_state.get("auto_speak", True):
            play_tts(st.session_state["speak_trigger"])
            st.session_state["speak_trigger"] = None

# ============================================
# 🎵 MUSIC PLAYER - SEARCH ANY SONG
# ============================================

def _music_player():
    st.markdown("### 🎵 Music Player")
    st.caption("🔍 Koi bhi song, artist, ya genre search karein!")
    
    # Quick suggestions
    st.markdown("**⚡ Quick Suggestions:**")
    quick_suggestions = ["Atif Aslam", "Dil Dil Pakistan", "Arijit Singh", "Taylor Swift", "Workout Music", "EDM", "Lofi", "Hindi Songs"]
    cols = st.columns(4)
    for i, suggestion in enumerate(quick_suggestions[:4]):
        if cols[i % 4].button(suggestion, key=f"qs_music_{i}", use_container_width=True):
            st.session_state['music_search_input'] = suggestion
            st.rerun()
    
    st.markdown("---")
    
    # Search
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "🎵 Search Song / Artist:",
            placeholder="e.g. Atif Aslam, Fitness Motivation...",
            key="music_search_input",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("🔍 Search", key="music_search_btn", type="primary", use_container_width=True):
            if search_query:
                with st.spinner(f"🎵 Searching '{search_query}'..."):
                    results = search_youtube(search_query, max_results=8)
                    if results:
                        st.session_state['music_results'] = results
                        st.session_state['music_search'] = search_query
                        st.rerun()
                    else:
                        st.error("❌ No results found")
    
    # Show results
    if st.session_state['music_results']:
        results = st.session_state['music_results']
        search = st.session_state.get('music_search', '')
        
        st.success(f"🎵 {len(results)} songs found for '{search}'")
        
        cols = st.columns(2)
        for i, video_id in enumerate(results):
            col_idx = i % 2
            with cols[col_idx]:
                with st.container(border=True):
                    thumb_url = f"https://img.youtube.com/vi/{video_id}/default.jpg"
                    st.image(thumb_url, use_container_width=True)
                    
                    if st.button(f"▶️ Play", key=f"music_play_{i}", use_container_width=True, type="primary"):
                        st.session_state['active_music'] = video_id
                        st.rerun()
        
        if st.button("🗑️ Clear Results", key="music_clear", use_container_width=True):
            st.session_state['music_results'] = []
            st.session_state['music_search'] = ""
            st.rerun()
    
    # Active player
    if st.session_state.get('active_music'):
        video_id = st.session_state['active_music']
        
        st.divider()
        st.markdown(f"### 🎵 Now Playing")
        
        st.markdown(f"""
            <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:10px;background:#000;">
                <iframe style="position:absolute;top:0;left:0;width:100%;height:100%;"
                    src="https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0" 
                    frameborder="0" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("❌ Stop Music", use_container_width=True):
            st.session_state['active_music'] = None
            st.rerun()

# ============================================
# 🎬 VIDEO PLAYER - SEARCH ANY VIDEO
# ============================================

def _video_player():
    st.markdown("### 🎬 Video Player")
    st.caption("🔍 Koi bhi workout, exercise, ya informative video search karein!")
    
    # Quick suggestions
    st.markdown("**⚡ Quick Suggestions:**")
    quick_suggestions = ["Chest Workout", "Yoga for Beginners", "Cardio", "Full Body Workout", "Gym Motivation", "Weight Loss"]
    cols = st.columns(3)
    for i, suggestion in enumerate(quick_suggestions[:3]):
        if cols[i].button(suggestion, key=f"qs_video_{i}", use_container_width=True):
            st.session_state['video_search_input'] = suggestion
            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "🔍 Search Video:",
            placeholder="e.g. Chest workout, Yoga, Cardio...",
            key="video_search_input",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("🔍 Search", key="video_search_btn", type="primary", use_container_width=True):
            if search_query:
                with st.spinner(f"🔍 Searching '{search_query}'..."):
                    results = search_youtube(search_query, max_results=6)
                    if results:
                        st.session_state['video_results'] = results
                        st.session_state['video_search'] = search_query
                        st.rerun()
                    else:
                        st.error("❌ No results found")
    
    # Show results
    if st.session_state['video_results']:
        results = st.session_state['video_results']
        search = st.session_state.get('video_search', '')
        
        st.success(f"📹 {len(results)} videos found for '{search}'")
        
        cols = st.columns(3)
        for i, video_id in enumerate(results):
            col_idx = i % 3
            with cols[col_idx]:
                with st.container(border=True):
                    thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    st.image(thumb_url, use_container_width=True)
                    
                    if st.button(f"▶️ Play", key=f"video_play_{i}", use_container_width=True, type="primary"):
                        st.session_state['active_video'] = video_id
                        st.rerun()
        
        if st.button("🗑️ Clear Results", key="video_clear", use_container_width=True):
            st.session_state['video_results'] = []
            st.session_state['video_search'] = ""
            st.rerun()
    
    # Active player
    if st.session_state.get('active_video'):
        video_id = st.session_state['active_video']
        
        st.divider()
        st.markdown(f"### ▶️ Now Playing")
        
        st.markdown(f"""
            <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:10px;background:#000;">
                <iframe style="position:absolute;top:0;left:0;width:100%;height:100%;"
                    src="https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0" 
                    frameborder="0" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("❌ Stop Video", use_container_width=True):
            st.session_state['active_video'] = None
            st.rerun()

# ============================================
# 💬 CHAT TAB
# ============================================

def _chat_tab(page: str, gym_stats: dict):
    st.markdown("### 💬 AI Chat with Voice")
    st.caption("🎤 **Roman Urdu mein sawal poochiye ya microphone use karein**")
    
    st.markdown("#### ⚡ Quick Questions")
    chips = [
        "Kitne members hain?",
        "Aaj ki attendance?",
        "Diet plan batao",
        "Workout routine",
        "Fees collection?",
        "Expenses kya hain?"
    ]
    cols = st.columns(3)
    for i, chip in enumerate(chips):
        if cols[i % 3].button(chip, key=f"chip_{i}", use_container_width=True):
            _push_and_respond(chip, page, gym_stats)
    
    st.divider()
    
    st.markdown("### 🎤 Voice Input")
    
    if hasattr(st, "audio_input"):
        voice_file = st.audio_input("🎙️ Press and speak (Roman Urdu/English)", key="mic_recorder_main")
        if voice_file is not None:
            audio_bytes = voice_file.read()
            with st.spinner("🎧 Sun raha hoon..."):
                transcribed = transcribe_mic(audio_bytes)
                if transcribed:
                    st.success(f"🗣️ Aapne kaha: **{transcribed}**")
                    _push_and_respond(transcribed, page, gym_stats)
                else:
                    st.error("❌ Samajh nahi aaya. Dobara bolein.")
    
    st.divider()
    
    history = st.session_state.get("ai_chat_history", [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    if st.session_state.get("speak_trigger") and st.session_state.get("auto_speak", True):
        play_tts(st.session_state["speak_trigger"])
        st.session_state["speak_trigger"] = None
    
    st.divider()
    
    key = f"chat_input_{st.session_state.get('ai_input_counter', 0)}"
    col1, col2, col3 = st.columns([6, 1, 1])
    user_input = col1.text_input("💬 Roman Urdu mein likhein:", key=key, label_visibility="collapsed",
                                 placeholder="e.g. Aaj kitne members aaye?")
    send = col2.button("Send ➤", key="send_chat_btn", type="primary", use_container_width=True)
    clear = col3.button("🗑 Clear", key="clear_chat_btn", use_container_width=True)
    
    if clear:
        st.session_state["ai_chat_history"] = []
        st.session_state["ai_last_question"] = ""
        st.session_state["ai_input_counter"] += 1
        st.rerun()
    
    if send and user_input.strip():
        _push_and_respond(user_input.strip(), page, gym_stats)

# ============================================
# MAIN RENDER
# ============================================

def render(gym_id=None, role=None):
    _init_state()
    
    st.markdown("""
        <div style='text-align:center;padding:1rem;'>
            <h1>🤖 AI Gym Assistant</h1>
            <p style='font-size:1.1rem;'>💬 Chat • 🎵 Music • 🎬 Video</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    current_page = st.session_state.get("page", "AI Assistant")
    gym_stats = {}
    try:
        gym_stats = db.get_stats(gym_id)
    except:
        pass
    
    tab1, tab2, tab3 = st.tabs(["💬 AI Chat", "🎬 Video", "🎵 Music"])
    
    with tab1:
        _chat_tab(current_page, gym_stats)
    
    with tab2:
        _video_player()
    
    with tab3:
        _music_player()

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    render(None, "admin")