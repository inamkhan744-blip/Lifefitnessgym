path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Purana block jo floating alerts bana raha tha
old_block = """    /* 🚀 iOS FLOATING TOASTS (For Alerts) */
    div[data-testid="stAlert"] {{
        position: fixed !important;
        top: 20px !important;
        right: 20px !important;
        z-index: 99999 !important;
        width: 320px !important;
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255,255,255,0.9) !important;
        border-radius: 16px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.15) !important;
        animation: fadeInPage 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards !important;
        color: var(--gp-text) !important;
    }}
    div[data-testid="stAlert"] * {{ color: var(--gp-text) !important; }}"""

# Naya block jo alerts ko normal jagah par rakhega
new_block = """    /* Normal Alerts (Fixed to stay in flow) */
    div[data-testid="stAlert"] {{
        position: relative !important;
        top: auto !important;
        right: auto !important;
        width: auto !important;
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid var(--gp-border) !important;
        border-radius: var(--gp-radius) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        color: var(--gp-text) !important;
    }}
    div[data-testid="stAlert"] * {{ color: var(--gp-text) !important; }}"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Fixed the floating alert bug! Alerts will now stay in their proper place.")
else:
    # Fallback: Agar exact match na mile to line by line dhoond kar replace karein
    import re
    content = re.sub(r'position: fixed !important;\s*top: 20px !important;\s*right: 20px !important;\s*z-index: 99999 !important;', 'position: relative !important;', content)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Applied fallback fix for floating alerts!")
