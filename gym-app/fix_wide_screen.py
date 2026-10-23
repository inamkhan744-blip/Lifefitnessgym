path = "themes.py"
with open(path, "r") as f:
    content = f.read()

wide_fix_css = """
/* 🚀 FIX WIDE SCREEN LAYOUT (Desktop/Laptop) */
@media (min-width: 1024px) {
    .main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
    /* Streamlit ke default containers ko bhi expand karein */
    [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {
        max-width: 100% !important;
    }
}
"""

if "FIX WIDE SCREEN LAYOUT" not in content:
    # CSS ko file ke aakhir wale </style> se pehle dalein
    parts = content.rsplit("</style>", 1)
    if len(parts) == 2:
        content = parts[0] + wide_fix_css + "</style>" + parts[1]
        with open(path, "w") as f:
            f.write(content)
        print("✅ Wide screen layout fixed! App will now stretch on laptops.")
    else:
        print("❌ Could not find </style> to inject.")
else:
    print("ℹ️ Wide screen fix already applied.")
