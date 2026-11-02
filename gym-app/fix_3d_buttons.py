import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Black & White theme ke button ko dark karein taake white text nazar aaye
content = content.replace('"btn_gradient": "linear-gradient(135deg, #F3F4F6, #9CA3AF)"', '"btn_gradient": "linear-gradient(135deg, #4B5563, #1F2937)"')

# 2. Purane flat button CSS ko hata kar naya 3D CSS lagayein (Main Area)
old_main_btn = '''/* Solid Buttons (No Glass) */
.stButton > button {{ 
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important; 
    border: 1px solid rgba(255,255,255,0.2) !important; 
    border-radius: var(--gp-radius) !important; 
    font-weight: 800 !important; 
    padding: 12px 24px !important; 
    box-shadow: var(--gp-btn-shadow) !important; 
    transition: all 0.3s ease !important;
}}
.stButton > button *, .stButton > button span, .stButton > button p {{ 
    color: #FFFFFF !important; 
    font-weight: 800 !important; 
    font-size: 15px !important;
}}
.stButton > button:hover {{ 
    box-shadow: var(--gp-btn-hover-shadow) !important; 
    transform: translateY(-3px) !important; 
}}'''

new_main_btn = '''/* TRUE 3D POP-OUT BUTTONS (Main Area) */
.stButton > button {{ 
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important; 
    border: 1px solid rgba(255,255,255,0.4) !important; 
    border-radius: var(--gp-radius) !important; 
    font-weight: 800 !important; 
    padding: 12px 24px !important; 
    
    /* 3D Magic: Hard edge + Soft shadow + Inner highlights */
    box-shadow: 
        0 6px 0 rgba(0,0,0,0.2), 
        0 10px 20px rgba(0,0,0,0.2), 
        inset 0 2px 3px rgba(255,255,255,0.5), 
        inset 0 -4px 8px rgba(0,0,0,0.2) !important; 
        
    transform: perspective(500px) rotateX(2deg) translateY(-2px) !important;
    transition: all 0.2s ease !important;
}}
.stButton > button *, .stButton > button span, .stButton > button p {{ 
    color: #FFFFFF !important; 
    font-weight: 800 !important; 
    font-size: 15px !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5) !important;
}}
.stButton > button:hover {{ 
    transform: perspective(500px) rotateX(0deg) translateY(-4px) !important;
    box-shadow: 
        0 10px 0 rgba(0,0,0,0.2), 
        0 15px 25px rgba(0,0,0,0.3), 
        inset 0 2px 3px rgba(255,255,255,0.6), 
        inset 0 -4px 8px rgba(0,0,0,0.2) !important; 
}}
.stButton > button:active {{ 
    transform: perspective(500px) rotateX(0deg) translateY(4px) !important;
    box-shadow: 
        0 0px 0 rgba(0,0,0,0.2), 
        0 5px 10px rgba(0,0,0,0.1), 
        inset 0 2px 5px rgba(0,0,0,0.3) !important; 
}}'''

content = content.replace(old_main_btn, new_main_btn)

# 3. Sidebar buttons ko bhi 3D banayein
old_sidebar_btn = '''section[data-testid="stSidebar"] .stButton > button, section[data-testid="stSidebar"] .nav-btn button {{ 
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important; 
    border: none !important; 
    font-weight: 700 !important; 
    box-shadow: var(--gp-btn-shadow) !important; 
    transition: all 0.3s ease !important; 
}}
section[data-testid="stSidebar"] .stButton > button:hover, section[data-testid="stSidebar"] .nav-btn button:hover {{ 
    box-shadow: var(--gp-btn-hover-shadow) !important; 
    transform: translateY(-2px) !important; 
}}
section[data-testid="stSidebar"] .nav-btn-active button, section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{ 
    background: var(--gp-btn-grad) !important; 
    box-shadow: var(--gp-btn-shadow) !important; 
    transform: translateY(-2px) !important; 
}}'''

new_sidebar_btn = '''/* TRUE 3D POP-OUT BUTTONS (Sidebar) */
section[data-testid="stSidebar"] .stButton > button, section[data-testid="stSidebar"] .nav-btn button {{ 
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important; 
    border: 1px solid rgba(255,255,255,0.3) !important; 
    font-weight: 800 !important; 
    border-radius: var(--gp-radius) !important;
    
    box-shadow: 
        0 5px 0 rgba(0,0,0,0.2), 
        0 8px 15px rgba(0,0,0,0.15), 
        inset 0 2px 3px rgba(255,255,255,0.4), 
        inset 0 -4px 8px rgba(0,0,0,0.2) !important; 
        
    transform: perspective(500px) rotateX(2deg) translateY(-1px) !important;
    transition: all 0.2s ease !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover, section[data-testid="stSidebar"] .nav-btn button:hover {{ 
    transform: perspective(500px) rotateX(0deg) translateY(-3px) !important;
    box-shadow: 
        0 8px 0 rgba(0,0,0,0.2), 
        0 12px 20px rgba(0,0,0,0.2), 
        inset 0 2px 3px rgba(255,255,255,0.5), 
        inset 0 -4px 8px rgba(0,0,0,0.2) !important; 
}}
section[data-testid="stSidebar"] .stButton > button:active,
section[data-testid="stSidebar"] .nav-btn button:active {{ 
    transform: perspective(500px) rotateX(0deg) translateY(3px) !important;
    box-shadow: 
        0 0px 0 rgba(0,0,0,0.2), 
        0 3px 8px rgba(0,0,0,0.1), 
        inset 0 2px 5px rgba(0,0,0,0.3) !important; 
}}
section[data-testid="stSidebar"] .nav-btn-active button, section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{ 
    background: var(--gp-btn-grad) !important; 
}}'''

content = content.replace(old_sidebar_btn, new_sidebar_btn)

with open(path, "w") as f:
    f.write(content)
print("✅ TRUE 3D Buttons applied successfully!")
