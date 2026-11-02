import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# Purana kharab block (single brackets wala) dhoondein aur nikal dein
pattern = re.compile(r'/\* 🚀 3D TABLES \(Mobile Safe\) \*/.*?box-shadow: inset 0 0 20px var\(--gp-accent\)22 !important;\s*\}', re.DOTALL)
content = pattern.sub("", content)

# Naya perfect code (Double brackets ke sath)
correct_table_css = """/* 🚀 3D TABLES (Mobile Safe) */
table, [data-testid="stDataFrame"] {{
    width: 100%;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    border-radius: var(--gp-radius) !important;
    background: rgba(255,255,255,0.95) !important;
    border: 1px solid rgba(255,255,255,0.6) !important;
    box-shadow: 
        0 6px 0 rgba(0,0,0,0.15), 
        0 10px 20px rgba(0,0,0,0.1) !important; 
    transform: translateY(-3px) !important;
    transition: all 0.2s ease !important;
    overflow: hidden !important;
    margin-bottom: 20px !important;
}}

table:hover, [data-testid="stDataFrame"]:hover {{
    transform: translateY(-5px) !important;
    box-shadow: 
        0 8px 0 rgba(0,0,0,0.15), 
        0 15px 30px rgba(0,0,0,0.15) !important;
}}

th {{
    background: var(--gp-accent) !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    padding: 14px 15px !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    border-bottom: 2px solid rgba(0,0,0,0.1) !important;
}}

td {{
    padding: 12px 15px !important;
    border-bottom: 1px solid rgba(0,0,0,0.05) !important;
    color: #0F172A !important; 
    font-weight: 600 !important;
}}

tr:nth-child(even) td {{
    background: rgba(0,0,0,0.02) !important;
}}

tr:hover td {{
    background: rgba(255,255,255,1) !important;
    box-shadow: inset 0 0 20px var(--gp-accent)22 !important;
}}
"""

if "3D TABLES (Mobile Safe)" not in content:
    content = content.replace("</style>\n{particle_html}", correct_table_css + "\n</style>\n{particle_html}")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Syntax error fixed! 3D Tables restored perfectly.")
else:
    print("ℹ️ Fix is already applied.")
