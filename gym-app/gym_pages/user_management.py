import streamlit as st
import pandas as pd
import database as db
import styles

ROLES = ["admin", "staff", "auditor"]


def render(current_user_id):
    styles.page_header("🔐", "User Management", "Manage system accounts and role-based access")

    users = db.get_all_users()
    gyms = db.get_all_gyms()
    gym_opts = {"All Gyms (Admin)": None} | {g.name: g.id for g in gyms}

    # ============================================
    # USER STATS
    # ============================================
    
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("👥 Total Users", len(users))
    with col_s2:
        st.metric("👑 Admins", len([u for u in users if u.role == "admin"]))
    with col_s3:
        st.metric("🧑‍💼 Staff", len([u for u in users if u.role == "staff"]))
    with col_s4:
        st.metric("🔍 Auditors", len([u for u in users if u.role == "auditor"]))
    
    st.divider()

    # ── Add User ───────────────────────────────────────────────────────────────
    with st.expander("➕ Add New User", expanded=False):
        with st.form("add_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                username = st.text_input("Username *", placeholder="jsmith", key="au_username")
                full_name = st.text_input("Full Name *", placeholder="John Smith", key="au_fullname")
                password = st.text_input("Password *", type="password", key="au_password")
            with c2:
                role = st.selectbox("Role *", ROLES, key="au_role")
                gym_sel = st.selectbox("Assigned Gym", list(gym_opts.keys()), key="au_gym")
                st.caption("Admins see all gyms. Staff/Auditors are scoped to a gym.")

            if st.form_submit_button("✅ Create User", type="primary", width="stretch"):
                if not username.strip() or not full_name.strip() or not password:
                    st.error("Username, full name, and password are required.")
                else:
                    ok, msg = db.add_user(
                        username=username.strip(),
                        full_name=full_name.strip(),
                        password=password,
                        role=role,
                        gym_id=gym_opts[gym_sel],
                    )
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

    st.divider()

    # ── User List ──────────────────────────────────────────────────────────────
    st.markdown(f"**{len(users)} User(s)**")

    role_icons = {"admin": "👑", "staff": "🧑‍💼", "auditor": "🔍"}

    rows = []
    for u in users:
        gym_name = next((g.name for g in gyms if g.id == u.gym_id), "All Gyms")
        rows.append({
            "Role": f"{role_icons.get(u.role, '')} {u.role.capitalize()}",
            "Username": u.username,
            "Full Name": u.full_name,
            "Gym": gym_name,
            "Active": "✅" if u.is_active else "❌",
            "Created": u.created_at.strftime("%Y-%m-%d") if u.created_at else "—",
        })
    
    # Search and Filter
    col_search1, col_search2 = st.columns([2, 1])
    with col_search1:
        search_user = st.text_input("🔍 Search Users", placeholder="Search by username or name...", key="user_search")
    with col_search2:
        role_filter = st.selectbox("Filter by Role", ["All"] + ROLES, key="role_filter")
    
    # Apply filters
    filtered_rows = rows
    if search_user:
        filtered_rows = [r for r in filtered_rows if search_user.lower() in r["Username"].lower() or search_user.lower() in r["Full Name"].lower()]
    if role_filter != "All":
        filtered_rows = [r for r in filtered_rows if role_filter in r["Role"].lower()]
    
    if filtered_rows:
        st.dataframe(pd.DataFrame(filtered_rows), width="stretch", hide_index=True)
        st.caption(f"📋 Showing {len(filtered_rows)} of {len(rows)} users")
    else:
        st.info("No users found matching your search.")

    st.divider()

    # ── Edit / Delete ──────────────────────────────────────────────────────────
    st.markdown("**Edit or Remove a User**")
    user_opts = {f"{u.username} ({u.role})": u.id for u in users if u.id != current_user_id}

    if not user_opts:
        st.info("No other users to manage.")
        return

    sel_label = st.selectbox("Select user", list(user_opts.keys()), key="um_sel_user")
    sel_uid = user_opts[sel_label]
    sel_user = next((u for u in users if u.id == sel_uid), None)

    if not sel_user:
        return

    with st.form(f"edit_user_form_{sel_uid}"):
        st.info("💡 **Username change karo toh saare records (fee, attendance, logs) automatically follow karenge**")
        
        c1, c2 = st.columns(2)
        with c1:
            # 🆕 USERNAME FIELD
            new_username = st.text_input(
                "Username *",
                value=sel_user.username,
                key=f"eu_username_{sel_uid}",
                help="⚠️ Rename karega — saare records (fee, attendance, logs, shifts) automatically naye username se link honge"
            )
            new_name = st.text_input("Full Name *", value=sel_user.full_name,
                                     key=f"eu_name_{sel_uid}")
            new_role = st.selectbox("Role *", ROLES, index=ROLES.index(sel_user.role),
                                    key=f"eu_role_{sel_uid}")
            new_pw = st.text_input("New Password (leave blank to keep)", type="password",
                                   key=f"eu_pw_{sel_uid}")
        with c2:
            gym_keys = list(gym_opts.keys())
            cur_gym_name = next((g.name for g in gyms if g.id == sel_user.gym_id), "All Gyms (Admin)")
            gym_idx = gym_keys.index(cur_gym_name) if cur_gym_name in gym_keys else 0
            new_gym = st.selectbox("Assigned Gym", gym_keys, index=gym_idx,
                                   key=f"eu_gym_{sel_uid}")
            is_active = st.checkbox("Active Account", value=sel_user.is_active,
                                    key=f"eu_active_{sel_uid}")

        cs, cd = st.columns(2)
        save = cs.form_submit_button("💾 Save Changes", type="primary")
        delete = cd.form_submit_button("🗑️ Delete User")

        if save:
            # 🆕 STEP 1: Handle username rename (with records update)
            new_username_clean = new_username.strip()
            
            if new_username_clean != sel_user.username:
                # Validate username
                if not new_username_clean:
                    st.error("❌ Username khali nahi ho sakta")
                elif len(new_username_clean) < 3:
                    st.error("❌ Username kam se kam 3 characters ka hona chahiye")
                elif " " in new_username_clean:
                    st.error("❌ Username mein space nahi ho sakti")
                else:
                    # Check if new username already exists
                    session = db.SessionLocal()
                    try:
                        existing = session.query(db.User).filter_by(username=new_username_clean).first()
                        if existing and existing.id != sel_uid:
                            st.error(f"❌ Username '{new_username_clean}' already exists!")
                        else:
                            # Perform rename + update all records
                            from sqlalchemy import text
                            old_un = sel_user.username
                            new_un = new_username_clean
                            
                            # Update user
                            user_to_rename = session.query(db.User).filter_by(id=sel_uid).first()
                            user_to_rename.username = new_un
                            
                            # Update all related records
                            r1 = session.execute(
                                text("UPDATE fee_records SET collected_by = :new WHERE collected_by = :old"),
                                {"new": new_un, "old": old_un}
                            )
                            r2 = session.execute(
                                text("UPDATE attendance SET marked_by = :new WHERE marked_by = :old"),
                                {"new": new_un, "old": old_un}
                            )
                            r3 = session.execute(
                                text('UPDATE activity_logs SET "user" = :new WHERE "user" = :old'),
                                {"new": new_un, "old": old_un}
                            )
                            r4 = session.execute(
                                text("UPDATE shift_sessions SET staff_user = :new WHERE staff_user = :old"),
                                {"new": new_un, "old": old_un}
                            )
                            r5 = session.execute(
                                text("UPDATE staff_targets SET staff_username = :new WHERE staff_username = :old"),
                                {"new": new_un, "old": old_un}
                            )
                            
                            session.commit()
                            
                            total_updated = r1.rowcount + r2.rowcount + r3.rowcount + r4.rowcount + r5.rowcount
                            
                            st.success(f"✅ Username renamed: '{old_un}' → '{new_un}'")
                            st.info(f"📊 {total_updated} records automatically updated")
                            
                            # Clear cache to refresh
                            try:
                                from gym_pages.fee_collection import _cached_members, _cached_fee_records
                                _cached_members.clear()
                                _cached_fee_records.clear()
                            except Exception:
                                pass
                            
                            # Update sel_user reference for other fields
                            sel_user.username = new_un
                            
                    except Exception as e:
                        session.rollback()
                        st.error(f"❌ Rename error: {e}")
                        return
                    finally:
                        session.close()
            
            # 🆕 STEP 2: Update other fields
            ok, msg = db.update_user(
                user_id=sel_uid,
                full_name=new_name,
                role=new_role,
                gym_id=gym_opts[new_gym],
                is_active=is_active,
                new_password=new_pw or None,
            )
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.rerun()

        if delete:
            st.session_state["confirm_del_user"] = sel_uid

    if st.session_state.get("confirm_del_user") == sel_uid:
        st.error(f"⚠️ **{sel_user.username}** ko delete karne se ye records remain karenge:")
        st.caption("• Fee collections — records toot jayenge (collected_by mein username rahega)")
        st.caption("• Attendance — records toot jayenge")
        st.caption("• Activity logs — records toot jayenge")
        st.info("💡 **Better option:** Delete ki jagah **rename** karo — saare records intact rahenge")
        
        cc, cx = st.columns(2)
        if cc.button("✅ Haan, Delete Karo", type="primary", key=f"cdu_yes_{sel_uid}"):
            db.delete_user(sel_uid)
            st.success("✅ User deleted. (Records preserved)")
            st.session_state.pop("confirm_del_user", None)
            st.rerun()
        if cx.button("❌ Cancel", key=f"cdu_no_{sel_uid}"):
            st.session_state.pop("confirm_del_user", None)
            st.rerun()