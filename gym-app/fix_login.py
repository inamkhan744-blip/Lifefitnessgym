import os

path = "auth.py"
if not os.path.exists(path):
    print("❌ auth.py nahi mili")
    exit()

with open(path, "r") as f:
    content = f.read()

css_fix = """
    # 🔥 LOGIN PAGE RESPONSIVE FIX
    st.markdown(\"\"\"
    <style>
    /* Center the login form and limit width */
    .main .block-container {
        max-width: 450px !important;
        margin: 0 auto !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-top: 4rem !important;
    }
    
    /* Fix input fields */
    div[data-testid="stTextInput"] {
        width: 100% !important;
    }
    div[data-testid="stTextInput"] input {
        width: 100% !important;
        box-sizing: border-box !important;
        padding: 12px 15px !important;
        border-radius: 10px !important;
    }
    
    /* Fix Button width */
    .stButton > button {
        width: 100% !important;
        box-sizing: border-box !important;
        padding: 14px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        margin-top: 10px !important;
    }
    
    /* Hide default Streamlit header/footer for cleaner login */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    \"\"\", unsafe_allow_html=True)
"""

if "def login_page():" in content:
    if "LOGIN PAGE RESPONSIVE FIX" not in content:
        content = content.replace("def login_page():", "def login_page():\n" + css_fix)
        with open(path, "w") as f:
            f.write(content)
        print("✅ Login page responsive layout fixed!")
    else:
        print("ℹ️ Login page already fixed.")
else:
    print("❌ Could not find login_page function in auth.py")
