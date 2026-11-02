import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purana kharab block (single brackets wala) dhoondein aur nikal dein
pattern = re.compile(r'/\* 🚀 TRUE 3D BUTTONS \(Mobile Safe\) \*/.*?background: var\(--gp-btn-grad\) !important;\s*\}', re.DOTALL)
content = pattern.sub("", content)

# 2. Naya sahi syntax (double brackets) wala code
correct_3d_css = """
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
"""

# 3. Isay wapas </style> ke upar daalein
if "TRUE 3D BUTTONS (Mobile Safe)" not in content:
    content = content.replace("</style>\n{particle_html}", correct_3d_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Syntax error fixed! True 3D buttons restored.")
else:
    print("ℹ️ Fix is already applied.")
