path = "themes.py"
with open(path, "r") as f:
    content = f.read()

# CSS jo text ko mota karegi
thick_css = """
/* 🔥 FORCE THICKER TEXT FOR BETTER READABILITY */
.main p, .main span:not(.material-symbols-rounded), .main div, .main label {
    font-weight: 500 !important; /* Base text mota karein */
}
h1, h2, h3, h4, h5, h6, .page-header h1 {
    font-weight: 800 !important; /* Headings aur zyada moti */
}
.stButton > button, .stButton > button span, .stButton > button p {
    font-weight: 800 !important; /* Buttons ki writing bilkul clear */
    letter-spacing: 0.5px !important;
}
button[data-baseweb="tab"] {
    font-weight: 700 !important; /* Tabs ki writing */
}
.stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
    font-weight: 600 !important; /* Input boxes ki writing */
}
div[data-baseweb="select"] div[role="combobox"] {
    font-weight: 600 !important; /* Dropdowns ki writing */
}
/* Settings Page Cards */
.design-option h3 { font-weight: 800 !important; }
.design-option p { font-weight: 500 !important; }
"""

# Is CSS ko build_css function ke andar </style> se pehle daalein
if "FORCE THICKER TEXT" not in content:
    content = content.replace("</style>\n<div class=\"theme-marker", thick_css + "\n</style>\n<div class=\"theme-marker")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Font thickness increased successfully!")
else:
    print("ℹ️ Font thickness is already applied.")
