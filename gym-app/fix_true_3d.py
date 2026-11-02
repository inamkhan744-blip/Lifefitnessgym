import re

# 1. Fix themes.py for True Mobile 3D
path_themes = "themes.py"
with open(path_themes, "r") as f:
    content = f.read()

# Purana 3D block hatao
content = re.sub(r'/\* TRUE 3D POP-OUT BUTTONS \(Main Area\) \*/.*?(?=/\* Solid Buttons|/\* Tables)', '', content, flags=re.DOTALL)
content = re.sub(r'/\* TRUE 3D POP-OUT BUTTONS \(Sidebar\) \*/.*?(?=/\* Inputs & Selectboxes)', '', content, flags=re.DOTALL)

# Naya Mobile-Safe 3D CSS
new_3d_css = """
/* 🚀 TRUE 3D BUTTONS (Mobile Safe) */
.stButton > button, 
section[data-testid="stSidebar"] .stButton > button, 
section[data-testid="stSidebar"] .nav-btn button {
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important; 
    border: 1px solid rgba(255,255,255,0.2) !important; 
    border-radius: var(--gp-radius) !important; 
    font-weight: 800 !important; 
    padding: 12px 24px !important; 
    
    /* The Magic 3D Shadow */
    box-shadow: 
        0 6px 0 rgba(0,0,0,0.4), /* Hard shadow bottom */
        0 10px 15px rgba(0,0,0,0.2) !important; 
        
    transform: translateY(-3px) !important; /* Lift up */
    transition: all 0.1s ease !important; /* Fast response */
}

.stButton > button *, 
section[data-testid="stSidebar"] .stButton > button *, 
section[data-testid="stSidebar"] .nav-btn button * {
    color: #FFFFFF !important; 
    font-weight: 800 !important; 
    font-size: 15px !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.4) !important;
}

/* Hover State */
.stButton > button:hover, 
section[data-testid="stSidebar"] .stButton > button:hover, 
section[data-testid="stSidebar"] .nav-btn button:hover {
    transform: translateY(-5px) !important;
    box-shadow: 
        0 8px 0 rgba(0,0,0,0.4), 
        0 12px 20px rgba(0,0,0,0.3) !important;
}

/* Click/Press State (Sach mein dhasna) */
.stButton > button:active, 
section[data-testid="stSidebar"] .stButton > button:active, 
section[data-testid="stSidebar"] .nav-btn button:active {
    transform: translateY(4px) !important; /* Push down */
    box-shadow: 
        0 0px 0 rgba(0,0,0,0.4), /* Shadow gone */
        0 2px 5px rgba(0,0,0,0.2) !important;
}

/* Active Menu item */
section[data-testid="stSidebar"] .nav-btn-active button {
    background: var(--gp-btn-grad) !important;
}
"""

if "TRUE 3D BUTTONS (Mobile Safe)" not in content:
    # Isay </style> se pehle dalein
    content = content.replace("</style>\n{particle_html}", new_3d_css + "\n</style>\n{particle_html}")
    with open(path_themes, "w") as f:
        f.write(content)
    print("✅ themes.py updated with True Mobile 3D!")


# 2. Fix settings.py to make Preview Buttons 3D
path_settings = "gym_pages/settings.py"
with open(path_settings, "r") as f:
    settings_content = f.read()

old_preview_btn = '<div style="background: {spec[\'btn_gradient\']}; color: #FFF; text-align: center; border-radius: 4px; padding: 4px; font-size: 10px; font-weight: bold; box-shadow: {spec[\'btn_shadow\']};">'

new_preview_btn = '<div style="background: {spec[\'btn_gradient\']}; color: #FFF; text-align: center; border-radius: 6px; padding: 6px; font-size: 10px; font-weight: bold; box-shadow: 0 3px 0 rgba(0,0,0,0.3); transform: translateY(-1px); margin-bottom: 4px; text-shadow: 0 1px 2px rgba(0,0,0,0.4);">'

if old_preview_btn in settings_content:
    settings_content = settings_content.replace(old_preview_btn, new_preview_btn)
    with open(path_settings, "w") as f:
        f.write(settings_content)
    print("✅ settings.py preview buttons updated to 3D!")
else:
    print("ℹ️ Preview button pattern not found, but main app is fixed.")
