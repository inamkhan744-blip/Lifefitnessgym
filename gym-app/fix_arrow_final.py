import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Purana kharab block hatao
pattern = re.compile(r'/\* 🚀 TRANSPARENT HEADER & FLOATING ARROW \*/.*?(?=/\* Cards & Dark Boxes)', re.DOTALL)
content = pattern.sub("", content)

# Naya perfect CSS
new_css = """/* 🚀 HEADER & SIDEBAR ARROW FIX */
header[data-testid="stHeader"] {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border-bottom: none !important;
    z-index: 99999 !important;
}}
[data-testid="stToolbar"] {{ display: none !important; }}
#MainMenu {{ display: none !important; visibility: hidden !important; }}
footer {{ display: none !important; visibility: hidden !important; }}

/* Force Sidebar Open/Close Button to show */
[data-testid="stSidebarCollapsedControl"], 
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}}

/* Make the arrow button look like a nice floating circle */
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {{
    background: rgba(255, 255, 255, 0.9) !important;
    border-radius: 50% !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    margin: 10px !important;
}}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {{
    color: #0F172A !important;
    fill: #0F172A !important;
}}

"""

if "HEADER & SIDEBAR ARROW FIX" not in content:
    content = content.replace("</style>\n{particle_html}", new_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Arrow button fixed! No height:0 this time.")
else:
    print("ℹ️ Fix already applied.")
