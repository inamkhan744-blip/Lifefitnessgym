"""
GymPro Theme System v7.0 - Premium Duotone Edition
18 Themes with Advanced Glass Effects & Deep Gradients
"""

import streamlit as st
from datetime import date
import random

# ─── THEMES ──────────
THEMES = {
    # 🔥 EXISTING THEMES (Kept Safe)
    "black_white": {
        "name": "Black & White", "emoji": "⚪⚫",
        "bg": "#000000", "sidebar_bg": "rgba(0, 0, 0, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#FFFFFF", "primary_gradient": "linear-gradient(135deg, #FFFFFF, #CCCCCC)",
        "primary_dim": "rgba(255, 255, 255, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(255, 255, 255, 0.2)",
        "glow": "0 0 60px rgba(255, 255, 255, 0.15)", "vibe": "⚪⚫ Classic", "motivation": "Simplicity is Strength! 🖤🤍",
    },
    "energy_burst": {
        "name": "Energy Burst", "emoji": "⚡",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#FFC947", "primary_gradient": "linear-gradient(135deg, #FFC947, #FF6B6B)",
        "primary_dim": "rgba(255, 201, 71, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(255, 201, 71, 0.2)",
        "glow": "0 0 60px rgba(255, 201, 71, 0.15)", "vibe": "⚡ Premium Gold", "motivation": "Dominate Your Gym! 💪",
    },
    "royal_purple": {
        "name": "Royal Purple", "emoji": "👑",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#A855F7", "primary_gradient": "linear-gradient(135deg, #A855F7, #8B5CF6)",
        "primary_dim": "rgba(168, 85, 247, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(168, 85, 247, 0.2)",
        "glow": "0 0 60px rgba(168, 85, 247, 0.15)", "vibe": "👑 Royal Purple", "motivation": "Rule Like a King! 👑",
    },
    "ocean_blue": {
        "name": "Ocean Blue", "emoji": "🌊",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#3B82F6", "primary_gradient": "linear-gradient(135deg, #3B82F6, #06B6D4)",
        "primary_dim": "rgba(59, 130, 246, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(59, 130, 246, 0.2)",
        "glow": "0 0 60px rgba(59, 130, 246, 0.15)", "vibe": "🌊 Deep Ocean", "motivation": "Flow Like Water! 🌊",
    },
    "emerald_green": {
        "name": "Emerald Green", "emoji": "💎",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#10B981", "primary_gradient": "linear-gradient(135deg, #10B981, #34D399)",
        "primary_dim": "rgba(16, 185, 129, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(16, 185, 129, 0.2)",
        "glow": "0 0 60px rgba(16, 185, 129, 0.15)", "vibe": "💎 Emerald Fresh", "motivation": "Grow Stronger Daily! 💪",
    },
    "crimson_red": {
        "name": "Crimson Red", "emoji": "🔥",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#EF4444", "primary_gradient": "linear-gradient(135deg, #EF4444, #DC2626)",
        "primary_dim": "rgba(239, 68, 68, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(239, 68, 68, 0.2)",
        "glow": "0 0 60px rgba(239, 68, 68, 0.15)", "vibe": "🔥 Intense Crimson", "motivation": "Burn Calories, Not Goals! 🔥",
    },
    "cyber_cyan": {
        "name": "Cyber Cyan", "emoji": "🚀",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#06B6D4", "primary_gradient": "linear-gradient(135deg, #06B6D4, #3B82F6)",
        "primary_dim": "rgba(6, 182, 212, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(6, 182, 212, 0.2)",
        "glow": "0 0 60px rgba(6, 182, 212, 0.15)", "vibe": "🚀 Cyber Future", "motivation": "Upgrade Your Limits! 🚀",
    },
    "neon_pink": {
        "name": "Neon Pink", "emoji": "💖",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#EC4899", "primary_gradient": "linear-gradient(135deg, #EC4899, #F472B6)",
        "primary_dim": "rgba(236, 72, 153, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(236, 72, 153, 0.2)",
        "glow": "0 0 60px rgba(236, 72, 153, 0.15)", "vibe": "💖 Neon Glow", "motivation": "Shine Like a Star! ✨",
    },
    "midnight_galaxy": {
        "name": "Midnight Galaxy", "emoji": "🌌",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#8B5CF6", "primary_gradient": "linear-gradient(135deg, #8B5CF6, #EC4899)",
        "primary_dim": "rgba(139, 92, 246, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(139, 92, 246, 0.2)",
        "glow": "0 0 60px rgba(139, 92, 246, 0.15)", "vibe": "🌌 Galaxy Dreams", "motivation": "Reach for the Stars! 🌟",
    },
    "sunset_orange": {
        "name": "Sunset Orange", "emoji": "🌅",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#F97316", "primary_gradient": "linear-gradient(135deg, #F97316, #F59E0B)",
        "primary_dim": "rgba(249, 115, 22, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(249, 115, 22, 0.2)",
        "glow": "0 0 60px rgba(249, 115, 22, 0.15)", "vibe": "🌅 Warm Sunset", "motivation": "End the Day Strong! 💪",
    },
    "ice_blue": {
        "name": "Ice Blue", "emoji": "❄️",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#38BDF8", "primary_gradient": "linear-gradient(135deg, #38BDF8, #818CF8)",
        "primary_dim": "rgba(56, 189, 248, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(56, 189, 248, 0.2)",
        "glow": "0 0 60px rgba(56, 189, 248, 0.15)", "vibe": "❄️ Cool Ice", "motivation": "Stay Frosty! ❄️",
    },
    "forest_green": {
        "name": "Forest Green", "emoji": "🌲",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#22C55E", "primary_gradient": "linear-gradient(135deg, #22C55E, #16A34A)",
        "primary_dim": "rgba(34, 197, 94, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(34, 197, 94, 0.2)",
        "glow": "0 0 60px rgba(34, 197, 94, 0.15)", "vibe": "🌲 Forest Fresh", "motivation": "Grow Like a Tree! 🌳",
    },
    "cherry_blossom": {
        "name": "Cherry Blossom", "emoji": "🌸",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#F472B6", "primary_gradient": "linear-gradient(135deg, #F472B6, #EC4899)",
        "primary_dim": "rgba(244, 114, 182, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(244, 114, 182, 0.2)",
        "glow": "0 0 60px rgba(244, 114, 182, 0.15)", "vibe": "🌸 Spring Vibes", "motivation": "Bloom Where You Are! 🌸",
    },
    "golden_hour": {
        "name": "Golden Hour", "emoji": "🌇",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#FBBF24", "primary_gradient": "linear-gradient(135deg, #FBBF24, #F59E0B)",
        "primary_dim": "rgba(251, 191, 36, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(251, 191, 36, 0.2)",
        "glow": "0 0 60px rgba(251, 191, 36, 0.15)", "vibe": "🌇 Golden Hour", "motivation": "Make It Golden! ✨",
    },
    "dark_knight": {
        "name": "Dark Knight", "emoji": "🦇",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#94A3B8", "primary_gradient": "linear-gradient(135deg, #94A3B8, #64748B)",
        "primary_dim": "rgba(148, 163, 184, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(148, 163, 184, 0.2)",
        "glow": "0 0 60px rgba(148, 163, 184, 0.15)", "vibe": "🦇 Dark Knight", "motivation": "Be the Hero! 🦸",
    },
    "tropical_sunset": {
        "name": "Tropical Sunset", "emoji": "🏝️",
        "bg": "#0A0A0A", "sidebar_bg": "rgba(10, 10, 10, 0.95)", "card_bg": "rgba(20, 20, 20, 0.85)",
        "border": "#2A2A2A", "primary": "#F472B6", "primary_gradient": "linear-gradient(135deg, #F472B6, #F97316)",
        "primary_dim": "rgba(244, 114, 182, 0.15)", "success": "#1EB980", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#8A8A8A", "text_dim": "#5A5A5A", "shadow": "rgba(244, 114, 182, 0.2)",
        "glow": "0 0 60px rgba(244, 114, 182, 0.15)", "vibe": "🏝️ Tropical Vibes", "motivation": "Paradise Workout! 🌴",
    },

    # 🚀 NEW PREMIUM DUOTONE THEMES (Background Gradients)
    "synthwave": {
        "name": "Synthwave 84", "emoji": "🌆",
        "bg": "radial-gradient(circle at top left, #1A0B2E, #0D0515)",
        "sidebar_bg": "rgba(13, 5, 21, 0.7)", "card_bg": "rgba(30, 15, 45, 0.6)",
        "border": "rgba(255, 0, 128, 0.3)", "primary": "#FF007F", "primary_gradient": "linear-gradient(135deg, #FF007F, #7000FF)",
        "primary_dim": "rgba(255, 0, 127, 0.15)", "success": "#00F0FF", "danger": "#FF5A5A",
        "text": "#FFFFFF", "text_muted": "#A78BFA", "text_dim": "#6D28D9", "shadow": "rgba(255, 0, 127, 0.3)",
        "glow": "0 0 40px rgba(255, 0, 128, 0.4)", "vibe": "🌆 Neon Nights", "motivation": "Rule the Night! 🌃",
    },
    "aurora": {
        "name": "Aurora Borealis", "emoji": "🌌",
        "bg": "linear-gradient(135deg, #022c22, #0f172a)",
        "sidebar_bg": "rgba(2, 44, 34, 0.6)", "card_bg": "rgba(15, 23, 42, 0.5)",
        "border": "rgba(52, 211, 153, 0.2)", "primary": "#34D399", "primary_gradient": "linear-gradient(135deg, #34D399, #3B82F6)",
        "primary_dim": "rgba(52, 211, 153, 0.15)", "success": "#34D399", "danger": "#F87171",
        "text": "#F8FAFC", "text_muted": "#94A3B8", "text_dim": "#475569", "shadow": "rgba(52, 211, 153, 0.3)",
        "glow": "0 0 50px rgba(52, 211, 153, 0.2)", "vibe": "🌌 Ethereal Glow", "motivation": "Shine Bright! ✨",
    },
    "cyberpunk": {
        "name": "Cyberpunk 2077", "emoji": "🤖",
        "bg": "linear-gradient(to right bottom, #111111, #1a1a2e)",
        "sidebar_bg": "rgba(17, 17, 17, 0.8)", "card_bg": "rgba(26, 26, 46, 0.7)",
        "border": "rgba(250, 204, 21, 0.3)", "primary": "#FACC15", "primary_gradient": "linear-gradient(135deg, #FACC15, #06B6D4)",
        "primary_dim": "rgba(250, 204, 21, 0.15)", "success": "#06B6D4", "danger": "#EF4444",
        "text": "#FFFFFF", "text_muted": "#94A3B8", "text_dim": "#475569", "shadow": "rgba(250, 204, 21, 0.2)",
        "glow": "0 0 40px rgba(250, 204, 21, 0.3)", "vibe": "🤖 Tech Future", "motivation": "Wake Up Samurai! ⚔️",
    },
    "luxury_gold": {
        "name": "Luxury Gold", "emoji": "🥇",
        "bg": "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        "sidebar_bg": "rgba(15, 12, 41, 0.8)", "card_bg": "rgba(48, 43, 99, 0.4)",
        "border": "rgba(255, 215, 0, 0.2)", "primary": "#FFD700", "primary_gradient": "linear-gradient(135deg, #FFD700, #FF8C00)",
        "primary_dim": "rgba(255, 215, 0, 0.15)", "success": "#10B981", "danger": "#EF4444",
        "text": "#FFFFFF", "text_muted": "#D1D5DB", "text_dim": "#6B7280", "shadow": "rgba(255, 215, 0, 0.3)",
        "glow": "0 0 60px rgba(255, 215, 0, 0.2)", "vibe": "🥇 Pure Luxury", "motivation": "Only the Best! 👑",
    },
    "deep_ocean": {
        "name": "Deep Ocean", "emoji": "🐋",
        "bg": "linear-gradient(to bottom, #000428, #004e92)",
        "sidebar_bg": "rgba(0, 4, 40, 0.8)", "card_bg": "rgba(0, 78, 146, 0.3)",
        "border": "rgba(0, 242, 254, 0.2)", "primary": "#00F2FE", "primary_gradient": "linear-gradient(135deg, #00F2FE, #4FACFE)",
        "primary_dim": "rgba(0, 242, 254, 0.15)", "success": "#38BDF8", "danger": "#F87171",
        "text": "#FFFFFF", "text_muted": "#93C5FD", "text_dim": "#1E3A8A", "shadow": "rgba(0, 242, 254, 0.3)",
        "glow": "0 0 50px rgba(0, 242, 254, 0.2)", "vibe": "🐋 Abyss Blue", "motivation": "Dive Deeper! 🌊",
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
    bg = t.get("bg", "#0A0A0A")
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

body, p, span, div, h1, h2, h3, h4, h5, h6,
button, input, select, textarea, label, td, th, li, a, small, caption {{
    font-family: 'Inter', sans-serif !important;
}}

/* Expander Fix */
details > summary {{ list-style: none !important; -webkit-appearance: none !important; }}
details > summary::-webkit-details-marker, details > summary::marker {{ display: none !important; content: '' !important; }}
[data-testid="stExpander"] summary ._arr, [data-testid="stExpander"] summary span[class*="_arr"], [data-testid="stExpander"] summary .stExpanderArrow {{
    display: none !important; font-size: 0 !important; color: transparent !important;
    width: 0 !important; height: 0 !important; overflow: hidden !important;
    position: absolute !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important;
}}
[data-testid="stExpander"] summary {{ display: flex !important; align-items: center !important; gap: 8px !important; }}
[data-testid="stExpander"] summary span {{ font-size: inherit !important; color: inherit !important; display: inline !important; }}
[data-testid="stExpander"] summary span:empty {{ display: none !important; }}

/* App Background - Upgraded to handle Gradients */
.stApp {{
    background: {bg}!important;
    background-attachment: fixed !important;
    color: {text}!important;
}}

/* Premium Glass Cards - Upgraded for better transparency */
.metric-card, [data-testid="metric-container"],.pro-card {{
    background: {c_bg}!important;
    backdrop-filter: blur(24px) saturate(1.5)!important;
    -webkit-backdrop-filter: blur(24px) saturate(1.5)!important;
    border: 1px solid {border}!important;
    border-radius: 16px!important;
    padding: 24px!important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 0 0 1px rgba(255,255,255,0.05)!important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1)!important;
}}

.metric-card:hover, [data-testid="metric-container"]:hover,.pro-card:hover {{
    border-color: {p}!important;
    box-shadow: 0 12px 40px {shadow}, {glow}!important;
    transform: translateY(-5px) scale(1.01)!important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {s_bg}!important;
    backdrop-filter: blur(30px)!important;
    border-right: 1px solid {border}!important;
}}

/* Buttons with Gradient */
.stButton > button, section[data-testid="stSidebar"] .stButton > button {{
    background: {p_grad}!important;
    color: #0A0A0A!important;
    font-weight: 700!important;
    border-radius: 12px!important;
    border: none!important;
    padding: 12px 24px!important;
    transition: all 0.3s ease!important;
    box-shadow: 0 4px 15px {shadow}!important;
}}

.stButton > button:hover, section[data-testid="stSidebar"] .stButton > button:hover {{
    transform: translateY(-2px) scale(1.02)!important;
    box-shadow: 0 8px 25px {shadow}, {glow}!important;
}}

/* KPI Metrics */
[data-testid="stMetricLabel"] {{ color: {t_muted}!important; font-size: 13px!important; text-transform: uppercase!important; letter-spacing: 1px!important; font-weight: 600!important; }}
[data-testid="stMetricValue"] {{ color: {text}!important; font-size: 34px!important; font-weight: 800!important; text-shadow: 0 2px 10px rgba(0,0,0,0.5)!important; }}

/* Tables */
.stDataFrame {{ background: {c_bg}!important; border: 1px solid {border}!important; border-radius: 12px!important; }}
.stDataFrame thead th {{ background: {c_bg}!important; color: {p}!important; font-weight: 700!important; border-bottom: 2px solid {p_dim}!important; }}
.stDataFrame tbody tr:hover td {{ background: {p_dim}!important; }}

/* Inputs */
.stTextInput input,.stSelectbox > div > div,.stNumberInput input {{
    background: {c_bg}!important; border: 1px solid {border}!important; color: {text}!important; border-radius: 10px!important; backdrop-filter: blur(10px)!important;
}}
.stTextInput input:focus {{ border-color: {p}!important; box-shadow: 0 0 0 3px {p_dim}!important; }}

/* Selectbox Fixes */
div[data-testid="stSelectbox"] label {{ color: {text}!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] {{ background: {c_bg}!important; border: 1px solid {border}!important; border-radius: 10px!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] {{ color: {text}!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] span {{ color: {text}!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="listbox"] {{ background: {c_bg}!important; border: 1px solid {border}!important; border-radius: 10px!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"] {{ background: {c_bg}!important; color: {text}!important; padding: 8px 12px!important; border-radius: 6px!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"]:hover {{ background: {p_dim}!important; color: {p}!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"][aria-selected="true"] {{ background: {p_grad}!important; color: #0A0A0A!important; font-weight: 700!important; }}
div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {{ fill: {text}!important; opacity: 0.6!important; }}

/* Sidebar Text Force */
section[data-testid="stSidebar"] * {{ color: {text}!important; }}

/* Badges */
.badge-paid {{background: {success}; color: #000; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700;}}
.badge-partial {{background: {p}; color: #000; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700;}}
.badge-unpaid {{background: {danger}; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 700;}}

/* Top Accent Line */
.stApp::before {{
    content: ""; display: block; height: 4px; background: {p_grad}!important;
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999; box-shadow: 0 0 20px {shadow}!important;
}}

/* Fix for stray text */
.stMarkdown:empty {{ display: none !important; }}
.stMarkdown:has(>:empty:only-child) {{ display: none !important; }}
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
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            text-align: center;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 2.5rem; text-shadow: 0 4px 15px {t['shadow']};">{t['emoji']}</div>
            <div style="font-weight: 800; color: {t['text']}; font-size: 1.1rem; margin-top: 5px;">
                {t['name']}
            </div>
            <div style="font-size: 0.8rem; color: {t['primary']}; font-weight: 700; letter-spacing: 1px;">
                {t['vibe']}
            </div>
            <div style="font-size: 0.75rem; color: {t['text_muted']}; font-style: italic; margin-top: 8px;">
                "{t['motivation']}"
            </div>
        </div>
    """, unsafe_allow_html=True)

    return key