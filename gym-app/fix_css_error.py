import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purana kharab code delete karein
pattern = re.compile(r'/\* 🚨 ULTIMATE HEADER REMOVAL \*/.*?\.stApp > header \{ display: none !important; \}', re.DOTALL)
content = pattern.sub("", content)

# 2. Naya sahi syntax (double brackets) wala code dalein
escaped_css = """
    /* 🚨 ULTIMATE HEADER REMOVAL (Corrected) */
    header[data-testid="stHeader"] {{ display: none !important; height: 0 !important; }}
    [data-testid="stToolbar"] {{ display: none !important; height: 0 !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    #MainMenu {{ display: none !important; visibility: hidden !important; }}
    footer {{ display: none !important; visibility: hidden !important; }}
    .stApp > header {{ display: none !important; }}
"""

# Isay pehle </style> ke upar dalein
if "ULTIMATE HEADER REMOVAL (Corrected)" not in content:
    content = content.replace("</style>", escaped_css + "\n</style>", 1)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Syntax error fixed! Header will now disappear.")
else:
    print("ℹ️ Fix already applied.")
