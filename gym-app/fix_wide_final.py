import re

# 1. themes.py se kharab code hatao
path_themes = "themes.py"
with open(path_themes, "r") as f:
    themes_content = f.read()

# Wo block dhoondein jo pichli baar ghalti se dala tha
pattern = re.compile(r'/\* 🚀 FIX WIDE SCREEN LAYOUT.*?\}\s*\}\s*\}', re.DOTALL)
# Agar regex se na hate to direct text replace
bad_block = """/* 🚀 FIX WIDE SCREEN LAYOUT (Desktop/Laptop) */
@media (min-width: 1024px) {
    .main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
    [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {
        max-width: 100% !important;
    }
}"""

themes_content = themes_content.replace(bad_block, "")
themes_content = pattern.sub("", themes_content)

with open(path_themes, "w") as f:
    f.write(themes_content)
print("✅ themes.py fixed (Syntax Error removed)!")

# 2. styles.py mein wide screen fix dalein (yahan brackets safe hain)
path_styles = "styles.py"
with open(path_styles, "r") as f:
    styles_content = f.read()

wide_css = """
/* Desktop Full Width Fix */
@media (min-width: 1024px) {
    .main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
}
"""

if "Desktop Full Width Fix" not in styles_content:
    # GLOBAL_CSS ke andar </style> se pehle dalein
    styles_content = styles_content.replace("</style>", wide_css + "\n</style>", 1)
    with open(path_styles, "w") as f:
        f.write(styles_content)
    print("✅ styles.py updated with Full Width Fix!")
else:
    print("ℹ️ Wide screen fix already in styles.py")
