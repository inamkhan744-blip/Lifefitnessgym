import streamlit as st
import database as db


ROLE_PAGES = {
    "admin":   ["Dashboard", "Members", "Membership Cards", "Attendance", "Progress Tracker",
                "Fee Collection", "Expenses", "Inventory", "Reports",
                "Message Center", "WhatsApp", "Complaints", "Audit",
                "Gym Setup", "User Management", "AI Assistant", "Staff Targets"],
    "staff":   ["Dashboard", "Members", "Membership Cards", "Attendance", "Progress Tracker",
                "Fee Collection", "Expenses", "Inventory", "Complaints", "AI Assistant"],
    "auditor": ["Dashboard", "Audit", "Reports", "AI Assistant"],
}

ROLE_ICONS = {
    "admin":   "👑",
    "staff":   "🧑‍💼",
    "auditor": "🔍",
}


def login_page():
    """Login page with clean design"""
    
    st.markdown("""
    <style>
    .login-box {
        max-width: 420px;
        margin: 60px auto;
        padding: 2.5rem;
        background: #1E293B;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 25px 50px rgba(0,0,0,0.5);
    }
    .login-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        color: #7C3AED;
        margin-bottom: 0.25rem;
    }
    .login-sub {
        text-align: center;
        color: #94A3B8;
        margin-bottom: 2rem;
        font-size: 0.95rem;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-title">🏋️ GymPro</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Professional Gym Management</div>', unsafe_allow_html=True)
        st.divider()
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            user = db.get_user_by_username(username)
            if user and db.verify_password(password, user.password_hash) and user.is_active:
                
                # 🔥 LOG STAFF LOGIN (for all non-admin users)
                if user.role.lower() != "admin":
                    try:
                        db.log_staff_login(user.username)
                    except:
                        pass  # Ignore if function doesn't exist
                
                st.session_state["user_id"] = user.id
                st.session_state["username"] = user.username
                st.session_state["full_name"] = user.full_name
                st.session_state["role"] = user.role
                st.session_state["user_gym_id"] = user.gym_id
                st.session_state["page"] = "Dashboard"
                st.session_state["selected_gym_id"] = user.gym_id
                st.rerun()
            else:
                st.error("Invalid credentials or account inactive.")
        
        st.divider()


def require_login():
    return "user_id" in st.session_state


def logout():
    # 🔥 LOG STAFF LOGOUT
    username = st.session_state.get("username", "")
    role = st.session_state.get("role", "")
    
    if username and role.lower() != "admin":
        try:
            db.log_staff_logout(username)
        except:
            pass  # Ignore if function doesn't exist
    
    for key in ["user_id", "username", "full_name", "role", "user_gym_id", "page", "selected_gym_id"]:
        st.session_state.pop(key, None)
    st.rerun()


def current_role():
    return st.session_state.get("role", "")


def allowed_pages():
    return ROLE_PAGES.get(current_role(), [])


def can_access(page):
    return page in allowed_pages()