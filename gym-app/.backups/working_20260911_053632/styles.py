GLOBAL_CSS = """
<style>
/* ── Layout ─────────────────────────────────────────────────── */
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
section[data-testid="stSidebar"] { background: #0F172A; border-right: 1px solid #1E293B; }

/* ── Metric Cards ────────────────────────────────────────────── */
.metric-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.75rem;
}
.metric-card .label {
    color: #94A3B8;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #E2E8F0;
    line-height: 1;
}
.metric-card .sub {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 0.25rem;
}
.metric-purple .value { color: #A78BFA; }
.metric-green  .value { color: #34D399; }
.metric-red    .value { color: #F87171; }
.metric-blue   .value { color: #60A5FA; }
.metric-amber  .value { color: #FBBF24; }

/* ── Status badges ───────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.badge-green  { background: #064E3B; color: #34D399; }
.badge-red    { background: #450A0A; color: #F87171; }
.badge-amber  { background: #451A03; color: #FBBF24; }
.badge-blue   { background: #0C1A3A; color: #60A5FA; }
.badge-gray   { background: #1E293B; color: #94A3B8; }

/* ── Page header ─────────────────────────────────────────────── */
.page-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom:1px solid var(--gp-border);
}
.page-header .icon { font-size: 1.8rem; }
.page-header h1 {
    font-size: 1.7rem;
    font-weight: 800;
    color: #E2E8F0;
    margin: 0;
}
.page-header .sub {
    color: #64748B;
    font-size: 0.85rem;
}

/* ── Table styles ────────────────────────────────────────────── */
.stDataFrame thead th { background: #1E293B !important; color: #7C3AED !important; font-weight: 700 !important; }
.stDataFrame tbody tr:hover td { background: #1E3A5F22 !important; }

/* ── Sidebar nav button ──────────────────────────────────────── */
.nav-btn button {
    background: transparent !important;
    border: none !important;
    color: #94A3B8 !important;
    font-size: 0.9rem !important;
    text-align: left !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
}
.nav-btn button:hover {
    background: #1E293B !important;
    color: #E2E8F0 !important;
}
.nav-btn-active button {
    background: #3B1B8C !important;
    color: #C4B5FD !important;
    font-weight: 700 !important;
}

/* ── WhatsApp link ───────────────────────────────────────────── */
.wa-link a {
    color: #34D399;
    font-weight: 600;
    text-decoration: none;
}
.wa-link a:hover { text-decoration: underline; }

/* ── Divider ─────────────────────────────────────────────────── */
hr { border-color: #1E293B !important; }

/* ── 🔥 FIX: Expander arrow + hide stray text ───────────────── */
[data-testid="stExpander"] details > summary {
    list-style: none;
    display: flex;
    align-items: center;
    gap: 8px;
}
[data-testid="stExpander"] details > summary::-webkit-details-marker {
    display: none;
}
[data-testid="stExpander"] details > summary::before {
    content: '▶';
    font-size: 0.7rem;
    color: #94A3B8;
    transition: transform 0.2s;
    margin-right: 6px;
}
[data-testid="stExpander"] details[open] > summary::before {
    transform: rotate(90deg);
}

/* ── 🔥 Hide empty elements ──────────────────────────────────── */
.stMarkdown:empty {
    display: none !important;
}
.stMarkdown:has(>:empty) {
    display: none !important;
}
.stMarkdown:has(>:empty:only-child) {
    display: none !important;
}

/* ── ★★★ TOAST NOTIFICATIONS ★★★ ────────────────────────────── */
@keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}
.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 99999;
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 380px;
    width: 100%;
    pointer-events: none;
}
.toast {
    padding: 14px 20px;
    border-radius: 12px;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    animation: slideInRight 0.4s ease-out forwards;
    display: flex;
    align-items: center;
    gap: 12px;
    pointer-events: auto;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
}
.toast-success {
    background: linear-gradient(135deg, #065F46, #047857);
    border-left: 4px solid #34D399;
}
.toast-error {
    background: linear-gradient(135deg, #7F1D1D, #991B1B);
    border-left: 4px solid #F87171;
}
.toast-warning {
    background: linear-gradient(135deg, #78350F, #92400E);
    border-left: 4px solid #FBBF24;
}
.toast-info {
    background: linear-gradient(135deg, #1E3A5F, #1E40AF);
    border-left: 4px solid #60A5FA;
}
.toast .toast-icon { font-size: 20px; flex-shrink: 0; }
.toast .toast-close {
    margin-left: auto;
    cursor: pointer;
    opacity: 0.6;
    font-size: 18px;
    transition: opacity 0.2s;
    background: none;
    border: none;
    color: #FFFFFF;
}
.toast .toast-close:hover { opacity: 1; }
.toast-fade-out {
    animation: fadeOut 0.4s ease-in forwards;
}
@media (max-width: 600px) {
    .toast-container {
        top: 10px;
        right: 10px;
        max-width: calc(100% - 20px);
    }
}
</style>
"""


def inject_css():
    import streamlit as st
    import database as _db
    import themes as _th

    # Active theme
    auto  = _db.get_setting("theme_auto", "0") == "1"
    key   = _th.get_daily_theme() if auto else _db.get_setting("theme_key", "design_1")
    key = _th.normalize_theme_key(key)
    st.session_state["current_theme"] = key
    st.session_state["_gympro_theme"] = key

    # Structural CSS first; the selected design is the final visual authority.
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(_th.build_css(key), unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavSeparator"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, sub="", color=""):
    cls = f"metric-{color}" if color else ""
    return f"""
    <div class="metric-card {cls}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {"<div class='sub'>" + sub + "</div>" if sub else ""}
    </div>"""


def page_header(icon, title, sub=""):
    import streamlit as st
    st.markdown(f"""
    <div class="page-header">
        <span class="icon">{icon}</span>
        <div>
            <h1>{title}</h1>
            {"<div class='sub'>" + sub + "</div>" if sub else ""}
        </div>
    </div>""", unsafe_allow_html=True)


def badge(text, color="gray"):
    return f'<span class="badge badge-{color}">{text}</span>'


# ── ★★★ TOAST NOTIFICATIONS FUNCTIONS ★★★ ──────────────────────

def show_toast(message, type="success", duration=4000):
    """
    Show a toast notification.
    
    Parameters:
    - message: str - The message to display
    - type: str - 'success', 'error', 'warning', 'info'
    - duration: int - Time in milliseconds to show the toast (default: 4000)
    """
    if "toasts" not in st.session_state:
        st.session_state.toasts = []
    
    # Create toast object
    toast = {
        "message": message,
        "type": type,
        "duration": duration,
        "timestamp": datetime.now().timestamp()
    }
    
    # Add to toasts list
    st.session_state.toasts.append(toast)
    
    # Keep only last 50 toasts
    if len(st.session_state.toasts) > 50:
        st.session_state.toasts = st.session_state.toasts[-50:]
    
    # Render toasts
    render_toasts()


def render_toasts():
    """Render all pending toast notifications"""
    if "toasts" not in st.session_state or not st.session_state.toasts:
        return
    
    import streamlit as st
    import time
    
    # Get current toasts
    toasts = st.session_state.toasts
    
    # Build toast HTML
    toast_html = '<div class="toast-container">'
    
    # Icons for each type
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    
    for toast in toasts[-5:]:  # Show last 5 toasts
        toast_type = toast.get("type", "info")
        icon = icons.get(toast_type, "ℹ️")
        message = toast.get("message", "")
        
        toast_html += f"""
        <div class="toast toast-{toast_type}">
            <span class="toast-icon">{icon}</span>
            <span>{message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
        </div>
        """
    
    toast_html += '</div>'
    
    # Inject toast HTML
    st.markdown(toast_html, unsafe_allow_html=True)
    
    # Auto-clear toasts after duration
    # Note: This is handled by the CSS animation


def toast_success(message, duration=4000):
    """Show success toast"""
    show_toast(message, "success", duration)


def toast_error(message, duration=4000):
    """Show error toast"""
    show_toast(message, "error", duration)


def toast_warning(message, duration=4000):
    """Show warning toast"""
    show_toast(message, "warning", duration)


def toast_info(message, duration=4000):
    """Show info toast"""
    show_toast(message, "info", duration)


def clear_toasts():
    """Clear all toasts"""
    if "toasts" in st.session_state:
        st.session_state.toasts = []


# ── AUTO-RENDER TOASTS (call this at the end of each page) ──
def render_toasts_auto():
    """Auto-render toasts if any exist"""
    if "toasts" in st.session_state and st.session_state.toasts:
        render_toasts()