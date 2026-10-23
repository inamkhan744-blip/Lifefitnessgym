path = "themes.py"
with open(path, "r") as f:
    content = f.read()

header_css = """
    /* 🚨 HIDE STREAMLIT DEFAULT WHITE HEADER BAR */
    header[data-testid="stHeader"] {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border-bottom: none !important;
    }
    /* Hide the 3 dots menu */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    """

if "HIDE STREAMLIT DEFAULT WHITE HEADER BAR" not in content:
    # Add the fix inside the build_css style block
    content = content.replace("</style>\n<div class=\"theme-marker", header_css + "\n</style>\n<div class=\"theme-marker")
    with open(path, "w") as f:
        f.write(content)
    print("✅ White header bar removed successfully!")
else:
    print("ℹ️ Header is already transparent.")
