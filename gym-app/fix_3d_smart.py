import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purane saare table blocks ko delete karein (chahe wo TRUE ho ya EXTREME)
content = re.sub(r'/\*\s*🚀\s*(TRUE|EXTREME)\s*3D\s*TABLES.*?(?=/\*|\Z)', '', content, flags=re.DOTALL)

# 2. Naya Perfect 3D Table CSS (Single brackets mein, baad mein escape karenge)
css = """
/* 🚀 EXTREME 3D TABLES */
[data-testid="stDataFrame"], .stDataFrame, table {
    background-color: #FFFFFF !important;
    border: 1px solid rgba(0,0,0,0.1) !important;
    border-radius: 16px !important;
    box-shadow: 0 12px 0px rgba(0,0,0,0.15), 0 20px 30px rgba(0,0,0,0.1) !important; 
    transform: translateY(-6px) !important;
    transition: all 0.2s ease !important;
    margin-bottom: 30px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"]:hover, .stDataFrame:hover, table:hover {
    transform: translateY(-8px) !important;
    box-shadow: 0 15px 0px rgba(0,0,0,0.15), 0 25px 35px rgba(0,0,0,0.15) !important;
}
.main .block-container, [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], [data-testid="stAppViewContainer"] {
    overflow: visible !important;
}
th {
    background: var(--gp-btn-grad) !important; 
    color: #FFFFFF !important;
    font-weight: 800 !important;
    padding: 14px 15px !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
}
td {
    padding: 12px 15px !important;
    border-bottom: 1px solid rgba(0,0,0,0.05) !important;
    color: #0F172A !important; 
    font-weight: 600 !important;
}
tr:nth-child(even) td {
    background: rgba(0,0,0,0.02) !important;
}
tr:hover td {
    background: rgba(255,255,255,1) !important;
    box-shadow: inset 0 0 20px var(--gp-accent)22 !important;
}
"""

# 3. 🔥 ASAL FIX: Brackets ko double karein taake f-string error na aaye
css_escaped = css.replace("{", "{{").replace("}", "}}")

# 4. Isay file ke aakhir wale </style> se pehle dalein
parts = content.rsplit("</style>", 1)
if len(parts) == 2:
    content = parts[0] + css_escaped + "</style>" + parts[1]
    with open(path, "w") as f:
        f.write(content)
    print("✅ Tables 3D Shadow FIXED! Brackets escaped successfully.")
else:
    print("❌ Error: </style> not found")
