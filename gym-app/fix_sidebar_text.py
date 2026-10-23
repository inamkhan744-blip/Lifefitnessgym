path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Naya CSS jo sidebar ke box aur text ko fix karega
sidebar_fix_css = """
/* 🔥 FORCE SIDEBAR TEXT & BOX FIX */
section[data-testid="stSidebar"] * {
    font-weight: 600 !important; /* Sidebar ki writing ko mota karein */
}

/* Jo dark box "SIGNED IN AS" wala hai usay white karein */
section[data-testid="stSidebar"] div[style*="background:#1E293B"],
section[data-testid="stSidebar"] div[style*="background: #1E293B"],
section[data-testid="stSidebar"] div[style*="background-color:#1E293B"],
section[data-testid="stSidebar"] div[style*="background-color: #1E293B"],
section[data-testid="stSidebar"] div[style*="background:linear-gradient"],
section[data-testid="stSidebar"] div[style*="background: linear-gradient"] {
    background: rgba(255, 255, 255, 0.8) !important;
    border: 1px solid var(--gp-border) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
}

/* Us box ke andar ka text dark karein */
section[data-testid="stSidebar"] div[style*="background:#1E293B"] *,
section[data-testid="stSidebar"] div[style*="background: #1E293B"] *,
section[data-testid="stSidebar"] div[style*="background-color:#1E293B"] *,
section[data-testid="stSidebar"] div[style*="background-color: #1E293B"] *,
section[data-testid="stSidebar"] div[style*="background:linear-gradient"] *,
section[data-testid="stSidebar"] div[style*="background: linear-gradient"] * {
    color: var(--gp-text) !important;
    font-weight: 800 !important; /* Box ke andar ka text aur zyada mota */
}

/* Selectbox (Dropdown) ki writing moti karein */
section[data-testid="stSidebar"] div[data-baseweb="select"] div[role="combobox"] span {
    font-weight: 700 !important;
}
"""

# Is CSS ko file mein daalein
if "FORCE SIDEBAR TEXT & BOX FIX" not in content:
    content = content.replace("</style>\n<div class=\"theme-marker", sidebar_fix_css + "\n</style>\n<div class=\"theme-marker")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Sidebar text and dark box fixed!")
else:
    print("ℹ️ Sidebar fix already applied.")
