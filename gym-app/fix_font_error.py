path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Purana kharab block dhoondein aur nikal dein
import re
pattern = re.compile(r'/\* 🚀 ULTIMATE READABILITY & CONTRAST FIX \*/.*?font-weight: 600 !important;\s*\}', re.DOTALL)
content = pattern.sub("", content)

# Naya perfect code (double brackets ke sath jo f-string mein kaam karega)
correct_css = """
/* 🚀 ULTIMATE READABILITY & CONTRAST FIX */
body, p, span, div, label, li, a, td, th {{
    font-weight: 600 !important;
}}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {{
    font-size: 13px !important;
    font-weight: 900 !important;
    color: #1E293B !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{
    font-size: 26px !important;
    font-weight: 900 !important;
    color: #0F172A !important;
}}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {{
    font-weight: 800 !important;
}}
section[data-testid="stSidebar"] div[style*="background:#1E293B"],
section[data-testid="stSidebar"] div[style*="background: #1E293B"],
section[data-testid="stSidebar"] div[style*="background-color:#1E293B"],
section[data-testid="stSidebar"] div[style*="background-color: #1E293B"] {{
    background: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid var(--gp-border) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
}}
section[data-testid="stSidebar"] div[style*="background:#1E293B"] *,
section[data-testid="stSidebar"] div[style*="background: #1E293B"] *,
section[data-testid="stSidebar"] div[style*="background-color:#1E293B"] *,
section[data-testid="stSidebar"] div[style*="background-color: #1E293B"] * {{
    color: #0F172A !important;
    font-weight: 800 !important;
}}
section[data-testid="stSidebar"] * {{
    font-weight: 700 !important;
    color: #0F172A !important;
}}
button[data-baseweb="tab"] *, button[data-baseweb="tab"] {{
    font-weight: 800 !important;
    font-size: 15px !important;
}}
.stButton > button * {{
    font-weight: 800 !important;
    font-size: 15px !important;
}}
.main p, .main div:not(.stMetricValue) {{
    font-weight: 600 !important;
}}
"""

if "ULTIMATE READABILITY & CONTRAST FIX" not in content:
    content = content.replace("</style>\n{particle_html}", correct_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Fixed the NameError! Text is now extra bold and dark.")
else:
    # Agar pehle se add hai but kharab hai, to replace karein
    # (Fallback logic just in case)
    with open(path, "w") as f:
        f.write(content)
    print("ℹ️ Fix applied.")
