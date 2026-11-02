import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purane header/arrow wale saare blocks dhoondein aur hata dein
pattern = re.compile(r'/\*\s*🚀 TRANSPARENT HEADER.*?(?=/\* Floating Alert|/\* Cards & Dark Boxes|/\* Inputs|</style>)', re.DOTALL)
content = pattern.sub("", content)

# Fallback agar upar wala match na ho
pattern2 = re.compile(r'header\[data-testid="stHeader"\].*?footer \{\{.*?\}\}', re.DOTALL)
content = pattern2.sub("", content)

# 2. Naya Perfect CSS (Double brackets ke sath taake f-string error na aaye)
new_css = """/* 🚀 HEADER & SIDEBAR ARROW FIX (BULLETPROOF) */
header[data-testid="stHeader"] {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}}

/* Toolbar ko visible rakhein taake arrow kaam kare */
[data-testid="stToolbar"] {{
    display: flex !important;
    visibility: visible !important;
}}

/* Sirf Deploy aur Menu ko chhupayein, arrow ko nahi */
[data-testid="stDeployButton"], #MainMenu, footer {{
    display: none !important;
    visibility: hidden !important;
}}

/* Arrow button ko screen par float karwayein (Glass Circle) */
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

/* Arrow ke nishan ka color dark karein */
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg,
button[kind="header"] svg {{
    fill: #0F172A !important;
    color: #0F172A !important;
    width: 24px !important;
    height: 24px !important;
}}

"""

# 3. Naya CSS file ke aakhir wale </style> se pehle dalein
parts = content.rsplit("</style>", 1)
if len(parts) == 2:
    content = parts[0] + new_css + "</style>" + parts[1]
    with open(path, "w") as f:
        f.write(content)
    print("✅ Arrow button restored via Shell perfectly!")
else:
    print("❌ Error: </style> not found in themes.py")
