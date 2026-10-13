"""
GymPro Theme System v6.0 - Premium Dark Edition
12 Premium Themes with Glass Effects
"""

import streamlit as st
from datetime import date
import random

# ─── THEMES - Premium Dark Dashboard ──────────
THEMES = {
    "black_white": {
        "name": "Black & White",
        "emoji": "⚪⚫",
        "bg": "#000000",
        "sidebar_bg": "rgba(0, 0, 0, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#FFFFFF",
        "primary_gradient": "linear-gradient(135deg, #FFFFFF, #CCCCCC)",
        "primary_dim": "rgba(255, 255, 255, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(255, 255, 255, 0.2)",
        "glow": "0 0 60px rgba(255, 255, 255, 0.15)",
        "vibe": "⚪⚫ Classic",
        "motivation": "Simplicity is Strength! 🖤🤍",
    },
    # 🔥 EXISTING THEMES
    "energy_burst": {
        "name": "Energy Burst",
        "emoji": "⚡",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#FFC947",
        "primary_gradient": "linear-gradient(135deg, #FFC947, #FF6B6B)",
        "primary_dim": "rgba(255, 201, 71, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(255, 201, 71, 0.2)",
        "glow": "0 0 60px rgba(255, 201, 71, 0.15)",
        "vibe": "⚡ Premium Gold",
        "motivation": "Dominate Your Gym! 💪",
    },
    "royal_purple": {
        "name": "Royal Purple",
        "emoji": "👑",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#A855F7",
        "primary_gradient": "linear-gradient(135deg, #A855F7, #8B5CF6)",
        "primary_dim": "rgba(168, 85, 247, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(168, 85, 247, 0.2)",
        "glow": "0 0 60px rgba(168, 85, 247, 0.15)",
        "vibe": "👑 Royal Purple",
        "motivation": "Rule Like a King! 👑",
    },
    "ocean_blue": {
        "name": "Ocean Blue",
        "emoji": "🌊",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#3B82F6",
        "primary_gradient": "linear-gradient(135deg, #3B82F6, #06B6D4)",
        "primary_dim": "rgba(59, 130, 246, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(59, 130, 246, 0.2)",
        "glow": "0 0 60px rgba(59, 130, 246, 0.15)",
        "vibe": "🌊 Deep Ocean",
        "motivation": "Flow Like Water! 🌊",
    },
    "emerald_green": {
        "name": "Emerald Green",
        "emoji": "💎",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#10B981",
        "primary_gradient": "linear-gradient(135deg, #10B981, #34D399)",
        "primary_dim": "rgba(16, 185, 129, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(16, 185, 129, 0.2)",
        "glow": "0 0 60px rgba(16, 185, 129, 0.15)",
        "vibe": "💎 Emerald Fresh",
        "motivation": "Grow Stronger Daily! 💪",
    },
    "crimson_red": {
        "name": "Crimson Red",
        "emoji": "🔥",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#EF4444",
        "primary_gradient": "linear-gradient(135deg, #EF4444, #DC2626)",
        "primary_dim": "rgba(239, 68, 68, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(239, 68, 68, 0.2)",
        "glow": "0 0 60px rgba(239, 68, 68, 0.15)",
        "vibe": "🔥 Intense Crimson",
        "motivation": "Burn Calories, Not Goals! 🔥",
    },
    "cyber_cyan": {
        "name": "Cyber Cyan",
        "emoji": "🚀",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#06B6D4",
        "primary_gradient": "linear-gradient(135deg, #06B6D4, #3B82F6)",
        "primary_dim": "rgba(6, 182, 212, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(6, 182, 212, 0.2)",
        "glow": "0 0 60px rgba(6, 182, 212, 0.15)",
        "vibe": "🚀 Cyber Future",
        "motivation": "Upgrade Your Limits! 🚀",
    },
    "neon_pink": {
        "name": "Neon Pink",
        "emoji": "💖",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#EC4899",
        "primary_gradient": "linear-gradient(135deg, #EC4899, #F472B6)",
        "primary_dim": "rgba(236, 72, 153, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(236, 72, 153, 0.2)",
        "glow": "0 0 60px rgba(236, 72, 153, 0.15)",
        "vibe": "💖 Neon Glow",
        "motivation": "Shine Like a Star! ✨",
    },
    "midnight_galaxy": {
        "name": "Midnight Galaxy",
        "emoji": "🌌",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#8B5CF6",
        "primary_gradient": "linear-gradient(135deg, #8B5CF6, #EC4899)",
        "primary_dim": "rgba(139, 92, 246, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(139, 92, 246, 0.2)",
        "glow": "0 0 60px rgba(139, 92, 246, 0.15)",
        "vibe": "🌌 Galaxy Dreams",
        "motivation": "Reach for the Stars! 🌟",
    },

    # 🆕 NEW THEMES
    "sunset_orange": {
        "name": "Sunset Orange",
        "emoji": "🌅",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#F97316",
        "primary_gradient": "linear-gradient(135deg, #F97316, #F59E0B)",
        "primary_dim": "rgba(249, 115, 22, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(249, 115, 22, 0.2)",
        "glow": "0 0 60px rgba(249, 115, 22, 0.15)",
        "vibe": "🌅 Warm Sunset",
        "motivation": "End the Day Strong! 💪",
    },
    "ice_blue": {
        "name": "Ice Blue",
        "emoji": "❄️",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#38BDF8",
        "primary_gradient": "linear-gradient(135deg, #38BDF8, #818CF8)",
        "primary_dim": "rgba(56, 189, 248, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(56, 189, 248, 0.2)",
        "glow": "0 0 60px rgba(56, 189, 248, 0.15)",
        "vibe": "❄️ Cool Ice",
        "motivation": "Stay Frosty! ❄️",
    },
    "forest_green": {
        "name": "Forest Green",
        "emoji": "🌲",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#22C55E",
        "primary_gradient": "linear-gradient(135deg, #22C55E, #16A34A)",
        "primary_dim": "rgba(34, 197, 94, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(34, 197, 94, 0.2)",
        "glow": "0 0 60px rgba(34, 197, 94, 0.15)",
        "vibe": "🌲 Forest Fresh",
        "motivation": "Grow Like a Tree! 🌳",
    },
    "cherry_blossom": {
        "name": "Cherry Blossom",
        "emoji": "🌸",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#F472B6",
        "primary_gradient": "linear-gradient(135deg, #F472B6, #EC4899)",
        "primary_dim": "rgba(244, 114, 182, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(244, 114, 182, 0.2)",
        "glow": "0 0 60px rgba(244, 114, 182, 0.15)",
        "vibe": "🌸 Spring Vibes",
        "motivation": "Bloom Where You Are! 🌸",
    },
    "golden_hour": {
        "name": "Golden Hour",
        "emoji": "🌇",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#FBBF24",
        "primary_gradient": "linear-gradient(135deg, #FBBF24, #F59E0B)",
        "primary_dim": "rgba(251, 191, 36, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(251, 191, 36, 0.2)",
        "glow": "0 0 60px rgba(251, 191, 36, 0.15)",
        "vibe": "🌇 Golden Hour",
        "motivation": "Make It Golden! ✨",
    },
    "dark_knight": {
        "name": "Dark Knight",
        "emoji": "🦇",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#94A3B8",
        "primary_gradient": "linear-gradient(135deg, #94A3B8, #64748B)",
        "primary_dim": "rgba(148, 163, 184, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(148, 163, 184, 0.2)",
        "glow": "0 0 60px rgba(148, 163, 184, 0.15)",
        "vibe": "🦇 Dark Knight",
        "motivation": "Be the Hero! 🦸",
    },
    "tropical_sunset": {
        "name": "Tropical Sunset",
        "emoji": "🏝️",
        "bg": "#0A0A0A",
        "sidebar_bg": "rgba(10, 10, 10, 0.95)",
        "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A",
        "primary": "#F472B6",
        "primary_gradient": "linear-gradient(135deg, #F472B6, #F97316)",
        "primary_dim": "rgba(244, 114, 182, 0.15)",
        "success": "#1EB980",
        "danger": "#FF5A5A",
        "text": "#FFFFFF",
        "text_muted": "#8A8A8A",
        "text_dim": "#5A5A5A",
        "shadow": "rgba(244, 114, 182, 0.2)",
        "glow": "0 0 60px rgba(244, 114, 182, 0.15)",
        "vibe": "🏝️ Tropical Vibes",
        "motivation": "Paradise Workout! 🌴",
    },
}

THEME_KEYS = list(THEMES.keys())
THEME_NAMES = {k: f"{v['emoji']} {v['name']}" for k, v in THEMES.items()}

def get_daily_theme() -> str:
    idx = date.today().toordinal() % len(THEME_KEYS)
    return THEME_KEYS[idx]

def get_random_theme() -> str:
    return random.choice(THEME_KEYS)

def build_css(key: str) -> str:
    t = THEMES.get(key, THEMES["energy_burst"])

    p = t["primary"]
    p_grad = t["primary_gradient"]
    p_dim = t["primary_dim"]
    bg = t["bg"]
    s_bg = t["sidebar_bg"]
    c_bg = t["card_bg"]
    border = t["border"]
    text = t["text"]
    t_muted = t["text_muted"]
    success = t["success"]
    danger = t["danger"]
    shadow = t["shadow"]
    glow = t["glow"]

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Target font specifically — wildcard on SVG causes mobile double-render */
body, p, span, div, h1, h2, h3, h4, h5, h6,
button, input, select, textarea, label,
td, th, li, a, small, caption {{
    font-family: 'Inter', sans-serif !important;
}}

/* ── 🔥 FIX: Expander arrow - Complete fix for "arrwEditMember D" leak ── */
details > summary {{
    list-style: none !important;
    -webkit-appearance: none !important;
}}
details > summary::-webkit-details-marker,
details > summary::marker {{
    display: none !important;
    content: '' !important;
}}

/* 🔥 FIX: Hide _arr class completely */
[data-testid="stExpander"] summary ._arr,
[data-testid="stExpander"] summary span[class*="_arr"],
[data-testid="stExpander"] summary .stExpanderArrow {{
    display: none !important;
    font-size: 0 !important;
    color: transparent !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}}

/* 🔥 Force proper text rendering in expanders */
[data-testid="stExpander"] summary {{
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}}
[data-testid="stExpander"] summary span {{
    font-size: inherit !important;
    color: inherit !important;
    display: inline !important;
}}
[data-testid="stExpander"] summary span:empty {{
    display: none !important;
}}

.stApp {{
    background: {bg}!important;
    color: {text}!important;
}}

/* ── Premium Glass Cards ───────────────────────────────────── */
.metric-card, [data-testid="metric-container"],.pro-card {{
    background: {c_bg}!important;
    backdrop-filter: blur(16px) saturate(1.2)!important;
    -webkit-backdrop-filter: blur(16px) saturate(1.2)!important;
    border: 1px solid {border}!important;
    border-radius: 12px!important;
    padding: 20px!important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4)!important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)!important;
}}

.metric-card:hover, [data-testid="metric-container"]:hover,.pro-card:hover {{
    border-color: {p}!important;
    box-shadow: 0 8px 24px {shadow}, {glow}!important;
    transform: translateY(-3px)!important;
}}

/* ── KPI Metrics ───────────────────────────────────────────── */
[data-testid="stMetricLabel"] {{
    color: {t_muted}!important;
    font-size: 12px!important;
    text-transform: uppercase!important;
    letter-spacing: 1.2px!important;
    font-weight: 600!important;
}}

[data-testid="stMetricValue"] {{
    color: {text}!important;
    font-size: 32px!important;
    font-weight: 800!important;
}}

/* ── Sidebar - Premium Buttons ─────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: {s_bg}!important;
    backdrop-filter: blur(24px)!important;
    border-right: 1px solid {border}!important;
}}

section[data-testid="stSidebar"].stButton > button {{
    background: {p}!important;
    color: #0A0A0A!important;
    font-weight: 700!important;
    border-radius: 10px!important;
    border: none!important;
    padding: 12px!important;
    transition: all 0.3s ease!important;
}}

section[data-testid="stSidebar"].stButton > button:hover {{
    transform: scale(1.03)!important;
    box-shadow: 0 6px 20px {shadow}!important;
}}

/* ── Main Buttons ──────────────────────────────────────────── */
.stButton > button {{
    background: {p}!important;
    color: #0A0A0A!important;
    font-weight: 700!important;
    border-radius: 10px!important;
    border: none!important;
    padding: 10px 24px!important;
    transition: all 0.3s ease!important;
}}

.stButton > button:hover {{
    background: {p}dd!important;
    box-shadow: 0 6px 20px {shadow}!important;
    transform: translateY(-2px)!important;
}}

/* ── Tables ────────────────────────────────────────────────── */
.stDataFrame {{
    background: {c_bg}!important;
    border: 1px solid {border}!important;
    border-radius: 10px!important;
}}

.stDataFrame thead th {{
    background: {c_bg}!important;
    color: {p}!important;
    font-weight: 700!important;
    border-bottom: 2px solid {p_dim}!important;
}}

.stDataFrame tbody tr:hover td {{
    background: {p_dim}!important;
}}

/* ── Inputs ────────────────────────────────────────────────── */
.stTextInput input,.stSelectbox > div > div,.stNumberInput input {{
    background: {c_bg}!important;
    border: 1px solid {border}!important;
    color: {text}!important;
    border-radius: 10px!important;
}}

.stTextInput input:focus {{
    border-color: {p}!important;
    box-shadow: 0 0 0 3px {p_dim}!important;
}}

/* ── Status Badges ─────────────────────────────────────────── */
.badge-paid {{background: {success}; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700;}}
.badge-partial {{background: {p}; color: #0A0A0A; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700;}}
.badge-unpaid {{background: {danger}; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700;}}

/* ── Section Header ────────────────────────────────────────── */
.section-header {{
    font-size: 18px;
    font-weight: 700;
    color: {text};
    margin: 24px 0 16px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid {border};
}}

/* ── Top Accent Line ───────────────────────────────────────── */
.stApp::before {{
    content: "";
    display: block;
    height: 3px;
    background: linear-gradient(90deg, transparent, {p}, transparent)!important;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
    box-shadow: 0 0 30px {shadow}!important;
}}

/* ── SELECTBOX TEXT VISIBILITY FIX ────────────────────────── */
/* Force white text in selectbox */
div[data-testid="stSelectbox"] label {{
    color: {text}!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    background: {c_bg}!important;
    border: 1px solid {border}!important;
    border-radius: 10px!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] {{
    color: {text}!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] span {{
    color: {text}!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="listbox"] {{
    background: {c_bg}!important;
    border: 1px solid {border}!important;
    border-radius: 10px!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"] {{
    background: {c_bg}!important;
    color: {text}!important;
    padding: 8px 12px!important;
    border-radius: 6px!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"]:hover {{
    background: {p_dim}!important;
    color: {p}!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"][aria-selected="true"] {{
    background: {p_grad}!important;
    color: #0A0A0A!important;
    font-weight: 700!important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {{
    fill: {text}!important;
    opacity: 0.6!important;
}}

/* Sidebar selectbox */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label {{
    color: {text}!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    background: {c_bg}!important;
    border: 1px solid {border}!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] {{
    color: {text}!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] span {{
    color: {text}!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="listbox"] {{
    background: {c_bg}!important;
    border: 1px solid {border}!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"] {{
    background: {c_bg}!important;
    color: {text}!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"]:hover {{
    background: {p_dim}!important;
    color: {p}!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"][aria-selected="true"] {{
    background: {p_grad}!important;
    color: #0A0A0A!important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {{
    fill: {text}!important;
}}

/* Force all sidebar text to white */
section[data-testid="stSidebar"] * {{
    color: {text}!important;
}}

section[data-testid="stSidebar"] label {{
    color: {text}!important;
}}

section[data-testid="stSidebar"] .stCheckbox label {{
    color: {text}!important;
}}

section[data-testid="stSidebar"] .stCheckbox label span {{
    color: {text}!important;
}}

/* ── Scoped fix for any remaining stray text ──────────────── */
.stMarkdown:empty {{
    display: none !important;
}}
.stMarkdown:has(>:empty:only-child) {{
    display: none !important;
}}
</style>
"""

def apply_theme(key: str = None, auto_rotate: bool = False):
    if key is None:
        key = "energy_burst" if not auto_rotate else get_daily_theme()

    if key not in THEMES:
        key = "energy_burst"

    st.session_state['current_theme'] = key
    st.markdown(build_css(key), unsafe_allow_html=True)

    t = THEMES[key]
    st.sidebar.markdown(f"""
        <div style="
            background: {t['card_bg']};
            border: 1px solid {t['border']};
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            text-align: center;
            backdrop-filter: blur(12px);
        ">
            <div style="font-size: 2.5rem;">{t['emoji']}</div>
            <div style="font-weight: 800; color: {t['text']}; font-size: 1rem;">
                {t['name']}
            </div>
            <div style="font-size: 0.75rem; color: {t['primary']}; font-weight: 600;">
                {t['vibe']}
            </div>
            <div style="font-size: 0.65rem; color: {t['text_muted']}; font-style: italic; margin-top: 6px;">
                "{t['motivation']}"
            </div>
        </div>
    """, unsafe_allow_html=True)

    return key