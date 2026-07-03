"""
GymPro Theme System
-------------------
6 sober 3D themes.  Admin manually select kar sakta hai ya daily auto-rotate.
"""
from datetime import date

THEMES: dict[str, dict] = {
    "dark_slate": {
        "name":        "Dark Slate",
        "emoji":       "🪨",
        "bg":          "#0F172A",
        "sidebar_bg":  "#080E1C",
        "card_bg":     "#1E293B",
        "border":      "#2D3D53",
        "primary":     "#7C3AED",
        "primary_dim": "#3B1B8C22",
        "text":        "#E2E8F0",
        "text_muted":  "#94A3B8",
        "text_dim":    "#475569",
        "shadow":      "rgba(124,58,237,0.15)",
    },
    "carbon": {
        "name":        "Carbon",
        "emoji":       "⚫",
        "bg":          "#0C0C0C",
        "sidebar_bg":  "#060606",
        "card_bg":     "#161616",
        "border":      "#262626",
        "primary":     "#22C55E",
        "primary_dim": "#14532D22",
        "text":        "#E5E5E5",
        "text_muted":  "#A3A3A3",
        "text_dim":    "#525252",
        "shadow":      "rgba(34,197,94,0.12)",
    },
    "midnight": {
        "name":        "Midnight",
        "emoji":       "🌌",
        "bg":          "#070D1A",
        "sidebar_bg":  "#040810",
        "card_bg":     "#0D1626",
        "border":      "#1E2D45",
        "primary":     "#38BDF8",
        "primary_dim": "#0C4A6E22",
        "text":        "#E0EEFF",
        "text_muted":  "#7DA4CC",
        "text_dim":    "#3D5A7A",
        "shadow":      "rgba(56,189,248,0.12)",
    },
    "graphite": {
        "name":        "Graphite",
        "emoji":       "🟤",
        "bg":          "#111010",
        "sidebar_bg":  "#0A0909",
        "card_bg":     "#1C1A1A",
        "border":      "#2E2B2B",
        "primary":     "#F59E0B",
        "primary_dim": "#78350F22",
        "text":        "#F5F0E8",
        "text_muted":  "#A89880",
        "text_dim":    "#574F44",
        "shadow":      "rgba(245,158,11,0.12)",
    },
    "forest": {
        "name":        "Forest",
        "emoji":       "🌲",
        "bg":          "#071510",
        "sidebar_bg":  "#040D09",
        "card_bg":     "#0D2118",
        "border":      "#1A3D2A",
        "primary":     "#10B981",
        "primary_dim": "#064E3B22",
        "text":        "#E0F5EE",
        "text_muted":  "#6EAD91",
        "text_dim":    "#2D5C43",
        "shadow":      "rgba(16,185,129,0.12)",
    },
    "bordeaux": {
        "name":        "Bordeaux",
        "emoji":       "🍷",
        "bg":          "#0E0710",
        "sidebar_bg":  "#070409",
        "card_bg":     "#18101C",
        "border":      "#301840",
        "primary":     "#C026D3",
        "primary_dim": "#4A044E22",
        "text":        "#F0E8F5",
        "text_muted":  "#B07EC0",
        "text_dim":    "#5C3870",
        "shadow":      "rgba(192,38,211,0.12)",
    },
}

THEME_KEYS  = list(THEMES.keys())
THEME_NAMES = {k: f"{v['emoji']} {v['name']}" for k, v in THEMES.items()}


def get_daily_theme() -> str:
    """Day of year ke hisaab se theme rotate karo."""
    idx = date.today().toordinal() % len(THEME_KEYS)
    return THEME_KEYS[idx]


def build_css(key: str) -> str:
    """Ek theme ka complete CSS return karo — Streamlit elements override karta hai."""
    t = THEMES.get(key, THEMES["dark_slate"])
    p        = t["primary"]
    p_dim    = t["primary_dim"]
    bg       = t["bg"]
    s_bg     = t["sidebar_bg"]
    c_bg     = t["card_bg"]
    border   = t["border"]
    text     = t["text"]
    t_muted  = t["text_muted"]
    t_dim    = t["text_dim"]
    shadow   = t["shadow"]

    return f"""
<style>
/* ── Base layout ─────────────────────────────────────────────── */
.stApp,
.stApp > .main {{
    background-color: {bg} !important;
    color: {text} !important;
}}
.main .block-container {{
    background-color: {bg} !important;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}}

/* ── Sidebar ─────────────────────────────────────────────────── */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {{
    background: {s_bg} !important;
    border-right: 1px solid {border} !important;
}}

/* ── Cards / metric ──────────────────────────────────────────── */
.metric-card {{
    background: linear-gradient(145deg, {c_bg} 0%, {bg} 100%) !important;
    border: 1px solid {border} !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.4rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow:
        0 1px 2px rgba(0,0,0,0.4),
        0 4px 12px {shadow},
        inset 0 1px 0 rgba(255,255,255,0.04),
        inset 0 0 0 1px rgba(255,255,255,0.02) !important;
    transform: perspective(600px) translateZ(0) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}}
.metric-card:hover {{
    transform: perspective(600px) translateZ(6px) translateY(-2px) !important;
    box-shadow:
        0 2px 4px rgba(0,0,0,0.5),
        0 8px 24px {shadow},
        inset 0 1px 0 rgba(255,255,255,0.06) !important;
}}
.metric-card .label {{ color: {t_muted} !important; }}
.metric-card .value {{ color: {text} !important; }}
.metric-card .sub   {{ color: {t_dim} !important; }}

/* ── Streamlit native metric boxes ───────────────────────────── */
[data-testid="metric-container"] {{
    background: linear-gradient(145deg, {c_bg}, {bg}) !important;
    border: 1px solid {border} !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
    box-shadow:
        0 2px 8px rgba(0,0,0,0.35),
        0 4px 16px {shadow},
        inset 0 1px 0 rgba(255,255,255,0.04) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}}
[data-testid="metric-container"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow:
        0 4px 14px rgba(0,0,0,0.45),
        0 6px 20px {shadow} !important;
}}
[data-testid="stMetricValue"]  {{ color: {text} !important; }}
[data-testid="stMetricLabel"]  {{ color: {t_muted} !important; }}
[data-testid="stMetricDelta"]  {{ color: {p} !important; }}

/* ── Buttons ─────────────────────────────────────────────────── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {{
    background: linear-gradient(135deg, {p}, {p}cc) !important;
    border: none !important;
    color: #fff !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px {shadow}, inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: all 0.18s ease !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px {shadow} !important;
}}
.stButton > button[kind="secondary"] {{
    background: {c_bg} !important;
    border: 1px solid {border} !important;
    color: {t_muted} !important;
    border-radius: 10px !important;
}}

/* ── Tabs ────────────────────────────────────────────────────── */
[data-testid="stTabs"] button[role="tab"] {{
    color: {t_muted} !important;
    border-radius: 8px 8px 0 0 !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: {p} !important;
    border-bottom: 2px solid {p} !important;
    background: {p_dim} !important;
}}

/* ── Inputs ──────────────────────────────────────────────────── */
.stTextInput input,
.stSelectbox > div > div,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input {{
    background: {c_bg} !important;
    border: 1px solid {border} !important;
    color: {text} !important;
    border-radius: 10px !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.2) !important;
}}
.stTextInput input:focus,
.stTextArea textarea:focus {{
    border-color: {p} !important;
    box-shadow: 0 0 0 3px {p_dim}, inset 0 2px 4px rgba(0,0,0,0.2) !important;
}}

/* ── Expanders ───────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background: {c_bg} !important;
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}}

/* ── Dividers / hr ───────────────────────────────────────────── */
hr {{ border-color: {border} !important; }}

/* ── Page header ─────────────────────────────────────────────── */
.page-header {{ border-bottom: 1px solid {border} !important; }}
.page-header h1 {{ color: {text} !important; }}
.page-header .sub {{ color: {t_dim} !important; }}

/* ── Table ───────────────────────────────────────────────────── */
.stDataFrame thead th {{
    background: {c_bg} !important;
    color: {p} !important;
    font-weight: 700 !important;
}}
.stDataFrame tbody tr:hover td {{
    background: {p_dim} !important;
}}

/* ── Sidebar nav buttons ─────────────────────────────────────── */
.nav-btn button {{
    background: transparent !important;
    border: none !important;
    color: {t_muted} !important;
    font-size: 0.9rem !important;
    text-align: left !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
}}
.nav-btn button:hover {{
    background: {c_bg} !important;
    color: {text} !important;
}}
.nav-btn-active button {{
    background: {p_dim} !important;
    color: {p} !important;
    font-weight: 700 !important;
    border-left: 3px solid {p} !important;
}}

/* ── Alerts / info boxes ─────────────────────────────────────── */
[data-testid="stAlert"] {{
    background: {c_bg} !important;
    border-radius: 10px !important;
}}

/* ── 3D depth accent line at top of page ─────────────────────── */
.stApp::before {{
    content: "";
    display: block;
    height: 3px;
    background: linear-gradient(90deg, transparent, {p}, {p}88, transparent);
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
}}

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {bg}; }}
::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {p}88; }}
</style>
"""
