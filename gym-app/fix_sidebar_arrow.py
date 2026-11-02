import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Purana header hide karne wala block dhoondein
old_header = """/* Hide Header */
header[data-testid="stHeader"] {{ display: none !important; height: 0 !important; }}
[data-testid="stToolbar"] {{ display: none !important; height: 0 !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stStatusWidget"] {{ display: none !important; }}
#MainMenu {{ display: none !important; visibility: hidden !important; }}
footer {{ display: none !important; visibility: hidden !important; }}
.stApp > header {{ display: none !important; }}"""

# Naya block (Transparent header + Floating arrow button)
new_header = """/* 🚀 TRANSPARENT HEADER & FLOATING ARROW */
header[data-testid="stHeader"] {{ 
    background: transparent !important; 
    background-color: transparent !important;
    box-shadow: none !important;
    border-bottom: none !important;
    height: 0 !important;
    overflow: visible !important;
    z-index: 99999 !important;
}}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stStatusWidget"] {{ display: none !important; }}
#MainMenu {{ display: none !important; visibility: hidden !important; }}
footer {{ display: none !important; visibility: hidden !important; }}

/* The side arrow button */
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {{ 
    display: flex !important; 
    visibility: visible !important;
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(10px) !important;
    border-radius: 50% !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    padding: 8px !important;
    margin-top: 15px !important;
    margin-left: 15px !important;
    z-index: 999999 !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    position: fixed !important;
    left: 10px !important;
    top: 10px !important;
}}
[data-testid="stSidebarCollapsedControl"] svg, [data-testid="collapsedControl"] svg {{
    color: #0F172A !important;
    fill: #0F172A !important;
    width: 24px !important;
    height: 24px !important;
}}"""

if old_header in content:
    content = content.replace(old_header, new_header)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Sidebar Arrow Button Restored!")
else:
    print("ℹ️ Pattern not found, trying regex...")
    # Fallback regex if exact match fails
    pattern = re.compile(r'/\* Hide Header \*/.*?\.stApp > header \{\{ display: none !important; \}\}', re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(new_header, content)
        with open(path, "w") as f:
            f.write(content)
        print("✅ Applied regex fix for Sidebar Arrow!")
    else:
        print("❌ Could not find the header block.")
