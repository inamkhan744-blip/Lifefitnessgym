"""
GymPro Theme System v45.0 - FINAL MASTERPIECE
45 Themes, True 3D Buttons, True 3D Tables, Fixed Header Arrow, Wide Screen Fix.
"""

import streamlit as st
from datetime import date
import random

DESIGN_THEMES = {
    "design_1": {"name": "Clean Slate", "emoji": "☁️", "bg_gradient": "linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#0F172A", "accent2": "#475569", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(0, 0, 0, 0.1)", "text": "#0F172A", "muted": "#64748B", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.05)", "glow": "0 0 20px rgba(0,0,0,0.05)", "neon_glow": "0 0 15px rgba(0,0,0,0.05)", "particles": "☁️", "description": "Clean white & gray", "btn_gradient": "linear-gradient(135deg, #1E293B, #0F172A)", "btn_shadow": "0 4px 15px rgba(15,23,42,0.2)", "btn_hover_shadow": "0 8px 25px rgba(15,23,42,0.3)", "scrollbar_color": "#94A3B8"},
    "design_2": {"name": "Sky High", "emoji": "🌤️", "bg_gradient": "linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%)", "sidebar_gradient": "#F0F9FF", "accent": "#0284C7", "accent2": "#38BDF8", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(2, 132, 199, 0.2)", "text": "#082F49", "muted": "#0369A1", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(2,132,199,0.1)", "glow": "0 0 20px rgba(2,132,199,0.05)", "neon_glow": "0 0 15px rgba(2,132,199,0.1)", "particles": "🌤️", "description": "Fresh sky blue", "btn_gradient": "linear-gradient(135deg, #0EA5E9, #0284C7)", "btn_shadow": "0 4px 15px rgba(2,132,199,0.2)", "btn_hover_shadow": "0 8px 25px rgba(2,132,199,0.3)", "scrollbar_color": "#38BDF8"},
    "design_3": {"name": "Peach Fuzz", "emoji": "🍑", "bg_gradient": "linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#EA580C", "accent2": "#F97316", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(234, 88, 12, 0.2)", "text": "#431407", "muted": "#9A3412", "font": "'Inter', sans-serif", "radius": "20px", "shadow": "0 10px 30px rgba(234,88,12,0.1)", "glow": "0 0 20px rgba(234,88,12,0.05)", "neon_glow": "0 0 15px rgba(234,88,12,0.1)", "particles": "🍑", "description": "Soft warm peach", "btn_gradient": "linear-gradient(135deg, #F97316, #EA580C)", "btn_shadow": "0 4px 15px rgba(234,88,12,0.2)", "btn_hover_shadow": "0 8px 25px rgba(234,88,12,0.3)", "scrollbar_color": "#F97316"},
    "design_4": {"name": "Minty Fresh", "emoji": "🌿", "bg_gradient": "linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#059669", "accent2": "#10B981", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(5, 150, 105, 0.2)", "text": "#022C22", "muted": "#047857", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(5,150,105,0.1)", "glow": "0 0 20px rgba(5,150,105,0.05)", "neon_glow": "0 0 15px rgba(5,150,105,0.1)", "particles": "🌿", "description": "Refreshing mint", "btn_gradient": "linear-gradient(135deg, #10B981, #059669)", "btn_shadow": "0 4px 15px rgba(5,150,105,0.2)", "btn_hover_shadow": "0 8px 25px rgba(5,150,105,0.3)", "scrollbar_color": "#34D399"},
    "design_5": {"name": "Blush & Rose", "emoji": "🌸", "bg_gradient": "linear-gradient(135deg, #FDF2F8 0%, #FCE7F3 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#DB2777", "accent2": "#F472B6", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(219, 39, 119, 0.2)", "text": "#500724", "muted": "#BE185D", "font": "'Inter', sans-serif", "radius": "24px", "shadow": "0 10px 30px rgba(219,39,119,0.1)", "glow": "0 0 20px rgba(219,39,119,0.05)", "neon_glow": "0 0 15px rgba(219,39,119,0.1)", "particles": "🌸", "description": "Gentle pink", "btn_gradient": "linear-gradient(135deg, #EC4899, #DB2777)", "btn_shadow": "0 4px 15px rgba(219,39,119,0.2)", "btn_hover_shadow": "0 8px 25px rgba(219,39,119,0.3)", "scrollbar_color": "#F472B6"},
    "design_6": {"name": "Lavender Fields", "emoji": "💜", "bg_gradient": "linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#7C3AED", "accent2": "#A78BFA", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(124, 58, 237, 0.2)", "text": "#2E1065", "muted": "#6D28D9", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(124,58,237,0.1)", "glow": "0 0 20px rgba(124,58,237,0.05)", "neon_glow": "0 0 15px rgba(124,58,237,0.1)", "particles": "💜", "description": "Elegant purple", "btn_gradient": "linear-gradient(135deg, #8B5CF6, #7C3AED)", "btn_shadow": "0 4px 15px rgba(124,58,237,0.2)", "btn_hover_shadow": "0 8px 25px rgba(124,58,237,0.3)", "scrollbar_color": "#A78BFA"},
    "design_7": {"name": "Lemonade", "emoji": "🍋", "bg_gradient": "linear-gradient(135deg, #FEFCE8 0%, #FEF08A 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#CA8A04", "accent2": "#FDE047", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(202, 138, 4, 0.2)", "text": "#422006", "muted": "#854D0E", "font": "'Inter', sans-serif", "radius": "14px", "shadow": "0 10px 30px rgba(202,138,4,0.1)", "glow": "0 0 20px rgba(202,138,4,0.05)", "neon_glow": "0 0 15px rgba(202,138,4,0.1)", "particles": "🍋", "description": "Bright yellow", "btn_gradient": "linear-gradient(135deg, #FACC15, #EAB308)", "btn_shadow": "0 4px 15px rgba(202,138,4,0.2)", "btn_hover_shadow": "0 8px 25px rgba(202,138,4,0.3)", "scrollbar_color": "#FDE047"},
    "design_8": {"name": "Arctic Light", "emoji": "❄️", "bg_gradient": "linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#0891B2", "accent2": "#06B6D4", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(8, 145, 178, 0.2)", "text": "#083344", "muted": "#0E7490", "font": "'Inter', sans-serif", "radius": "18px", "shadow": "0 10px 30px rgba(8,145,178,0.1)", "glow": "0 0 20px rgba(8,145,178,0.05)", "neon_glow": "0 0 15px rgba(8,145,178,0.1)", "particles": "❄️", "description": "Cool crisp cyan", "btn_gradient": "linear-gradient(135deg, #22D3EE, #0891B2)", "btn_shadow": "0 4px 15px rgba(8,145,178,0.2)", "btn_hover_shadow": "0 8px 25px rgba(8,145,178,0.3)", "scrollbar_color": "#06B6D4"},
    "design_9": {"name": "Candy Pop", "emoji": "🍭", "bg_gradient": "linear-gradient(135deg, #FFFFFF 0%, #F3E8FF 100%)", "sidebar_gradient": "#FAF5FF", "accent": "#E11D48", "accent2": "#06B6D4", "surface": "rgba(255, 255, 255, 0.9)", "border": "rgba(225, 29, 72, 0.2)", "text": "#111827", "muted": "#4B5563", "font": "'Inter', sans-serif", "radius": "24px", "shadow": "0 10px 30px rgba(225,29,72,0.1)", "glow": "0 0 20px rgba(225,29,72,0.05)", "neon_glow": "0 0 15px rgba(225,29,72,0.1)", "particles": "🍭", "description": "Fun pink & cyan", "btn_gradient": "linear-gradient(135deg, #E11D48, #06B6D4)", "btn_shadow": "0 4px 15px rgba(225,29,72,0.2)", "btn_hover_shadow": "0 8px 25px rgba(225,29,72,0.3)", "scrollbar_color": "#E11D48"},
    "design_10": {"name": "Golden Sand", "emoji": "🏜️", "bg_gradient": "linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)", "sidebar_gradient": "#FFFBEB", "accent": "#B45309", "accent2": "#F59E0B", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(180, 83, 9, 0.2)", "text": "#451A03", "muted": "#92400E", "font": "'Playfair Display', serif", "radius": "16px", "shadow": "0 10px 30px rgba(180,83,9,0.1)", "glow": "0 0 20px rgba(180,83,9,0.05)", "neon_glow": "0 0 15px rgba(180,83,9,0.1)", "particles": "🏜️", "description": "Warm luxurious sand", "btn_gradient": "linear-gradient(135deg, #F59E0B, #B45309)", "btn_shadow": "0 4px 15px rgba(180,83,9,0.2)", "btn_hover_shadow": "0 8px 25px rgba(180,83,9,0.3)", "scrollbar_color": "#F59E0B"},
    "design_11": {"name": "Ocean Breeze", "emoji": "🌊", "bg_gradient": "linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#0D9488", "accent2": "#14B8A6", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(13, 148, 136, 0.2)", "text": "#042F2E", "muted": "#115E59", "font": "'Inter', sans-serif", "radius": "20px", "shadow": "0 10px 30px rgba(13,148,136,0.1)", "glow": "0 0 20px rgba(13,148,136,0.05)", "neon_glow": "0 0 15px rgba(13,148,136,0.1)", "particles": "🌊", "description": "Calm teal & aqua", "btn_gradient": "linear-gradient(135deg, #14B8A6, #0D9488)", "btn_shadow": "0 4px 15px rgba(13,148,136,0.2)", "btn_hover_shadow": "0 8px 25px rgba(13,148,136,0.3)", "scrollbar_color": "#14B8A6"},
    "design_12": {"name": "Ice & Fire", "emoji": "🔥", "bg_gradient": "linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#DC2626", "accent2": "#2563EB", "surface": "rgba(255, 255, 255, 0.9)", "border": "rgba(220, 38, 38, 0.2)", "text": "#0F172A", "muted": "#475569", "font": "'Space Mono', monospace", "radius": "12px", "shadow": "0 10px 30px rgba(220,38,38,0.1)", "glow": "0 0 20px rgba(220,38,38,0.05)", "neon_glow": "0 0 15px rgba(220,38,38,0.1)", "particles": "🔥", "description": "Bold red & blue", "btn_gradient": "linear-gradient(135deg, #DC2626, #2563EB)", "btn_shadow": "0 4px 15px rgba(220,38,38,0.2)", "btn_hover_shadow": "0 8px 25px rgba(220,38,38,0.3)", "scrollbar_color": "#DC2626"},
    "design_13": {"name": "Spring Meadow", "emoji": "🌺", "bg_gradient": "linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#16A34A", "accent2": "#F472B6", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(22, 163, 74, 0.2)", "text": "#052E16", "muted": "#15803D", "font": "'Inter', sans-serif", "radius": "18px", "shadow": "0 10px 30px rgba(22,163,74,0.1)", "glow": "0 0 20px rgba(22,163,74,0.05)", "neon_glow": "0 0 15px rgba(22,163,74,0.1)", "particles": "🌺", "description": "Fresh green & pink", "btn_gradient": "linear-gradient(135deg, #16A34A, #F472B6)", "btn_shadow": "0 4px 15px rgba(22,163,74,0.2)", "btn_hover_shadow": "0 8px 25px rgba(22,163,74,0.3)", "scrollbar_color": "#16A34A"},
    "design_14": {"name": "Sunset Glow", "emoji": "🌅", "bg_gradient": "linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#E11D48", "accent2": "#F97316", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(225, 29, 72, 0.2)", "text": "#4C0519", "muted": "#BE123C", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(225,29,72,0.1)", "glow": "0 0 20px rgba(225,29,72,0.05)", "neon_glow": "0 0 15px rgba(225,29,72,0.1)", "particles": "🌅", "description": "Warm sunset", "btn_gradient": "linear-gradient(135deg, #E11D48, #F97316)", "btn_shadow": "0 4px 15px rgba(225,29,72,0.2)", "btn_hover_shadow": "0 8px 25px rgba(225,29,72,0.3)", "scrollbar_color": "#E11D48"},
    "design_15": {"name": "Royal Blue", "emoji": "👑", "bg_gradient": "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)", "sidebar_gradient": "#FFFFFF", "accent": "#1D4ED8", "accent2": "#D4AF37", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(29, 78, 216, 0.2)", "text": "#172554", "muted": "#1E40AF", "font": "'Playfair Display', serif", "radius": "16px", "shadow": "0 10px 30px rgba(29,78,216,0.1)", "glow": "0 0 20px rgba(29,78,216,0.05)", "neon_glow": "0 0 15px rgba(29,78,216,0.1)", "particles": "👑", "description": "Royal blue & gold", "btn_gradient": "linear-gradient(135deg, #1D4ED8, #D4AF37)", "btn_shadow": "0 4px 15px rgba(29,78,216,0.2)", "btn_hover_shadow": "0 8px 25px rgba(29,78,216,0.3)", "scrollbar_color": "#1D4ED8"},
    "design_16": {"name": "Midnight Galaxy", "emoji": "🌌", "bg_gradient": "linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%)", "sidebar_gradient": "#0B0F19", "accent": "#8B5CF6", "accent2": "#3B82F6", "surface": "rgba(255, 255, 255, 0.1)", "border": "rgba(139, 92, 246, 0.3)", "text": "#F8FAFC", "muted": "#94A3B8", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.5)", "glow": "0 0 20px rgba(139,92,246,0.2)", "neon_glow": "0 0 15px rgba(139,92,246,0.3)", "particles": "🌌", "description": "Deep space purple", "btn_gradient": "linear-gradient(135deg, #8B5CF6, #3B82F6)", "btn_shadow": "0 4px 15px rgba(139,92,246,0.4)", "btn_hover_shadow": "0 8px 25px rgba(139,92,246,0.6)", "scrollbar_color": "#8B5CF6"},
    "design_17": {"name": "Cyber Punk", "emoji": "🤖", "bg_gradient": "linear-gradient(135deg, #000000 0%, #1A1A2E 100%)", "sidebar_gradient": "#0F0F1A", "accent": "#00F0FF", "accent2": "#FF003C", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(0, 240, 255, 0.3)", "text": "#E2E8F0", "muted": "#718096", "font": "'Space Mono', monospace", "radius": "8px", "shadow": "0 10px 30px rgba(0,0,0,0.8)", "glow": "0 0 20px rgba(0,240,255,0.2)", "neon_glow": "0 0 15px rgba(255,0,60,0.3)", "particles": "🤖", "description": "Neon Cyan & Red", "btn_gradient": "linear-gradient(135deg, #00F0FF, #FF003C)", "btn_shadow": "0 4px 15px rgba(0,240,255,0.4)", "btn_hover_shadow": "0 8px 25px rgba(255,0,60,0.5)", "scrollbar_color": "#00F0FF"},
    "design_18": {"name": "Dark Knight", "emoji": "🦇", "bg_gradient": "linear-gradient(135deg, #111827 0%, #374151 100%)", "sidebar_gradient": "#0F172A", "accent": "#F59E0B", "accent2": "#D97706", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(245, 158, 11, 0.3)", "text": "#F3F4F6", "muted": "#9CA3AF", "font": "'Inter', sans-serif", "radius": "12px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(245,158,11,0.15)", "neon_glow": "0 0 15px rgba(245,158,11,0.2)", "particles": "🦇", "description": "Dark gray & gold", "btn_gradient": "linear-gradient(135deg, #F59E0B, #D97706)", "btn_shadow": "0 4px 15px rgba(245,158,11,0.4)", "btn_hover_shadow": "0 8px 25px rgba(245,158,11,0.6)", "scrollbar_color": "#F59E0B"},
    "design_19": {"name": "Crimson Red", "emoji": "🩸", "bg_gradient": "linear-gradient(135deg, #1F0000 0%, #450A0A 100%)", "sidebar_gradient": "#2A0000", "accent": "#EF4444", "accent2": "#DC2626", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(239, 68, 68, 0.3)", "text": "#FEF2F2", "muted": "#FCA5A5", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(239,68,68,0.2)", "neon_glow": "0 0 15px rgba(239,68,68,0.3)", "particles": "🩸", "description": "Intense red", "btn_gradient": "linear-gradient(135deg, #EF4444, #DC2626)", "btn_shadow": "0 4px 15px rgba(239,68,68,0.4)", "btn_hover_shadow": "0 8px 25px rgba(239,68,68,0.6)", "scrollbar_color": "#EF4444"},
    "design_20": {"name": "Emerald Green", "emoji": "💎", "bg_gradient": "linear-gradient(135deg, #022C22 0%, #064E3B 100%)", "sidebar_gradient": "#011F18", "accent": "#10B981", "accent2": "#34D399", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(16, 185, 129, 0.3)", "text": "#ECFDF5", "muted": "#6EE7B7", "font": "'Inter', sans-serif", "radius": "20px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(16,185,129,0.2)", "neon_glow": "0 0 15px rgba(16,185,129,0.3)", "particles": "💎", "description": "Deep emerald", "btn_gradient": "linear-gradient(135deg, #10B981, #34D399)", "btn_shadow": "0 4px 15px rgba(16,185,129,0.4)", "btn_hover_shadow": "0 8px 25px rgba(16,185,129,0.6)", "scrollbar_color": "#10B981"},
    "design_21": {"name": "Energy Burst", "emoji": "⚡", "bg_gradient": "linear-gradient(135deg, #18181B 0%, #27272A 100%)", "sidebar_gradient": "#111111", "accent": "#FACC15", "accent2": "#F59E0B", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(250, 204, 21, 0.3)", "text": "#FAFAFA", "muted": "#A1A1AA", "font": "'Space Mono', monospace", "radius": "12px", "shadow": "0 10px 30px rgba(0,0,0,0.8)", "glow": "0 0 20px rgba(250,204,21,0.2)", "neon_glow": "0 0 15px rgba(250,204,21,0.3)", "particles": "⚡", "description": "Dark carbon & yellow", "btn_gradient": "linear-gradient(135deg, #FACC15, #F59E0B)", "btn_shadow": "0 4px 15px rgba(250,204,21,0.4)", "btn_hover_shadow": "0 8px 25px rgba(250,204,21,0.6)", "scrollbar_color": "#FACC15"},
    "design_22": {"name": "Black & White", "emoji": "♟️", "bg_gradient": "linear-gradient(135deg, #000000 0%, #1F2937 100%)", "sidebar_gradient": "#0A0A0A", "accent": "#F3F4F6", "accent2": "#9CA3AF", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(243, 244, 246, 0.2)", "text": "#FFFFFF", "muted": "#9CA3AF", "font": "'Inter', sans-serif", "radius": "0px", "shadow": "0 10px 30px rgba(0,0,0,0.8)", "glow": "0 0 20px rgba(255,255,255,0.1)", "neon_glow": "0 0 15px rgba(255,255,255,0.15)", "particles": "♟️", "description": "Pure monochrome", "btn_gradient": "linear-gradient(135deg, #4B5563, #1F2937)", "btn_shadow": "0 4px 15px rgba(255,255,255,0.2)", "btn_hover_shadow": "0 8px 25px rgba(255,255,255,0.4)", "scrollbar_color": "#9CA3AF"},
    "design_23": {"name": "Deep Ocean", "emoji": "🐋", "bg_gradient": "linear-gradient(135deg, #000428 0%, #004E92 100%)", "sidebar_gradient": "#000A1A", "accent": "#00D2FF", "accent2": "#3A7BD5", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(0, 210, 255, 0.3)", "text": "#E0F2FE", "muted": "#7DD3FC", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(0,210,255,0.2)", "neon_glow": "0 0 15px rgba(0,210,255,0.3)", "particles": "🐋", "description": "Abyss blue", "btn_gradient": "linear-gradient(135deg, #00D2FF, #3A7BD5)", "btn_shadow": "0 4px 15px rgba(0,210,255,0.4)", "btn_hover_shadow": "0 8px 25px rgba(0,210,255,0.6)", "scrollbar_color": "#00D2FF"},
    "design_24": {"name": "Mystic Night", "emoji": "🌙", "bg_gradient": "linear-gradient(135deg, #0B0C10 0%, #1F2833 100%)", "sidebar_gradient": "#080A0F", "accent": "#66FCF1", "accent2": "#45A29E", "surface": "rgba(255, 255, 255, 0.03)", "border": "rgba(102, 252, 241, 0.2)", "text": "#C5C6C7", "muted": "#45A29E", "font": "'Inter', sans-serif", "radius": "14px", "shadow": "0 10px 30px rgba(0,0,0,0.7)", "glow": "0 0 20px rgba(102,252,241,0.15)", "neon_glow": "0 0 15px rgba(102,252,241,0.2)", "particles": "🌙", "description": "Dark teal & gray", "btn_gradient": "linear-gradient(135deg, #66FCF1, #45A29E)", "btn_shadow": "0 4px 15px rgba(102,252,241,0.3)", "btn_hover_shadow": "0 8px 25px rgba(102,252,241,0.5)", "scrollbar_color": "#66FCF1"},
    "design_25": {"name": "Neon Dream", "emoji": "💜", "bg_gradient": "linear-gradient(135deg, #1A0B2E 0%, #3B0B54 100%)", "sidebar_gradient": "#120621", "accent": "#FF00FF", "accent2": "#8B5CF6", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(255, 0, 255, 0.3)", "text": "#FDF4FF", "muted": "#E879F9", "font": "'Inter', sans-serif", "radius": "20px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(255,0,255,0.2)", "neon_glow": "0 0 15px rgba(255,0,255,0.3)", "particles": "💜", "description": "Neon purple", "btn_gradient": "linear-gradient(135deg, #FF00FF, #8B5CF6)", "btn_shadow": "0 4px 15px rgba(255,0,255,0.4)", "btn_hover_shadow": "0 8px 25px rgba(255,0,255,0.6)", "scrollbar_color": "#FF00FF"},
    "design_26": {"name": "The Matrix", "emoji": "🟢", "bg_gradient": "linear-gradient(135deg, #000000 0%, #001A00 100%)", "sidebar_gradient": "#001100", "accent": "#00FF41", "accent2": "#008F11", "surface": "rgba(0, 255, 65, 0.05)", "border": "rgba(0, 255, 65, 0.3)", "text": "#E0FFE0", "muted": "#00FF41", "font": "'Space Mono', monospace", "radius": "0px", "shadow": "0 10px 30px rgba(0,255,65,0.1)", "glow": "0 0 20px rgba(0,255,65,0.2)", "neon_glow": "0 0 15px rgba(0,255,65,0.3)", "particles": "🟢", "description": "Hacker terminal", "btn_gradient": "linear-gradient(135deg, #00FF41, #008F11)", "btn_shadow": "0 4px 15px rgba(0,255,65,0.4)", "btn_hover_shadow": "0 8px 25px rgba(0,255,65,0.6)", "scrollbar_color": "#00FF41"},
    "design_27": {"name": "Synthwave", "emoji": "🌆", "bg_gradient": "linear-gradient(135deg, #2B00FF 0%, #FF00A0 100%)", "sidebar_gradient": "#1A005C", "accent": "#00FFFF", "accent2": "#FF00FF", "surface": "rgba(50, 0, 80, 0.5)", "border": "rgba(0, 255, 255, 0.4)", "text": "#FFFFFF", "muted": "#FFD1FF", "font": "'Playfair Display', serif", "radius": "20px", "shadow": "0 10px 30px rgba(255,0,255,0.2)", "glow": "0 0 20px rgba(0,255,255,0.2)", "neon_glow": "0 0 15px rgba(255,0,255,0.3)", "particles": "🌆", "description": "Retro 80s neon", "btn_gradient": "linear-gradient(135deg, #FF00FF, #00FFFF)", "btn_shadow": "0 4px 15px rgba(255,0,255,0.4)", "btn_hover_shadow": "0 8px 25px rgba(0,255,255,0.5)", "scrollbar_color": "#FF00FF"},
    "design_28": {"name": "Vaporwave", "emoji": "🌴", "bg_gradient": "linear-gradient(135deg, #FF6B6B 0%, #C778FF 50%, #4ECDC4 100%)", "sidebar_gradient": "#1A0F2E", "accent": "#FFD166", "accent2": "#FF6B6B", "surface": "rgba(255, 255, 255, 0.2)", "border": "rgba(255, 255, 255, 0.4)", "text": "#FFFFFF", "muted": "#E2E8F0", "font": "'Inter', sans-serif", "radius": "24px", "shadow": "0 10px 30px rgba(0,0,0,0.2)", "glow": "0 0 20px rgba(255,255,255,0.2)", "neon_glow": "0 0 15px rgba(255,255,255,0.3)", "particles": "🌴", "description": "Aesthetic retro", "btn_gradient": "linear-gradient(135deg, #FFD166, #FF6B6B)", "btn_shadow": "0 4px 15px rgba(255,107,107,0.4)", "btn_hover_shadow": "0 8px 25px rgba(255,209,102,0.6)", "scrollbar_color": "#FFD166"},
    "design_29": {"name": "Cyber Neon", "emoji": "⚡", "bg_gradient": "linear-gradient(135deg, #000000 0%, #1A1A00 100%)", "sidebar_gradient": "#0D0D00", "accent": "#FFFF00", "accent2": "#FFD700", "surface": "rgba(20, 20, 0, 0.7)", "border": "rgba(255, 255, 0, 0.4)", "text": "#FFFFFF", "muted": "#CCCC00", "font": "'Space Mono', monospace", "radius": "8px", "shadow": "0 10px 30px rgba(255,255,0,0.15)", "glow": "0 0 20px rgba(255,255,0,0.2)", "neon_glow": "0 0 15px rgba(255,255,0,0.3)", "particles": "⚡", "description": "Highlighter yellow", "btn_gradient": "linear-gradient(135deg, #FFFF00, #FFA500)", "btn_shadow": "0 4px 15px rgba(255,255,0,0.4)", "btn_hover_shadow": "0 8px 25px rgba(255,255,0,0.6)", "scrollbar_color": "#FFFF00"},
    "design_30": {"name": "Neon Tokyo", "emoji": "🏮", "bg_gradient": "linear-gradient(135deg, #0A001A 0%, #2D004D 100%)", "sidebar_gradient": "#05000D", "accent": "#FF2A6D", "accent2": "#05D9E8", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(255, 42, 109, 0.3)", "text": "#FFFFFF", "muted": "#B794F4", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.7)", "glow": "0 0 20px rgba(255,42,109,0.2)", "neon_glow": "0 0 15px rgba(5,217,232,0.3)", "particles": "🏮", "description": "Pink & cyan neon", "btn_gradient": "linear-gradient(135deg, #FF2A6D, #05D9E8)", "btn_shadow": "0 4px 15px rgba(255,42,109,0.4)", "btn_hover_shadow": "0 8px 25px rgba(5,217,232,0.6)", "scrollbar_color": "#FF2A6D"},
    "design_31": {"name": "Forest Green", "emoji": "🌲", "bg_gradient": "linear-gradient(135deg, #F0FDF4 0%, #BBF7D0 100%)", "sidebar_gradient": "#DCFCE7", "accent": "#15803D", "accent2": "#22C55E", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(21, 128, 61, 0.2)", "text": "#052E16", "muted": "#166534", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(21,128,61,0.1)", "glow": "0 0 20px rgba(21,128,61,0.05)", "neon_glow": "0 0 15px rgba(21,128,61,0.1)", "particles": "🌲", "description": "Light forest", "btn_gradient": "linear-gradient(135deg, #22C55E, #15803D)", "btn_shadow": "0 4px 15px rgba(21,128,61,0.3)", "btn_hover_shadow": "0 8px 25px rgba(21,128,61,0.4)", "scrollbar_color": "#22C55E"},
    "design_32": {"name": "Autumn Leaves", "emoji": "🍂", "bg_gradient": "linear-gradient(135deg, #FFF7ED 0%, #FED7AA 100%)", "sidebar_gradient": "#FFEDD5", "accent": "#C2410C", "accent2": "#F97316", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(194, 65, 12, 0.2)", "text": "#431407", "muted": "#9A3412", "font": "'Playfair Display', serif", "radius": "16px", "shadow": "0 10px 30px rgba(194,65,12,0.1)", "glow": "0 0 20px rgba(194,65,12,0.05)", "neon_glow": "0 0 15px rgba(194,65,12,0.1)", "particles": "🍂", "description": "Warm autumn", "btn_gradient": "linear-gradient(135deg, #F97316, #C2410C)", "btn_shadow": "0 4px 15px rgba(194,65,12,0.3)", "btn_hover_shadow": "0 8px 25px rgba(194,65,12,0.4)", "scrollbar_color": "#F97316"},
    "design_33": {"name": "Tropical Paradise", "emoji": "🏝️", "bg_gradient": "linear-gradient(135deg, #ECFDF5 0%, #A7F3D0 100%)", "sidebar_gradient": "#D1FAE5", "accent": "#047857", "accent2": "#FBBF24", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(4, 120, 87, 0.2)", "text": "#022C22", "muted": "#065F46", "font": "'Inter', sans-serif", "radius": "24px", "shadow": "0 10px 30px rgba(4,120,87,0.1)", "glow": "0 0 20px rgba(4,120,87,0.05)", "neon_glow": "0 0 15px rgba(4,120,87,0.1)", "particles": "🏝️", "description": "Teal & sunny yellow", "btn_gradient": "linear-gradient(135deg, #047857, #FBBF24)", "btn_shadow": "0 4px 15px rgba(4,120,87,0.3)", "btn_hover_shadow": "0 8px 25px rgba(4,120,87,0.4)", "scrollbar_color": "#047857"},
    "design_34": {"name": "Aurora Borealis", "emoji": "🌌", "bg_gradient": "linear-gradient(135deg, #022C22 0%, #0F172A 50%, #2E1065 100%)", "sidebar_gradient": "#042F2E", "accent": "#34D399", "accent2": "#818CF8", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(52, 211, 153, 0.2)", "text": "#F8FAFC", "muted": "#94A3B8", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(52,211,153,0.2)", "neon_glow": "0 0 15px rgba(129,140,248,0.3)", "particles": "🌌", "description": "Green to purple sky", "btn_gradient": "linear-gradient(135deg, #34D399, #818CF8)", "btn_shadow": "0 4px 15px rgba(52,211,153,0.4)", "btn_hover_shadow": "0 8px 25px rgba(52,211,153,0.6)", "scrollbar_color": "#34D399"},
    "design_35": {"name": "Desert Night", "emoji": "🌵", "bg_gradient": "linear-gradient(135deg, #18181B 0%, #3F3F46 100%)", "sidebar_gradient": "#09090B", "accent": "#F97316", "accent2": "#FCD34D", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(249, 115, 22, 0.3)", "text": "#FAFAFA", "muted": "#A1A1AA", "font": "'Inter', sans-serif", "radius": "12px", "shadow": "0 10px 30px rgba(0,0,0,0.7)", "glow": "0 0 20px rgba(249,115,22,0.2)", "neon_glow": "0 0 15px rgba(249,115,22,0.3)", "particles": "🌵", "description": "Dark orange & sand", "btn_gradient": "linear-gradient(135deg, #F97316, #FCD34D)", "btn_shadow": "0 4px 15px rgba(249,115,22,0.4)", "btn_hover_shadow": "0 8px 25px rgba(249,115,22,0.6)", "scrollbar_color": "#F97316"},
    "design_36": {"name": "Cherry Blossom", "emoji": "🌸", "bg_gradient": "linear-gradient(135deg, #FDF2F8 0%, #FBCFE8 100%)", "sidebar_gradient": "#FCE7F3", "accent": "#BE185D", "accent2": "#F472B6", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(190, 24, 93, 0.2)", "text": "#500724", "muted": "#9D174D", "font": "'Inter', sans-serif", "radius": "20px", "shadow": "0 10px 30px rgba(190,24,93,0.1)", "glow": "0 0 20px rgba(190,24,93,0.05)", "neon_glow": "0 0 15px rgba(190,24,93,0.1)", "particles": "🌸", "description": "Soft cherry pink", "btn_gradient": "linear-gradient(135deg, #F472B6, #BE185D)", "btn_shadow": "0 4px 15px rgba(190,24,93,0.3)", "btn_hover_shadow": "0 8px 25px rgba(190,24,93,0.4)", "scrollbar_color": "#F472B6"},
    "design_37": {"name": "Strawberry Lemonade", "emoji": "🍓", "bg_gradient": "linear-gradient(135deg, #FFF1F2 0%, #FEF08A 100%)", "sidebar_gradient": "#FFE4E6", "accent": "#E11D48", "accent2": "#CA8A04", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(225, 29, 72, 0.2)", "text": "#4C0519", "muted": "#881337", "font": "'Inter', sans-serif", "radius": "18px", "shadow": "0 10px 30px rgba(225,29,72,0.1)", "glow": "0 0 20px rgba(225,29,72,0.05)", "neon_glow": "0 0 15px rgba(225,29,72,0.1)", "particles": "🍓", "description": "Pink & yellow", "btn_gradient": "linear-gradient(135deg, #E11D48, #CA8A04)", "btn_shadow": "0 4px 15px rgba(225,29,72,0.3)", "btn_hover_shadow": "0 8px 25px rgba(225,29,72,0.4)", "scrollbar_color": "#E11D48"},
    "design_38": {"name": "Mango Tango", "emoji": "🥭", "bg_gradient": "linear-gradient(135deg, #FFFBEB 0%, #FDE68A 100%)", "sidebar_gradient": "#FEF3C7", "accent": "#D97706", "accent2": "#EA580C", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(217, 119, 6, 0.2)", "text": "#451A03", "muted": "#92400E", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(217,119,6,0.1)", "glow": "0 0 20px rgba(217,119,6,0.05)", "neon_glow": "0 0 15px rgba(217,119,6,0.1)", "particles": "🥭", "description": "Mango yellow & orange", "btn_gradient": "linear-gradient(135deg, #D97706, #EA580C)", "btn_shadow": "0 4px 15px rgba(217,119,6,0.3)", "btn_hover_shadow": "0 8px 25px rgba(217,119,6,0.4)", "scrollbar_color": "#D97706"},
    "design_39": {"name": "Rose Gold", "emoji": "🥇", "bg_gradient": "linear-gradient(135deg, #FFF1F2 0%, #FECDD3 100%)", "sidebar_gradient": "#FFE4E6", "accent": "#E11D48", "accent2": "#F59E0B", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(225, 29, 72, 0.2)", "text": "#4C0519", "muted": "#9F1239", "font": "'Playfair Display', serif", "radius": "20px", "shadow": "0 10px 30px rgba(225,29,72,0.1)", "glow": "0 0 20px rgba(225,29,72,0.05)", "neon_glow": "0 0 15px rgba(225,29,72,0.1)", "particles": "🥇", "description": "Rose gold luxury", "btn_gradient": "linear-gradient(135deg, #E11D48, #F59E0B)", "btn_shadow": "0 4px 15px rgba(225,29,72,0.3)", "btn_hover_shadow": "0 8px 25px rgba(225,29,72,0.4)", "scrollbar_color": "#E11D48"},
    "design_40": {"name": "Liquid Silver", "emoji": "🥈", "bg_gradient": "linear-gradient(135deg, #F8FAFC 0%, #CBD5E1 100%)", "sidebar_gradient": "#F1F5F9", "accent": "#475569", "accent2": "#94A3B8", "surface": "rgba(255, 255, 255, 0.8)", "border": "rgba(71, 85, 105, 0.2)", "text": "#0F172A", "muted": "#64748B", "font": "'Inter', sans-serif", "radius": "12px", "shadow": "0 10px 30px rgba(0,0,0,0.1)", "glow": "0 0 20px rgba(0,0,0,0.05)", "neon_glow": "0 0 15px rgba(0,0,0,0.1)", "particles": "🥈", "description": "Platinum & steel", "btn_gradient": "linear-gradient(135deg, #475569, #94A3B8)", "btn_shadow": "0 4px 15px rgba(71,85,105,0.3)", "btn_hover_shadow": "0 8px 25px rgba(71,85,105,0.5)", "scrollbar_color": "#475569"},
    "design_41": {"name": "Royal Crown", "emoji": "👑", "bg_gradient": "linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%)", "sidebar_gradient": "#020617", "accent": "#D4AF37", "accent2": "#F3D98B", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(212, 175, 55, 0.3)", "text": "#F8FAFC", "muted": "#94A3B8", "font": "'Playfair Display', serif", "radius": "12px", "shadow": "0 10px 30px rgba(0,0,0,0.8)", "glow": "0 0 20px rgba(212,175,55,0.2)", "neon_glow": "0 0 15px rgba(212,175,55,0.3)", "particles": "👑", "description": "Dark & pure gold", "btn_gradient": "linear-gradient(135deg, #D4AF37, #F3D98B)", "btn_shadow": "0 4px 15px rgba(212,175,55,0.4)", "btn_hover_shadow": "0 8px 25px rgba(212,175,55,0.6)", "scrollbar_color": "#D4AF37"},
    "design_42": {"name": "Platinum", "emoji": "💎", "bg_gradient": "linear-gradient(135deg, #E2E8F0 0%, #FFFFFF 100%)", "sidebar_gradient": "#F8FAFC", "accent": "#334155", "accent2": "#94A3B8", "surface": "rgba(255, 255, 255, 0.9)", "border": "rgba(51, 65, 85, 0.2)", "text": "#0F172A", "muted": "#475569", "font": "'Playfair Display', serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.1)", "glow": "0 0 20px rgba(0,0,0,0.05)", "neon_glow": "0 0 15px rgba(0,0,0,0.1)", "particles": "💎", "description": "Bright clean luxury", "btn_gradient": "linear-gradient(135deg, #334155, #94A3B8)", "btn_shadow": "0 4px 15px rgba(51,65,85,0.3)", "btn_hover_shadow": "0 8px 25px rgba(51,65,85,0.5)", "scrollbar_color": "#334155"},
    "design_43": {"name": "Emerald & Gold", "emoji": "💰", "bg_gradient": "linear-gradient(135deg, #022C22 0%, #064E3B 100%)", "sidebar_gradient": "#011F18", "accent": "#D4AF37", "accent2": "#10B981", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(212, 175, 55, 0.3)", "text": "#ECFDF5", "muted": "#6EE7B7", "font": "'Playfair Display', serif", "radius": "12px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(212,175,55,0.2)", "neon_glow": "0 0 15px rgba(16,185,129,0.3)", "particles": "💰", "description": "Rich green & gold", "btn_gradient": "linear-gradient(135deg, #D4AF37, #10B981)", "btn_shadow": "0 4px 15px rgba(212,175,55,0.4)", "btn_hover_shadow": "0 8px 25px rgba(212,175,55,0.6)", "scrollbar_color": "#D4AF37"},
    "design_44": {"name": "Midnight Velvet", "emoji": "🍷", "bg_gradient": "linear-gradient(135deg, #1A001A 0%, #4A0033 100%)", "sidebar_gradient": "#0D000D", "accent": "#E879F9", "accent2": "#F472B6", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(232, 121, 249, 0.3)", "text": "#FDF4FF", "muted": "#C084FC", "font": "'Playfair Display', serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.8)", "glow": "0 0 20px rgba(232,121,249,0.2)", "neon_glow": "0 0 15px rgba(232,121,249,0.3)", "particles": "🍷", "description": "Deep plum velvet", "btn_gradient": "linear-gradient(135deg, #E879F9, #F472B6)", "btn_shadow": "0 4px 15px rgba(232,121,249,0.4)", "btn_hover_shadow": "0 8px 25px rgba(232,121,249,0.6)", "scrollbar_color": "#E879F9"},
    "design_45": {"name": "Golden Hour", "emoji": "🌇", "bg_gradient": "linear-gradient(135deg, #1C1917 0%, #44403C 100%)", "sidebar_gradient": "#0C0A09", "accent": "#FBBF24", "accent2": "#F59E0B", "surface": "rgba(255, 255, 255, 0.05)", "border": "rgba(251, 191, 36, 0.3)", "text": "#FAFAF9", "muted": "#A8A29E", "font": "'Inter', sans-serif", "radius": "16px", "shadow": "0 10px 30px rgba(0,0,0,0.6)", "glow": "0 0 20px rgba(251,191,36,0.2)", "neon_glow": "0 0 15px rgba(251,191,36,0.3)", "particles": "🌇", "description": "Warm stone & gold", "btn_gradient": "linear-gradient(135deg, #FBBF24, #F59E0B)", "btn_shadow": "0 4px 15px rgba(251,191,36,0.4)", "btn_hover_shadow": "0 8px 25px rgba(251,191,36,0.6)", "scrollbar_color": "#FBBF24"},
}

THEMES = DESIGN_THEMES
THEME_KEYS = list(DESIGN_THEMES.keys())
THEME_NAMES = {k: f"{v['emoji']} {v['name']}" for i, (k, v) in enumerate(DESIGN_THEMES.items())}

LEGACY_THEME_ALIASES = {
    "dark_slate": "design_1", "energy_burst": "design_21", "royal_purple": "design_6", "ocean_blue": "design_2",
    "emerald_green": "design_20", "crimson_red": "design_19", "cyber_cyan": "design_17", "neon_pink": "design_25",
    "midnight_galaxy": "design_16", "sunset_orange": "design_14", "ice_blue": "design_8", "forest_green": "design_31",
    "cherry_blossom": "design_36", "golden_hour": "design_45", "dark_knight": "design_18", "tropical_sunset": "design_33",
}
for i in range(46, 100):
    LEGACY_THEME_ALIASES[f"design_{i}"] = THEME_KEYS[i % len(THEME_KEYS)]

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
    
    particle_html = ""
    for i in range(6):
        size = random.randint(20, 40)
        left = random.randint(5, 95)
        delay = random.randint(0, 10)
        duration = random.randint(15, 25)
        opacity = random.uniform(0.1, 0.3)
        particle_html += f'<div class="gp-particle" style="left:{left}vw; animation-delay:-{delay}s; animation-duration:{duration}s; font-size:{size}px; opacity:{opacity};">{t["particles"]}</div>'

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,700&family=Inter:wght@300;400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');

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

@keyframes gradientMove {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
@keyframes floatParticle {{ 0% {{ transform: translateY(100vh) rotate(0deg); }} 100% {{ transform: translateY(-10vh) rotate(360deg); }} }}
@keyframes fadeInPage {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes neonPulse {{ 0%, 100% {{ text-shadow: 0 0 10px var(--gp-accent)44, 0 0 20px var(--gp-accent)22; }} 50% {{ text-shadow: 0 0 20px var(--gp-accent)66, 0 0 30px var(--gp-accent)44; }} }}

/* Custom Text Selection & Scrollbar */
::selection {{ background: var(--gp-accent) !important; color: #FFFFFF !important; }}
::-webkit-scrollbar {{ width: 8px !important; height: 8px !important; }}
::-webkit-scrollbar-track {{ background: transparent !important; }}
::-webkit-scrollbar-thumb {{ background: var(--gp-scrollbar) !important; border-radius: 10px !important; }}

/* Floating Particles */
.gp-particle {{ position: fixed; bottom: -50px; z-index: 0; pointer-events: none; animation: floatParticle linear infinite; }}

.stApp, [data-testid="stAppViewContainer"] {{ background: var(--gp-bg) !important; background-size: 400% 400% !important; animation: gradientMove 20s ease infinite !important; color: var(--gp-text) !important; min-height: 100vh !important; position: relative; z-index: 1; }}
.main .block-container {{ animation: fadeInPage 0.6s ease-out forwards !important; }}

/* Force ALL text to be dark/light depending on theme */
.main, .main p, .main span:not(.material-symbols-rounded), .main div, .main h1, .main h2, .main h3, .main h4, .main h5, .main h6, .main label, [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"], [data-testid="stMetricValue"] > div, [data-testid="stHeading"] {{ color: var(--gp-text) !important; }}
[data-testid="stMetricValue"] > div {{ font-weight: 900 !important; text-shadow: none !important; }}
h1, h2, h3, .page-header h1 {{ animation: neonPulse 3s infinite alternate !important; }}

/* Tabs, Captions */
button[data-baseweb="tab"] {{ color: var(--gp-text) !important; opacity: 0.7 !important; font-weight: 700 !important; }}
button[data-baseweb="tab"] * {{ color: var(--gp-text) !important; }}
button[data-baseweb="tab"]:hover {{ opacity: 1 !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color: var(--gp-accent) !important; opacity: 1 !important; border-bottom: 3px solid var(--gp-accent) !important; }}
button[data-baseweb="tab"][aria-selected="true"] * {{ color: var(--gp-accent) !important; }}
[data-testid="stCaptionContainer"], .stCaption, small {{ color: var(--gp-muted) !important; opacity: 1 !important; }}

/* 🚀 EXTREME 3D TABLES */
[data-testid="stDataFrame"], .stDataFrame, table {{
    background-color: #FFFFFF !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    border-radius: 16px !important;
    box-shadow: 0 12px 0px rgba(0,0,0,0.15), 0 20px 30px rgba(0,0,0,0.1) !important; 
    transform: translateY(-6px) !important;
    transition: all 0.2s ease !important;
    margin-bottom: 30px !important;
    overflow: hidden !important;
}}
[data-testid="stDataFrame"]:hover, .stDataFrame:hover, table:hover {{
    transform: translateY(-8px) !important;
    box-shadow: 0 15px 0px rgba(0,0,0,0.15), 0 25px 35px rgba(0,0,0,0.15) !important;
}}
.main .block-container, [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], [data-testid="stAppViewContainer"] {{
    overflow: visible !important;
}}
th {{
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important;
    font-weight: 800 !important;
    padding: 14px 15px !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    border-bottom: 2px solid rgba(0,0,0,0.1) !important;
}}
td {{
    padding: 12px 15px !important;
    border-bottom: 1px solid rgba(0,0,0,0.05) !important;
    color: #0F172A !important; 
    font-weight: 600 !important;
}}
tr:nth-child(even) td {{ background: rgba(0,0,0,0.02) !important; }}
tr:hover td {{ background: rgba(255,255,255,1) !important; box-shadow: inset 0 0 20px var(--gp-accent)22 !important; }}

/* 🚀 TRUE 3D BUTTONS (Mobile Safe) */
.stButton > button, 
section[data-testid="stSidebar"] .stButton > button, 
section[data-testid="stSidebar"] .nav-btn button {{
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important; 
    border: 1px solid rgba(255,255,255,0.2) !important; 
    border-radius: var(--gp-radius) !important; 
    font-weight: 800 !important; 
    padding: 12px 24px !important; 
    box-shadow: 0 6px 0 rgba(0,0,0,0.4), 0 10px 15px rgba(0,0,0,0.2) !important; 
    transform: translateY(-3px) !important; 
    transition: all 0.1s ease !important; 
}}
.stButton > button *, 
section[data-testid="stSidebar"] .stButton > button *, 
section[data-testid="stSidebar"] .nav-btn button * {{
    color: #FFFFFF !important; 
    font-weight: 800 !important; 
    font-size: 15px !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.4) !important;
}}
.stButton > button:hover, 
section[data-testid="stSidebar"] .stButton > button:hover, 
section[data-testid="stSidebar"] .nav-btn button:hover {{
    transform: translateY(-5px) !important;
    box-shadow: 0 8px 0 rgba(0,0,0,0.4), 0 12px 20px rgba(0,0,0,0.3) !important;
}}
.stButton > button:active, 
section[data-testid="stSidebar"] .stButton > button:active, 
section[data-testid="stSidebar"] .nav-btn button:active {{
    transform: translateY(4px) !important; 
    box-shadow: 0 0px 0 rgba(0,0,0,0.4), 0 2px 5px rgba(0,0,0,0.2) !important;
}}
section[data-testid="stSidebar"] .nav-btn-active button {{
    background: var(--gp-btn-grad) !important;
}}

/* Sidebar & Inputs */
section[data-testid="stSidebar"] {{ background-color: var(--gp-sidebar) !important; border-right: 1px solid var(--gp-border) !important; box-shadow: 4px 0 15px rgba(0,0,0,0.03) !important; z-index: 1000; }}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span:not(.material-symbols-rounded), section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stMarkdown div {{ color: var(--gp-text) !important; }}
section[data-testid="stSidebar"] div[style*="background:#1E293B"], section[data-testid="stSidebar"] div[style*="background:#0F172A"] {{ background: rgba(255,255,255,0.8) !important; border: 1px solid var(--gp-border) !important; }}
section[data-testid="stSidebar"] div[style*="background:#1E293B"] *, section[data-testid="stSidebar"] div[style*="background:#0F172A"] * {{ color: var(--gp-text) !important; }}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, div[data-baseweb="select"] > div {{ background-color: rgba(255,255,255,0.9) !important; color: #000000 !important; border: 1px solid rgba(0,0,0,0.1) !important; border-radius: 10px !important; box-shadow: inset 0 2px 5px rgba(0,0,0,0.05) !important; transition: all 0.3s ease !important; }}
.stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTextArea textarea:focus {{ box-shadow: inset 0 2px 5px rgba(0,0,0,0.05), 0 0 0 3px var(--gp-accent)44 !important; border-color: var(--gp-accent) !important; }}
div[data-baseweb="select"] div[role="combobox"], div[data-baseweb="select"] svg {{ color: #000000 !important; fill: #000000 !important; }}
ul[role="listbox"] {{ background-color: #FFFFFF !important; box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important; border-radius: 10px !important; }}
li[role="option"] {{ color: #000000 !important; padding: 10px !important; }}

/* Checkboxes, Radios, Progress, Spinner */
[data-testid="stCheckbox"] > div[role="checkbox"], [data-testid="stCheckbox"] div[data-baseweb="checkbox"] > div {{ background-color: var(--gp-accent) !important; border-color: var(--gp-accent) !important; }}
[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {{ border-color: var(--gp-accent) !important; }}
[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child[aria-checked="true"] {{ background-color: var(--gp-accent) !important; }}
[data-testid="stProgress"] > div > div > div > div {{ background: var(--gp-btn-grad) !important; box-shadow: 0 0 10px var(--gp-accent) !important; }}
[data-testid="stExpander"] {{ background: rgba(255,255,255,0.5) !important; backdrop-filter: blur(15px) !important; border: 1px solid var(--gp-border) !important; border-radius: var(--gp-radius) !important; box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important; }}
[data-testid="stExpander"] details > summary {{ font-weight: 700 !important; color: var(--gp-text) !important; background: transparent !important; }}
[data-testid="stSpinner"] > div > div {{ border-top-color: var(--gp-accent) !important; border-right-color: var(--gp-accent2) !important; box-shadow: 0 0 15px var(--gp-accent) !important; }}

/* 🚀 HEADER & SIDEBAR ARROW FIX (BULLETPROOF) */
header[data-testid="stHeader"] {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}}
[data-testid="stToolbar"] {{
    display: flex !important;
    visibility: visible !important;
}}
[data-testid="stDeployButton"], #MainMenu, footer {{
    display: none !important;
    visibility: hidden !important;
}}
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[kind="header"] {{
    display: flex !important;
    visibility: visible !important;
    position: fixed !important;
    top: 15px !important;
    left: 15px !important;
    z-index: 9999999 !important;
    background: white !important;
    border-radius: 50% !important;
    padding: 8px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
}}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg,
button[kind="header"] svg {{
    fill: #0F172A !important;
    color: #0F172A !important;
    width: 24px !important;
    height: 24px !important;
}}

/* 🚀 DESKTOP FULL WIDTH FIX */
@media (min-width: 1024px) {{
    .main .block-container {{
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }}
    [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {{
        max-width: 100% !important;
    }}
}}

/* Floating Alert */
div[data-testid="stAlert"] {{ position: fixed !important; top: 70px !important; right: 20px !important; z-index: 99999 !important; width: 350px !important; background: rgba(255, 255, 255, 0.85) !important; backdrop-filter: blur(20px) !important; -webkit-backdrop-filter: blur(20px) !important; border: 1px solid rgba(255,255,255,0.9) !important; border-radius: 16px !important; box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important; animation: fadeInPage 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards !important; color: var(--gp-text) !important; }}
div[data-testid="stAlert"] * {{ color: var(--gp-text) !important; }}

/* Cards & Dark Boxes */
div[style*="background:#1E293B"], div[style*="background: #1E293B"], div[style*="background:#0F172A"], div[style*="background: #0F172A"], div[style*="background-color:#0F172A"], div[style*="background-color: #0F172A"], div[style*="background-color:#1E293B"], div[style*="background-color: #1E293B"] {{ background: rgba(255, 255, 255, 0.7) !important; border: 1px solid var(--gp-border) !important; }}
div[style*="background:#1E293B"] *, div[style*="background: #1E293B"] *, div[style*="background:#0F172A"] *, div[style*="background: #0F172A"] *, div[style*="background-color:#0F172A"] *, div[style*="background-color: #0F172A"] *, div[style*="background-color:#1E293B"] *, div[style*="background-color: #1E293B"] * {{ color: var(--gp-text) !important; }}
.metric-card, [data-testid="metric-container"], .pro-card, [data-testid="stExpander"], .dash-hero, .dash-kpi {{ background: linear-gradient(135deg, rgba(255,255,255,0.7), rgba(255,255,255,0.3)) !important; border: 1px solid rgba(255,255,255,0.9) !important; border-radius: var(--gp-radius) !important; backdrop-filter: blur(20px) saturate(1.5) !important; -webkit-backdrop-filter: blur(20px) saturate(1.5) !important; box-shadow: 0 10px 30px rgba(0,0,0,0.05), inset 0 0 0 1px rgba(255,255,255,0.5) !important; transition: all 0.4s ease !important; z-index: 2; position: relative; }}
.metric-card:hover, [data-testid="metric-container"]:hover, .pro-card:hover {{ box-shadow: 0 15px 40px rgba(0,0,0,0.1), inset 0 0 0 1px rgba(255,255,255,0.8) !important; transform: translateY(-5px) rotateX(2deg) scale(1.02) !important; }}
hr {{ border-color: var(--gp-border) !important; }}
</style>
{particle_html}
<div class="theme-marker theme-design-{number}" aria-hidden="true"></div>
"""

def apply_theme(key: str = None, auto_rotate: bool = False):
    key = normalize_theme_key(key or (get_daily_theme() if auto_rotate else current_theme()))
    st.session_state["current_theme"] = key
    st.session_state["_gympro_theme"] = key
    st.markdown(build_css(key), unsafe_allow_html=True)
    return key