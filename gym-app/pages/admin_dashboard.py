import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db
import styles

def render(gym_id, role, username):
    
    # ============================================
    # GET GYMS
    # ============================================
    
    gyms = db.get_all_gyms()
    
    # ============================================
    # ANNOUNCEMENT SECTION
    # ============================================
    
    if role.lower() in ["admin", "owner"] and gyms:
        with st.expander("📢 Post Announcement", expanded=False):
            with st.form("announcement_form", clear_on_submit=True):
                if gym_id:
                    sel_gid = gym_id
                    gym_name = next((g.name for g in gyms if g.id == gym_id), "")
                    st.text_input("🏋️ Gym", value=gym_name, disabled=True)
                else:
                    opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
                    chosen = st.selectbox("🏋️ Gym", list(opts.keys()))
                    sel_gid = opts[chosen]
                
                message = st.text_area("📝 Announcement Message", placeholder="Type your announcement here...", height=80)
                
                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    set_expiry = st.checkbox("Set Expiry Date")
                with col_exp2:
                    if set_expiry:
                        expiry_date = st.date_input("Expiry Date", value=date.today() + timedelta(days=7))
                    else:
                        expiry_date = None
                
                if st.form_submit_button("📢 Post Announcement", type="primary", use_container_width=True):
                    if not message.strip():
                        st.error("❌ Please enter a message!")
                    else:
                        expires_at = datetime.combine(expiry_date, datetime.min.time()) if expiry_date else None
                        ok, msg = db.add_announcement(sel_gid, message, username, expires_at)
                        if ok:
                            st.success("✅ Announcement posted!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
        
        st.divider()
    
    # ============================================
    # SHOW ACTIVE ANNOUNCEMENT BANNER
    # ============================================
    
    active_announcement = db.get_active_announcement(gym_id=gym_id)
    
    if active_announcement:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #7C3AED, #6D28D9);
                    border-radius:12px;
                    padding:0.8rem 1.2rem;
                    margin-bottom:1rem;
                    border:1px solid rgba(255,255,255,0.1);
                    box-shadow:0 4px 20px rgba(124,58,237,0.3);
                    display:flex;
                    justify-content:space-between;
                    align-items:center;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:1.3rem;">📢</span>
                <div>
                    <div style="color:rgba(255,255,255,0.6); font-size:0.6rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em;">
                        Announcement
                    </div>
                    <div style="color:white; font-weight:500; font-size:0.95rem;">
                        {active_announcement.message}
                    </div>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
                <span style="background:rgba(255,255,255,0.12); padding:2px 10px; border-radius:9999px; font-size:0.55rem; color:rgba(255,255,255,0.8);">
                    {active_announcement.created_by}
                </span>
                <span style="background:rgba(255,255,255,0.08); padding:2px 8px; border-radius:4px; font-size:0.5rem; color:rgba(255,255,255,0.5);">
                    {active_announcement.created_at.strftime('%d %b') if active_announcement.created_at else ''}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ============================================
    # DASHBOARD HEADER
    # ============================================
    
    styles.page_header("📊", "Dashboard", "Real-time overview across all operations")

    # Custom 3D CSS
    st.markdown("""
    <style>
    .glass-card-3d {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9));
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 20px 35px -12px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .glass-card-3d:hover {
        transform: translateY(-4px);
        box-shadow: 0 25px 40px -15px rgba(0,0,0,0.5);
        border-color: rgba(255,255,255,0.2);
    }
    .metric-value-3d {
        font-size: 38px;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF, #A78BFA);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        letter-spacing: -1px;
    }
    .metric-label-3d {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #94A3B8;
    }
    .alert-box-critical {
        background: rgba(239, 68, 68, 0.12);
        border-left: 4px solid #EF4444;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
    }
    .alert-box-urgent {
        background: rgba(245, 158, 11, 0.12);
        border-left: 4px solid #F59E0B;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
    }
    .alert-box-absent {
        background: rgba(59, 130, 246, 0.12);
        border-left: 4px solid #3B82F6;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
    }
    .badge-paid {
        background: #10B981;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-partial {
        background: #F59E0B;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-unpaid {
        background: #EF4444;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    if not gyms and role == "admin":
        st.info("👋 Welcome! Head to **Gym Setup** to create your first gym.")
        return

    stats = db.get_stats(gym_id)

    # ── 5 KPI Cards ────────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">👥 TOTAL MEMBERS</div>
            <div class="metric-value-3d">{stats['total_members']}</div>
            <div style="font-size:11px; color:#475569;">All registered</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">✅ ACTIVE MEMBERS</div>
            <div class="metric-value-3d">{stats['active_members']}</div>
            <div style="font-size:11px; color:#475569;">{stats['total_members'] - stats['active_members']} inactive</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">💰 MONTH REVENUE</div>
            <div class="metric-value-3d">PKR {stats['month_revenue']:,.0f}</div>
            <div style="font-size:11px; color:#475569;">Total: PKR {stats['total_revenue']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c4:
        net = stats["month_revenue"] - stats["month_expenses"]
        color_net = "#10B981" if net >= 0 else "#EF4444"
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">📈 MONTH NET P/L</div>
            <div class="metric-value-3d" style="background:linear-gradient(135deg, #FFF, {color_net}); -webkit-background-clip:text; background-clip:text;">PKR {net:,.0f}</div>
            <div style="font-size:11px; color:#475569;">Exp: PKR {stats['month_expenses']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c5:
        inv_rev = stats.get("inventory_revenue", 0)
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">📦 INVENTORY SALES</div>
            <div class="metric-value-3d">PKR {inv_rev:,.0f}</div>
            <div style="font-size:11px; color:#475569;">From POS</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── ALERTS SECTION ────────────────────────────────────────────────────────
    bday_members = db.get_birthday_members(days_ahead=3, gym_id=gym_id)
    expiring_now = db.get_expiring_members(days=7, gym_id=gym_id)
    absent_alert = db.get_absent_members(days=3, gym_id=gym_id)
    low_stock = db.get_stock_items(gym_id=gym_id, low_stock_only=True)

    critical = [(m, d) for m, d in expiring_now if d <= 1]
    urgent = [(m, d) for m, d in expiring_now if 2 <= d <= 3]
    
    st.markdown("### ⚠️ ATTENTION REQUIRED")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown('<div class="alert-box-critical"><strong>🔴 CRITICAL (0-1 din)</strong></div>', unsafe_allow_html=True)
        if critical:
            for m, d in critical[:5]:
                st.write(f"• **{m.full_name}** — {d} day(s) left")
        else:
            st.write("✅ No critical expiries")
    
    with col_b:
        st.markdown('<div class="alert-box-urgent"><strong>🟠 URGENT (2-3 din)</strong></div>', unsafe_allow_html=True)
        if urgent:
            for m, d in urgent[:5]:
                st.write(f"• **{m.full_name}** — {d} days left")
        else:
            st.write("✅ No urgent expiries")
    
    with col_c:
        st.markdown('<div class="alert-box-absent"><strong>🔵 ABSENT 3+ DAYS</strong></div>', unsafe_allow_html=True)
        if absent_alert:
            for m in absent_alert[:5]:
                st.write(f"• **{m.full_name}**")
        else:
            st.write("✅ Everyone active")
    
    if bday_members:
        bday_text = "🎂 " + ", ".join([f"{m.full_name} ({d} day(s))" for m, d in bday_members[:3]])
        st.info(bday_text)
    if low_stock:
        stock_text = "📦 Low stock: " + ", ".join([f"{i.item_name} ({i.quantity} left)" for i in low_stock[:3]])
        st.warning(stock_text)

    st.markdown("---")

    # ── LEADERBOARD + PEAK HOUR ──────────────────────────────────────────────
    col_lb, col_ph = st.columns(2)
    
    with col_lb:
        st.markdown("### 🏆 Monthly Attendance Leaderboard")
        leaderboard = db.get_attendance_leaderboard(gym_id=gym_id, limit=5)
        if leaderboard:
            for rank, entry in enumerate(leaderboard[:5], 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #334155;">
                    <span style="font-weight:700; color:#A78BFA;">{medal}</span>
                    <span style="flex:1; margin-left:12px;"><strong>{entry['member'].full_name}</strong></span>
                    <span style="color:#94A3B8;">{entry['count']} sessions</span>
                    <span style="color:#F59E0B;">🔥 {entry['streak']}d</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No attendance data yet.")
    
    with col_ph:
        st.markdown("### ⏰ Peak Hour")
        hour_data = db.get_attendance_by_hour(gym_id=gym_id)
        if any(hour_data.values()):
            peak_hour = max(hour_data, key=lambda h: hour_data[h])
            peak_count = hour_data[peak_hour]
            am_pm = "AM" if peak_hour < 12 else "PM"
            hour_12 = peak_hour if peak_hour <= 12 else peak_hour - 12
            total_att = sum(hour_data.values())
            
            st.markdown(f"""
            <div class="glass-card-3d" style="text-align:center;">
                <div style="font-size:48px; font-weight:800; background:linear-gradient(135deg,#FFF,#A78BFA); -webkit-background-clip:text; background-clip:text; color:transparent;">
                    {hour_12}:00 {am_pm}
                </div>
                <div style="font-size:14px; color:#94A3B8;">🔥 {peak_count} check-ins at this hour</div>
                <div style="margin-top:12px; padding-top:12px; border-top:1px solid #334155;">
                    <div style="font-size:11px; color:#475569;">📊 Total Logged: {total_att} all-time entries</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No attendance records yet.")
    
    st.markdown("---")
    
    # ── RECENT SCAN-INS ──────────────────────────────────────────────────────
    st.markdown("### 🎯 Recent Scan-Ins (Today)")
    scans = db.get_recent_scans(gym_id=gym_id, limit=10, today_only=True)
    if scans:
        scan_df = pd.DataFrame([{
            "Time": s["time"],
            "Member": s["name"],
            "Serial": s["serial"],
            "Marked By": s["marked_by"],
        } for s in scans])
        st.dataframe(scan_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No QR check-ins yet today.")
    
    st.markdown("---")
    
    # ── MEMBERS & FEE STATUS ─────────────────────────────────────────────────
    st.markdown("### 👥 Members & Fee Status")
    st.caption("Recent registrations + fee status ek hi jagah")
    
    all_members = db.get_members(gym_id=gym_id)
    all_fees = db.get_fee_records(gym_id=gym_id)
    
    member_paid = {}
    for f in all_fees:
        member_paid[f.member_id] = member_paid.get(f.member_id, 0) + f.amount
    
    unified_rows = []
    for m in all_members:
        expected_fee = getattr(m, "fee_amount", 0) or 0
        paid = member_paid.get(m.id, 0)
        pending = max(expected_fee - paid, 0)
        
        if expected_fee == 0 and paid == 0:
            status_badge = '<span class="badge-paid">⚪ No Fee</span>'
            status_key = "none"
        elif paid >= expected_fee and expected_fee > 0:
            status_badge = '<span class="badge-paid">🟢 PAID</span>'
            status_key = "paid"
        elif paid > 0 and paid < expected_fee:
            status_badge = '<span class="badge-partial">🟡 PARTIAL</span>'
            status_key = "partial"
        else:
            status_badge = '<span class="badge-unpaid">🔴 UNPAID</span>'
            status_key = "unpaid"
        
        unified_rows.append({
            "Serial": m.serial_number,
            "Name": m.full_name,
            "Phone": m.phone or "—",
            "Type": m.membership_type,
            "Fee": f"PKR {expected_fee:,.0f}",
            "Paid": f"PKR {paid:,.0f}",
            "Pending": f"PKR {pending:,.0f}",
            "Status": status_badge,
            "_status_key": status_key,
        })
    
    total_count = len(unified_rows)
    paid_count = sum(1 for r in unified_rows if r["_status_key"] == "paid")
    unpaid_count = sum(1 for r in unified_rows if r["_status_key"] == "unpaid")
    partial_count = sum(1 for r in unified_rows if r["_status_key"] == "partial")
    
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(styles.metric_card("Total Members", total_count, "All registered", "purple"), unsafe_allow_html=True)
    with s2:
        st.markdown(styles.metric_card("🟢 Paid", paid_count, "Fee cleared", "green"), unsafe_allow_html=True)
    with s3:
        st.markdown(styles.metric_card("🟡 Partial", partial_count, "Some pending", "amber"), unsafe_allow_html=True)
    with s4:
        st.markdown(styles.metric_card("🔴 Unpaid", unpaid_count, "Need to collect", "red"), unsafe_allow_html=True)
    
    if "fee_filter" not in st.session_state:
        st.session_state.fee_filter = "all"
    
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        if st.button(f"All ({total_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "all" else "secondary"):
            st.session_state.fee_filter = "all"
            st.rerun()
    with fc2:
        if st.button(f"🟢 Paid ({paid_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "paid" else "secondary"):
            st.session_state.fee_filter = "paid"
            st.rerun()
    with fc3:
        if st.button(f"🟡 Partial ({partial_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "partial" else "secondary"):
            st.session_state.fee_filter = "partial"
            st.rerun()
    with fc4:
        if st.button(f"🔴 Unpaid ({unpaid_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "unpaid" else "secondary"):
            st.session_state.fee_filter = "unpaid"
            st.rerun()
    
    search_query = st.text_input("🔍 Search by Name / Serial / Phone", placeholder="Type to search...")
    
    filtered_rows = [r for r in unified_rows if st.session_state.fee_filter == "all" or r["_status_key"] == st.session_state.fee_filter]
    if search_query:
        q = search_query.lower()
        filtered_rows = [r for r in filtered_rows if q in r["Name"].lower() or q in r["Serial"].lower()]
    
    if filtered_rows:
        display_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in filtered_rows[:25]]
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
        st.caption(f"📋 Showing {len(display_rows)} of {len(filtered_rows)} members")
    
    st.markdown("---")
    
    # ── EXPIRING MEMBERSHIPS ─────────────────────────────────────────────────
    expiring = db.get_expiring_members(days=7, gym_id=gym_id)
    if expiring:
        st.markdown(f"### ⚠️ {len(expiring)} Membership(s) Expiring in 7 Days")
        
        critical = [x for x in expiring if x[1] <= 1]
        urgent = [x for x in expiring if 2 <= x[1] <= 3]
        soon = [x for x in expiring if x[1] >= 4]
        
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown(styles.metric_card("🔴 Critical", len(critical), "Aaj ya kal expire", "red"), unsafe_allow_html=True)
        with e2:
            st.markdown(styles.metric_card("🟠 Urgent", len(urgent), "2-3 din mein", "amber"), unsafe_allow_html=True)
        with e3:
            st.markdown(styles.metric_card("🟡 Soon", len(soon), "4-7 din mein", "blue"), unsafe_allow_html=True)
        
        exp_rows = []
        for m, days_left in expiring[:20]:
            urgency = "🔴 Critical" if days_left <= 1 else "🟠 Urgent" if days_left <= 3 else "🟡 Soon"
            exp_rows.append({
                "Urgency": urgency,
                "Name": m.full_name,
                "Serial": m.serial_number,
                "Phone": m.phone or "—",
                "Expires On": m.expiry_date,
                "Days Left": "TODAY!" if days_left == 0 else f"{days_left} day(s)",
            })
        st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)
        st.info("💡 **Tip:** Critical members ko foran WhatsApp/Call karein renewal ke liye!")
    
    st.markdown("---")
    st.caption("✨ Simplified dashboard · No graphs · Clean 3D design · Just what matters")

    # ============================================
    # ✅ STAFF TARGETS SECTION (Function ke ANDAR)
    # ============================================
    
    if role.lower() not in ["admin", "owner"]:
        st.divider()
        st.subheader("🎯 My Performance Targets")
        
        current_month = date.today().strftime("%Y-%m")
        progress = db.get_staff_progress(username, current_month)
        
        if progress:
            targets_exist = any([
                progress['new_members']['target'] > 0,
                progress['fee_collection']['target'] > 0,
                progress['attendance']['target'] > 0
            ])
            
            if targets_exist:
                overall_pct = progress['overall']
                prize_amount = progress.get('prize_amount', 0)
                prize_status = progress.get('prize_status', 'Pending')
                
                if prize_status == "Awarded":
                    prize_color = "#34D399"
                    prize_emoji = "🏆"
                    prize_text = "🎉 Prize Awarded!"
                elif prize_status == "Pending":
                    prize_color = "#FBBF24"
                    prize_emoji = "🎯"
                    prize_text = "⏳ Target In Progress"
                else:
                    prize_color = "#94A3B8"
                    prize_emoji = "📌"
                    prize_text = "⏳ Not Completed"
                
                st.markdown(f"""
                <div style="background:linear-gradient(145deg, #1E293B, #0F172A);
                            border:2px solid {prize_color};
                            border-radius:16px;
                            padding:1.5rem;
                            margin-bottom:1rem;
                            text-align:center;
                            box-shadow:0 8px 30px rgba(0,0,0,0.3);">
                    <div style="font-size:3rem;margin-bottom:0.3rem;">{prize_emoji}</div>
                    <div style="font-size:1.5rem;font-weight:800;color:#F8FAFC;">
                        Prize / Inam
                    </div>
                    <div style="font-size:2.5rem;font-weight:900;color:{prize_color};margin:0.3rem 0;">
                        PKR {prize_amount:,.2f}
                    </div>
                    <div style="font-size:1rem;font-weight:600;color:{prize_color};">
                        {prize_text}
                    </div>
                    <div style="font-size:0.8rem;color:#94A3B8;margin-top:0.3rem;">
                        {progress['completed_targets']}/{progress['total_targets']} targets completed
                    </div>
                    <div style="font-size:0.7rem;color:#64748B;margin-top:0.2rem;">
                        💡 All 3 targets must be completed to win the prize!
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Overall Progress", f"{overall_pct:.0f}%", f"{progress['completed_targets']}/{progress['total_targets']} targets completed")
                with col2:
                    pct = progress['new_members']['percentage']
                    st.metric("👤 New Members", f"{progress['new_members']['achieved']:.0f}/{progress['new_members']['target']:.0f}", f"{pct:.0f}% done")
                with col3:
                    pct = progress['fee_collection']['percentage']
                    st.metric("💰 Fee Collection", f"PKR {progress['fee_collection']['achieved']:,.0f}/{progress['fee_collection']['target']:,.0f}", f"{pct:.0f}% done")
                with col4:
                    pct = progress['attendance']['percentage']
                    st.metric("✅ Attendance", f"{progress['attendance']['achieved']:.0f}/{progress['attendance']['target']:.0f}", f"{pct:.0f}% done")
                
                st.markdown("#### 📈 Target Progress")
                pct = min(100, progress['new_members']['percentage'])
                st.progress(pct / 100, text=f"👤 New Members: {pct:.0f}%")
                pct = min(100, progress['fee_collection']['percentage'])
                st.progress(pct / 100, text=f"💰 Fee Collection: {pct:.0f}%")
                pct = min(100, progress['attendance']['percentage'])
                st.progress(pct / 100, text=f"✅ Attendance: {pct:.0f}%")
                
                if overall_pct >= 80:
                    st.success("🏆 Excellent! You're crushing your targets! Keep it up! 💪")
                elif overall_pct >= 50:
                    st.info("💪 Good progress! You're halfway there! Keep pushing!")
                elif overall_pct > 0:
                    st.warning("🎯 You've started! Focus on completing your targets this month.")
                else:
                    st.info("📝 No targets achieved yet. Keep working towards your goals!")
                
                if overall_pct >= 100:
                    st.balloons()
                    st.success(f"🎉 Congratulations! You've won PKR {prize_amount:,.2f}! 🏆")
            else:
                st.info("📝 No targets assigned for this month. Your admin will assign targets soon!")
                st.caption("💡 Tip: Targets are set monthly by your admin for New Members, Fee Collection, and Attendance.")
        else:
            st.info("📝 No targets found. Your admin will assign targets soon!")

    # ============================================
    # ✅ STAFF ATTENDANCE SECTION (Function ke ANDAR)
    # ============================================
    
    st.divider()
    
    if role.lower() == "admin":
        # Admin view - All staff
        st.subheader("👥 Staff Attendance Overview")
        st.caption("All staff login/logout status")
        
        staff_summary = db.get_staff_attendance_summary(gym_id=gym_id)
        
        if staff_summary:
            online_count = sum(1 for s in staff_summary if "Online" in s['status'])
            total_staff = len(staff_summary)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Total Staff", total_staff)
            with col2:
                st.metric("🟢 Online Now", online_count)
            with col3:
                st.metric("⏳ Today's Logins", sum(1 for s in staff_summary if s['logins'] > 0))
            
            staff_data = []
            for s in staff_summary:
                staff_data.append({
                    "Name": s['full_name'],
                    "Role": s['role'],
                    "Status": s['status'],
                    "Today": s['today_status'],
                    "Logins (30d)": s['logins'],
                    "Hours This Month": f"{s['total_hours']}h"
                })
            
            st.dataframe(pd.DataFrame(staff_data), use_container_width=True, hide_index=True)
        else:
            st.info("No staff attendance data available")
    
    else:
        # Staff view - Only their own attendance
        st.subheader("📋 My Attendance")
        st.caption("Track your daily login/logout history")
        
        try:
            my_summary = db.get_my_attendance_summary(username)
            
            if my_summary:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📅 Today", my_summary['today_status'])
                with col2:
                    st.metric("📊 This Month", f"{my_summary['total_days']} days")
                with col3:
                    st.metric("⏱️ Total Hours", f"{my_summary['total_hours']}h")
                with col4:
                    st.metric("🔥 Streak", f"{my_summary['current_streak']} days")
                
                if my_summary['today_login']:
                    st.caption(f"Logged in at: {my_summary['today_login']}")
            
            with st.expander("📋 Recent Attendance History", expanded=False):
                history = db.get_staff_attendance(staff_username=username, date_from=date.today() - timedelta(days=30))
                
                if history:
                    rows = []
                    for r in history[:30]:
                        status = "🟢 Online" if r.logout_time is None else "🔴 Offline"
                        duration = f"{r.session_duration or 0} min"
                        rows.append({
                            "Date": r.login_time.strftime("%Y-%m-%d"),
                            "Login": r.login_time.strftime("%I:%M %p"),
                            "Logout": r.logout_time.strftime("%I:%M %p") if r.logout_time else "—",
                            "Duration": duration,
                            "Status": status
                        })
                    
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No attendance records found")
        except:
            pass

    # ============================================
    # ✅ STAFF STATUS SECTION - MOVED INSIDE FUNCTION
    # ============================================
    
    st.markdown("---")
    
    if role.lower() == "admin":
        st.subheader("👥 Staff Status")
        
        # 🔥 Auto logout inactive staff before showing
        inactive_count = db.check_and_update_staff_status()
        if inactive_count > 0:
            st.info(f"⏳ {inactive_count} staff auto-logged out due to inactivity")
        
        staff_summary = db.get_staff_attendance_summary(gym_id=gym_id)
        
        if staff_summary:
            online = sum(1 for s in staff_summary if "Online" in s['status'])
            total = len(staff_summary)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🟢 Online Now", online)
            with col2:
                st.metric("👥 Total Staff", total)
            
            # Show staff list with status
            for s in staff_summary[:5]:
                st.write(f"• {s['full_name']} — {s['status']}")
            if len(staff_summary) > 5:
                st.write(f"... and {len(staff_summary)-5} more")
        else:
            st.info("No staff attendance data")

    st.markdown("---")
    st.caption("✨ Simplified dashboard · No graphs · Clean 3D design · Just what matters")