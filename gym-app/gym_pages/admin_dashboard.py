import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db
import styles

def render(gym_id, role, username):
    gyms = db.get_all_gyms()

    # ============================================
    # ULTRA MODERN DARK THEME CSS
    # ============================================
    st.markdown("""
    <style>
        /* ===== GLOBAL ===== */
        .stApp {
            background: #0A0A0A !important;
            color: #FFFFFF !important;
        }
        
        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #141414; }
        ::-webkit-scrollbar-thumb { background: #FFC947; border-radius: 10px; }
        
        /* ===== GLASS CARD ===== */
        .glass-card {
            background: rgba(20, 20, 20, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 201, 71, 0.08);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }
        .glass-card:hover {
            border-color: #FFC947;
            transform: translateY(-4px);
            box-shadow: 0 12px 48px rgba(255, 201, 71, 0.15);
        }
        
        /* ===== KPI CARDS ===== */
        .kpi-card {
            background: linear-gradient(145deg, #141414, #1A1A1A);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #FFC947, #FF6B6B, #FFC947);
            background-size: 200% 100%;
            animation: shimmer 3s ease-in-out infinite;
        }
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        .kpi-card:hover {
            transform: translateY(-6px);
            border-color: #FFC947;
            box-shadow: 0 8px 30px rgba(255, 201, 71, 0.15);
        }
        .kpi-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #8A8A8A;
            font-weight: 600;
        }
        .kpi-value {
            font-size: 34px;
            font-weight: 800;
            background: linear-gradient(135deg, #FFFFFF 0%, #FFC947 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 8px 0;
        }
        .kpi-subtext {
            font-size: 11px;
            color: #6A6A6A;
        }
        
        /* ===== BADGES ===== */
        .badge-paid {
            background: linear-gradient(135deg, #1EB980, #10B981);
            color: white;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }
        .badge-partial {
            background: linear-gradient(135deg, #FFC947, #F59E0B);
            color: #0A0A0A;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }
        .badge-unpaid {
            background: linear-gradient(135deg, #FF5A5A, #EF4444);
            color: white;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }
        .badge-none {
            background: #2A2A2A;
            color: #8A8A8A;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }
        
        /* ===== ALERT CARDS ===== */
        .alert-critical {
            background: rgba(239, 68, 68, 0.08);
            border-left: 4px solid #EF4444;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 8px 0;
            backdrop-filter: blur(8px);
        }
        .alert-urgent {
            background: rgba(245, 158, 11, 0.08);
            border-left: 4px solid #F59E0B;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 8px 0;
            backdrop-filter: blur(8px);
        }
        .alert-absent {
            background: rgba(59, 130, 246, 0.08);
            border-left: 4px solid #3B82F6;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 8px 0;
            backdrop-filter: blur(8px);
        }
        
        /* ===== ANNOUNCEMENT BANNER ===== */
        .announce-banner {
            background: linear-gradient(135deg, #1A1A1A, #0F0F0F);
            border: 1px solid #FFC947;
            border-radius: 16px;
            padding: 16px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(255, 201, 71, 0.05);
        }
        
        /* ===== SECTION HEADER ===== */
        .section-header {
            font-size: 20px;
            font-weight: 700;
            color: #FFFFFF;
            margin: 28px 0 20px 0;
            padding-bottom: 12px;
            border-bottom: 2px solid rgba(255, 201, 71, 0.15);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .section-header::after {
            content: '';
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, rgba(255, 201, 71, 0.3), transparent);
        }
        
        /* ===== BUTTONS ===== */
        .stButton > button {
            background: linear-gradient(135deg, #FFC947, #F59E0B);
            color: #0A0A0A;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            padding: 10px 24px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 201, 71, 0.2);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(255, 201, 71, 0.3);
        }
        .stButton > button:active {
            transform: translateY(0px);
        }
        
        /* ===== DATAFRAME ===== */
        .dataframe {
            background: #141414 !important;
            border: 1px solid #2A2A2A !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }
        .dataframe thead {
            background: #1A1A1A !important;
        }
        .dataframe th {
            color: #FFC947 !important;
            font-weight: 600 !important;
            padding: 12px !important;
        }
        .dataframe td {
            padding: 10px 12px !important;
            color: #E0E0E0 !important;
        }
        .dataframe tr:hover {
            background: rgba(255, 201, 71, 0.05) !important;
        }
        
        /* ===== EXPANDER ===== */
        .streamlit-expanderHeader {
            background: #141414 !important;
            border: 1px solid #2A2A2A !important;
            border-radius: 12px !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }
        .streamlit-expanderHeader:hover {
            border-color: #FFC947 !important;
        }
        
        /* ===== INPUTS ===== */
        .stTextInput > div > div > input {
            background: #141414 !important;
            border: 1px solid #2A2A2A !important;
            border-radius: 12px !important;
            color: #FFFFFF !important;
            padding: 12px 16px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #FFC947 !important;
            box-shadow: 0 0 0 2px rgba(255, 201, 71, 0.1) !important;
        }
        .stSelectbox > div > div {
            background: #141414 !important;
            border: 1px solid #2A2A2A !important;
            border-radius: 12px !important;
        }
        
        /* ===== PROGRESS BAR ===== */
        .stProgress > div > div {
            background: linear-gradient(90deg, #FFC947, #FF6B6B) !important;
            border-radius: 20px !important;
        }
        
        /* ===== INFO/WARNING/SUCCESS ===== */
        .stAlert {
            border-radius: 12px !important;
            border: none !important;
            backdrop-filter: blur(8px) !important;
        }
        .stAlert > div {
            background: transparent !important;
        }
        
        /* ===== METRIC CARDS ===== */
        .metric-card {
            background: #141414;
            border: 1px solid #2A2A2A;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # ============================================
    # 🚨 FRAUD ALERT BANNER (Anti-Theft)
    # ============================================
    if role.lower() in ["admin", "owner"]:
        try:
            alerts = db.check_fraud_alerts(gym_id=gym_id)
            if alerts:
                critical = [a for a in alerts if a["severity"] == "critical"]
                warnings = [a for a in alerts if a["severity"] == "warning"]

                header_color = "#7F1D1D" if critical else "#78350F"
                border_color = "#EF4444" if critical else "#F59E0B"
                title_color  = "#FCA5A5" if critical else "#FCD34D"
                title_text   = f"🚨 {len(critical)} CRITICAL ALERT{'S' if len(critical)!=1 else ''} — Fori Attention Chahiye!" if critical else f"⚠️ {len(warnings)} Suspicious Activity Alert{'s' if len(warnings)!=1 else ''} Aaj"

                rows_html = ""
                for a in alerts:
                    bg   = "#450A0A" if a["severity"] == "critical" else "#422006"
                    bc   = "#EF4444" if a["severity"] == "critical" else "#F59E0B"
                    rows_html += f"""
                    <div style="background:{bg};border-left:4px solid {bc};border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.5rem;">
                        <div style="font-weight:700;color:#F8FAFC;font-size:0.95rem;">{a['icon']} {a['title']}</div>
                        <div style="color:#CBD5E1;font-size:0.82rem;margin-top:0.2rem;">{a['detail']}</div>
                    </div>"""

                st.markdown(f"""
                <div style="background:{header_color};border:2px solid {border_color};border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;">
                    <div style="font-size:1.1rem;font-weight:800;color:{title_color};margin-bottom:0.75rem;">{title_text}</div>
                    {rows_html}
                    <div style="color:#94A3B8;font-size:0.75rem;margin-top:0.5rem;">Auditor page → 🛡️ Staff Monitor tab mein full details dekhein.</div>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

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
    # SHOW ACTIVE ANNOUNCEMENT
    # ============================================
    active_announcement = db.get_active_announcement(gym_id=gym_id)
    if active_announcement:
        created_date = active_announcement.created_at.strftime('%d %b %Y') if active_announcement.created_at else ''
        st.markdown(f"""
        <div class="announce-banner">
            <div style="display:flex; align-items:center; gap:16px;">
                <span style="font-size:28px;">📢</span>
                <div>
                    <div style="color:#FFC947; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px;">★ ANNOUNCEMENT</div>
                    <div style="color:#FFFFFF; font-weight:500; font-size:15px; margin-top:4px;">{active_announcement.message}</div>
                </div>
            </div>
            <div style="text-align:right;">
                <span style="background:linear-gradient(135deg,#FFC947,#F59E0B); padding:4px 16px; border-radius:20px; font-size:11px; color:#0A0A0A; font-weight:700;">{active_announcement.created_by}</span>
                <div style="font-size:10px; color:#6A6A6A; margin-top:4px;">{created_date}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ============================================
    # DASHBOARD HEADER
    # ============================================
    st.markdown('<div class="section-header">📊 Dashboard Overview</div>', unsafe_allow_html=True)

    if not gyms and role == "admin":
        st.info("👋 Welcome! Head to **Gym Setup** to create your first gym.")
        return

    stats = db.get_stats(gym_id)

    # ── 5 KPI CARDS ────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">👥 Total Members</div>
            <div class="kpi-value">{stats['total_members']}</div>
            <div class="kpi-subtext">All registered</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        inactive = stats['total_members'] - stats['active_members']
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">✅ Active Members</div>
            <div class="kpi-value">{stats['active_members']}</div>
            <div class="kpi-subtext">{inactive} inactive</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">💰 Month Revenue</div>
            <div class="kpi-value" style="background:linear-gradient(135deg,#FFC947,#F59E0B); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">PKR {stats['month_revenue']:,.0f}</div>
            <div class="kpi-subtext">Total: PKR {stats['total_revenue']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        net = stats["month_revenue"] - stats["month_expenses"]
        net_color = "#1EB980" if net >= 0 else "#FF5A5A"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">📈 Month Net P/L</div>
            <div class="kpi-value" style="background:linear-gradient(135deg,{net_color},{net_color}); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">PKR {net:,.0f}</div>
            <div class="kpi-subtext">Exp: PKR {stats['month_expenses']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        inv_rev = stats.get("inventory_revenue", 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">📦 Inventory Sales</div>
            <div class="kpi-value" style="background:linear-gradient(135deg,#6EE7B7,#34D399); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">PKR {inv_rev:,.0f}</div>
            <div class="kpi-subtext">From POS</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ALERTS SECTION ────────────────────────────────────────────────────────
    bday_members = db.get_birthday_members(days_ahead=3, gym_id=gym_id)
    expiring_now = db.get_expiring_members(days=7, gym_id=gym_id)
    absent_alert = db.get_absent_members(days=3, gym_id=gym_id)
    low_stock = db.get_stock_items(gym_id=gym_id, low_stock_only=True)

    critical = [(m, d) for m, d in expiring_now if d <= 1]
    urgent = [(m, d) for m, d in expiring_now if 2 <= d <= 3]

    st.markdown('<div class="section-header">⚠️ Attention Required</div>', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown('<div class="alert-critical"><strong>🔴 CRITICAL (0-1 DAYS)</strong></div>', unsafe_allow_html=True)
        if critical:
            for m, d in critical[:5]:
                st.write(f"• **{m.full_name}** — {d} day(s) left")
        else:
            st.write("✅ No critical expiries")

    with col_b:
        st.markdown('<div class="alert-urgent"><strong>🟡 URGENT (2-3 DAYS)</strong></div>', unsafe_allow_html=True)
        if urgent:
            for m, d in urgent[:5]:
                st.write(f"• **{m.full_name}** — {d} days left")
        else:
            st.write("✅ No urgent expiries")

    with col_c:
        st.markdown('<div class="alert-absent"><strong>🔵 ABSENT 3+ DAYS</strong></div>', unsafe_allow_html=True)
        if absent_alert:
            for m in absent_alert[:5]:
                st.write(f"• **{m.full_name}**")
        else:
            st.write("✅ Everyone active")

    if bday_members:
        bday_text = "🎂 **Upcoming Birthdays:** " + ", ".join([f"{m.full_name} ({d} day(s))" for m, d in bday_members[:3]])
        st.info(bday_text)
    if low_stock:
        stock_text = "📦 **Low Stock Alert:** " + ", ".join([f"{i.item_name} ({i.quantity} left)" for i in low_stock[:3]])
        st.warning(stock_text)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── LEADERBOARD + PEAK HOUR ──────────────────────────────────────────────
    col_lb, col_ph = st.columns(2)

    with col_lb:
        st.markdown('<div class="section-header">🏆 Monthly Attendance Leaderboard</div>', unsafe_allow_html=True)
        leaderboard = db.get_attendance_leaderboard(gym_id=gym_id, limit=5)
        if leaderboard:
            for rank, entry in enumerate(leaderboard[:5], 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                st.markdown(f"""
                <div class="glass-card" style="display:flex; justify-content:space-between; align-items:center; padding:14px 20px; margin-bottom:10px;">
                    <div style="display:flex; align-items:center; gap:14px;">
                        <span style="font-size:22px; font-weight:800; color:#FFC947;">{medal}</span>
                        <span style="font-weight:600; color:#FFFFFF;">{entry['member'].full_name}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:16px; color:#FFFFFF; font-weight:600;">{entry['count']} sessions</div>
                        <div style="font-size:11px; color:#FFC947;">🔥 {entry['streak']} day streak</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No attendance data yet.")

    with col_ph:
        st.markdown('<div class="section-header">⏰ Peak Hour Analysis</div>', unsafe_allow_html=True)
        hour_data = db.get_attendance_by_hour(gym_id=gym_id)
        if any(hour_data.values()):
            peak_hour = max(hour_data, key=lambda h: hour_data[h])
            peak_count = hour_data[peak_hour]
            am_pm = "AM" if peak_hour < 12 else "PM"
            hour_12 = peak_hour if peak_hour <= 12 else peak_hour - 12
            if hour_12 == 0: hour_12 = 12
            total_att = sum(hour_data.values())

            st.markdown(f"""
            <div class="glass-card" style="text-align:center; padding:40px 20px;">
                <div style="font-size:56px; font-weight:900; background:linear-gradient(135deg,#FFC947,#FF6B6B); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px;">{hour_12}:00 {am_pm}</div>
                <div style="font-size:16px; color:#8A8A8A; margin-bottom:16px;">🔥 {peak_count} check-ins at this hour</div>
                <div style="border-top:1px solid #2A2A2A; padding-top:16px;">
                    <div style="font-size:13px; color:#6A6A6A;">📊 Total Logged: {total_att} all-time entries</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No attendance records yet.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── RECENT SCAN-INS ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🎯 Recent Scan-Ins (Today)</div>', unsafe_allow_html=True)
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MEMBERS & FEE STATUS ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">👥 Members & Fee Status</div>', unsafe_allow_html=True)

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
            status_badge = '<span class="badge-none">⚪ NO FEE</span>'
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
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Members</div>
            <div class="kpi-value">{total_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🟢 Paid</div>
            <div class="kpi-value" style="background:linear-gradient(135deg,#1EB980,#10B981); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{paid_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🟡 Partial</div>
            <div class="kpi-value" style="background:linear-gradient(135deg,#FFC947,#F59E0B); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{partial_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with s4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">🔴 Unpaid</div>
            <div class="kpi-value" style="background:linear-gradient(135deg,#FF5A5A,#EF4444); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{unpaid_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── FILTER BUTTONS ──────────────────────────────────────────────────────
    if "fee_filter" not in st.session_state:
        st.session_state.fee_filter = "all"

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        if st.button(f"📊 All ({total_count})", use_container_width=True,
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ── EXPIRING MEMBERSHIPS ─────────────────────────────────────────────────
    expiring = db.get_expiring_members(days=7, gym_id=gym_id)
    if expiring:
        st.markdown(f'<div class="section-header">⚠️ {len(expiring)} Membership(s) Expiring in 7 Days</div>', unsafe_allow_html=True)

        critical = [x for x in expiring if x[1] <= 1]
        urgent = [x for x in expiring if 2 <= x[1] <= 3]
        soon = [x for x in expiring if x[1] >= 4]

        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown(f"""
            <div class="kpi-card" style="border-left:4px solid #EF4444;">
                <div class="kpi-label">🔴 Critical</div>
                <div class="kpi-value" style="background:linear-gradient(135deg,#EF4444,#DC2626); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{len(critical)}</div>
                <div class="kpi-subtext">Aaj ya kal expire</div>
            </div>
            """, unsafe_allow_html=True)
        with e2:
            st.markdown(f"""
            <div class="kpi-card" style="border-left:4px solid #F59E0B;">
                <div class="kpi-label">🟠 Urgent</div>
                <div class="kpi-value" style="background:linear-gradient(135deg,#F59E0B,#D97706); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{len(urgent)}</div>
                <div class="kpi-subtext">2-3 din mein</div>
            </div>
            """, unsafe_allow_html=True)
        with e3:
            st.markdown(f"""
            <div class="kpi-card" style="border-left:4px solid #3B82F6;">
                <div class="kpi-label">🟡 Soon</div>
                <div class="kpi-value" style="background:linear-gradient(135deg,#3B82F6,#2563EB); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{len(soon)}</div>
                <div class="kpi-subtext">4-7 din mein</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

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

    # ============================================
    # STAFF TARGETS SECTION
    # ============================================
    if role.lower() not in ["admin", "owner"]:
        st.markdown('<div class="section-header">🎯 My Performance Targets</div>', unsafe_allow_html=True)

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
                    prize_color = "#1EB980"
                    prize_emoji = "🏆"
                    prize_text = "🎉 Prize Awarded!"
                elif prize_status == "Pending":
                    prize_color = "#FFC947"
                    prize_emoji = "🎯"
                    prize_text = "⏳ Target In Progress"
                else:
                    prize_color = "#8A8A8A"
                    prize_emoji = "📌"
                    prize_text = "⏳ Not Completed"

                st.markdown(f"""
                <div class="glass-card" style="text-align:center; border:2px solid {prize_color}; padding:36px;">
                    <div style="font-size:52px; margin-bottom:8px;">{prize_emoji}</div>
                    <div style="font-size:22px; font-weight:700; color:#FFFFFF; margin-bottom:8px;">Prize / Inam</div>
                    <div style="font-size:44px; font-weight:900; color:{prize_color}; margin:12px 0;">PKR {prize_amount:,.2f}</div>
                    <div style="font-size:18px; font-weight:600; color:{prize_color}; margin-bottom:8px;">{prize_text}</div>
                    <div style="font-size:14px; color:#8A8A8A;">{progress['completed_targets']}/{progress['total_targets']} targets completed</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">📊 Overall Progress</div>
                        <div class="kpi-value">{overall_pct:.0f}%</div>
                        <div class="kpi-subtext">{progress['completed_targets']}/{progress['total_targets']} targets</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    pct = progress['new_members']['percentage']
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">👤 New Members</div>
                        <div class="kpi-value">{progress['new_members']['achieved']:.0f}/{progress['new_members']['target']:.0f}</div>
                        <div class="kpi-subtext">{pct:.0f}% done</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    pct = progress['fee_collection']['percentage']
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">💰 Fee Collection</div>
                        <div class="kpi-value" style="font-size:24px;">PKR {progress['fee_collection']['achieved']:,.0f}</div>
                        <div class="kpi-subtext">{pct:.0f}% of {progress['fee_collection']['target']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    pct = progress['attendance']['percentage']
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">✅ Attendance</div>
                        <div class="kpi-value">{progress['attendance']['achieved']:.0f}/{progress['attendance']['target']:.0f}</div>
                        <div class="kpi-subtext">{pct:.0f}% done</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**📈 Target Progress**")
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
        else:
            st.info("📝 No targets found. Your admin will assign targets soon!")

    # ============================================
    # STAFF ATTENDANCE SECTION
    # ============================================
    st.markdown('<div class="section-header">👥 Staff Attendance</div>', unsafe_allow_html=True)

    if role.lower() == "admin":
        staff_summary = db.get_staff_attendance_summary(gym_id=gym_id)

        if staff_summary:
            online_count = sum(1 for s in staff_summary if "Online" in s['status'])
            total_staff = len(staff_summary)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">👥 Total Staff</div>
                    <div class="kpi-value">{total_staff}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">🟢 Online Now</div>
                    <div class="kpi-value" style="background:linear-gradient(135deg,#1EB980,#10B981); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{online_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                logins_today = sum(1 for s in staff_summary if s['logins'] > 0)
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">⏳ Today's Logins</div>
                    <div class="kpi-value" style="background:linear-gradient(135deg,#3B82F6,#2563EB); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{logins_today}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

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
        try:
            my_summary = db.get_my_attendance_summary(username)

            if my_summary:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">📅 Today</div>
                        <div class="kpi-value" style="font-size:22px;">{my_summary['today_status']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">📊 This Month</div>
                        <div class="kpi-value">{my_summary['total_days']}</div>
                        <div class="kpi-subtext">days</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">⏱️ Total Hours</div>
                        <div class="kpi-value">{my_summary['total_hours']}h</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">🔥 Streak</div>
                        <div class="kpi-value" style="background:linear-gradient(135deg,#FF6B6B,#EE5A24); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{my_summary['current_streak']}</div>
                        <div class="kpi-subtext">days</div>
                    </div>
                    """, unsafe_allow_html=True)

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
        except Exception as e:
            pass