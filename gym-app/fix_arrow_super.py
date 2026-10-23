import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purane saare header hide karne wale rules delete karein
content = re.sub(r'header\[data-testid="stHeader"\].*?\}', '', content, flags=re.DOTALL)
content = re.sub(r'/\* 🚀 HEADER & SIDEBAR ARROW FIX \*/.*?</style>', '</style>', content, flags=re.DOTALL)

# 2. Naya Super Fix CSS (Bilkul end mein dalein taake sabko override kare)
super_fix_css = """
/* 🚀 ULTIMATE HEADER & ARROW FIX */
header[data-testid="stHeader"] {
    display: block !important;
    visibility: visible !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    height: 60px !important;
    z-index: 99999 !important;
}

/* Hide deploy button / menu / footer */
[data-testid="stToolbar"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* FORCE SHOW THE ARROW BUTTON */
[data-testid="stSidebarCollapsedControl"], 
[data-testid="collapsedControl"],
button[kind="header"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 15px !important;
    left: 15px !important;
    z-index: 999999 !important;
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 50% !important;
    padding: 10px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
}

/* Arrow ka color dark karein */
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg,
button[kind="header"] svg {
    fill: #0F172A !important;
    color: #0F172A !important;
    width: 24px !important;
    height: 24px !important;
}
</style>
"""

# 3. Isay file ke aakhir mein </style> se pehle dalein
if "ULTIMATE HEADER & ARROW FIX" not in content:
    # Replace the last </style> with our new CSS + </style>
    content = content[::-1].replace(">elyts/<"[::-1], super_fix_css[::-1], 1)[::-1]
    with open(path, "w") as f:
        f.write(content)
    print("✅ Arrow button forced to show! Header is now transparent.")
else:
    print("ℹ️ Fix already applied.")
