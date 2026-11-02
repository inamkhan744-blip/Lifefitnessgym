import re

path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# 1. Purana Table CSS block hatao
# Hum 'table {' se lekar 'tr:hover td {' tak ka block replace karenge
pattern = re.compile(r'table \{.*?tr:hover td \{[^\}]*\}', re.DOTALL)

# 2. Naya 3D Table CSS (Buttons jaisa shadow)
new_table_css = """/* 🚀 3D TABLES (Mobile Safe) */
table, [data-testid="stDataFrame"] {
    width: 100%;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    border-radius: var(--gp-radius) !important;
    background: rgba(255,255,255,0.95) !important;
    border: 1px solid rgba(255,255,255,0.6) !important;
    
    /* The Magic 3D Shadow (Same as Buttons) */
    box-shadow: 
        0 6px 0 rgba(0,0,0,0.15), 
        0 10px 20px rgba(0,0,0,0.1) !important; 
        
    transform: translateY(-3px) !important;
    transition: all 0.2s ease !important;
    overflow: hidden !important;
    margin-bottom: 20px !important;
}

/* Hover effect for Tables */
table:hover, [data-testid="stDataFrame"]:hover {
    transform: translateY(-5px) !important;
    box-shadow: 
        0 8px 0 rgba(0,0,0,0.15), 
        0 15px 30px rgba(0,0,0,0.15) !important;
}

/* Table Headers */
th {
    background: var(--gp-accent) !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    padding: 14px 15px !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    border-bottom: 2px solid rgba(0,0,0,0.1) !important;
}

/* Table Cells */
td {
    padding: 12px 15px !important;
    border-bottom: 1px solid rgba(0,0,0,0.05) !important;
    color: #0F172A !important; /* Force dark text for readability */
    font-weight: 600 !important;
}

/* Zebra Striping & Hover */
tr:nth-child(even) td {
    background: rgba(0,0,0,0.02) !important;
}
tr:hover td {
    background: rgba(255,255,255,1) !important;
    box-shadow: inset 0 0 20px var(--gp-accent)22 !important;
}"""

if pattern.search(content):
    content = pattern.sub(new_table_css, content)
    with open(path, "w") as f:
        f.write(content)
    print("✅ 3D Shadows applied to Tables successfully!")
else:
    print("❌ Could not find the table CSS block to replace.")
