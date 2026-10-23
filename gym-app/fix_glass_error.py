import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purana kharab block dhoondein aur nikal dein
pattern = re.compile(r'/\* 🚀 GLASSMORPHISM & 3D SIDEBAR BUTTONS \*/.*?font-size: 15px !important;\s*\}', re.DOTALL)
content = pattern.sub("", content)

# 2. Naya sahi syntax (double brackets) wala code
correct_glass_css = """
/* 🚀 GLASSMORPHISM & 3D SIDEBAR BUTTONS */
section[data-testid="stSidebar"] .stButton > button, 
section[data-testid="stSidebar"] .nav-btn button {{
    background: linear-gradient(135deg, rgba(255,255,255,0.6), rgba(255,255,255,0.1)) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255,255,255,0.8) !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08), inset 0 2px 2px rgba(255,255,255,0.9), inset 0 -4px 6px rgba(0,0,0,0.1) !important;
    transform: perspective(500px) rotateX(2deg) translateY(-2px) !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    color: #1E293B !important;
    padding: 14px 20px !important;
    border-radius: 12px !important;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}}

section[data-testid="stSidebar"] .nav-btn-active button {{
    background: var(--gp-btn-grad) !important;
    border: 1px solid rgba(255,255,255,0.5) !important;
    box-shadow: 0 12px 25px var(--gp-accent)66, inset 0 3px 2px rgba(255,255,255,0.4), inset 0 -5px 8px rgba(0,0,0,0.3) !important;
    transform: perspective(500px) rotateX(0deg) translateY(-3px) scale(1.02) !important;
}}

section[data-testid="stSidebar"] .nav-btn-active button * {{
    color: #FFFFFF !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
}}

section[data-testid="stSidebar"] .stButton > button:hover, 
section[data-testid="stSidebar"] .nav-btn button:hover {{
    transform: perspective(500px) rotateX(0deg) translateY(-5px) scale(1.02) !important;
    box-shadow: 0 15px 30px rgba(0,0,0,0.15), inset 0 2px 2px rgba(255,255,255,1), inset 0 -4px 6px rgba(0,0,0,0.1) !important;
}}

section[data-testid="stSidebar"] .stButton > button:active,
section[data-testid="stSidebar"] .nav-btn button:active {{
    transform: perspective(500px) rotateX(0deg) translateY(4px) !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1), inset 0 2px 5px rgba(0,0,0,0.2) !important;
}}

section[data-testid="stSidebar"] .stButton > button *, 
section[data-testid="stSidebar"] .nav-btn button * {{
    font-weight: 800 !important;
    font-size: 15px !important;
}}
"""

if "GLASSMORPHISM & 3D SIDEBAR BUTTONS" not in content:
    content = content.replace("</style>\n{particle_html}", correct_glass_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Fixed the f-string syntax error! Glass and 3D buttons are back.")
else:
    print("ℹ️ Fix is already applied.")
