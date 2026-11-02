"""
GymPro Theme System v13.0 - 30 ULTRA PREMIUM GRADIENT THEMES
2-Color Gradients + 3D Buttons + Particle Animation + Neon Glow
"""

import streamlit as st
from datetime import date
import random

# ─────────────────────────────────────────────────────────────────────────────
# 30 ULTRA PREMIUM GRADIENT THEMES
# ─────────────────────────────────────────────────────────────────────────────

DESIGN_THEMES = {
    # ── 1. Purple Galaxy ──
    "design_1": {
        "name": "Purple Galaxy", "emoji": "🌌",
        "bg_gradient": "linear-gradient(135deg, #1a0a2e 0%, #0d1b3e 50%, #1a0a2e 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0d0a1a, #0a0a2a)",
        "accent": "#7C3AED", "accent2": "#3B82F6",
        "surface": "rgba(20,15,40,0.6)", "border": "rgba(124,58,237,0.3)",
        "text": "#F0EEFF", "muted": "#A8A0CC",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(124,58,237,0.15)",
        "glow": "0 0 60px rgba(124,58,237,0.08)",
        "neon_glow": "0 0 30px rgba(124,58,237,0.15), 0 0 60px rgba(124,58,237,0.05)",
        "particles": "🌌",
        "description": "🌌 Deep purple to blue galaxy gradient",
        "btn_gradient": "linear-gradient(135deg, #7C3AED, #3B82F6)",
        "btn_shadow": "0 8px 25px rgba(124,58,237,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(124,58,237,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#7C3AED",
    },
    # ── 2. Ocean Sunset ──
    "design_2": {
        "name": "Ocean Sunset", "emoji": "🌊",
        "bg_gradient": "linear-gradient(135deg, #0c1929 0%, #0a3d5c 50%, #0c1929 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #080f1a, #051a2a)",
        "accent": "#0EA5E9", "accent2": "#06B6D4",
        "surface": "rgba(10,30,50,0.6)", "border": "rgba(14,165,233,0.3)",
        "text": "#E8F4FD", "muted": "#7AA9C9",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(14,165,233,0.15)",
        "glow": "0 0 60px rgba(14,165,233,0.08)",
        "neon_glow": "0 0 30px rgba(14,165,233,0.15), 0 0 60px rgba(14,165,233,0.05)",
        "particles": "🌊",
        "description": "🌊 Deep ocean blue to cyan gradient",
        "btn_gradient": "linear-gradient(135deg, #0EA5E9, #06B6D4)",
        "btn_shadow": "0 8px 25px rgba(14,165,233,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(14,165,233,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#0EA5E9",
    },
    # ── 3. Forest Glow ──
    "design_3": {
        "name": "Forest Glow", "emoji": "🌿",
        "bg_gradient": "linear-gradient(135deg, #051a0d 0%, #0a3d1a 50%, #051a0d 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #030f08, #051a0d)",
        "accent": "#10B981", "accent2": "#34D399",
        "surface": "rgba(5,30,15,0.6)", "border": "rgba(16,185,129,0.3)",
        "text": "#E8F5ED", "muted": "#80B098",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(16,185,129,0.15)",
        "glow": "0 0 60px rgba(16,185,129,0.08)",
        "neon_glow": "0 0 30px rgba(16,185,129,0.15), 0 0 60px rgba(16,185,129,0.05)",
        "particles": "🌿",
        "description": "🌿 Fresh green to teal gradient",
        "btn_gradient": "linear-gradient(135deg, #10B981, #34D399)",
        "btn_shadow": "0 8px 25px rgba(16,185,129,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(16,185,129,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#10B981",
    },
    # ── 4. Rose Gold ──
    "design_4": {
        "name": "Rose Gold", "emoji": "🌸",
        "bg_gradient": "linear-gradient(135deg, #1a0a14 0%, #3d0a2a 50%, #1a0a14 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0f0510, #1a0a14)",
        "accent": "#EC4899", "accent2": "#F472B6",
        "surface": "rgba(30,15,25,0.6)", "border": "rgba(236,72,153,0.3)",
        "text": "#FDF0F5", "muted": "#C090A8",
        "font": "'Inter', sans-serif", "radius": "18px",
        "shadow": "0 20px 60px rgba(236,72,153,0.15)",
        "glow": "0 0 60px rgba(236,72,153,0.08)",
        "neon_glow": "0 0 30px rgba(236,72,153,0.15), 0 0 60px rgba(236,72,153,0.05)",
        "particles": "🌸",
        "description": "🌸 Elegant pink to rose gold gradient",
        "btn_gradient": "linear-gradient(135deg, #EC4899, #F472B6)",
        "btn_shadow": "0 8px 25px rgba(236,72,153,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(236,72,153,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#EC4899",
    },
    # ── 5. Midnight Fire ──
    "design_5": {
        "name": "Midnight Fire", "emoji": "🔥",
        "bg_gradient": "linear-gradient(135deg, #0a0000 0%, #3d0a0a 50%, #0a0000 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050000, #0a0000)",
        "accent": "#EF4444", "accent2": "#DC2626",
        "surface": "rgba(25,5,5,0.6)", "border": "rgba(239,68,68,0.3)",
        "text": "#FFF0F0", "muted": "#C08080",
        "font": "'Inter', sans-serif", "radius": "14px",
        "shadow": "0 20px 60px rgba(239,68,68,0.15)",
        "glow": "0 0 60px rgba(239,68,68,0.08)",
        "neon_glow": "0 0 30px rgba(239,68,68,0.15), 0 0 60px rgba(239,68,68,0.05)",
        "particles": "🔥",
        "description": "🔥 Bold red to dark crimson gradient",
        "btn_gradient": "linear-gradient(135deg, #EF4444, #DC2626)",
        "btn_shadow": "0 8px 25px rgba(239,68,68,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(239,68,68,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#EF4444",
    },
    # ── 6. Neon Dream ──
    "design_6": {
        "name": "Neon Dream", "emoji": "💜",
        "bg_gradient": "linear-gradient(135deg, #0a001a 0%, #1a0040 50%, #0a001a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050010, #0a001a)",
        "accent": "#8B5CF6", "accent2": "#22D3EE",
        "surface": "rgba(15,10,30,0.6)", "border": "rgba(139,92,246,0.3)",
        "text": "#F0EEFF", "muted": "#A8A0CC",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(139,92,246,0.15)",
        "glow": "0 0 60px rgba(139,92,246,0.08)",
        "neon_glow": "0 0 30px rgba(139,92,246,0.15), 0 0 60px rgba(139,92,246,0.05)",
        "particles": "💜",
        "description": "💜 Cyber purple to cyan gradient",
        "btn_gradient": "linear-gradient(135deg, #8B5CF6, #22D3EE)",
        "btn_shadow": "0 8px 25px rgba(139,92,246,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(139,92,246,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#8B5CF6",
    },
    # ── 7. Royal Crown ──
    "design_7": {
        "name": "Royal Crown", "emoji": "👑",
        "bg_gradient": "linear-gradient(135deg, #0a0806 0%, #2a1a0a 50%, #0a0806 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050302, #0a0806)",
        "accent": "#D4AF37", "accent2": "#F3D98B",
        "surface": "rgba(20,15,8,0.6)", "border": "rgba(212,175,55,0.3)",
        "text": "#F5EDE0", "muted": "#B8A888",
        "font": "'Playfair Display', serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(212,175,55,0.15)",
        "glow": "0 0 60px rgba(212,175,55,0.08)",
        "neon_glow": "0 0 30px rgba(212,175,55,0.15), 0 0 60px rgba(212,175,55,0.05)",
        "particles": "👑",
        "description": "👑 Royal gold to dark brown gradient",
        "btn_gradient": "linear-gradient(135deg, #D4AF37, #F3D98B)",
        "btn_shadow": "0 8px 25px rgba(212,175,55,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(212,175,55,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#D4AF37",
    },
    # ── 8. Arctic Chill ──
    "design_8": {
        "name": "Arctic Chill", "emoji": "❄️",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a2a4a 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#60A5FA", "accent2": "#93C5FD",
        "surface": "rgba(15,20,40,0.6)", "border": "rgba(96,165,250,0.3)",
        "text": "#F0F4FF", "muted": "#A0B0CC",
        "font": "'Inter', sans-serif", "radius": "18px",
        "shadow": "0 20px 60px rgba(96,165,250,0.15)",
        "glow": "0 0 60px rgba(96,165,250,0.08)",
        "neon_glow": "0 0 30px rgba(96,165,250,0.15), 0 0 60px rgba(96,165,250,0.05)",
        "particles": "❄️",
        "description": "❄️ Cool ice blue to navy gradient",
        "btn_gradient": "linear-gradient(135deg, #60A5FA, #93C5FD)",
        "btn_shadow": "0 8px 25px rgba(96,165,250,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(96,165,250,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#60A5FA",
    },
    # ── 9. Tropical Heat ──
    "design_9": {
        "name": "Tropical Heat", "emoji": "🏝️",
        "bg_gradient": "linear-gradient(135deg, #1a0a00 0%, #3d1a00 50%, #1a0a00 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0f0500, #1a0a00)",
        "accent": "#F97316", "accent2": "#F59E0B",
        "surface": "rgba(30,15,5,0.6)", "border": "rgba(249,115,22,0.3)",
        "text": "#FFF0E0", "muted": "#C4A080",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(249,115,22,0.15)",
        "glow": "0 0 60px rgba(249,115,22,0.08)",
        "neon_glow": "0 0 30px rgba(249,115,22,0.15), 0 0 60px rgba(249,115,22,0.05)",
        "particles": "🏝️",
        "description": "🏝️ Warm orange to golden gradient",
        "btn_gradient": "linear-gradient(135deg, #F97316, #F59E0B)",
        "btn_shadow": "0 8px 25px rgba(249,115,22,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(249,115,22,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#F97316",
    },
    # ── 10. Mystic Night ──
    "design_10": {
        "name": "Mystic Night", "emoji": "🌙",
        "bg_gradient": "linear-gradient(135deg, #060c18 0%, #1a0a2e 50%, #060c18 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #030810, #060c18)",
        "accent": "#818CF8", "accent2": "#A78BFA",
        "surface": "rgba(10,12,30,0.6)", "border": "rgba(129,140,248,0.3)",
        "text": "#F0EEFF", "muted": "#A8A0CC",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(129,140,248,0.15)",
        "glow": "0 0 60px rgba(129,140,248,0.08)",
        "neon_glow": "0 0 30px rgba(129,140,248,0.15), 0 0 60px rgba(129,140,248,0.05)",
        "particles": "🌙",
        "description": "🌙 Dark navy to purple gradient",
        "btn_gradient": "linear-gradient(135deg, #818CF8, #A78BFA)",
        "btn_shadow": "0 8px 25px rgba(129,140,248,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(129,140,248,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#818CF8",
    },
    # ── 11. Spring Bloom ──
    "design_11": {
        "name": "Spring Bloom", "emoji": "🌺",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #2a0a3d 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#F472B6", "accent2": "#10B981",
        "surface": "rgba(20,10,25,0.6)", "border": "rgba(244,114,182,0.3)",
        "text": "#FDF0F5", "muted": "#C0A0B0",
        "font": "'Inter', sans-serif", "radius": "20px",
        "shadow": "0 20px 60px rgba(244,114,182,0.15)",
        "glow": "0 0 60px rgba(244,114,182,0.08)",
        "neon_glow": "0 0 30px rgba(244,114,182,0.15), 0 0 60px rgba(244,114,182,0.05)",
        "particles": "🌺",
        "description": "🌺 Pink to green spring gradient",
        "btn_gradient": "linear-gradient(135deg, #F472B6, #10B981)",
        "btn_shadow": "0 8px 25px rgba(244,114,182,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(244,114,182,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#F472B6",
    },
    # ── 12. Cyber Punk ──
    "design_12": {
        "name": "Cyber Punk", "emoji": "🚀",
        "bg_gradient": "linear-gradient(135deg, #050a18 0%, #0a0030 50%, #050a18 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #030510, #050a18)",
        "accent": "#22D3EE", "accent2": "#818CF8",
        "surface": "rgba(10,12,30,0.6)", "border": "rgba(34,211,238,0.3)",
        "text": "#E8FBFF", "muted": "#88A0C0",
        "font": "'Space Mono', monospace", "radius": "12px",
        "shadow": "0 20px 60px rgba(34,211,238,0.15)",
        "glow": "0 0 60px rgba(34,211,238,0.08)",
        "neon_glow": "0 0 30px rgba(34,211,238,0.15), 0 0 60px rgba(34,211,238,0.05)",
        "particles": "🚀",
        "description": "🚀 Cyber punk cyan to purple gradient",
        "btn_gradient": "linear-gradient(135deg, #22D3EE, #818CF8)",
        "btn_shadow": "0 8px 25px rgba(34,211,238,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(34,211,238,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#22D3EE",
    },
    # ── 13. Golden Hour ──
    "design_13": {
        "name": "Golden Hour", "emoji": "🌅",
        "bg_gradient": "linear-gradient(135deg, #0a0806 0%, #3d2a0a 50%, #0a0806 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050302, #0a0806)",
        "accent": "#FBBF24", "accent2": "#F97316",
        "surface": "rgba(20,15,5,0.6)", "border": "rgba(251,191,36,0.3)",
        "text": "#F5EDE0", "muted": "#C4A080",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(251,191,36,0.15)",
        "glow": "0 0 60px rgba(251,191,36,0.08)",
        "neon_glow": "0 0 30px rgba(251,191,36,0.15), 0 0 60px rgba(251,191,36,0.05)",
        "particles": "🌅",
        "description": "🌅 Golden yellow to orange gradient",
        "btn_gradient": "linear-gradient(135deg, #FBBF24, #F97316)",
        "btn_shadow": "0 8px 25px rgba(251,191,36,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(251,191,36,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#FBBF24",
    },
    # ── 14. Deep Ocean ──
    "design_14": {
        "name": "Deep Ocean", "emoji": "🐠",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #0a2a3d 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#0891B2", "accent2": "#06B6D4",
        "surface": "rgba(10,20,35,0.6)", "border": "rgba(8,145,178,0.3)",
        "text": "#E8F4FD", "muted": "#80A8C0",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(8,145,178,0.15)",
        "glow": "0 0 60px rgba(8,145,178,0.08)",
        "neon_glow": "0 0 30px rgba(8,145,178,0.15), 0 0 60px rgba(8,145,178,0.05)",
        "particles": "🐠",
        "description": "🐠 Deep navy to teal ocean gradient",
        "btn_gradient": "linear-gradient(135deg, #0891B2, #06B6D4)",
        "btn_shadow": "0 8px 25px rgba(8,145,178,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(8,145,178,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#0891B2",
    },
    # ── 15. Candy Crush ──
    "design_15": {
        "name": "Candy Crush", "emoji": "🍭",
        "bg_gradient": "linear-gradient(135deg, #1a0a1a 0%, #3d0a2a 50%, #1a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0f0510, #1a0a1a)",
        "accent": "#EC4899", "accent2": "#FBBF24",
        "surface": "rgba(30,10,25,0.6)", "border": "rgba(236,72,153,0.3)",
        "text": "#FDF0F5", "muted": "#C090A8",
        "font": "'Inter', sans-serif", "radius": "20px",
        "shadow": "0 20px 60px rgba(236,72,153,0.15)",
        "glow": "0 0 60px rgba(236,72,153,0.08)",
        "neon_glow": "0 0 30px rgba(236,72,153,0.15), 0 0 60px rgba(236,72,153,0.05)",
        "particles": "🍭",
        "description": "🍭 Candy pink to yellow gradient",
        "btn_gradient": "linear-gradient(135deg, #EC4899, #FBBF24)",
        "btn_shadow": "0 8px 25px rgba(236,72,153,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(236,72,153,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#EC4899",
    },

    # ── 16. Midnight Blue ──
    "design_16": {
        "name": "Midnight Blue", "emoji": "🌙",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #0a1a3d 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#1E3A5F", "accent2": "#3B82F6",
        "surface": "rgba(10,15,30,0.6)", "border": "rgba(30,58,95,0.3)",
        "text": "#E8EEF8", "muted": "#809AB8",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(30,58,95,0.15)",
        "glow": "0 0 60px rgba(30,58,95,0.08)",
        "neon_glow": "0 0 30px rgba(30,58,95,0.15), 0 0 60px rgba(30,58,95,0.05)",
        "particles": "🌙",
        "description": "🌙 Deep midnight blue gradient",
        "btn_gradient": "linear-gradient(135deg, #1E3A5F, #3B82F6)",
        "btn_shadow": "0 8px 25px rgba(30,58,95,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(30,58,95,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#1E3A5F",
    },
    # ── 17. Sunset Vibes ──
    "design_17": {
        "name": "Sunset Vibes", "emoji": "🌅",
        "bg_gradient": "linear-gradient(135deg, #1a0a00 0%, #3d1a2a 50%, #1a0a00 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0f0500, #1a0a00)",
        "accent": "#F97316", "accent2": "#EC4899",
        "surface": "rgba(30,10,15,0.6)", "border": "rgba(249,115,22,0.3)",
        "text": "#FFF0E8", "muted": "#C49080",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(249,115,22,0.15)",
        "glow": "0 0 60px rgba(249,115,22,0.08)",
        "neon_glow": "0 0 30px rgba(249,115,22,0.15), 0 0 60px rgba(249,115,22,0.05)",
        "particles": "🌅",
        "description": "🌅 Warm sunset orange to pink gradient",
        "btn_gradient": "linear-gradient(135deg, #F97316, #EC4899)",
        "btn_shadow": "0 8px 25px rgba(249,115,22,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(249,115,22,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#F97316",
    },
    # ── 18. Emerald Dream ──
    "design_18": {
        "name": "Emerald Dream", "emoji": "💚",
        "bg_gradient": "linear-gradient(135deg, #051a0d 0%, #0a3d2a 50%, #051a0d 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #030f08, #051a0d)",
        "accent": "#10B981", "accent2": "#D4AF37",
        "surface": "rgba(5,25,15,0.6)", "border": "rgba(16,185,129,0.3)",
        "text": "#E8F5ED", "muted": "#80B098",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(16,185,129,0.15)",
        "glow": "0 0 60px rgba(16,185,129,0.08)",
        "neon_glow": "0 0 30px rgba(16,185,129,0.15), 0 0 60px rgba(16,185,129,0.05)",
        "particles": "💚",
        "description": "💚 Emerald green to gold gradient",
        "btn_gradient": "linear-gradient(135deg, #10B981, #D4AF37)",
        "btn_shadow": "0 8px 25px rgba(16,185,129,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(16,185,129,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#10B981",
    },
    # ── 19. Lavender Haze ──
    "design_19": {
        "name": "Lavender Haze", "emoji": "💜",
        "bg_gradient": "linear-gradient(135deg, #1a0a2a 0%, #3d1a5c 50%, #1a0a2a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0f0518, #1a0a2a)",
        "accent": "#A78BFA", "accent2": "#7C3AED",
        "surface": "rgba(20,10,35,0.6)", "border": "rgba(167,139,250,0.3)",
        "text": "#F0EEFF", "muted": "#B0A0D0",
        "font": "'Inter', sans-serif", "radius": "18px",
        "shadow": "0 20px 60px rgba(167,139,250,0.15)",
        "glow": "0 0 60px rgba(167,139,250,0.08)",
        "neon_glow": "0 0 30px rgba(167,139,250,0.15), 0 0 60px rgba(167,139,250,0.05)",
        "particles": "💜",
        "description": "💜 Soft lavender to purple gradient",
        "btn_gradient": "linear-gradient(135deg, #A78BFA, #7C3AED)",
        "btn_shadow": "0 8px 25px rgba(167,139,250,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(167,139,250,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#A78BFA",
    },
    # ── 20. Tropical Paradise ──
    "design_20": {
        "name": "Tropical Paradise", "emoji": "🏝️",
        "bg_gradient": "linear-gradient(135deg, #051a0d 0%, #0a3d3d 50%, #051a0d 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #030f08, #051a0d)",
        "accent": "#06B6D4", "accent2": "#10B981",
        "surface": "rgba(5,25,25,0.6)", "border": "rgba(6,182,212,0.3)",
        "text": "#E8F5F5", "muted": "#80B0B0",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(6,182,212,0.15)",
        "glow": "0 0 60px rgba(6,182,212,0.08)",
        "neon_glow": "0 0 30px rgba(6,182,212,0.15), 0 0 60px rgba(6,182,212,0.05)",
        "particles": "🏝️",
        "description": "🏝️ Teal to green tropical gradient",
        "btn_gradient": "linear-gradient(135deg, #06B6D4, #10B981)",
        "btn_shadow": "0 8px 25px rgba(6,182,212,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(6,182,212,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#06B6D4",
    },
    # ── 21. Ruby Glow ──
    "design_21": {
        "name": "Ruby Glow", "emoji": "❤️",
        "bg_gradient": "linear-gradient(135deg, #0a0000 0%, #3d0a1a 50%, #0a0000 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050000, #0a0000)",
        "accent": "#EF4444", "accent2": "#EC4899",
        "surface": "rgba(25,5,10,0.6)", "border": "rgba(239,68,68,0.3)",
        "text": "#FFF0F0", "muted": "#C08090",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(239,68,68,0.15)",
        "glow": "0 0 60px rgba(239,68,68,0.08)",
        "neon_glow": "0 0 30px rgba(239,68,68,0.15), 0 0 60px rgba(239,68,68,0.05)",
        "particles": "❤️",
        "description": "❤️ Ruby red to pink gradient",
        "btn_gradient": "linear-gradient(135deg, #EF4444, #EC4899)",
        "btn_shadow": "0 8px 25px rgba(239,68,68,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(239,68,68,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#EF4444",
    },
    # ── 22. Sapphire Sky ──
    "design_22": {
        "name": "Sapphire Sky", "emoji": "💎",
        "bg_gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a3d7c 50%, #0a0a2e 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050518, #0a0a2e)",
        "accent": "#3B82F6", "accent2": "#8B5CF6",
        "surface": "rgba(10,10,40,0.6)", "border": "rgba(59,130,246,0.3)",
        "text": "#EEF4FF", "muted": "#90A8C0",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(59,130,246,0.15)",
        "glow": "0 0 60px rgba(59,130,246,0.08)",
        "neon_glow": "0 0 30px rgba(59,130,246,0.15), 0 0 60px rgba(59,130,246,0.05)",
        "particles": "💎",
        "description": "💎 Sapphire blue to purple gradient",
        "btn_gradient": "linear-gradient(135deg, #3B82F6, #8B5CF6)",
        "btn_shadow": "0 8px 25px rgba(59,130,246,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(59,130,246,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#3B82F6",
    },
    # ── 23. Autumn Leaves ──
    "design_23": {
        "name": "Autumn Leaves", "emoji": "🍂",
        "bg_gradient": "linear-gradient(135deg, #1a0a00 0%, #3d2a0a 50%, #1a0a00 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0f0500, #1a0a00)",
        "accent": "#F59E0B", "accent2": "#8B6914",
        "surface": "rgba(30,15,5,0.6)", "border": "rgba(245,158,11,0.3)",
        "text": "#F5EDE0", "muted": "#C4A080",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(245,158,11,0.15)",
        "glow": "0 0 60px rgba(245,158,11,0.08)",
        "neon_glow": "0 0 30px rgba(245,158,11,0.15), 0 0 60px rgba(245,158,11,0.05)",
        "particles": "🍂",
        "description": "🍂 Warm autumn orange to brown gradient",
        "btn_gradient": "linear-gradient(135deg, #F59E0B, #8B6914)",
        "btn_shadow": "0 8px 25px rgba(245,158,11,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(245,158,11,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#F59E0B",
    },
    # ── 24. Spring Meadow ──
    "design_24": {
        "name": "Spring Meadow", "emoji": "🌸",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #2a3d1a 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#F472B6", "accent2": "#10B981",
        "surface": "rgba(15,25,10,0.6)", "border": "rgba(244,114,182,0.3)",
        "text": "#FDF0F5", "muted": "#B0C0A0",
        "font": "'Inter', sans-serif", "radius": "18px",
        "shadow": "0 20px 60px rgba(244,114,182,0.15)",
        "glow": "0 0 60px rgba(244,114,182,0.08)",
        "neon_glow": "0 0 30px rgba(244,114,182,0.15), 0 0 60px rgba(244,114,182,0.05)",
        "particles": "🌸",
        "description": "🌸 Spring pink to mint green gradient",
        "btn_gradient": "linear-gradient(135deg, #F472B6, #10B981)",
        "btn_shadow": "0 8px 25px rgba(244,114,182,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(244,114,182,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#F472B6",
    },
    # ── 25. Cosmic Dust ──
    "design_25": {
        "name": "Cosmic Dust", "emoji": "✨",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #2a1a3d 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#D4AF37", "accent2": "#8B5CF6",
        "surface": "rgba(15,10,30,0.6)", "border": "rgba(212,175,55,0.3)",
        "text": "#F5F0E8", "muted": "#C0B0A0",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(212,175,55,0.15)",
        "glow": "0 0 60px rgba(212,175,55,0.08)",
        "neon_glow": "0 0 30px rgba(212,175,55,0.15), 0 0 60px rgba(212,175,55,0.05)",
        "particles": "✨",
        "description": "✨ Cosmic purple to gold gradient",
        "btn_gradient": "linear-gradient(135deg, #D4AF37, #8B5CF6)",
        "btn_shadow": "0 8px 25px rgba(212,175,55,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(212,175,55,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#D4AF37",
    },
    # ── 26. Arctic Frost ──
    "design_26": {
        "name": "Arctic Frost", "emoji": "❄️",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a3d5c 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#93C5FD", "accent2": "#60A5FA",
        "surface": "rgba(15,20,40,0.6)", "border": "rgba(147,197,253,0.3)",
        "text": "#F0F8FF", "muted": "#B0C8D0",
        "font": "'Inter', sans-serif", "radius": "18px",
        "shadow": "0 20px 60px rgba(147,197,253,0.15)",
        "glow": "0 0 60px rgba(147,197,253,0.08)",
        "neon_glow": "0 0 30px rgba(147,197,253,0.15), 0 0 60px rgba(147,197,253,0.05)",
        "particles": "❄️",
        "description": "❄️ Frosty white to ice blue gradient",
        "btn_gradient": "linear-gradient(135deg, #93C5FD, #60A5FA)",
        "btn_shadow": "0 8px 25px rgba(147,197,253,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(147,197,253,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#93C5FD",
    },
    # ── 27. Volcano Fire ──
    "design_27": {
        "name": "Volcano Fire", "emoji": "🌋",
        "bg_gradient": "linear-gradient(135deg, #0a0000 0%, #3d0a00 50%, #0a0000 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050000, #0a0000)",
        "accent": "#F97316", "accent2": "#EF4444",
        "surface": "rgba(25,5,0,0.6)", "border": "rgba(249,115,22,0.3)",
        "text": "#FFF0E8", "muted": "#C09080",
        "font": "'Inter', sans-serif", "radius": "14px",
        "shadow": "0 20px 60px rgba(249,115,22,0.15)",
        "glow": "0 0 60px rgba(249,115,22,0.08)",
        "neon_glow": "0 0 30px rgba(249,115,22,0.15), 0 0 60px rgba(249,115,22,0.05)",
        "particles": "🌋",
        "description": "🌋 Volcanic red to orange gradient",
        "btn_gradient": "linear-gradient(135deg, #F97316, #EF4444)",
        "btn_shadow": "0 8px 25px rgba(249,115,22,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(249,115,22,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#F97316",
    },
    # ── 28. Ocean Breeze ──
    "design_28": {
        "name": "Ocean Breeze", "emoji": "🌊",
        "bg_gradient": "linear-gradient(135deg, #0a1a2a 0%, #0a3d5c 50%, #0a1a2a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050f18, #0a1a2a)",
        "accent": "#06B6D4", "accent2": "#0EA5E9",
        "surface": "rgba(10,25,40,0.6)", "border": "rgba(6,182,212,0.3)",
        "text": "#E8F4FD", "muted": "#80A8C0",
        "font": "'Inter', sans-serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(6,182,212,0.15)",
        "glow": "0 0 60px rgba(6,182,212,0.08)",
        "neon_glow": "0 0 30px rgba(6,182,212,0.15), 0 0 60px rgba(6,182,212,0.05)",
        "particles": "🌊",
        "description": "🌊 Fresh cyan to blue ocean gradient",
        "btn_gradient": "linear-gradient(135deg, #06B6D4, #0EA5E9)",
        "btn_shadow": "0 8px 25px rgba(6,182,212,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(6,182,212,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#06B6D4",
    },
    # ── 29. Royal Purple ──
    "design_29": {
        "name": "Royal Purple", "emoji": "👑",
        "bg_gradient": "linear-gradient(135deg, #0a0a1a 0%, #2a0a5c 50%, #0a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #050510, #0a0a1a)",
        "accent": "#8B5CF6", "accent2": "#D4AF37",
        "surface": "rgba(15,10,35,0.6)", "border": "rgba(139,92,246,0.3)",
        "text": "#F0EEFF", "muted": "#B0A8C0",
        "font": "'Playfair Display', serif", "radius": "16px",
        "shadow": "0 20px 60px rgba(139,92,246,0.15)",
        "glow": "0 0 60px rgba(139,92,246,0.08)",
        "neon_glow": "0 0 30px rgba(139,92,246,0.15), 0 0 60px rgba(139,92,246,0.05)",
        "particles": "👑",
        "description": "👑 Royal purple to gold gradient",
        "btn_gradient": "linear-gradient(135deg, #8B5CF6, #D4AF37)",
        "btn_shadow": "0 8px 25px rgba(139,92,246,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(139,92,246,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#8B5CF6",
    },
    # ── 30. Candy Land ──
    "design_30": {
        "name": "Candy Land", "emoji": "🍬",
        "bg_gradient": "linear-gradient(135deg, #1a0a1a 0%, #3d0a4a 50%, #1a0a1a 100%)",
        "sidebar_gradient": "linear-gradient(180deg, #0f0518, #1a0a1a)",
        "accent": "#EC4899", "accent2": "#A78BFA",
        "surface": "rgba(30,10,35,0.6)", "border": "rgba(236,72,153,0.3)",
        "text": "#FDF0F8", "muted": "#C090B0",
        "font": "'Inter', sans-serif", "radius": "20px",
        "shadow": "0 20px 60px rgba(236,72,153,0.15)",
        "glow": "0 0 60px rgba(236,72,153,0.08)",
        "neon_glow": "0 0 30px rgba(236,72,153,0.15), 0 0 60px rgba(236,72,153,0.05)",
        "particles": "🍬",
        "description": "🍬 Sweet candy pink to purple gradient",
        "btn_gradient": "linear-gradient(135deg, #EC4899, #A78BFA)",
        "btn_shadow": "0 8px 25px rgba(236,72,153,0.3), inset 0 -4px 0 rgba(0,0,0,0.2)",
        "btn_hover_shadow": "0 12px 35px rgba(236,72,153,0.4), inset 0 -2px 0 rgba(0,0,0,0.2)",
        "scrollbar_color": "#EC4899",
    },
}

THEMES = DESIGN_THEMES
THEME_KEYS = list(DESIGN_THEMES.keys())
THEME_NAMES = {k: f"{v['emoji']} {v['name']}" for i, (k, v) in enumerate(DESIGN_THEMES.items())}

LEGACY_THEME_ALIASES = {
    "dark_slate": "design_1", "energy_burst": "design_7",
    "royal_purple": "design_29", "ocean_blue": "design_2",
    "emerald_green": "design_3", "crimson_red": "design_5",
    "cyber_cyan": "design_12", "neon_pink": "design_4",
    "midnight_galaxy": "design_10", "sunset_orange": "design_9",
    "ice_blue": "design_8", "forest_green": "design_3",
    "cherry_blossom": "design_11", "golden_hour": "design_13",
    "dark_knight": "design_14", "tropical_sunset": "design_9",
}

def normalize_theme_key(key=None):
    key = str(key or "design_1")
    return LEGACY_THEME_ALIASES.get(key, key if key in DESIGN_THEMES else "design_1")

def current_theme():
    return normalize_theme_key(st.session_state.get("current_theme") or st.session_state.get("_gympro_theme"))

def get_daily_theme():
    return THEME_KEYS[date.today().toordinal() % len(THEME_KEYS)]

def build_css(key: str = "design_1") -> str:
    key = normalize_theme_key(key)
    t = DESIGN_THEMES[key]
    number = int(key.split("_")[1])
    
    return f"""
<style>
/* ── Google Fonts ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,700&family=Inter:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');

/* ── CSS Variables ──────────────────────────────────────────────── */
:root {{
  --gp-bg: {t["bg_gradient"]};
  --gp-surface: {t["surface"]};
  --gp-sidebar: {t["sidebar_gradient"]};
  --gp-border: {t["border"]};
  --gp-accent: {t["accent"]};
  --gp-accent2: {t["accent2"]};
  --gp-text: {t["text"]};
  --gp-muted: {t["muted"]};
  --gp-radius: {t["radius"]};
  --gp-shadow: {t["shadow"]};
  --gp-glow: {t["neon_glow"]};
  --gp-font: {t["font"]};
  --gp-btn-grad: {t["btn_gradient"]};
  --gp-btn-shadow: {t["btn_shadow"]};
  --gp-btn-hover-shadow: {t["btn_hover_shadow"]};
  --gp-scrollbar: {t["scrollbar_color"]};
}}

/* ── Animated Gradient Background ────────────────────────────────── */
@keyframes gradientMove {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

.stApp, [data-testid="stAppViewContainer"] {{
    background: var(--gp-bg) !important;
    background-size: 400% 400% !important;
    animation: gradientMove 15s ease infinite !important;
    color: var(--gp-text) !important;
    min-height: 100vh !important;
}}

section[data-testid="stSidebar"] {{
    background: var(--gp-sidebar) !important;
    border-right: 1px solid var(--gp-border) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
}}

.main .block-container {{
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}}

/* ── Particle Animation ──────────────────────────────────────────── */
@keyframes floatParticle {{
    0% {{ transform: translateY(0px) rotate(0deg) scale(1); opacity: 0; }}
    20% {{ opacity: 1; }}
    80% {{ opacity: 1; }}
    100% {{ transform: translateY(-60px) rotate(360deg) scale(1.2); opacity: 0; }}
}}

.particle-container {{
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    pointer-events: none !important;
    z-index: 0 !important;
    overflow: hidden !important;
}}

.particle {{
    position: absolute !important;
    font-size: 28px !important;
    animation: floatParticle {random.randint(8, 16)}s ease-in-out infinite !important;
    opacity: 0 !important;
}}

/* ── 3D CARDS with Neon Glow ────────────────────────────────────── */
.metric-card, [data-testid="metric-container"], .pro-card,
[data-testid="stExpander"], [data-testid="stDataFrame"], .design-option {{
    background: var(--gp-surface) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
    box-shadow: var(--gp-shadow), var(--gp-glow) !important;
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    transform: perspective(800px) rotateX(2deg) translateY(0px) !important;
    position: relative !important;
    z-index: 1 !important;
}}

.metric-card:hover, [data-testid="metric-container"]:hover,
.pro-card:hover, [data-testid="stExpander"]:hover {{
    transform: perspective(800px) rotateX(0deg) translateY(-10px) scale(1.02) !important;
    box-shadow: var(--gp-shadow), var(--gp-glow) !important;
    border-color: var(--gp-accent) !important;
}}

/* ── CUSTOM SCROLLBAR ────────────────────────────────────────────── */
::-webkit-scrollbar {{
    width: 8px !important;
    height: 8px !important;
}}
::-webkit-scrollbar-track {{
    background: rgba(0,0,0,0.2) !important;
    border-radius: 10px !important;
}}
::-webkit-scrollbar-thumb {{
    background: var(--gp-scrollbar) !important;
    border-radius: 10px !important;
    box-shadow: 0 0 20px var(--gp-scrollbar)55 !important;
}}
::-webkit-scrollbar-thumb:hover {{
    background: var(--gp-accent2) !important;
}}

/* ── ★★★ 3D BUTTONS ★★★ ────────────────────────────────────── */
.stButton > button {{
    background: var(--gp-btn-grad) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    padding: 12px 24px !important;
    border-radius: var(--gp-radius) !important;
    box-shadow: var(--gp-btn-shadow) !important;
    transform: perspective(500px) rotateX(3deg) !important;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    cursor: pointer !important;
    letter-spacing: 0.5px !important;
    position: relative !important;
    overflow: hidden !important;
    z-index: 1 !important;
}}

.stButton > button::after {{
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.15) 0%, transparent 50%) !important;
    pointer-events: none !important;
    border-radius: var(--gp-radius) !important;
}}

.stButton > button:hover {{
    transform: perspective(500px) rotateX(0deg) translateY(-4px) scale(1.02) !important;
    box-shadow: var(--gp-btn-hover-shadow) !important;
}}

.stButton > button:active {{
    transform: perspective(500px) rotateX(2deg) translateY(2px) scale(0.98) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}}

.stButton > button span,
.stButton > button p,
.stButton > button div {{
    color: #FFFFFF !important;
}}

.stButton > button[kind="primary"] {{
    background: var(--gp-btn-grad) !important;
    box-shadow: var(--gp-btn-shadow) !important;
}}

/* ── SIDEBAR BUTTONS - 3D ────────────────────────────────────────── */
section[data-testid="stSidebar"] .stButton > button,
.nav-btn button,
.nav-btn-active button {{
    background: var(--gp-btn-grad) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 12px 18px !important;
    min-height: 48px !important;
    width: 100% !important;
    border-radius: 12px !important;
    text-align: left !important;
    box-shadow: var(--gp-btn-shadow) !important;
    transform: perspective(500px) rotateX(2deg) !important;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    z-index: 1 !important;
}}

section[data-testid="stSidebar"] .stButton > button:hover,
.nav-btn button:hover {{
    transform: perspective(500px) rotateX(0deg) translateX(8px) scale(1.02) !important;
    box-shadow: var(--gp-btn-hover-shadow) !important;
}}

section[data-testid="stSidebar"] .stButton > button span,
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button div,
.nav-btn button span,
.nav-btn button p,
.nav-btn-active button span,
.nav-btn-active button p {{
    color: #FFFFFF !important;
}}

/* ── LOADING ANIMATION ────────────────────────────────────────────── */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(30px) scale(0.95); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}

.main .block-container > * {{
    animation: fadeInUp 0.6s ease-out forwards !important;
    opacity: 0 !important;
}}

.main .block-container > *:nth-child(1) {{ animation-delay: 0.05s !important; }}
.main .block-container > *:nth-child(2) {{ animation-delay: 0.10s !important; }}
.main .block-container > *:nth-child(3) {{ animation-delay: 0.15s !important; }}
.main .block-container > *:nth-child(4) {{ animation-delay: 0.20s !important; }}
.main .block-container > *:nth-child(5) {{ animation-delay: 0.25s !important; }}
.main .block-container > *:nth-child(6) {{ animation-delay: 0.30s !important; }}
.main .block-container > *:nth-child(7) {{ animation-delay: 0.35s !important; }}
.main .block-container > *:nth-child(8) {{ animation-delay: 0.40s !important; }}
.main .block-container > *:nth-child(9) {{ animation-delay: 0.45s !important; }}
.main .block-container > *:nth-child(10) {{ animation-delay: 0.50s !important; }}

/* ── FORCE SIDEBAR TEXT WHITE ──────────────────────────────────── */
section[data-testid="stSidebar"] * {{
    color: var(--gp-text) !important;
}}
section[data-testid="stSidebar"] label {{
    color: var(--gp-text) !important;
}}
section[data-testid="stSidebar"] .stCheckbox label {{
    color: var(--gp-text) !important;
}}
section[data-testid="stSidebar"] .stCheckbox label span {{
    color: var(--gp-text) !important;
}}

/* ── ★★★ SIDEBAR SECTION HEADERS FIX ★★★ ──────────────────────── */
/* Fix for "AI & SUPPORT", "GENERAL MANAGEMENT", "MEMBER & IDENTITY" */
section[data-testid="stSidebar"] div[style*="font-size:0.6rem"] {{
    color: #FFFFFF !important;
    opacity: 1 !important;
}}

section[data-testid="stSidebar"] div[style*="font-size:0.6rem"] * {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] div[style*="color:#475569"] {{
    color: #FFFFFF !important;
    opacity: 1 !important;
}}

section[data-testid="stSidebar"] div[style*="color:#475569"] * {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] .stMarkdown div {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] .stMarkdown div * {{
    color: #FFFFFF !important;
}}

/* Fix for "Switch Gym Location" and other sidebar labels */
section[data-testid="stSidebar"] div[style*="font-size:0.65rem"] {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] div[style*="font-size:0.65rem"] * {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] .stSelectbox label {{
    color: #FFFFFF !important;
}}

/* ── ★★★ INPUT & SELECTBOX FIX ★★★ ────────────────────────────── */
/* Fix for text input - Force white text */
.stTextInput input,
.stTextInput input::placeholder,
.stTextInput input:focus,
.stTextInput input:active {{
    color: #FFFFFF !important;
    background: rgba(20,20,40,0.6) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
    padding: 12px 16px !important;
}}

/* Fix for all text inputs in sidebar */
section[data-testid="stSidebar"] .stTextInput input {{
    color: #FFFFFF !important;
    background: rgba(255,255,255,0.05) !important;
}}

/* Fix for number inputs */
.stNumberInput input,
.stNumberInput input:focus {{
    color: #FFFFFF !important;
    background: rgba(20,20,40,0.6) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
}}

/* Fix for text areas */
.stTextArea textarea,
.stTextArea textarea:focus {{
    color: #FFFFFF !important;
    background: rgba(20,20,40,0.6) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
}}

/* Fix for selectbox - dropdown */
div[data-testid="stSelectbox"] label {{
    color: var(--gp-text) !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    background: rgba(20,20,40,0.6) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] {{
    color: #FFFFFF !important;
    background: transparent !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] span {{
    color: #FFFFFF !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="listbox"] {{
    background: rgba(20,20,40,0.95) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"] {{
    color: #FFFFFF !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    background: transparent !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"]:hover {{
    background: rgba(124, 58, 237, 0.15) !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"][aria-selected="true"] {{
    background: var(--gp-btn-grad) !important;
    color: #FFFFFF !important;
}}

div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {{
    fill: #FFFFFF !important;
    opacity: 0.6 !important;
}}

/* Fix for selectbox in sidebar */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    background: rgba(255,255,255,0.05) !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="combobox"] span {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="listbox"] {{
    background: rgba(10,10,20,0.95) !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"] {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="option"]:hover {{
    background: rgba(124, 58, 237, 0.15) !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {{
    fill: #FFFFFF !important;
}}

/* ── DIVIDER ──────────────────────────────────────────────────────── */
hr {{ border-color: var(--gp-border) !important; }}

/* ── METRIC CARDS ─────────────────────────────────────────────────── */
.metric-card .label {{
    color: var(--gp-muted) !important;
}}
.metric-card .value {{
    color: var(--gp-text) !important;
}}
.metric-card .sub {{
    color: var(--gp-muted) !important;
}}

/* ── SECTION HEADER ───────────────────────────────────────────────── */
.section-header {{
    font-size: 20px;
    font-weight: 800;
    color: var(--gp-text);
    margin: 24px 0 16px 0;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--gp-border);
    letter-spacing: -0.5px;
}}

/* ── TOP ACCENT LINE ────────────────────────────────────────────── */
.stApp::before {{
    content: "";
    display: block;
    height: 4px;
    background: var(--gp-btn-grad) !important;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
    box-shadow: 0 0 40px rgba(124, 58, 237, 0.15) !important;
}}

/* ── DASHBOARD COMPONENTS ────────────────────────────────────────── */
.dash-hero, .settings-hero {{
    background: var(--gp-surface) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: calc(var(--gp-radius) + 8px) !important;
    padding: 2rem !important;
    margin-bottom: 1.3rem !important;
    box-shadow: var(--gp-shadow), var(--gp-glow) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    transform: perspective(800px) rotateX(2deg) !important;
    position: relative !important;
    z-index: 1 !important;
}}
.dash-hero:hover {{
    transform: perspective(800px) rotateX(0deg) translateY(-4px) !important;
    box-shadow: var(--gp-shadow), var(--gp-glow) !important;
}}
.dash-hero {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}}
.dash-hero h1, .settings-hero h1 {{
    color: var(--gp-text);
    margin: .25rem 0;
    font-size: clamp(1.7rem, 3vw, 2.8rem);
    letter-spacing: -.04em;
}}
.dash-hero p, .settings-hero p {{
    color: var(--gp-muted);
    margin: 0;
}}
.dash-eyebrow, .design-number {{
    font-size: .68rem;
    font-weight: 800;
    letter-spacing: .14em;
    text-transform: uppercase;
    color: var(--gp-muted) !important;
}}
.dash-hero-chip {{
    border: 1px solid var(--gp-accent);
    color: var(--gp-accent);
    border-radius: 999px;
    padding: .45rem .8rem;
    font-size: .75rem;
    font-weight: 800;
    background: var(--gp-surface);
    box-shadow: 0 0 20px var(--gp-accent)44;
}}
.dash-dot {{ color: var(--gp-accent); padding: 0 .35rem; }}

.dash-kpi {{
    background: var(--gp-surface) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
    padding: 1.2rem !important;
    min-height: 106px !important;
    box-shadow: var(--gp-shadow), var(--gp-glow) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    transform: perspective(800px) rotateX(2deg) !important;
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    position: relative !important;
    z-index: 1 !important;
}}
.dash-kpi:hover {{
    transform: perspective(800px) rotateX(0deg) translateY(-8px) scale(1.02) !important;
    box-shadow: var(--gp-shadow), var(--gp-glow) !important;
    border-color: var(--gp-accent) !important;
}}
.dash-kpi-value {{
    font-size: clamp(1.45rem, 2.5vw, 2.35rem);
    font-weight: 800;
    color: var(--gp-text);
    margin: .45rem 0 .2rem;
}}
.dash-kpi-hint {{
    color: var(--gp-muted);
    font-size: .76rem;
}}
.dash-kpi::after {{
    content: "";
    display: block;
    width: 34px;
    height: 3px;
    margin-top: 1rem;
    background: var(--gp-btn-grad);
    border-radius: 9px;
    box-shadow: 0 0 20px var(--gp-accent)44;
}}

.dash-alert {{
    border-radius: var(--gp-radius);
    padding: .8rem 1rem;
    margin: .5rem 0;
    border-left: 4px solid var(--gp-accent);
    background: var(--gp-surface);
    color: var(--gp-text);
    box-shadow: var(--gp-glow);
}}
.dash-alert-critical {{ border-color: #E11D48; }}
.dash-alert-warning {{ border-color: #D4AF37; }}
.dash-alert-info {{ border-color: #2563EB; }}

.dash-command {{
    background: var(--gp-surface) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
    padding: .9rem 1.1rem !important;
    margin-bottom: 1rem !important;
    color: var(--gp-muted) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
}}
.dash-command span {{
    float: right;
    color: var(--gp-accent);
    font-weight: 800;
}}

.dash-orbit {{
    min-height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 2rem;
    border: 1px solid var(--gp-border);
    border-radius: 32px;
    background: var(--gp-surface);
    box-shadow: var(--gp-shadow), var(--gp-glow);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}}
.dash-orbit strong {{
    font-size: clamp(3.5rem, 8vw, 7rem);
    line-height: 1;
    color: var(--gp-text);
    letter-spacing: -.08em;
}}
.dash-orbit span {{
    color: var(--gp-muted);
    margin-top: .6rem;
}}

.design-option {{
    padding: 1.2rem;
    margin: .5rem 0 .65rem;
    min-height: 145px;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    background: var(--gp-surface) !important;
    border: 1px solid var(--gp-border) !important;
    border-radius: var(--gp-radius) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
}}
.design-option.selected {{ outline: 2px solid var(--gp-accent); box-shadow: 0 0 30px var(--gp-accent)44; }}
.design-option h3 {{ margin: .3rem 0; color: var(--gp-text); font-size: 1.05rem; }}
.design-option p {{ margin: 0; color: var(--gp-muted); font-size: .82rem; line-height: 1.5; }}

.design-swatch {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-top: .1rem;
}}
.design-swatch span {{
    display: block;
    width: 32px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid rgba(255,255,255,.25);
}}

/* ── RESPONSIVE ──────────────────────────────────────────────────── */
@media (max-width: 720px) {{
    .main .block-container {{ padding: .8rem .7rem 3rem; }}
    .dash-hero {{ align-items: flex-start; flex-direction: column; padding: 1.25rem; }}
    .dash-hero-chip {{ align-self: flex-start; }}
    .dash-kpi {{ margin-bottom: .65rem; }}
    .design-option {{ min-height: 0; }}
    .stButton > button {{ font-size: 12px !important; padding: 10px 16px !important; }}
    section[data-testid="stSidebar"] .stButton > button,
    .nav-btn button {{
        font-size: 12px !important;
        padding: 10px 14px !important;
        min-height: 42px !important;
    }}
}}
</style>
<div class="theme-marker theme-design-{number}" aria-hidden="true"></div>
"""

def apply_theme(key: str = None, auto_rotate: bool = False):
    key = normalize_theme_key(key or (get_daily_theme() if auto_rotate else current_theme()))
    st.session_state["current_theme"] = key
    st.session_state["_gympro_theme"] = key
    st.markdown(build_css(key), unsafe_allow_html=True)
    return key

# ── GLOBAL CSS ──────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

.metric-card {
    background: rgba(20,20,30,0.5);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.75rem;
    backdrop-filter: blur(8px);
}
.metric-card .label {
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1;
}
.metric-card .sub {
    font-size: 0.75rem;
    margin-top: 0.25rem;
}
.metric-purple .value { color: #A78BFA; }
.metric-green  .value { color: #34D399; }
.metric-red    .value { color: #F87171; }
.metric-blue   .value { color: #60A5FA; }
.metric-amber  .value { color: #FBBF24; }

.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.badge-green  { background: #064E3B; color: #34D399; }
.badge-red    { background: #450A0A; color: #F87171; }
.badge-amber  { background: #451A03; color: #FBBF24; }
.badge-blue   { background: #0C1A3A; color: #60A5FA; }
.badge-gray   { background: #1E293B; color: #94A3B8; }

.page-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.page-header .icon { font-size: 1.8rem; }
.page-header h1 { font-size: 1.7rem; font-weight: 800; margin: 0; }
.page-header .sub { font-size: 0.85rem; opacity: 0.7; }

.stDataFrame thead th { background: rgba(20,20,30,0.5) !important; color: #7C3AED !important; font-weight: 700 !important; }
.stDataFrame tbody tr:hover td { background: rgba(124,58,237,0.05) !important; }

.nav-btn button {
    background: transparent !important;
    border: none !important;
    font-size: 0.9rem !important;
    text-align: left !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
}
.nav-btn button:hover { background: rgba(255,255,255,0.05) !important; }
.nav-btn-active button { background: rgba(124,58,237,0.15) !important; font-weight: 700 !important; }

.wa-link a { color: #34D399; font-weight: 600; text-decoration: none; }
.wa-link a:hover { text-decoration: underline; }

hr { border-color: rgba(255,255,255,0.05) !important; }

[data-testid="stExpander"] details > summary {
    list-style: none;
    display: flex;
    align-items: center;
    gap: 8px;
}
[data-testid="stExpander"] details > summary::-webkit-details-marker { display: none; }
[data-testid="stExpander"] details > summary::before {
    content: '▶';
    font-size: 0.7rem;
    transition: transform 0.2s;
    margin-right: 6px;
}
[data-testid="stExpander"] details[open] > summary::before { transform: rotate(90deg); }

.stMarkdown:empty { display: none !important; }
.stMarkdown:has(>:empty) { display: none !important; }
.stMarkdown:has(>:empty:only-child) { display: none !important; }

@media (max-width: 768px) {
    .main .block-container { padding: 0.75rem 0.5rem; }
    .metric-card .value { font-size: 1.4rem; }
    .page-header h1 { font-size: 1.3rem; }
}
</style>
"""

def inject_css():
    import streamlit as st
    import database as _db

    auto = _db.get_setting("theme_auto", "0") == "1"
    key = get_daily_theme() if auto else _db.get_setting("theme_key", "design_1")
    key = normalize_theme_key(key)
    st.session_state["current_theme"] = key
    st.session_state["_gympro_theme"] = key

    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(build_css(key), unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavSeparator"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def metric_card(label, value, sub="", color=""):
    cls = f"metric-{color}" if color else ""
    return f"""
    <div class="metric-card {cls}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {"<div class='sub'>" + sub + "</div>" if sub else ""}
    </div>"""

def page_header(icon, title, sub=""):
    import streamlit as st
    st.markdown(f"""
    <div class="page-header">
        <span class="icon">{icon}</span>
        <div>
            <h1>{title}</h1>
            {"<div class='sub'>" + sub + "</div>" if sub else ""}
        </div>
    </div>""", unsafe_allow_html=True)

def badge(text, color="gray"):
    return f'<span class="badge badge-{color}">{text}</span>'