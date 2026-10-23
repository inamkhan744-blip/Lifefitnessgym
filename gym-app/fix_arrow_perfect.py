import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purana kharab block delete karein
content = re.sub(r'/\* 🚀 ULTIMATE HEADER & ARROW FIX \*/.*?</style>', '</style>', content, flags=re.DOTALL)

# 2. Naya PERFECT CSS (Double brackets ke sath)
new_css = """/* 🚀 ULTIMATE HEADER & ARROW FIX */
header[data-testid="stHeader"] {{
    display: block !important;
    visibility: visible !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    height: 60px !important;
    z-index: 99999 !important;
}}
[data-testid="stToolbar"] {{ display: none !important; }}
#MainMenu {{ visibility: hidden !important; }}
footer {{ visibility: hidden !important; }}
[data-testid="stSidebarCollapsedControl"], 
[data-testid="collapsedControl"],
button[kind="header"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 15px !important;
    left: 15px !important;
    z-index: 999999 !important;
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 50% !important;
    padding: 10px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
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
"""

# 3. File ke sabse aakhir wale </style> se pehle dalein
parts = content.rsplit("</style>", 1)
if len(parts) == 2:
    content = parts[0] + new_css + "</style>" + parts[1]
    with open(path, "w") as f:
        f.write(content)
    print("✅ Syntax error fixed! Arrow button restored perfectly.")
else:
    print("❌ Could not find </style> to inject.")
