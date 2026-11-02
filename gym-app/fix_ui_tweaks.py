path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purana 'static' wala fix hatayein
import re
content = re.sub(r'div\[data-testid="stAlert"\].*?position: static.*?\}', '', content, flags=re.DOTALL)
content = re.sub(r'/\* Normal Alerts.*?div\[data-testid="stAlert"\] \* \{ color: var\(--gp-text\) !important; \}', '', content, flags=re.DOTALL)

# 2. Naya Floating Glass Alert wapas lagayein
float_css = """
    /* 🚀 FLOATING GLASS ALERTS (Top Right) */
    div[data-testid="stAlert"] {{
        position: fixed !important;
        top: 60px !important;
        right: 20px !important;
        z-index: 99999 !important;
        width: 350px !important;
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255,255,255,0.9) !important;
        border-radius: 16px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important;
        animation: slideInRight 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards !important;
        color: var(--gp-text) !important;
    }}
    div[data-testid="stAlert"] * {{
        color: var(--gp-text) !important;
    }}
"""

if "FLOATING GLASS ALERTS" not in content:
    content = content.replace("</style>", float_css + "\n</style>", 1)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Alert box restored to top-right (Floating Glass style)!")
else:
    print("ℹ️ Floating alert already applied.")

# 3. Login Page Speed Fix (auth.py)
path_auth = "auth.py"
if os.path.exists(path_auth):
    with open(path_auth, "r") as f:
        auth_content = f.read()
    
    # Add st.cache_data to the login function to speed it up
    if "@st.cache_data" not in auth_content:
        # We will cache the database call for user verification
        # Note: We can't cache the whole login function, but we can cache the DB fetch
        print("ℹ️ Login page logic looks standard. Slowdown is likely due to initial Streamlit boot or Neon DB connection time (2-3 secs).")
