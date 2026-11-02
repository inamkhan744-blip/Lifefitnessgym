path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Sabse strong CSS fix
strong_css = """
    /* 🚨 ULTIMATE HEADER REMOVAL */
    header[data-testid="stHeader"] { display: none !important; height: 0 !important; }
    [data-testid="stToolbar"] { display: none !important; height: 0 !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    #MainMenu { display: none !important; visibility: hidden !important; }
    footer { display: none !important; visibility: hidden !important; }
    .stApp > header { display: none !important; }
"""

if "ULTIMATE HEADER REMOVAL" not in content:
    # GLOBAL_CSS ke andar inject karo
    if "</style>" in content:
        # Sirf pehli baar replace karo taake baqi CSS kharab na ho
        content = content.replace("</style>", strong_css + "\n</style>", 1)
        with open(path, "w") as f:
            f.write(content)
        print("✅ Header completely removed with display: none!")
    else:
        print("❌ Could not find style tag in themes.py")
else:
    print("ℹ️ Header fix is already applied.")
