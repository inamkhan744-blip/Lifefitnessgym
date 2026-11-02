path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Naya CSS jo specifically sidebar buttons ko target karega
button_css = """
/* 🚀 PREMIUM SIDEBAR BUTTONS */
section[data-testid="stSidebar"] .stButton > button, 
section[data-testid="stSidebar"] .nav-btn button, 
section[data-testid="stSidebar"] .nav-btn-active button {{
    font-size: 16px !important; /* Badi writing */
    font-weight: 800 !important; /* Mota text */
    padding: 16px 20px !important; /* Button ko lamba aur choda karein */
    min-height: 55px !important;
    border-radius: 12px !important; /* Thode round corners */
    letter-spacing: 0.5px !important;
    box-shadow: 0 8px 15px rgba(0,0,0,0.1), inset 0 -4px 0 rgba(0,0,0,0.15) !important; /* Deep 3D shadow */
    transform: translateY(-2px) !important; /* Upar utha hua */
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important; /* Text ko center karein */
}}

section[data-testid="stSidebar"] .stButton > button:hover, 
section[data-testid="stSidebar"] .nav-btn button:hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 20px rgba(0,0,0,0.15), inset 0 -2px 0 rgba(0,0,0,0.15) !important;
}}

section[data-testid="stSidebar"] .stButton > button:active,
section[data-testid="stSidebar"] .nav-btn button:active {{
    transform: translateY(4px) !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
}}

/* Button ke andar ka text force white aur bold */
section[data-testid="stSidebar"] .stButton > button *, 
section[data-testid="stSidebar"] .nav-btn button *,
section[data-testid="stSidebar"] .nav-btn-active button * {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.4) !important; /* Text par shadow */
    font-size: 15px !important;
}}
"""

if "PREMIUM SIDEBAR BUTTONS" not in content:
    content = content.replace("</style>\n{particle_html}", button_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Sidebar buttons upgraded to Premium 3D style!")
else:
    print("ℹ️ Buttons are already premium.")
