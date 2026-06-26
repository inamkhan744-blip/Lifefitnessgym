import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db

def render(gym_id, role, username):
    
    # ============================================
    # SIMPLE HEADER (No CSS)
    # ============================================
    
    st.title("🎯 Staff Target Management")
    st.caption("Set monthly targets for staff and track their performance")
    
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return
    
    if role.lower() not in ["admin", "owner"]:
        st.error("⛔ Access Denied! Only Admin can access this page.")
        return
    
    # ============================================
    # FILTERS
    # ============================================
    
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    
    with col_f1:
        if gym_id:
            sel_gid = gym_id
            st.text_input("🏋️ Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True)
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("🏋️ Gym", list(opts.keys()))
            sel_gid = opts[chosen]
    
    with col_f2:
        target_month = st.selectbox(
            "📅 Month",
            [(date.today().replace(day=1) - timedelta(days=30*i)).strftime("%Y-%m") for i in range(6)],
            index=0
        )
    
    with col_f3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # ============================================
    # STAFF PROGRESS CARDS
    # ============================================
    
    st.subheader(f"📊 Staff Progress - {target_month}")
    
    all_staff = db.get_all_staff_progress(gym_id=sel_gid, target_month=target_month)
    
    if not all_staff:
        st.info("📭 No staff found for this gym.")
        return
    
    for staff in all_staff:
        name = staff['full_name']
        role_name = staff['role']
        progress = staff['progress']
        
        with st.container():
            st.markdown("---")
            
            if progress:
                overall_pct = progress['overall']
                prize = progress['prize_amount']
                prize_status = progress['prize_status']
                status = progress['status']
                
                # Show staff name and progress
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**{name}**")
                    st.caption(f"👤 {role_name}")
                with col2:
                    if overall_pct >= 80:
                        st.success(f"🏆 {overall_pct:.0f}%")
                    elif overall_pct >= 50:
                        st.warning(f"💪 {overall_pct:.0f}%")
                    else:
                        st.error(f"🎯 {overall_pct:.0f}%")
                    st.caption(f"Status: {status}")
                
                # Progress bars
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown("**👤 New Members**")
                    st.progress(progress['new_members']['percentage'] / 100)
                    st.caption(f"{progress['new_members']['achieved']:.0f}/{progress['new_members']['target']:.0f}")
                
                with col_b:
                    st.markdown("**💰 Fee Collection**")
                    st.progress(progress['fee_collection']['percentage'] / 100)
                    st.caption(f"PKR {progress['fee_collection']['achieved']:,.0f}/{progress['fee_collection']['target']:,.0f}")
                
                with col_c:
                    st.markdown("**✅ Attendance**")
                    st.progress(progress['attendance']['percentage'] / 100)
                    st.caption(f"{progress['attendance']['achieved']:.0f}/{progress['attendance']['target']:.0f}")
                
                # Prize info
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.metric("🏆 Prize", f"PKR {prize:,.2f}")
                with col_p2:
                    if prize_status == "Awarded":
                        st.success(f"✅ {prize_status}")
                    elif prize_status == "Pending":
                        st.warning(f"⏳ {prize_status}")
                    else:
                        st.info(f"📌 {prize_status}")
            else:
                st.markdown(f"**{name}**")
                st.caption(f"👤 {role_name}")
                st.info("⏳ No targets set")
    
    st.markdown("---")
    
    # ============================================
    # SET NEW TARGET
    # ============================================
    
    st.subheader("🎯 Set New Target for Staff")
    st.caption("Set all three targets together for a staff member")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        staff_list = db.get_all_users()
        if sel_gid:
            staff_list = [u for u in staff_list if u.gym_id == sel_gid]
        staff_list = [u for u in staff_list if u.role.lower() != "admin" and u.username != username]
        
        if not staff_list:
            st.warning("⚠️ No staff members found. Add staff first!")
        else:
            staff_opts = {f"{u.full_name} (@{u.username})": u.username for u in staff_list}
            selected_staff_label = st.selectbox("👤 Select Staff", list(staff_opts.keys()))
            staff_username = staff_opts[selected_staff_label]
    
    with col_t2:
        # Show existing targets if any
        existing = db.get_staff_target(staff_username, target_month) if staff_list else None
        if existing:
            st.info(f"📋 Existing targets for this month:")
            st.caption(f"• New Members: {existing['new_members']['target']:.0f}")
            st.caption(f"• Fee Collection: PKR {existing['fee_collection']['target']:,.2f}")
            st.caption(f"• Attendance: {existing['attendance_target_percentage']:.0f}%")
            st.caption(f"• Prize: PKR {existing['prize_amount']:,.2f}")
    
    if staff_list:
        st.markdown("### 📊 Set Targets")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            new_members_target = st.number_input(
                "👤 New Members",
                min_value=0.0,
                step=1.0,
                value=0.0,
                help="Number of new members to add"
            )
        
        with col_b:
            fee_collection_target = st.number_input(
                "💰 Fee Collection (PKR)",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                help="Total fee to collect in PKR"
            )
        
        with col_c:
            attendance_percentage = st.number_input(
                "✅ Attendance Target (%)",
                min_value=0.0,
                max_value=100.0,
                step=5.0,
                value=80.0,
                help="Percentage of total active members to mark attendance daily"
            )
            
            # Show calculated target count
            total_members = len(db.get_members(gym_id=sel_gid, status="Active")) if sel_gid else 0
            if total_members > 0:
                target_count = (attendance_percentage / 100) * total_members
                st.caption(f"📊 {total_members} members × {attendance_percentage:.0f}% = **{target_count:.0f} members/day**")
            else:
                st.warning("⚠️ No active members in this gym.")
        
        st.markdown("### 🏆 Prize / Inam")
        prize_amount = st.number_input(
            "💰 Prize Amount (PKR)",
            min_value=0.0,
            step=500.0,
            value=0.0,
            help="Prize amount if all targets are completed"
        )
        
        if st.button("✅ Set Targets", type="primary", use_container_width=True):
            if new_members_target <= 0 or fee_collection_target <= 0 or attendance_percentage <= 0:
                st.error("❌ All targets must be greater than 0!")
            else:
                ok, msg = db.add_staff_target(
                    gym_id=sel_gid,
                    staff_username=staff_username,
                    new_members_target=new_members_target,
                    fee_collection_target=fee_collection_target,
                    attendance_target_percentage=attendance_percentage,
                    target_month=target_month,
                    created_by=username,
                    prize_amount=prize_amount
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    st.markdown("---")
    
    # ============================================
    # TARGET HISTORY
    # ============================================
    
    st.subheader("📋 Target History")
    
    all_targets = db.get_all_staff_targets(gym_id=sel_gid)
    
    if all_targets:
        rows = []
        for t in all_targets:
            staff = db.get_user_by_username(t.staff_username)
            
            # Calculate overall
            new_pct = (t.new_members_achieved / t.new_members_target * 100) if t.new_members_target > 0 else 0
            fee_pct = (t.fee_collection_achieved / t.fee_collection_target * 100) if t.fee_collection_target > 0 else 0
            
            # Get total members for attendance
            total_members = len(db.get_members(gym_id=sel_gid, status="Active")) if sel_gid else 0
            attendance_target_count = (t.attendance_target_percentage / 100) * total_members if total_members > 0 else 0
            att_pct = (t.attendance_achieved / attendance_target_count * 100) if attendance_target_count > 0 else 0
            
            overall = (new_pct + fee_pct + att_pct) / 3
            
            rows.append({
                "ID": t.id,
                "Staff": staff.full_name if staff else t.staff_username,
                "New Members": f"{t.new_members_achieved:.0f}/{t.new_members_target:.0f}",
                "Fee Collection": f"PKR {t.fee_collection_achieved:,.0f}/{t.fee_collection_target:,.0f}",
                "Attendance": f"{t.attendance_achieved:.0f}/{attendance_target_count:.0f} ({t.attendance_target_percentage:.0f}%)",
                "Progress": f"{min(100, overall):.0f}%",
                "Prize": f"PKR {t.prize_amount:,.2f}",
                "Status": "✅ Awarded" if t.prize_status == "Awarded" else "⏳ Pending",
                "Month": t.target_month,
            })
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Delete target
        if all_targets:
            st.caption("🗑️ Select a target to delete")
            del_opts = {f"{r['Staff']} - {r['Month']}": r['ID'] for r in rows}
            del_sel = st.selectbox("Select Target to Delete", list(del_opts.keys()))
            if st.button("🗑️ Delete Target", use_container_width=True):
                ok, msg = db.delete_staff_target(del_opts[del_sel])
                if ok:
                    st.success("✅ Target deleted!")
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("No targets set yet.")