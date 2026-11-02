import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purane saare kharab header blocks dhoondein aur nikal dein
# Hum 'header[data-testid="stHeader"]' se shuru hone wale saare blocks hata denge
pattern = re.compile(r'header\[data-testid="stHeader"\].*?(?=/\* Floating Alert|/\* Cards & Dark Boxes|/\* Inputs|</style>)', re.DOTALL)
content = pattern.sub("", content)

# 2. Naya Perfect CSS
new_header_css = """/* 🚀 TRANSPARENT HEADER & PERFECT SIDEBAR ARROW */
header[data-testid="stHeader"] {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    z-index: 99999 !important;
}}

/* Sidebar Control Button - Force Show */
[data-testid="stSidebarCollapsedControl"], 
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    background: #FFFFFF !important;
    border-radius: 50% !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    margin-top: 15px !important;
    margin-left: 15px !important;
    padding: 8px !important;
}}

[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {{
    color: #0F172A !important;
    fill: #0F172A !important;
    width: 24px !important;
    height: 24px !important;
}}

/* Hide Toolbar and Menu */
[data-testid="stToolbar"] {{ display: none !important; }}
#MainMenu {{ display: none !important; visibility: hidden !important; }}
footer {{ display: none !important; visibility: hidden !important; }}

"""

if "TRANSPARENT HEADER & PERFECT SIDEBAR ARROW" not in content:
    content = content.replace("</style>\n{particle_html}", new_header_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Arrow button forced to show! Header is now transparent.")
else:
    print("ℹ️ Fix already applied.")
