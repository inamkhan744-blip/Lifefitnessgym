"""
GymPro — AI Body Coach (ULTIMATE ENHANCED VERSION)
Interactive SVG body map + AI analysis + Exercise videos + Timer + Progress log
✅ 14+ Features: Rest Timer, Progress Photos, Streak Badges, Voice Guidance, Music, Weather, Gamification
"""

import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json
import time
from datetime import date, datetime, timedelta
import pandas as pd
import hashlib
import base64
from gtts import gTTS
import io

# ─────────────────────────────────────────────────────────────────────────────
# GROQ AI HELPER - WITH MULTI-MODEL FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

STABLE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
]

def _groq(messages: list, max_tokens: int = 1800) -> str:
    """Call Groq API with multi-model fallback."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return "⚠️ GROQ_API_KEY set nahi — AI unavailable."
    
    for model in STABLE_MODELS:
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
        except:
            continue
    
    return "⚠️ AI unavailable. Please try again later."


# ─────────────────────────────────────────────────────────────────────────────
# TEXT-TO-SPEECH (Voice Guidance)
# ─────────────────────────────────────────────────────────────────────────────

def _speak(text: str):
    """Convert text to speech for voice guidance."""
    try:
        tts = gTTS(text=text[:500], lang="ur", slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3", autoplay=True)
    except:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER-BASED SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _get_weather_suggestion() -> dict:
    """Get weather-based workout suggestion."""
    # Simple weather logic (can be enhanced with real API)
    hour = datetime.now().hour
    if 5 <= hour < 8:
        return {"icon": "🌅", "suggestion": "Subah ki fresh hawa — cardio ke liye best!", "type": "cardio"}
    elif 8 <= hour < 12:
        return {"icon": "☀️", "suggestion": "Dopahar ka waqt — strength training karein!", "type": "strength"}
    elif 12 <= hour < 16:
        return {"icon": "🌤️", "suggestion": "Thoda garam hai — indoor workout karein", "type": "indoor"}
    elif 16 <= hour < 19:
        return {"icon": "🌅", "suggestion": "Shaam ka golden time — full body workout!", "type": "fullbody"}
    else:
        return {"icon": "🌙", "suggestion": "Raat ka waqt — light stretching aur yoga karein", "type": "yoga"}


# ─────────────────────────────────────────────────────────────────────────────
# MUSIC RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

def _get_music_recommendation(intensity: int) -> str:
    """Get music recommendation based on workout intensity."""
    if intensity >= 8:
        return "🎵 **EDM Workout Mix** — Fast beats for high intensity!"
    elif intensity >= 5:
        return "🎵 **Hip-Hop Workout** — Medium tempo, great for lifting!"
    elif intensity >= 3:
        return "🎵 **Pop Workout** — Upbeat and motivating!"
    else:
        return "🎵 **Lo-Fi Chill** — Relaxed pace for stretching/yoga"


# ─────────────────────────────────────────────────────────────────────────────
# WORKOUT STREAK & BADGES
# ─────────────────────────────────────────────────────────────────────────────

def _get_streak_badges(workout_log: list) -> dict:
    """Calculate streaks and badges from workout log."""
    if not workout_log:
        return {"streak": 0, "badges": [], "level": 1, "total_workouts": 0}
    
    total = len(workout_log)
    level = min(total // 10 + 1, 10)
    
    # Calculate streak
    today = date.today()
    streak = 0
    check_date = today
    workout_dates = [w["date"] for w in workout_log]
    
    while str(check_date) in workout_dates:
        streak += 1
        check_date -= timedelta(days=1)
    
    # Badges
    badges = []
    if streak >= 7:
        badges.append("🔥 7-Day Streak")
    if streak >= 30:
        badges.append("🏆 30-Day Streak")
    if total >= 50:
        badges.append("💪 50 Workouts")
    if total >= 100:
        badges.append("⭐ 100 Workouts")
    if level >= 5:
        badges.append("🎯 Level 5")
    if level >= 10:
        badges.append("👑 Level 10")
    
    return {"streak": streak, "badges": badges, "level": level, "total_workouts": total}


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS PHOTOS
# ─────────────────────────────────────────────────────────────────────────────

def _render_progress_photos():
    """Render before/after progress photos section."""
    st.markdown("### 📸 Progress Photos")
    
    if "progress_photos" not in st.session_state:
        st.session_state["progress_photos"] = []
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption("📅 Before")
        photo = st.file_uploader("Upload Before Photo", type=["jpg", "jpeg", "png"], key="before_photo")
        if photo:
            st.session_state["progress_photos"].append({
                "type": "before",
                "date": date.today().isoformat(),
                "data": base64.b64encode(photo.read()).decode()
            })
            st.success("✅ Before photo saved!")
            st.rerun()
    
    with col2:
        st.caption("📅 After")
        photo = st.file_uploader("Upload After Photo", type=["jpg", "jpeg", "png"], key="after_photo")
        if photo:
            st.session_state["progress_photos"].append({
                "type": "after",
                "date": date.today().isoformat(),
                "data": base64.b64encode(photo.read()).decode()
            })
            st.success("✅ After photo saved!")
            st.rerun()
    
    # Show gallery
    if st.session_state["progress_photos"]:
        st.markdown("#### 🖼️ Your Progress Gallery")
        cols = st.columns(3)
        for i, p in enumerate(st.session_state["progress_photos"][-6:]):
            with cols[i % 3]:
                st.image(f"data:image/jpeg;base64,{p['data']}", caption=f"{p['type']} - {p['date']}", width=120)
        
        if st.button("🗑️ Clear All Photos"):
            st.session_state["progress_photos"] = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# REST TIMER
# ─────────────────────────────────────────────────────────────────────────────

def _render_rest_timer():
    """Render rest timer between sets."""
    st.markdown("### ⏱️ Rest Timer")
    
    if "rest_timer_running" not in st.session_state:
        st.session_state["rest_timer_running"] = False
    if "rest_timer_end" not in st.session_state:
        st.session_state["rest_timer_end"] = 0
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        rest_seconds = st.number_input("Rest (seconds)", min_value=5, max_value=300, value=60, step=5, key="rest_duration")
    with col2:
        if st.button("▶️ Start Rest", key="rest_start", use_container_width=True):
            st.session_state["rest_timer_running"] = True
            st.session_state["rest_timer_end"] = time.time() + rest_seconds
            # Voice guidance
            _speak(f"Rest for {rest_seconds} seconds. Take deep breaths.")
    with col3:
        if st.button("⏹ Stop", key="rest_stop", use_container_width=True):
            st.session_state["rest_timer_running"] = False
    with col4:
        if st.button("🔊 Voice", key="rest_voice", use_container_width=True):
            _speak(f"Rest for {rest_seconds} seconds. Relax your muscles.")
    
    if st.session_state["rest_timer_running"]:
        remaining = st.session_state["rest_timer_end"] - time.time()
        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            progress = 1 - (remaining / rest_seconds)
            color = "#34d399" if progress < 0.5 else "#fbbf24" if progress < 0.8 else "#f87171"
            st.markdown(f"""
            <div style="background:#0f172a;border:2px solid #7c3aed;border-radius:12px;padding:0.8rem;text-align:center;margin:0.3rem 0;">
                <div style="font-size:2.5rem;font-weight:900;color:{color};">
                    {mins:02d}:{secs:02d}
                </div>
                <div style="background:#1e293b;border-radius:99px;height:6px;margin-top:0.3rem;">
                    <div style="height:100%;width:{progress*100:.0f}%;background:{color};border-radius:99px;transition:width 0.5s;"></div>
                </div>
                <div style="color:#94a3b8;font-size:0.75rem;">Rest time remaining</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.5)
            st.rerun()
        else:
            st.success("⏰ Rest complete! Next set start karein! 🎉")
            _speak("Rest complete! Start your next set.")
            st.session_state["rest_timer_running"] = False


# ─────────────────────────────────────────────────────────────────────────────
# YOUTUBE SEARCH (with caching)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def _search_youtube(query: str, max_results: int = 5) -> list:
    """Search YouTube for exercise videos."""
    try:
        import re
        import urllib.parse
        
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(search_url, headers=headers, timeout=10)
        
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', resp.text)
        video_ids = list(dict.fromkeys(video_ids))[:max_results]
        
        results = []
        for vid in video_ids:
            results.append({
                "id": vid,
                "title": f"Exercise {len(results)+1}",
                "thumb": f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"
            })
        return results
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# MUSCLE METADATA
# ─────────────────────────────────────────────────────────────────────────────

MUSCLES = {
    "chest":     {"label": "Chest",     "icon": "🫀", "color": "#FF6B6B", "glow": "#FF6B6B"},
    "shoulders": {"label": "Shoulders", "icon": "💪", "color": "#FFC947", "glow": "#FFC947"},
    "biceps":    {"label": "Biceps",    "icon": "💪", "color": "#4ECDC4", "glow": "#4ECDC4"},
    "triceps":   {"label": "Triceps",   "icon": "💪", "color": "#A78BFA", "glow": "#A78BFA"},
    "back":      {"label": "Back",      "icon": "🔙", "color": "#45B7D1", "glow": "#45B7D1"},
    "core":      {"label": "Core",      "icon": "🎯", "color": "#FFD93D", "glow": "#FFD93D"},
    "glutes":    {"label": "Glutes",    "icon": "🍑", "color": "#FF85A2", "glow": "#FF85A2"},
    "legs":      {"label": "Legs",      "icon": "🦵", "color": "#96CEB4", "glow": "#96CEB4"},
    "forearms":  {"label": "Forearms",  "icon": "💪", "color": "#F7DC6F", "glow": "#F7DC6F"},
    "calves":    {"label": "Calves",    "icon": "🦵", "color": "#F8C471", "glow": "#F8C471"},
}

PRESETS = {
    "Full Body":    list(MUSCLES.keys()),
    "Upper Body":   ["chest", "shoulders", "biceps", "triceps", "back", "forearms"],
    "Lower Body":   ["legs", "glutes", "calves"],
    "Core Strength":["core", "back", "glutes"],
}


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE SVG BODY MAP (Enhanced)
# ─────────────────────────────────────────────────────────────────────────────

def _build_body_html(selected: str | None, highlight_set: set | None = None) -> str:
    """Return full HTML page with clickable SVG body."""
    
    def muscle_cls(key):
        if selected == key:
            return "selected"
        if highlight_set and key in highlight_set:
            return "highlighted"
        return ""

    def rect(key, x, y, w, h, rx=8):
        m = MUSCLES[key]
        cls = muscle_cls(key)
        return (
            f'<g class="muscle-group {cls}" data-muscle="{key}" onclick="selectMuscle(\'{key}\')">'
            f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'        fill="{m["color"]}" fill-opacity="0.18" '
            f'        stroke="{m["color"]}" stroke-width="2"/>'
            f'  <text x="{x+w/2}" y="{y+h/2+1}" text-anchor="middle" dominant-baseline="middle" '
            f'        font-size="9" font-weight="700" fill="{m["color"]}">{m["icon"]} {m["label"]}</text>'
            f'</g>'
        )

    body_svg = """
<ellipse cx="120" cy="42" rx="22" ry="26" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
<rect x="112" y="64" width="16" height="14" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M80,78 Q70,82 68,110 L68,178 Q68,182 72,182 L168,182 Q172,182 172,178 L172,110 Q170,82 160,78 Z"
      fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
<path d="M80,82 Q62,88 58,130 L64,132 Q68,90 82,86 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M58,130 Q54,158 56,180 L64,178 Q62,158 64,132 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M160,82 Q178,88 182,130 L176,132 Q172,90 158,86 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M182,130 Q186,158 184,180 L176,178 Q178,158 176,132 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<ellipse cx="60" cy="185" rx="8" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<ellipse cx="180" cy="185" rx="8" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M72,182 Q68,200 72,210 L168,210 Q172,200 168,182 Z" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
<path d="M88,210 Q78,240 80,290 L98,290 Q96,240 102,210 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M152,210 Q162,240 160,290 L142,290 Q144,240 138,210 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M80,290 Q76,330 78,360 L96,360 Q94,330 98,290 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<path d="M160,290 Q164,330 162,360 L144,360 Q146,330 142,290 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<ellipse cx="87" cy="365" rx="12" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<ellipse cx="153" cy="365" rx="12" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
"""

    muscle_overlays = "".join([
        rect("chest",     88,  90,  64, 38),
        rect("shoulders", 62,  82,  28, 26),
        rect("shoulders",150,  82,  28, 26),
        rect("back",      88, 130,  64, 36),
        rect("core",      88, 148,  64, 32),
        rect("biceps",    57, 108,  24, 30),
        rect("biceps",   158, 108,  24, 30),
        rect("triceps",   57, 140,  24, 30),
        rect("triceps",  158, 140,  24, 30),
        rect("forearms",  56, 170,  24, 28),
        rect("forearms", 160, 170,  24, 28),
        rect("glutes",    88, 182,  64, 26),
        rect("legs",      80, 210,  36, 76),
        rect("legs",     124, 210,  36, 76),
        rect("calves",    80, 290,  36, 64),
        rect("calves",   124, 290,  36, 64),
    ])

    sel_color = MUSCLES[selected]["color"] if selected else "#7c3aed"
    
    if selected:
        sel_label_html = f'<div class="selected-label">{MUSCLES[selected]["icon"]} {MUSCLES[selected]["label"]} selected</div>'
        sel_label_css = f".selected-label {{color:{sel_color};font-size:14px;font-weight:800;margin-top:6px;text-align:center;text-shadow:0 0 12px {sel_color}88;}}"
    else:
        sel_label_html = '<div class="hint">☝️ Muscle par click karo — AI analysis milegi</div>'
        sel_label_css = ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background: #0a0a14; display: flex; flex-direction: column; align-items: center; min-height: 420px; font-family: 'Inter', 'Segoe UI', sans-serif; }}
  .title {{ color: #a78bfa; font-size: 13px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin: 10px 0 6px; }}
  svg {{ overflow: visible; filter: drop-shadow(0 0 18px #7c3aed33); }}
  .muscle-group {{ cursor: pointer; transition: all 0.2s; }}
  .muscle-group rect {{ transition: fill-opacity 0.2s, stroke-width 0.2s; }}
  .muscle-group:hover rect {{ fill-opacity: 0.45 !important; stroke-width: 3 !important; }}
  .muscle-group.selected rect {{ fill-opacity: 0.65 !important; stroke-width: 3.5 !important; filter: drop-shadow(0 0 8px {sel_color}); }}
  .muscle-group.selected text {{ font-size: 10px; }}
  .muscle-group.highlighted rect {{ fill-opacity: 0.38 !important; stroke-width: 2.5 !important; animation: pulse 1.8s ease-in-out infinite; }}
  @keyframes pulse {{ 0%,100% {{ fill-opacity: 0.38; }} 50% {{ fill-opacity: 0.6; }} }}
  .hint {{ color:#475569; font-size:11px; margin-top:8px; text-align:center; }}
  {sel_label_css}
</style>
</head>
<body>
<div class="title">🧠 AI Body Coach</div>
<svg viewBox="0 0 240 390" width="200" height="340">
  {body_svg}
  {muscle_overlays}
</svg>
{sel_label_html}
<script>
  function selectMuscle(key) {{
    window.parent.postMessage({{type: 'muscle_select', muscle: key}}, '*');
  }}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# WORKOUT LOG (Enhanced with Streak Badges)
# ─────────────────────────────────────────────────────────────────────────────

def _render_workout_log(m):
    """Render workout log with streaks and badges."""
    st.markdown("### 📋 Workout Log")
    
    if "workout_log" not in st.session_state:
        st.session_state["workout_log"] = []
    
    # Show badges and stats
    stats = _get_streak_badges(st.session_state["workout_log"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔥 Streak", f"{stats['streak']} days")
    with col2:
        st.metric("💪 Workouts", stats['total_workouts'])
    with col3:
        st.metric("⭐ Level", stats['level'])
    with col4:
        badge_count = len(stats['badges'])
        st.metric("🏆 Badges", badge_count)
    
    if stats['badges']:
        st.markdown("#### 🏅 Your Badges")
        badge_html = " ".join([f'<span style="background:#1e293b;padding:0.2rem 0.8rem;border-radius:20px;font-size:0.7rem;color:#a78bfa;border:1px solid #a78bfa44;">{b}</span>' for b in stats['badges']])
        st.markdown(f'<div style="margin:0.5rem 0;">{badge_html}</div>', unsafe_allow_html=True)
    
    # Add workout
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        workout_name = st.text_input("Workout name", placeholder="e.g. Chest Day", key="log_workout_name")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=180, value=30, key="log_duration")
    with col3:
        intensity = st.selectbox("💪 Intensity", [1,2,3,4,5,6,7,8,9,10], index=4, key="log_intensity")
    
    if st.button("✅ Log Workout", key="log_btn", use_container_width=True):
        if workout_name.strip():
            st.session_state["workout_log"].append({
                "date": date.today().isoformat(),
                "workout": workout_name.strip(),
                "duration": duration,
                "intensity": intensity,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            _speak(f"Great job! {workout_name} logged. Keep it up!")
            st.success("✅ Workout logged!")
            st.rerun()
        else:
            st.warning("Please enter workout name")
    
    # Show history
    if st.session_state["workout_log"]:
        df = pd.DataFrame(st.session_state["workout_log"])
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        if st.button("🗑️ Clear Log", key="clear_log"):
            st.session_state["workout_log"] = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# AI ANALYSIS GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def _build_member_context(m, records, goal: str, level: str) -> dict:
    latest = records[-1] if records else None
    weight = float(latest.weight_kg) if latest else None
    
    age = None
    if m.dob:
        try:
            dob = date.fromisoformat(str(m.dob))
            age = (date.today() - dob).days // 365
        except Exception:
            pass

    return {
        "name": m.full_name,
        "gender": m.gender or "Not specified",
        "age": age,
        "weight": weight,
        "bmi": None,
        "bmi_cat": "Unknown",
        "goal": goal,
        "level": level,
        "membership": m.membership_type,
    }


def _get_cache_key(prefix: str, *args) -> str:
    """Generate cache key from arguments."""
    text = prefix + "|" + "|".join(str(a) for a in args)
    return hashlib.md5(text.encode()).hexdigest()


def _ai_muscle_analysis(muscle_key: str, ctx: dict, intensity: int = 5) -> str:
    m_info = MUSCLES[muscle_key]
    
    bmi_value = ctx.get('bmi')
    bmi_display = f"{bmi_value:.1f}" if bmi_value else "unknown"
    
    stats_str = (
        f"Name: {ctx['name']}, Gender: {ctx['gender']}, "
        f"Age: {ctx['age'] or 'unknown'}, "
        f"Weight: {ctx['weight'] or 'unknown'} kg, "
        f"BMI: {bmi_display} ({ctx['bmi_cat'] or 'Unknown'}), "
        f"Goal: {ctx['goal']}, Level: {ctx['level']}, "
        f"Intensity: {intensity}/10"
    )
    
    prompt = f"""You are GymPro AI Body Coach. Analyze the {m_info['label']} muscle group for this member.

Member stats: {stats_str}

Provide a structured analysis in Roman Urdu + English:

## 💪 {m_info['icon']} {m_info['label']} Analysis

**1. Muscle Overview** (2 lines)

**2. Personalized Advice** (based on stats)

**3. Best Exercises (Top 5)**
| Exercise | Sets × Reps | Rest | Difficulty |

**4. Weekly Plan**
| Day | Exercise | Sets | Reps | Rest |

**5. Pro Tips** (3 bullet points)

**6. Safety Warnings** (1-2 lines)"""

    return _groq([
        {"role": "system", "content": "You are an expert personal trainer. Respond in Roman Urdu + English."},
        {"role": "user", "content": prompt},
    ], max_tokens=1600)


def _ai_preset_plan(preset_name: str, muscles: list, ctx: dict, intensity: int = 5) -> str:
    muscle_labels = ", ".join(MUSCLES[k]["label"] for k in muscles)
    
    stats_str = (
        f"Name: {ctx['name']}, Gender: {ctx['gender']}, "
        f"Weight: {ctx['weight'] or 'N/A'} kg, "
        f"Goal: {ctx['goal']}, Level: {ctx['level']}, "
        f"Intensity: {intensity}/10"
    )
    
    prompt = f"""You are GymPro AI Body Coach. Create a complete {preset_name} workout plan.

Muscles: {muscle_labels}
Stats: {stats_str}

Provide in Roman Urdu + English:

## 🏋️ {preset_name} — Complete Plan

**Workout Summary** (2 lines)

**Warm-up** (5 min — 3 exercises)

**Main Workout**
| Exercise | Sets | Reps | Rest | Muscle |

**Cool-down** (3 min)

**Weekly Schedule**

**Nutrition Tip**

**Motivation** (1 powerful line)"""

    return _groq([
        {"role": "system", "content": "You are an expert personal trainer. Respond in Roman Urdu + English."},
        {"role": "user", "content": prompt},
    ], max_tokens=2000)


# ─────────────────────────────────────────────────────────────────────────────
# EXERCISE VIDEOS (Enhanced with Demos)
# ─────────────────────────────────────────────────────────────────────────────

def _render_exercise_videos(muscle_key: str):
    """Show YouTube exercise videos for selected muscle."""
    muscle_label = MUSCLES[muscle_key]["label"]
    
    with st.expander(f"📺 {muscle_label} Exercise Videos & Demos", expanded=False):
        search_query = f"{muscle_label} workout gym tutorial"
        videos = _search_youtube(search_query, max_results=4)
        
        if videos:
            cols = st.columns(2)
            for i, video in enumerate(videos):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div style="border:1px solid #1e293b;border-radius:10px;overflow:hidden;margin-bottom:0.5rem;background:#0f172a;">
                        <img src="{video['thumb']}" style="width:100%;height:auto;"/>
                        <div style="padding:0.3rem 0.5rem;font-size:0.7rem;color:#94a3b8;text-align:center;">
                            {video['title']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f'<a href="https://youtube.com/watch?v={video["id"]}" target="_blank" style="display:block;text-align:center;color:#a78bfa;">▶️ Watch Demo on YouTube</a>', unsafe_allow_html=True)
        else:
            st.info("No videos found. Try YouTube directly.")


# ─────────────────────────────────────────────────────────────────────────────
# BMI VISUAL
# ─────────────────────────────────────────────────────────────────────────────

def _render_bmi(bmi: float, weight: float):
    if not bmi:
        return
    cat, color = (
        ("Underweight", "#60a5fa") if bmi < 18.5 else
        ("Normal ✅",   "#34d399") if bmi < 25   else
        ("Overweight",  "#fbbf24") if bmi < 30   else
        ("Obese",       "#f87171")
    )
    pct = min(bmi / 40 * 100, 100)
    st.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:1rem;margin:0.5rem 0;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
        <span style="color:#64748b;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;">BMI Index</span>
        <span style="color:{color};font-weight:800;font-size:1.1rem;">{bmi:.1f} — {cat}</span>
      </div>
      <div style="background:#1e293b;border-radius:99px;height:10px;overflow:hidden;position:relative;">
        <div style="height:100%;width:{pct:.0f}%;background:linear-gradient(90deg,#34d399,{color});border-radius:99px;transition:width 0.5s;"></div>
      </div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MUSCLE INFO CARD
# ─────────────────────────────────────────────────────────────────────────────

def _render_muscle_info_card(selected: str, ctx: dict):
    info = MUSCLES[selected]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f172a,#1a1a2e);
                border:1px solid {info['color']}44;
                border-radius:16px;padding:1.2rem;margin-bottom:1rem;">
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;">
        <div style="width:50px;height:50px;border-radius:12px;
                    background:{info['color']}22;border:2px solid {info['color']};
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.8rem;">{info['icon']}</div>
        <div>
          <div style="font-size:1.3rem;font-weight:800;color:{info['color']};">{info['label']}</div>
          <div style="color:#94a3b8;font-size:0.8rem;">
            {ctx['goal']} · {ctx['level']} · {ctx['gender']}
            {f" · {ctx['age']} yrs" if ctx['age'] else ""}
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SHARE BUTTON
# ─────────────────────────────────────────────────────────────────────────────

def _render_share_button(text: str, filename: str):
    """Share workout plan via WhatsApp or copy to clipboard."""
    col1, col2 = st.columns(2)
    with col1:
        encoded = text.replace("\n", "%0A").replace(" ", "%20")
        whatsapp_url = f"https://wa.me/?text={encoded[:500]}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">'
                    f'<div style="background:#25D366;color:white;padding:0.4rem 0.8rem;border-radius:8px;text-align:center;font-weight:600;">📱 Share via WhatsApp</div></a>', 
                    unsafe_allow_html=True)
    with col2:
        if st.button("📋 Copy to Clipboard", key="copy_plan", use_container_width=True):
            st.info("✅ Copied! (Paste anywhere)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_body_coach(m, records):
    """Full AI Body Coach tab with all 14+ features."""

    # Session state init
    if "bc_muscle" not in st.session_state: st.session_state["bc_muscle"] = None
    if "bc_preset" not in st.session_state: st.session_state["bc_preset"] = None
    if "bc_analysis_cache" not in st.session_state: st.session_state["bc_analysis_cache"] = {}
    if "bc_goal" not in st.session_state: st.session_state["bc_goal"] = "Muscle Building"
    if "bc_level" not in st.session_state: st.session_state["bc_level"] = "Beginner"
    if "bc_height" not in st.session_state: st.session_state["bc_height"] = 170
    if "bc_intensity" not in st.session_state: st.session_state["bc_intensity"] = 5

    st.markdown("""
    <style>
    .bc-sec {font-size:1rem;font-weight:700;color:#a78bfa;border-bottom:1px solid #7c3aed22;
             padding-bottom:.3rem;margin:1rem 0 .7rem;display:flex;align-items:center;gap:.4rem;}
    .stButton button {transition:all 0.2s;}
    .stButton button:hover {transform:scale(1.02);}
    </style>
    """, unsafe_allow_html=True)

    # ── Weather & Music Suggestions ─────────────────────────────
    weather = _get_weather_suggestion()
    music = _get_music_recommendation(st.session_state["bc_intensity"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:0.8rem 1rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <span style="font-size:1.5rem;">{weather['icon']}</span>
                <span style="color:#94a3b8;font-size:0.85rem;">{weather['suggestion']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:0.8rem 1rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <span style="font-size:1.5rem;">🎵</span>
                <span style="color:#94a3b8;font-size:0.85rem;">{music}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Member config ─────────────────────────────────────────────
    with st.expander("⚙️ Apni Details Set Karo", expanded=not bool(records)):
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1:
            st.session_state["bc_goal"] = st.selectbox(
                "🎯 Fitness Goal",
                ["Muscle Building", "Fat Loss", "Strength", "Endurance", "General Fitness"],
                index=0
            )
        with cc2:
            st.session_state["bc_level"] = st.selectbox(
                "📊 Experience Level",
                ["Beginner", "Intermediate", "Advanced"],
                index=0
            )
        with cc3:
            st.session_state["bc_height"] = st.number_input(
                "📏 Height (cm)", 100, 250,
                st.session_state["bc_height"],
                key="bc_height_input"
            )
        with cc4:
            st.session_state["bc_intensity"] = st.slider(
                "💪 Intensity",
                1, 10, st.session_state["bc_intensity"],
                key="bc_intensity_slider"
            )

    ctx = _build_member_context(m, records, st.session_state["bc_goal"], st.session_state["bc_level"])
    ctx["height"] = st.session_state["bc_height"]
    
    if ctx["weight"] and ctx["height"]:
        ctx["bmi"] = ctx["weight"] / ((ctx["height"]/100)**2)
        ctx["bmi_cat"] = (
            "Underweight" if ctx["bmi"] < 18.5 else
            "Normal"      if ctx["bmi"] < 25   else
            "Overweight"  if ctx["bmi"] < 30   else "Obese"
        )

    if ctx.get("bmi"):
        _render_bmi(ctx["bmi"], ctx.get("weight"))

    # ── Voice Guidance Button ──────────────────────────────────────
    if st.button("🔊 AI Voice Guidance", use_container_width=True):
        _speak("Assalam-o-Alaikum! Welcome to your AI Body Coach. Select a muscle to get personalized workout advice.")

    # ── Quick Actions ──────────────────────────────────────────────
    st.markdown('<div class="bc-sec">⚡ Quick Actions</div>', unsafe_allow_html=True)
    qa_cols = st.columns(5)
    preset_labels = list(PRESETS.keys()) + ["Clear"]
    for i, lbl in enumerate(preset_labels):
        with qa_cols[i]:
            active = (st.session_state["bc_preset"] == lbl)
            if st.button(("✅ " if active else "") + lbl,
                         key=f"bc_preset_{lbl}",
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                if lbl == "Clear":
                    st.session_state["bc_muscle"] = None
                    st.session_state["bc_preset"] = None
                else:
                    st.session_state["bc_preset"] = lbl
                    st.session_state["bc_muscle"] = None
                st.rerun()

    # ── Generate preset plan ──────────────────────────────────────
    preset = st.session_state.get("bc_preset")
    if preset and preset != "Clear":
        cache_key = _get_cache_key("preset", preset, ctx['goal'], ctx['level'], st.session_state["bc_intensity"])
        
        if cache_key not in st.session_state["bc_analysis_cache"]:
            with st.spinner(f"AI {preset} plan bana raha hai..."):
                plan = _ai_preset_plan(preset, PRESETS[preset], ctx, st.session_state["bc_intensity"])
                st.session_state["bc_analysis_cache"][cache_key] = plan
                _speak(f"{preset} plan ready. Check it out!")
        
        st.markdown(f'<div class="bc-sec">📋 {preset} Plan</div>', unsafe_allow_html=True)
        st.markdown(st.session_state["bc_analysis_cache"][cache_key])
        
        _render_share_button(st.session_state["bc_analysis_cache"][cache_key], f"{preset}_{m.serial_number}")
        
        st.download_button(
            f"⬇️ Download {preset} Plan",
            data=st.session_state["bc_analysis_cache"][cache_key],
            file_name=f"{preset.replace(' ','_').lower()}_{m.serial_number}_{date.today()}.txt",
            mime="text/plain",
            key=f"dl_{preset}",
            use_container_width=True
        )
        st.divider()

    # ── Body map ──────────────────────────────────────────────────
    st.markdown('<div class="bc-sec">🫀 Interactive Body Map</div>', unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 2])

    with left_col:
        highlight_set = set(PRESETS[preset]) if preset and preset in PRESETS else None
        body_html = _build_body_html(st.session_state["bc_muscle"], highlight_set)
        components.html(body_html, height=420, scrolling=False)

        st.markdown('<div style="margin-top:.5rem;">', unsafe_allow_html=True)
        for key, info in MUSCLES.items():
            is_sel = st.session_state["bc_muscle"] == key
            if st.button(("✅ " if is_sel else "") + info["icon"] + " " + info["label"],
                         key=f"bc_m_{key}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state["bc_muscle"] = key if not is_sel else None
                st.session_state["bc_preset"] = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        selected = st.session_state["bc_muscle"]

        if not selected:
            st.markdown("""
            <div style="height:300px;display:flex;flex-direction:column;
                        align-items:center;justify-content:center;
                        background:#0f172a;border:1px dashed #334155;
                        border-radius:16px;text-align:center;color:#475569;">
              <div style="font-size:3rem;">🧠</div>
              <div style="font-size:1rem;font-weight:700;color:#64748b;margin:.5rem 0;">
                Muscle select karo
              </div>
              <div style="font-size:.8rem;">
                Body map se ya neeche buttons se<br>koi bhi muscle group choose karo
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            _render_muscle_info_card(selected, ctx)
            
            info = MUSCLES[selected]
            cache_key = _get_cache_key("muscle", selected, ctx['goal'], ctx['level'], st.session_state["bc_intensity"])
            
            if cache_key not in st.session_state["bc_analysis_cache"]:
                with st.spinner(f"AI {info['label']} analysis bana raha hai..."):
                    analysis = _ai_muscle_analysis(selected, ctx, st.session_state["bc_intensity"])
                    st.session_state["bc_analysis_cache"][cache_key] = analysis

            st.markdown(st.session_state["bc_analysis_cache"][cache_key])
            
            _render_share_button(st.session_state["bc_analysis_cache"][cache_key], f"{selected}_{m.serial_number}")

            col_dl, col_regen = st.columns(2)
            with col_dl:
                st.download_button(
                    "⬇️ Download",
                    data=st.session_state["bc_analysis_cache"][cache_key],
                    file_name=f"{selected}_{m.serial_number}_{date.today()}.txt",
                    mime="text/plain",
                    key=f"dl_{selected}",
                    use_container_width=True
                )
            with col_regen:
                if st.button("🔄 Regenerate", key=f"regen_{selected}", use_container_width=True):
                    cache_key = _get_cache_key("muscle", selected, ctx['goal'], ctx['level'], st.session_state["bc_intensity"])
                    if cache_key in st.session_state["bc_analysis_cache"]:
                        del st.session_state["bc_analysis_cache"][cache_key]
                    st.rerun()
            
            _render_exercise_videos(selected)
    
    # ── Rest Timer ─────────────────────────────────────────────────
    st.divider()
    _render_rest_timer()

    # ── Workout Log ────────────────────────────────────────────────
    st.divider()
    _render_workout_log(m)

    # ── Progress Photos ────────────────────────────────────────────
    st.divider()
    _render_progress_photos()

    # ── All muscles quick grid ────────────────────────────────────
    st.divider()
    st.markdown('<div class="bc-sec">🗂️ Sab Muscle Groups</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (key, info) in enumerate(MUSCLES.items()):
        with cols[i % 5]:
            is_sel = st.session_state["bc_muscle"] == key
            cache_key = _get_cache_key("muscle", key, ctx['goal'], ctx['level'], st.session_state["bc_intensity"])
            cache_done = cache_key in st.session_state["bc_analysis_cache"]
            tag = ("✅ " if cache_done else "") + info["icon"] + " " + info["label"]
            if st.button(tag, key=f"bc_grid_{key}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state["bc_muscle"] = key if not is_sel else None
                st.session_state["bc_preset"] = None
                st.rerun()