"""
GymPro — AI Body Coach
Interactive SVG body map with clickable muscle groups + AI-powered analysis.
Integrates with Member Portal (member_portal.py).
"""

import streamlit as st
import streamlit.components.v1 as components
import os, requests
from datetime import date, datetime

# ─────────────────────────────────────────────────────────────────────────────
# GROQ AI HELPER  (mirrors member_portal._groq)
# ─────────────────────────────────────────────────────────────────────────────

def _groq(messages: list, max_tokens: int = 1800) -> str:
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

# Quick-action muscle group presets
PRESETS = {
    "Full Body":    list(MUSCLES.keys()),
    "Upper Body":   ["chest", "shoulders", "biceps", "triceps", "back", "forearms"],
    "Lower Body":   ["legs", "glutes", "calves"],
    "Core Strength":["core", "back", "glutes"],
}


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE SVG BODY MAP (HTML Component)
# ─────────────────────────────────────────────────────────────────────────────

def _build_body_html(selected: str | None, highlight_set: set | None = None) -> str:
    """Return full HTML page with clickable SVG body + JS postMessage bridge."""

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

    # Body shape paths
    body_svg = """
<!-- ── Head ── -->
<ellipse cx="120" cy="42" rx="22" ry="26" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
<!-- Neck -->
<rect x="112" y="64" width="16" height="14" rx="4" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Torso -->
<path d="M80,78 Q70,82 68,110 L68,178 Q68,182 72,182 L168,182 Q172,182 172,178 L172,110 Q170,82 160,78 Z"
      fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
<!-- Left Arm upper -->
<path d="M80,82 Q62,88 58,130 L64,132 Q68,90 82,86 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Left Arm lower -->
<path d="M58,130 Q54,158 56,180 L64,178 Q62,158 64,132 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Right Arm upper -->
<path d="M160,82 Q178,88 182,130 L176,132 Q172,90 158,86 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Right Arm lower -->
<path d="M182,130 Q186,158 184,180 L176,178 Q178,158 176,132 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Left hand -->
<ellipse cx="60" cy="185" rx="8" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Right hand -->
<ellipse cx="180" cy="185" rx="8" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Hips / Pelvis -->
<path d="M72,182 Q68,200 72,210 L168,210 Q172,200 168,182 Z" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
<!-- Left Leg upper -->
<path d="M88,210 Q78,240 80,290 L98,290 Q96,240 102,210 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Right Leg upper -->
<path d="M152,210 Q162,240 160,290 L142,290 Q144,240 138,210 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Left Leg lower -->
<path d="M80,290 Q76,330 78,360 L96,360 Q94,330 98,290 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Right Leg lower -->
<path d="M160,290 Q164,330 162,360 L144,360 Q146,330 142,290 Z" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Left foot -->
<ellipse cx="87" cy="365" rx="12" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
<!-- Right foot -->
<ellipse cx="153" cy="365" rx="12" ry="7" fill="#1e293b" stroke="#334155" stroke-width="1"/>
"""

    # Muscle highlight overlays (positioned on body)
    muscle_overlays = "".join([
        rect("chest",     88,  90,  64, 38),
        rect("shoulders", 62,  82,  28, 26),   # left
        rect("shoulders",150,  82,  28, 26),   # right (same key, clicks both)
        rect("back",      88, 130,  64, 36),
        rect("core",      88, 148,  64, 32),
        rect("biceps",    57, 108,  24, 30),   # left
        rect("biceps",   158, 108,  24, 30),   # right
        rect("triceps",   57, 140,  24, 30),   # left
        rect("triceps",  158, 140,  24, 30),   # right
        rect("forearms",  56, 170,  24, 28),   # left
        rect("forearms",  160,170,  24, 28),   # right
        rect("glutes",    88, 182,  64, 26),
        rect("legs",      80, 210,  36, 76),   # left
        rect("legs",     124, 210,  36, 76),   # right
        rect("calves",    80, 290,  36, 64),   # left
        rect("calves",   124, 290,  36, 64),   # right
    ])

    # Selected glow colour
    sel_color = MUSCLES[selected]["color"] if selected else "#7c3aed"

    # Selected label HTML (computed outside f-string to avoid nesting issues)
    if selected:
        sel_label_html = (
            f'<div class="selected-label">'
            f'{MUSCLES[selected]["icon"]} {MUSCLES[selected]["label"]} selected</div>'
        )
        sel_label_css = (
            f".selected-label {{"
            f"color:{sel_color};font-size:14px;font-weight:800;"
            f"margin-top:6px;text-align:center;"
            f"text-shadow:0 0 12px {sel_color}88;}}"
        )
    else:
        sel_label_html = '<div class="hint">☝️ Muscle par click karo — AI analysis milegi</div>'
        sel_label_css  = ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: #0a0a14;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 420px;
    font-family: 'Inter', 'Segoe UI', sans-serif;
  }}
  .title {{
    color: #a78bfa;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 10px 0 6px;
  }}
  svg {{
    overflow: visible;
    filter: drop-shadow(0 0 18px #7c3aed33);
  }}
  .muscle-group {{
    cursor: pointer;
    transition: all 0.2s;
  }}
  .muscle-group rect {{
    transition: fill-opacity 0.2s, stroke-width 0.2s;
  }}
  .muscle-group:hover rect {{
    fill-opacity: 0.45 !important;
    stroke-width: 3 !important;
  }}
  .muscle-group.selected rect {{
    fill-opacity: 0.65 !important;
    stroke-width: 3.5 !important;
    filter: drop-shadow(0 0 8px {sel_color});
  }}
  .muscle-group.selected text {{ font-size: 10px; }}
  .muscle-group.highlighted rect {{
    fill-opacity: 0.38 !important;
    stroke-width: 2.5 !important;
    animation: pulse 1.8s ease-in-out infinite;
  }}
  @keyframes pulse {{
    0%,100% {{ fill-opacity: 0.38; }}
    50%      {{ fill-opacity: 0.6; }}
  }}
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
# AI ANALYSIS GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def _build_member_context(m, records, goal: str, level: str) -> dict:
    """Compile member stats into a dict for prompts."""
    latest = records[-1] if records else None
    weight = float(latest.weight_kg) if latest else None
    height = None  # not stored on Member model; user enters manually

    bmi, bmi_cat = None, "Unknown"
    if weight and height:
        bmi = weight / ((height / 100) ** 2)
        bmi_cat = (
            "Underweight" if bmi < 18.5 else
            "Normal"      if bmi < 25   else
            "Overweight"  if bmi < 30   else "Obese"
        )

    age = None
    if m.dob:
        try:
            dob = date.fromisoformat(str(m.dob))
            age = (date.today() - dob).days // 365
        except Exception:
            pass

    return {
        "name":    m.full_name,
        "gender":  m.gender or "Not specified",
        "age":     age,
        "weight":  weight,
        "bmi":     bmi,
        "bmi_cat": bmi_cat,
        "goal":    goal,
        "level":   level,
        "membership": m.membership_type,
    }


def _ai_muscle_analysis(muscle_key: str, ctx: dict) -> str:
    m_info = MUSCLES[muscle_key]
    stats_str = (
        f"Name: {ctx['name']}, Gender: {ctx['gender']}, "
        f"Age: {ctx['age'] or 'unknown'}, "
        f"Weight: {ctx['weight'] or 'unknown'} kg, "
        f"BMI: {ctx['bmi']:.1f if ctx['bmi'] else 'unknown'} ({ctx['bmi_cat']}), "
        f"Goal: {ctx['goal']}, Level: {ctx['level']}"
    )
    prompt = f"""You are GymPro AI Body Coach. Analyze the {m_info['label']} muscle group for this member.

Member stats: {stats_str}

Provide a structured analysis in Roman Urdu + English:

## 💪 {m_info['icon']} {m_info['label']} Analysis

**1. Muscle Overview** (2 lines — kya karta hai yeh muscle)

**2. Member ke liye Personalized Advice** (based on BMI, age, gender, goal — 3-4 lines)

**3. Best Exercises (Top 5)**
List each with: Exercise name | Sets × Reps | Rest | Difficulty

**4. Weekly Plan**
| Day | Exercise | Sets | Reps | Rest |
(3-4 rows)

**5. Pro Tips** (3 bullet points — form, breathing, common mistakes)

**6. Safety Warnings** (1-2 lines based on their BMI/level)

Keep it practical, encouraging, specific. No fluff."""

    return _groq([
        {"role": "system", "content": "You are an expert personal trainer and sports scientist. Respond in Roman Urdu mixed with English. Be specific and data-driven."},
        {"role": "user", "content": prompt},
    ], max_tokens=1600)


def _ai_preset_plan(preset_name: str, muscles: list, ctx: dict) -> str:
    muscle_labels = ", ".join(MUSCLES[k]["label"] for k in muscles)
    stats_str = (
        f"Name: {ctx['name']}, Gender: {ctx['gender']}, "
        f"Age: {ctx['age'] or 'N/A'}, Weight: {ctx['weight'] or 'N/A'} kg, "
        f"BMI: {round(ctx['bmi'],1) if ctx['bmi'] else 'N/A'} ({ctx['bmi_cat']}), "
        f"Goal: {ctx['goal']}, Level: {ctx['level']}"
    )
    prompt = f"""You are GymPro AI Body Coach. Create a complete {preset_name} workout plan.

Muscles targeted: {muscle_labels}
Member stats: {stats_str}

Provide in Roman Urdu + English:

## 🏋️ {preset_name} — Complete Plan

**Workout Summary** (goal-specific — 2 lines)

**Warm-up** (5 min — 3 exercises)

**Main Workout**
| Exercise | Sets | Reps | Rest | Muscle |
(8-12 exercises)

**Cool-down** (3 min)

**Weekly Schedule** (which days to do this)

**Nutrition Tip** (post-workout ke liye)

**Motivation** (1 powerful line)"""

    return _groq([
        {"role": "system", "content": "You are an expert personal trainer. Respond in Roman Urdu + English."},
        {"role": "user", "content": prompt},
    ], max_tokens=2000)


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
      <div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#475569;margin-top:3px;">
        <span>Under 18.5</span><span>Normal 18.5–25</span><span>Over 30</span>
      </div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER  (called from member_portal.py)
# ─────────────────────────────────────────────────────────────────────────────

def render_body_coach(m, records):
    """
    Full AI Body Coach tab.
    m       — Member ORM object
    records — list of BodyMeasurement objects (may be empty)
    """

    # ── Session state init ────────────────────────────────────────
    if "bc_muscle"  not in st.session_state: st.session_state["bc_muscle"]  = None
    if "bc_preset"  not in st.session_state: st.session_state["bc_preset"]  = None
    if "bc_analysis"not in st.session_state: st.session_state["bc_analysis"]= {}
    if "bc_goal"    not in st.session_state: st.session_state["bc_goal"]    = "Muscle Building"
    if "bc_level"   not in st.session_state: st.session_state["bc_level"]   = "Beginner"
    if "bc_height"  not in st.session_state: st.session_state["bc_height"]  = 170

    st.markdown("""
    <style>
    .bc-sec {font-size:1rem;font-weight:700;color:#a78bfa;border-bottom:1px solid #7c3aed22;
             padding-bottom:.3rem;margin:1rem 0 .7rem;display:flex;align-items:center;gap:.4rem;}
    .bc-tag {display:inline-flex;align-items:center;gap:.35rem;background:#1e293b;
             border:1px solid #334155;border-radius:8px;padding:.3rem .75rem;
             font-size:.78rem;color:#e2e8f0;cursor:pointer;transition:all .15s;}
    .bc-tag:hover {border-color:#7c3aed;color:#a78bfa;}
    .bc-tag.active {background:#7c3aed22;border-color:#7c3aed;color:#a78bfa;font-weight:700;}
    .bc-card {background:linear-gradient(135deg,#0f172a,#1a1a2e);border:1px solid #1e293b;
              border-radius:16px;padding:1.2rem;margin-bottom:.8rem;}
    .bc-muscle-btn {display:inline-flex;align-items:center;gap:.3rem;margin:.2rem;
                    padding:.4rem .9rem;border-radius:10px;font-size:.8rem;font-weight:700;
                    cursor:pointer;transition:all .2s;}
    </style>
    """, unsafe_allow_html=True)

    # ── Member config ─────────────────────────────────────────────
    with st.expander("⚙️ Apni Details Set Karo (pehli baar zaroor karein)", expanded=not bool(records)):
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.session_state["bc_goal"] = st.selectbox(
                "🎯 Fitness Goal",
                ["Muscle Building", "Fat Loss", "Strength", "Endurance", "General Fitness"],
                index=["Muscle Building","Fat Loss","Strength","Endurance","General Fitness"]
                    .index(st.session_state["bc_goal"]) if st.session_state["bc_goal"] in
                    ["Muscle Building","Fat Loss","Strength","Endurance","General Fitness"] else 0
            )
        with cc2:
            st.session_state["bc_level"] = st.selectbox(
                "📊 Experience Level",
                ["Beginner", "Intermediate", "Advanced"],
                index=["Beginner","Intermediate","Advanced"].index(st.session_state["bc_level"])
            )
        with cc3:
            st.session_state["bc_height"] = st.number_input(
                "📏 Height (cm)", 100, 250,
                st.session_state["bc_height"]
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

    # BMI bar
    if ctx.get("bmi"):
        _render_bmi(ctx["bmi"], ctx.get("weight"))

    st.markdown('<div class="bc-sec">⚡ Quick Actions</div>', unsafe_allow_html=True)

    # ── Quick action buttons ──────────────────────────────────────
    qa_cols = st.columns(5)
    preset_labels = list(PRESETS.keys()) + ["Clear"]
    for i, lbl in enumerate(preset_labels):
        with qa_cols[i]:
            active = (st.session_state["bc_preset"] == lbl)
            btn_style = "primary" if active else "secondary"
            if st.button(("✅ " if active else "") + lbl,
                         key=f"bc_preset_{lbl}",
                         use_container_width=True,
                         type=btn_style):
                if lbl == "Clear":
                    st.session_state["bc_muscle"]  = None
                    st.session_state["bc_preset"]  = None
                else:
                    st.session_state["bc_preset"]  = lbl
                    st.session_state["bc_muscle"]  = None
                st.rerun()

    # ── Generate preset plan ──────────────────────────────────────
    preset = st.session_state.get("bc_preset")
    if preset and preset != "Clear":
        cache_key = f"bc_preset_plan_{preset}_{ctx['goal']}_{ctx['level']}"
        if cache_key not in st.session_state["bc_analysis"]:
            with st.spinner(f"AI {preset} plan bana raha hai..."):
                plan = _ai_preset_plan(preset, PRESETS[preset], ctx)
                st.session_state["bc_analysis"][cache_key] = plan
        st.markdown(f'<div class="bc-sec">📋 {preset} Plan</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown(st.session_state["bc_analysis"][cache_key])
        st.download_button(
            f"⬇️ Download {preset} Plan",
            data=st.session_state["bc_analysis"][cache_key],
            file_name=f"{preset.replace(' ','_').lower()}_{m.serial_number}_{date.today()}.txt",
            mime="text/plain",
            key=f"dl_{preset}"
        )
        st.divider()

    # ── Body map + muscle selection ───────────────────────────────
    st.markdown('<div class="bc-sec">🫀 Interactive Body Map</div>', unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 2])

    with left_col:
        # Build highlight set for preset
        highlight_set = set(PRESETS[preset]) if preset and preset in PRESETS else None
        body_html = _build_body_html(st.session_state["bc_muscle"], highlight_set)

        # Render body SVG — use iframe-like component
        # We poll via a hidden text_input trick for click events
        components.html(body_html, height=420, scrolling=False)

        # Fallback: muscle select buttons below map
        st.markdown('<div style="margin-top:.5rem;">', unsafe_allow_html=True)
        for key, info in MUSCLES.items():
            is_sel = st.session_state["bc_muscle"] == key
            lbl = ("✅ " if is_sel else "") + info["icon"] + " " + info["label"]
            if st.button(lbl, key=f"bc_m_{key}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state["bc_muscle"]  = key if not is_sel else None
                st.session_state["bc_preset"]  = None
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
            info = MUSCLES[selected]
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.75rem;">
              <div style="width:44px;height:44px;border-radius:10px;
                          background:{info['color']}22;border:2px solid {info['color']};
                          display:flex;align-items:center;justify-content:center;
                          font-size:1.4rem;">{info['icon']}</div>
              <div>
                <div style="font-size:1.25rem;font-weight:900;color:{info['color']};">
                  {info['label']}
                </div>
                <div style="font-size:.75rem;color:#64748b;">
                  {ctx['goal']} · {ctx['level']} · {ctx['gender']}
                  {f" · Age {ctx['age']}" if ctx['age'] else ""}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            cache_key = f"bc_muscle_{selected}_{ctx['goal']}_{ctx['level']}"
            if cache_key not in st.session_state["bc_analysis"]:
                with st.spinner(f"AI {info['label']} analysis bana raha hai..."):
                    analysis = _ai_muscle_analysis(selected, ctx)
                    st.session_state["bc_analysis"][cache_key] = analysis

            st.markdown(st.session_state["bc_analysis"][cache_key])

            col_dl, col_regen = st.columns(2)
            with col_dl:
                st.download_button(
                    "⬇️ Download",
                    data=st.session_state["bc_analysis"][cache_key],
                    file_name=f"{selected}_{m.serial_number}_{date.today()}.txt",
                    mime="text/plain",
                    key=f"dl_{selected}"
                )
            with col_regen:
                if st.button("🔄 Regenerate", key=f"regen_{selected}", use_container_width=True):
                    if cache_key in st.session_state["bc_analysis"]:
                        del st.session_state["bc_analysis"][cache_key]
                    st.rerun()

    # ── All muscles quick grid ────────────────────────────────────
    st.divider()
    st.markdown('<div class="bc-sec">🗂️ Sab Muscle Groups</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (key, info) in enumerate(MUSCLES.items()):
        with cols[i % 5]:
            is_sel = st.session_state["bc_muscle"] == key
            cache_done = f"bc_muscle_{key}_{ctx['goal']}_{ctx['level']}" in st.session_state["bc_analysis"]
            tag = ("✅ " if cache_done else "") + info["icon"] + " " + info["label"]
            if st.button(tag, key=f"bc_grid_{key}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state["bc_muscle"]  = key if not is_sel else None
                st.session_state["bc_preset"]  = None
                st.rerun()
