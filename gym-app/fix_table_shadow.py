import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Purana table block dhoondein aur nikal dein
pattern = re.compile(r'/\* 🚀 TRUE 3D TABLES \(Mobile Safe\) \*/.*?tr:hover td \{[^\}]*\}', re.DOTALL)
content = pattern.sub("", content)

# Naya SUPER 3D Table CSS (Double brackets ke sath)
new_table_css = """/* 🚀 SUPER 3D TABLES (Force Shadow) */
[data-testid="stDataFrame"], table {{
    width: 100% !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    border-radius: var(--gp-radius) !important;
    background: rgba(255,255,255,0.98) !important;
    border: 2px solid rgba(0,0,0,0.1) !important;
    
    /* Deep 3D Shadow */
    box-shadow: 
        0 12px 0px rgba(0,0,0,0.15), 
        0 20px 30px rgba(0,0,0,0.2) !important; 
        
    transform: translateY(-6px) !important;
    transition: all 0.2s ease !important;
    margin-bottom: 30px !important;
}}

/* Hover Effect */
[data-testid="stDataFrame"]:hover, table:hover {{
    transform: translateY(-8px) !important;
    box-shadow: 
        0 14px 0px rgba(0,0,0,0.15), 
        0 25px 35px rgba(0,0,0,0.25) !important;
}}

/* 🔥 FIX: Streamlit ke containers ko bolo ke shadow ko cut na karein */
.main .block-container, [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {{
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

if "SUPER 3D TABLES (Force Shadow)" not in content:
    # Isay </style> se pehle dalein
    content = content.replace("</style>\n{particle_html}", new_table_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Table Shadow FIXED! Containers will no longer clip the 3D shadow.")
else:
    print("ℹ️ Fix already applied.")
