path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Naya aggressive CSS
aggressive_css = """
/* 🚀 ULTIMATE READABILITY & CONTRAST FIX */
/* 1. Base Font Weight Boost */
body, p, span, div, label, li, a, td, th {
    font-weight: 600 !important; /* Sab kuch mota */
}

/* 2. KPI Cards (Jo sabse zyada halke hain) */
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
    font-size: 13px !important;
    font-weight: 900 !important; /* Extra Bold */
    color: #1E293B !important; /* Bilkul dark color */
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-size: 26px !important;
    font-weight: 900 !important; /* Extra Bold */
    color: #0F172A !important;
}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {
    font-weight: 800 !important;
}

/* 3. Sidebar Dark Box Fix (The 'SIGNED IN AS' box) */
section[data-testid="stSidebar"] div[style*="background:#1E293B"],
section[data-testid="stSidebar"] div[style*="background: #1E293B"],
section[data-testid="stSidebar"] div[style*="background-color:#1E293B"],
section[data-testid="stSidebar"] div[style*="background-color: #1E293B"] {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid var(--gp-border) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
}
section[data-testid="stSidebar"] div[style*="background:#1E293B"] *,
section[data-testid="stSidebar"] div[style*="background: #1E293B"] *,
section[data-testid="stSidebar"] div[style*="background-color:#1E293B"] *,
section[data-testid="stSidebar"] div[style*="background-color: #1E293B"] * {
    color: #0F172A !important; /* Text ko dark karein */
    font-weight: 800 !important;
}

/* 4. Sidebar Text Boost */
section[data-testid="stSidebar"] * {
    font-weight: 700 !important;
    color: #0F172A !important;
}

/* 5. Tabs & Buttons */
button[data-baseweb="tab"] *, button[data-baseweb="tab"] {
    font-weight: 800 !important;
    font-size: 15px !important;
}
.stButton > button * {
    font-weight: 800 !important;
    font-size: 15px !important;
}

/* 6. Charts & General Text */
.main p, .main div:not(.stMetricValue) {
    font-weight: 600 !important;
}
"""

# Is CSS ko build_css ke aakhir mein dalein taake sab ko override kar sake
if "ULTIMATE READABILITY & CONTRAST FIX" not in content:
    # Ensure we replace the correct </style> (the last one in the build_css function)
    # There's only one main </style> in the f-string.
    content = content.replace("</style>\n{particle_html}", aggressive_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ BRUTAL FORCE applied! Text is now extra bold and dark.")
else:
    print("ℹ️ Fix is already applied.")
