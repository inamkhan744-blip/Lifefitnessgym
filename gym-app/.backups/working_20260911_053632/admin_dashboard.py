import streamlit as st
from utils import check_authentication, get_user_role


def render(gym_id=None, role=None, username=None):
    """Render the Admin Dashboard.

    Parameters
    ----------
    gym_id : str or None
        Identifier for the gym (optional, can be used for multi‑gym setups).
    role : str or None
        The role of the logged‑in user. Expected to be ``"admin"`` for this page.
    username : str or None
        The username of the logged‑in user (displayed in the header).
    """

    # ---------------------------------------------------------------------
    # Authentication & Authorization
    # ---------------------------------------------------------------------
    if not check_authentication():
        st.warning("You must be logged in to view the dashboard.")
        st.stop()

    if role != "admin":
        st.error("Access denied: Admin privileges are required.")
        st.stop()

    # ---------------------------------------------------------------------
    # Page Layout
    # ---------------------------------------------------------------------
    st.set_page_config(page_title="Admin Dashboard", layout="wide")

    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("static/logo.png", width=80)
    with col2:
        st.title(f"Welcome, {username or 'Admin'}!")
        st.subheader("Gym Management Admin Dashboard")

    # Sidebar navigation – simple placeholder links
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            [
                "Overview",
                "Members",
                "Attendance",
                "Payments",
                "Inventory",
                "Reports",
                "Settings",
            ],
        )

    # Main content area – show a placeholder based on selected page
    st.markdown("---")
    if page == "Overview":
        st.header("📊 Overview")
        st.info("Key metrics and quick stats will appear here.")
    elif page == "Members":
        st.header("👥 Members Management")
        st.info("Member list, add / edit member functionality.")
    elif page == "Attendance":
        st.header("🕒 Attendance")
        st.info("Attendance tracking and reports.")
    elif page == "Payments":
        st.header("💰 Payments & Fees")
        st.info("Fee collection, payment history, and financial summary.")
    elif page == "Inventory":
        st.header("📦 Inventory")
        st.info("Manage gym equipment, supplies, and stock levels.")
    elif page == "Reports":
        st.header("📈 Reports")
        st.info("Generate various operational reports.")
    elif page == "Settings":
        st.header("⚙️ Settings")
        st.info("Configure gym details, user roles, and system preferences.")
    else:
        st.write("Select a section from the sidebar.")

    # Footer
    st.markdown("---")
    st.caption("© 2024 Gym Management System – All rights reserved.")
