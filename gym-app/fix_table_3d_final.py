import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purana table CSS (jo kaam nahi kar raha) delete karein
pattern = re.compile(r'/\* 🚀 TRUE 3D TABLES \(Mobile Safe\) \*/.*?tr:hover td \{[^\}]*\}', re.DOTALL)
content = pattern.sub("", content)

# 2. Naya EXTREME 3D TABLE CSS (Double brackets ke sath)
new_table_css = """/* 🚀 EXTREME 3D TABLES */
[data-testid="stDataFrame"], .stDataFrame, table {{
    background-color: #FFFFFF !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    border-radius: 16px !important;
    
    /* Mota 3D Shadow (Bilkul buttons jaisa) */
    box-shadow: 
        0 12px 0px rgba(0,0,0,0.15), 
        0 20px 30px rgba(0,0,0,0.1) !important; 
        
    transform: translateY(-6px) !important;
    transition: all 0.2s ease !important;
    margin-bottom: 30px !important;
    overflow: hidden !important;
}}

/* Hover Effect */
[data-testid="stDataFrame"]:hover, .stDataFrame:hover, table:hover {{
    transform: translateY(-8px) !important;
    box-shadow: 
        0 15px 0px rgba(0,0,0,0.15), 
        0 25px 35px rgba(0,0,0,0.15) !important;
}}

/* 🔥 ASAL JUGAAD: Parent containers ko bolo ke shadow ko cut na karein */
.main .block-container, 
[data-testid="stVerticalBlock"], 
[data-testid="stHorizontalBlock"],
[data-testid="stAppViewContainer"] {{
    overflow: visible !important;
}}

/* Table Headers */
th {{
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important;
    font-weight: 800 !important;
    padding: 14px 15px !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
}}

/* Table Cells */
td {{
    padding: 12px 15px !important;
    border-bottom: 1px solid rgba(0,0,0,0.05) !important;
    color: #0F172A !important; 
    font-weight: 600 !important;
}}

/* Zebra Striping */
tr:nth-child(even) td {{
    background: rgba(0,0,0,0.02) !important;
}}

/* Row Hover */
tr:hover td {{
    background: rgba(255,255,255,1) !important;
    box-shadow: inset 0 0 20px var(--gp-accent)22 !important;
}}
"""

if "EXTREME 3D TABLES" not in content:
    # Isay </style> se pehle dalein
    content = content.replace("</style>\n{particle_html}", new_table_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Tables updated to EXTREME 3D! Parent overflow fixed.")
else:
    print("ℹ️ Fix already applied.")
