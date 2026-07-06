import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db
import styles
import gym_pages.ai_assistant as ai_assistant

def render(gym_id, role, username):
    gyms = db.get_all_gyms()

    # ============================================================
    # ULTRA MODERN DARK THEME CSS
    # ============================================================
    st.markdown("""
    <style>
        .stApp { background: #0A0A0A !important; color: #FFFFFF !important; }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #141414; }
        ::-webkit-scrollbar-thumb { background: #FFC947; border-radius: 10px; }

        .glass-card {
            background: rgba(20,20,20,0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,201,71,0.08);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .glass-card:hover {
            border-color: #FFC947;
            transform: translateY(-4px);
            box-shadow: 0 12px 48px rgba(255,201,71,0.15);
        }

        .kpi-card {
            background: linear-gradient(145deg,#141414,#1A1A1A);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px 16px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg,#FFC947,#FF6B6B,#FFC947);
            background-size: 200% 100%;
            animation: shimmer 3s ease-in-out infinite;
        }
        @keyframes shimmer {
            0%   { background-position: -200% 0; }
            100% { background-position:  200% 0; }
        }
        .kpi-card:hover {
            transform: translateY(-6px);
            border-color: #FFC947;
            box-shadow: 0 8px 30px rgba(255,201,71,0.15);
        }
        .kpi-label  { font-size:11px; text-transform:uppercase; letter-spacing:1.5px; color:#8A8A8A; font-weight:600; }
        .kpi-value  { font-size:34px; font-weight:800;
                      background:linear-gradient(135deg,#FFFFFF 0%,#FFC947 100%);
                      -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                      margin:8px 0; }
        .kpi-subtext { font-size:11px; color:#6A6A6A; }

        .badge-paid    { background:linear-gradient(135deg,#1EB980,#10B981); color:white; padding:4px 14px; border-radius:20px; font-size:11px; font-weight:700; }
        .badge-partial { background:linear-gradient(135deg,#FFC947,#F59E0B); color:#0A0A0A; padding:4px 14px; border-radius:20px; font-size:11px; font-weight:700; }
        .badge-unpaid  { background:linear-gradient(135deg,#FF5A5A,#EF4444); color:white; padding:4px 14px; border-radius:20px; font-size:11px; font-weight:700; }
        .badge-none    { background:#2A2A2A; color:#8A8A8A; padding:4px 14px; border-radius:20px; font-size:11px; font-weight:700; }

        .alert-critical { background:rgba(239,68,68,0.08); border-left:4px solid #EF4444; border-radius:12px; padding:16px 20px; margin:8px 0; }
        .alert-urgent   { background:rgba(245,158,11,0.08); border-left:4px solid #F59E0B; border-radius:12px; padding:16px 20px; margin:8px 0; }
        .alert-absent   { background:rgba(59,130,246,0.08); border-left:4px solid #3B82F6; border-radius:12px; padding:16px 20px; margin:8px 0; }

        .announce-banner {
            background:linear-gradient(135deg,#1A1A1A,#0F0F0F);
            border:1px solid #FFC947;
            border-radius:16px;
            padding:16px 24px;
            margin-bottom:20px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 4px 20px rgba(255,201,71,0.05);
        }

        .section-header {
            font-size:18px; font-weight:700; color:#FFFFFF;
            margin:24px 0 16px 0;
            padding-bottom:10px;
            border-bottom:2px solid rgba(255,201,71,0.15);
            display:flex; align-items:center; gap:10px;
        }
        .section-header::after { content:''; flex:1; height:1px; background:linear-gradient(90deg,rgba(255,201,71,0.3),transparent); }

        .stButton > button {
            background:linear-gradient(135deg,#FFC947,#F59E0B);
            color:#0A0A0A; border:none; border-radius:12px;
            font-weight:700; padding:10px 24px;
            transition:all 0.3s ease;
            box-shadow:0 4px 15px rgba(255,201,71,0.2);
        }
        .stButton > button:hover { transform:translateY(-2px); box-shadow:0 8px 30px rgba(255,201,71,0.3); }

        .dataframe { background:#141414 !important; border:1px solid #2A2A2A !important; border-radius:12px !important; }
        .dataframe thead { background:#1A1A1A !important; }
        .dataframe th  { color:#FFC947 !important; font-weight:600 !important; padding:12px !important; }
        .dataframe td  { padding:10px 12px !important; color:#E0E0E0 !important; }
        .dataframe tr:hover { background:rgba(255,201,71,0.05) !important; }

        .streamlit-expanderHeader {
            background:#141414 !important; border:1px solid #2A2A2A !important;
            border-radius:12px !important; color:#FFFFFF !important; font-weight:600 !important;
        }
        .streamlit-expanderHeader:hover { border-color:#FFC947 !important; }

        .stTextInput > div > div > input {
            background:#141414 !important; border:1px solid #2A2A2A !important;
            border-radius:12px !important; color:#FFFFFF !important; padding:12px 16px !important;
        }
        .stTextInput > div > div > input:focus { border-color:#FFC947 !important; }

        .stSelectbox > div > div { background:#141414 !important; border:1px solid #2A2A2A !important; border-radius:12px !important; }
        .stProgress > div > div  { background:linear-gradient(90deg,#FFC947,#FF6B6B) !important; border-radius:20px !important; }
        .stAlert { border-radius:12px !important; border:none !important; }
    </style>
    """, unsafe_allow_html=True)

    # ============================================================
    # FRAUD ALERT BANNER (admin/owner only)
    # ============================================================
    if role.lower() in ["admin", "owner"]:
        try:
            alerts = db.check_fraud_alerts(gym_id=gym_id)
            if alerts:
                critical = [a for a in alerts if a["severity"] == "critical"]
                warnings  = [a for a in alerts if a["severity"] == "warning"]
                header_color = "#7F1D1D" if critical else "#78350F"
                border_color = "#EF4444" if critical else "#F59E0B"
                title_color  = "#FCA5A5" if critical else "#FCD34D"
                title_text   = (f"🚨 {len(critical)} CRITICAL ALERT{'S' if len(critical)!=1 else ''} — Fori Attention Chahiye!"
                                if critical else
                                f"⚠️ {len(warnings)} Suspicious Activity Alert{'s' if len(warnings)!=1 else ''} Aaj")
                rows_html = ""
                for a in alerts:
                    bg = "#450A0A" if a["severity"] == "critical" else "#422006"
                    bc = "#EF4444" if a["severity"] == "critical" else "#F59E0B"
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

    # ============================================================
    # STAFF AI COACH (staff only)
    # ============================================================
    if role.lower() == "staff":
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                    border:1px solid #3B82F6;border-radius:14px;
                    padding:0.75rem 1rem;margin-bottom:0.75rem;">
            <span style="color:#60A5FA;font-weight:700;font-size:1rem;">🤖 AI Performance Coach</span>
            <span style="color:#94A3B8;font-size:0.8rem;"> — Aaj aapki performance ka live analysis</span>
        </div>
        """, unsafe_allow_html=True)
        try:
            ai_assistant.render_staff_ai_coach(username=username, role=role, gym_id=gym_id)
        except Exception as _e:
            st.warning(f"AI Coach load nahi hua: {_e}")
        st.divider()

    # ============================================================
    # HERO GREETING BANNER
    # ============================================================
    now  = datetime.now()
    hour = now.hour
    if hour < 12:    greeting, g_emoji = "Assalam-o-Alaikum", "🌅"
    elif hour < 17:  greeting, g_emoji = "Good Afternoon",    "☀️"
    else:             greeting, g_emoji = "Good Evening",      "🌙"

    _gym_label = "All Gyms"
    if gym_id and gyms:
        _gym_label = next((g.name for g in gyms if g.id == gym_id), "All Gyms")

    _rbadges = {
        "admin":   ("👑 Admin",   "#FFC947"),
        "staff":   ("🎯 Staff",   "#10B981"),
        "auditor": ("🔍 Auditor", "#3B82F6"),
        "owner":   ("🏆 Owner",   "#8B5CF6"),
    }
    rbadge, rbcolor = _rbadges.get(role.lower(), ("👤 User", "#8A8A8A"))

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#141414,#1A1A2E);
         border:1px solid rgba(255,201,71,0.25);border-radius:20px;
         padding:1.4rem 2rem;margin-bottom:1.2rem;
         box-shadow:0 4px 28px rgba(0,0,0,0.55);">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
        <div>
          <div style="font-size:0.78rem;color:#6A6A6A;letter-spacing:1px;text-transform:uppercase;">
            {g_emoji} {greeting}
          </div>
          <div style="font-size:1.75rem;font-weight:800;color:#FFFFFF;margin:3px 0;">
            {username}
            <span style="background:{rbcolor};color:#000;font-size:0.65rem;padding:3px 12px;
                   border-radius:20px;font-weight:700;margin-left:8px;vertical-align:middle;">{rbadge}</span>
          </div>
          <div style="font-size:0.95rem;color:#FFC947;font-weight:600;">🏋️ {_gym_label}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:1.6rem;font-weight:700;color:#FFFFFF;">{now.strftime('%I:%M %p')}</div>
          <div style="font-size:0.82rem;color:#6A6A6A;">{now.strftime('%A, %d %B %Y')}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Active announcement banner ────────────────────────────────────────────
    active_ann = db.get_active_announcement(gym_id=gym_id)
    if active_ann:
        _cd = active_ann.created_at.strftime('%d %b %Y') if active_ann.created_at else ''
        st.markdown(f"""
        <div class="announce-banner">
            <div style="display:flex;align-items:center;gap:16px;">
                <span style="font-size:26px;">📢</span>
                <div>
                    <div style="color:#FFC947;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;">★ ANNOUNCEMENT</div>
                    <div style="color:#FFFFFF;font-weight:500;font-size:15px;margin-top:3px;">{active_ann.message}</div>
                </div>
            </div>
            <div style="text-align:right;">
                <span style="background:linear-gradient(135deg,#FFC947,#F59E0B);padding:4px 14px;
                       border-radius:20px;font-size:11px;color:#0A0A0A;font-weight:700;">{active_ann.created_by}</span>
                <div style="font-size:10px;color:#6A6A6A;margin-top:4px;">{_cd}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if not gyms and role == "admin":
        st.info("👋 Welcome! Head to **Gym Setup** to create your first gym.")
        return

    # ============================================================
    # TABS
    # ============================================================
    stats = db.get_stats(gym_id)
    tab_home, tab_alerts, tab_members, tab_activity, tab_staff = st.tabs([
        "🏠 Overview", "🚨 Alerts", "👥 Members", "📊 Activity", "👔 Staff"
    ])

    # ════════════════════════════════════════════════════════════
    # TAB 1 — OVERVIEW
    # ════════════════════════════════════════════════════════════
    with tab_home:
        # 5 KPI cards
        inactive  = stats['total_members'] - stats['active_members']
        net       = stats["month_revenue"] - stats["month_expenses"]
        net_color = "#1EB980" if net >= 0 else "#FF5A5A"
        inv_rev   = stats.get("inventory_revenue", 0)

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:1.8rem;margin-bottom:6px;">👥</div>
                <div class="kpi-label">Total Members</div>
                <div class="kpi-value">{stats['total_members']}</div>
                <div class="kpi-subtext">{inactive} inactive</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:1.8rem;margin-bottom:6px;">✅</div>
                <div class="kpi-label">Active</div>
                <div class="kpi-value" style="color:#10B981;">{stats['active_members']}</div>
                <div class="kpi-subtext">Active members</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:1.8rem;margin-bottom:6px;">💰</div>
                <div class="kpi-label">Month Revenue</div>
                <div class="kpi-value" style="font-size:20px;background:linear-gradient(135deg,#FFC947,#F59E0B);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                  PKR {stats['month_revenue']:,.0f}</div>
                <div class="kpi-subtext">Total: PKR {stats['total_revenue']:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:1.8rem;margin-bottom:6px;">📈</div>
                <div class="kpi-label">Net P/L</div>
                <div class="kpi-value" style="font-size:20px;color:{net_color};">PKR {net:,.0f}</div>
                <div class="kpi-subtext">Exp: PKR {stats['month_expenses']:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with c5:
            st.markdown(f"""<div class="kpi-card">
                <div style="font-size:1.8rem;margin-bottom:6px;">📦</div>
                <div class="kpi-label">Inventory Sales</div>
                <div class="kpi-value" style="font-size:20px;background:linear-gradient(135deg,#6EE7B7,#34D399);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                  PKR {inv_rev:,.0f}</div>
                <div class="kpi-subtext">From POS</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Today's Snapshot
        st.markdown('<div class="section-header">📅 Today\'s Snapshot</div>', unsafe_allow_html=True)
        try:
            att_today     = db.get_attendance(gym_id=gym_id, check_date=date.today())
            present_today = sum(1 for a in att_today if a.status == "Present")
        except Exception:
            present_today = 0
        att_pct       = round(present_today / stats['active_members'] * 100) if stats['active_members'] else 0
        try:
            todays_fees_l = db.get_todays_fees(gym_id=gym_id)
            fees_today    = sum(todays_fees_l) if todays_fees_l else 0
        except Exception:
            fees_today = 0
        try:
            exp3_count    = len(db.get_expiring_members(days=3, gym_id=gym_id))
            absent3_count = len(db.get_absent_members(days=3, gym_id=gym_id))
        except Exception:
            exp3_count = absent3_count = 0

        sn1, sn2, sn3, sn4 = st.columns(4)
        with sn1:
            st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #10B981;">
                <div style="font-size:1.5rem;">🏃</div>
                <div class="kpi-label">Attendance Today</div>
                <div class="kpi-value" style="color:#10B981;">{present_today}</div>
                <div class="kpi-subtext">{att_pct}% checked in</div>
            </div>""", unsafe_allow_html=True)
        with sn2:
            st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #FFC947;">
                <div style="font-size:1.5rem;">💵</div>
                <div class="kpi-label">Fees Today</div>
                <div class="kpi-value" style="font-size:18px;color:#FFC947;">PKR {fees_today:,.0f}</div>
                <div class="kpi-subtext">Today's collection</div>
            </div>""", unsafe_allow_html=True)
        with sn3:
            st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #EF4444;">
                <div style="font-size:1.5rem;">⏰</div>
                <div class="kpi-label">Expiring (3d)</div>
                <div class="kpi-value" style="color:#EF4444;">{exp3_count}</div>
                <div class="kpi-subtext">Need renewal now</div>
            </div>""", unsafe_allow_html=True)
        with sn4:
            st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #3B82F6;">
                <div style="font-size:1.5rem;">🚨</div>
                <div class="kpi-label">Absent 3+ Days</div>
                <div class="kpi-value" style="color:#3B82F6;">{absent3_count}</div>
                <div class="kpi-subtext">At-risk members</div>
            </div>""", unsafe_allow_html=True)

        # Post Announcement (admin/owner)
        if role.lower() in ["admin", "owner"] and gyms:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📢 Post Announcement", expanded=False):
                with st.form("announcement_form", clear_on_submit=True):
                    if gym_id:
                        sel_gid  = gym_id
                        _gnm     = next((g.name for g in gyms if g.id == gym_id), "")
                        st.text_input("🏋️ Gym", value=_gnm, disabled=True)
                    else:
                        _opts   = {"All Gyms": None} | {g.name: g.id for g in gyms}
                        _chosen = st.selectbox("🏋️ Gym", list(_opts.keys()))
                        sel_gid = _opts[_chosen]
                    message   = st.text_area("📝 Message", placeholder="Type announcement here...", height=70)
                    ce1, ce2  = st.columns(2)
                    with ce1:
                        set_expiry = st.checkbox("Set Expiry Date")
                    with ce2:
                        expiry_date = st.date_input("Expiry", value=date.today() + timedelta(days=7)) if set_expiry else None
                    if st.form_submit_button("📢 Post", type="primary", use_container_width=True):
                        if not message.strip():
                            st.error("❌ Please enter a message!")
                        else:
                            expires_at = datetime.combine(expiry_date, datetime.min.time()) if expiry_date else None
                            ok, msg    = db.add_announcement(sel_gid, message, username, expires_at)
                            if ok:
                                st.success("✅ Posted!")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")

    # ════════════════════════════════════════════════════════════
    # TAB 2 — ALERTS
    # ════════════════════════════════════════════════════════════
    with tab_alerts:
        try:
            bday_members = db.get_birthday_members(days_ahead=7, gym_id=gym_id)
        except Exception:
            bday_members = []
        try:
            expiring = db.get_expiring_members(days=7, gym_id=gym_id)
        except Exception:
            expiring = []
        try:
            absent_alert = db.get_absent_members(days=3, gym_id=gym_id)
        except Exception:
            absent_alert = []
        try:
            low_stock = db.get_stock_items(gym_id=gym_id, low_stock_only=True)
        except Exception:
            low_stock = []

        # Summary KPI bar
        crit_count   = sum(1 for _, d in expiring if d <= 1)
        urgent_count = sum(1 for _, d in expiring if 2 <= d <= 3)

        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #EF4444;">
                <div class="kpi-label">🔴 Critical Expiry</div>
                <div class="kpi-value" style="color:#EF4444;">{crit_count}</div>
                <div class="kpi-subtext">0–1 days</div>
            </div>""", unsafe_allow_html=True)
        with a2:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #F59E0B;">
                <div class="kpi-label">🟠 Urgent Expiry</div>
                <div class="kpi-value" style="color:#F59E0B;">{urgent_count}</div>
                <div class="kpi-subtext">2–3 days</div>
            </div>""", unsafe_allow_html=True)
        with a3:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #3B82F6;">
                <div class="kpi-label">🔵 Absent 3+ Days</div>
                <div class="kpi-value" style="color:#3B82F6;">{len(absent_alert)}</div>
                <div class="kpi-subtext">At-risk members</div>
            </div>""", unsafe_allow_html=True)
        with a4:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #8B5CF6;">
                <div class="kpi-label">🎂 Birthdays Soon</div>
                <div class="kpi-value" style="color:#8B5CF6;">{len(bday_members)}</div>
                <div class="kpi-subtext">Within 7 days</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Expiring memberships — visual cards
        if expiring:
            st.markdown(f'<div class="section-header">⏰ {len(expiring)} Membership(s) Expiring in 7 Days</div>', unsafe_allow_html=True)
            for m, days_left in expiring[:20]:
                if days_left <= 1:
                    bg_c, bd_c, urg = "#1A0000", "#EF4444", "🔴 CRITICAL"
                elif days_left <= 3:
                    bg_c, bd_c, urg = "#1A0F00", "#F59E0B", "🟠 URGENT"
                else:
                    bg_c, bd_c, urg = "#0A0A1A", "#3B82F6", "🟡 SOON"
                exp_txt = "TODAY!" if days_left == 0 else f"{days_left} day{'s' if days_left != 1 else ''} left"
                st.markdown(f"""
                <div style="background:{bg_c};border-left:4px solid {bd_c};border-radius:10px;
                     padding:12px 18px;margin-bottom:8px;
                     display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-weight:700;color:#F8FAFC;font-size:0.95rem;">{m.full_name}</div>
                        <div style="color:#94A3B8;font-size:0.8rem;">
                            🆔 {m.serial_number} &nbsp;·&nbsp; 📞 {m.phone or '—'} &nbsp;·&nbsp; {m.membership_type or '—'}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.72rem;color:{bd_c};font-weight:700;">{urg}</div>
                        <div style="font-size:1rem;color:#FFFFFF;font-weight:700;">{exp_txt}</div>
                        <div style="font-size:0.7rem;color:#6A6A6A;">Expires: {m.expiry_date}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.info("💡 Critical members ko foran call/WhatsApp karein renewal ke liye!")
        else:
            st.success("✅ No memberships expiring in the next 7 days!")

        st.divider()

        # Absent members — photo grid
        if absent_alert:
            st.markdown(f'<div class="section-header">🚨 {len(absent_alert)} Members Absent 3+ Days</div>', unsafe_allow_html=True)
            COLS = 4
            for i in range(0, min(len(absent_alert), 16), COLS):
                row_ms   = absent_alert[i:i + COLS]
                row_cols = st.columns(COLS)
                for j, m in enumerate(row_ms):
                    with row_cols[j]:
                        photo_html = '<div style="font-size:2.5rem;text-align:center;line-height:1;">👤</div>'
                        if m.photo_path:
                            try:
                                import base64 as _b64, os as _os
                                photo_str = str(m.photo_path).strip()
                                if "<div" not in photo_str:
                                    fn = _os.path.basename(photo_str)
                                    for pp in [f"gym-app/uploads/{fn}", photo_str]:
                                        if pp and _os.path.exists(pp):
                                            from PIL import Image as _Img
                                            import io as _io
                                            _img = _Img.open(pp).convert("RGB")
                                            _img.thumbnail((80, 80))
                                            _buf = _io.BytesIO()
                                            _img.save(_buf, format="JPEG", quality=70)
                                            _b = _b64.b64encode(_buf.getvalue()).decode()
                                            photo_html = f'<div style="text-align:center;"><img src="data:image/jpeg;base64,{_b}" style="width:56px;height:56px;border-radius:50%;object-fit:cover;border:2px solid #3B82F6;"></div>'
                                            break
                            except Exception:
                                pass
                        st.markdown(f"""
                        <div style="background:#0A0A1A;border:1px solid #3B82F6;border-radius:12px;
                             padding:10px 8px;text-align:center;margin-bottom:8px;">
                            {photo_html}
                            <div style="color:#F8FAFC;font-weight:700;font-size:0.8rem;margin-top:6px;
                                 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{m.full_name}</div>
                            <div style="color:#94A3B8;font-size:0.68rem;">{m.serial_number}</div>
                            <div style="color:#3B82F6;font-size:0.68rem;">{m.membership_type or '—'}</div>
                        </div>""", unsafe_allow_html=True)
        else:
            st.success("✅ No members absent for 3+ consecutive days!")

        st.divider()

        # Birthdays + Low stock
        col_bday, col_stock = st.columns(2)
        with col_bday:
            st.markdown("#### 🎂 Upcoming Birthdays (7 days)")
            if bday_members:
                for m, d in bday_members[:6]:
                    st.markdown(f"🎁 **{m.full_name}** — {d} day{'s' if d != 1 else ''} away")
            else:
                st.info("No upcoming birthdays.")
        with col_stock:
            st.markdown("#### 📦 Low Stock Items")
            if low_stock:
                for item in low_stock[:6]:
                    pct = round(item.quantity / max(item.min_quantity, 1) * 100) if hasattr(item, 'min_quantity') else 0
                    st.markdown(f"⚠️ **{item.item_name}** — {item.quantity} remaining")
            else:
                st.success("✅ All stock levels OK.")

    # ════════════════════════════════════════════════════════════
    # TAB 3 — MEMBERS (fee status)
    # ════════════════════════════════════════════════════════════
    with tab_members:
        all_members = db.get_members(gym_id=gym_id)
        all_fees    = db.get_fee_records(gym_id=gym_id)

        member_paid = {}
        for f in all_fees:
            member_paid[f.member_id] = member_paid.get(f.member_id, 0) + f.amount

        unified_rows = []
        for m in all_members:
            expected_fee = getattr(m, "fee_amount", 0) or 0
            paid         = member_paid.get(m.id, 0)
            pending      = max(expected_fee - paid, 0)

            if expected_fee == 0 and paid == 0:
                status_badge = '<span class="badge-none">⚪ NO FEE</span>'
                status_key   = "none"
            elif paid >= expected_fee and expected_fee > 0:
                status_badge = '<span class="badge-paid">🟢 PAID</span>'
                status_key   = "paid"
            elif paid > 0:
                status_badge = '<span class="badge-partial">🟡 PARTIAL</span>'
                status_key   = "partial"
            else:
                status_badge = '<span class="badge-unpaid">🔴 UNPAID</span>'
                status_key   = "unpaid"

            unified_rows.append({
                "Serial":  m.serial_number,
                "Name":    m.full_name,
                "Phone":   m.phone or "—",
                "Type":    m.membership_type,
                "Fee":     f"PKR {expected_fee:,.0f}",
                "Paid":    f"PKR {paid:,.0f}",
                "Pending": f"PKR {pending:,.0f}",
                "Status":  status_badge,
                "_status_key": status_key,
            })

        total_count   = len(unified_rows)
        paid_count    = sum(1 for r in unified_rows if r["_status_key"] == "paid")
        unpaid_count  = sum(1 for r in unified_rows if r["_status_key"] == "unpaid")
        partial_count = sum(1 for r in unified_rows if r["_status_key"] == "partial")

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">👥 Total</div>
                <div class="kpi-value">{total_count}</div>
            </div>""", unsafe_allow_html=True)
        with s2:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">🟢 Paid</div>
                <div class="kpi-value" style="color:#1EB980;">{paid_count}</div>
            </div>""", unsafe_allow_html=True)
        with s3:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">🟡 Partial</div>
                <div class="kpi-value" style="color:#FFC947;">{partial_count}</div>
            </div>""", unsafe_allow_html=True)
        with s4:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">🔴 Unpaid</div>
                <div class="kpi-value" style="color:#FF5A5A;">{unpaid_count}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if "fee_filter" not in st.session_state:
            st.session_state.fee_filter = "all"

        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            if st.button(f"📊 All ({total_count})", use_container_width=True,
                         type="primary" if st.session_state.fee_filter == "all" else "secondary"):
                st.session_state.fee_filter = "all"; st.rerun()
        with fc2:
            if st.button(f"🟢 Paid ({paid_count})", use_container_width=True,
                         type="primary" if st.session_state.fee_filter == "paid" else "secondary"):
                st.session_state.fee_filter = "paid"; st.rerun()
        with fc3:
            if st.button(f"🟡 Partial ({partial_count})", use_container_width=True,
                         type="primary" if st.session_state.fee_filter == "partial" else "secondary"):
                st.session_state.fee_filter = "partial"; st.rerun()
        with fc4:
            if st.button(f"🔴 Unpaid ({unpaid_count})", use_container_width=True,
                         type="primary" if st.session_state.fee_filter == "unpaid" else "secondary"):
                st.session_state.fee_filter = "unpaid"; st.rerun()

        search_query = st.text_input("🔍 Search by Name / Serial", placeholder="Type to search...", key="dash_mem_search")

        filtered_rows = [r for r in unified_rows
                         if st.session_state.fee_filter == "all" or r["_status_key"] == st.session_state.fee_filter]
        if search_query:
            q = search_query.lower()
            filtered_rows = [r for r in filtered_rows if q in r["Name"].lower() or q in r["Serial"].lower()]

        if filtered_rows:
            display_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in filtered_rows[:30]]
            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
            st.caption(f"📋 {len(display_rows)} of {len(filtered_rows)} members")
        else:
            st.info("No members found matching your filter.")

    # ════════════════════════════════════════════════════════════
    # TAB 4 — ACTIVITY
    # ════════════════════════════════════════════════════════════
    with tab_activity:
        col_lb, col_ph = st.columns(2)

        with col_lb:
            st.markdown('<div class="section-header">🏆 Monthly Leaderboard</div>', unsafe_allow_html=True)
            try:
                leaderboard = db.get_attendance_leaderboard(gym_id=gym_id, limit=6)
            except Exception:
                leaderboard = []
            if leaderboard:
                for rank, entry in enumerate(leaderboard, 1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                    st.markdown(f"""
                    <div class="glass-card" style="display:flex;justify-content:space-between;align-items:center;
                         padding:12px 18px;margin-bottom:8px;">
                        <div style="display:flex;align-items:center;gap:12px;">
                            <span style="font-size:1.3rem;font-weight:800;color:#FFC947;">{medal}</span>
                            <span style="font-weight:600;color:#FFFFFF;">{entry['member'].full_name}</span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.95rem;color:#FFFFFF;font-weight:600;">{entry['count']} days</div>
                            <div style="font-size:0.75rem;color:#FFC947;">🔥 {entry['streak']}d streak</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("No attendance data yet.")

        with col_ph:
            st.markdown('<div class="section-header">⏰ Peak Hour</div>', unsafe_allow_html=True)
            try:
                hour_data = db.get_attendance_by_hour(gym_id=gym_id)
            except Exception:
                hour_data = {}
            if hour_data and any(hour_data.values()):
                peak_hour  = max(hour_data, key=lambda h: hour_data[h])
                peak_count = hour_data[peak_hour]
                am_pm      = "AM" if peak_hour < 12 else "PM"
                hour_12    = peak_hour % 12 or 12
                total_att  = sum(hour_data.values())
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;padding:32px 20px;">
                    <div style="font-size:48px;font-weight:900;
                         background:linear-gradient(135deg,#FFC947,#FF6B6B);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                        {hour_12}:00 {am_pm}
                    </div>
                    <div style="font-size:14px;color:#8A8A8A;margin:10px 0;">🔥 Peak — {peak_count} check-ins all-time</div>
                    <div style="border-top:1px solid #2A2A2A;padding-top:14px;font-size:12px;color:#6A6A6A;">
                        📊 {total_att} total attendance logs
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.info("No attendance records yet.")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="section-header">🎯 Recent Check-ins (Today)</div>', unsafe_allow_html=True)
        try:
            scans = db.get_recent_scans(gym_id=gym_id, limit=15, today_only=True)
        except Exception:
            scans = []
        if scans:
            scan_df = pd.DataFrame([{
                "Time":      s["time"],
                "Member":    s["name"],
                "Serial":    s["serial"],
                "Marked By": s["marked_by"],
            } for s in scans])
            st.dataframe(scan_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No check-ins yet today.")

    # ════════════════════════════════════════════════════════════
    # TAB 5 — STAFF
    # ════════════════════════════════════════════════════════════
    with tab_staff:

        # Performance targets (non-admin)
        if role.lower() not in ["admin", "owner"]:
            st.markdown('<div class="section-header">🎯 My Performance Targets</div>', unsafe_allow_html=True)
            current_month = date.today().strftime("%Y-%m")
            try:
                progress = db.get_staff_progress(username, current_month)
            except Exception:
                progress = None

            if progress:
                targets_exist = any([
                    progress['new_members']['target'] > 0,
                    progress['fee_collection']['target'] > 0,
                    progress['attendance']['target'] > 0,
                ])
                if targets_exist:
                    overall_pct  = progress['overall']
                    prize_amount = progress.get('prize_amount', 0)
                    prize_status = progress.get('prize_status', 'Pending')
                    if prize_status == "Awarded":
                        prize_color, prize_emoji, prize_text = "#1EB980", "🏆", "🎉 Prize Awarded!"
                    elif prize_status == "Pending":
                        prize_color, prize_emoji, prize_text = "#FFC947", "🎯", "⏳ In Progress"
                    else:
                        prize_color, prize_emoji, prize_text = "#8A8A8A", "📌", "⏳ Not Completed"

                    st.markdown(f"""
                    <div class="glass-card" style="text-align:center;border:2px solid {prize_color};padding:28px;">
                        <div style="font-size:44px;">{prize_emoji}</div>
                        <div style="font-size:18px;font-weight:700;color:#FFFFFF;margin:8px 0;">Prize / Inam</div>
                        <div style="font-size:38px;font-weight:900;color:{prize_color};">PKR {prize_amount:,.0f}</div>
                        <div style="font-size:15px;font-weight:600;color:{prize_color};">{prize_text}</div>
                        <div style="font-size:12px;color:#8A8A8A;margin-top:8px;">
                            {progress['completed_targets']}/{progress['total_targets']} targets completed
                        </div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**📈 Target Progress**")
                    pct = min(100, progress['new_members']['percentage'])
                    st.progress(pct / 100, text=f"👤 New Members: {pct:.0f}% ({progress['new_members']['achieved']:.0f}/{progress['new_members']['target']:.0f})")
                    pct = min(100, progress['fee_collection']['percentage'])
                    st.progress(pct / 100, text=f"💰 Fee Collection: {pct:.0f}%")
                    pct = min(100, progress['attendance']['percentage'])
                    st.progress(pct / 100, text=f"✅ Attendance: {pct:.0f}%")

                    if overall_pct >= 100:
                        st.balloons()
                        st.success(f"🎉 Congratulations! Prize won: PKR {prize_amount:,.0f}! 🏆")
                    elif overall_pct >= 80:
                        st.success("🏆 Excellent! Almost there — push hard!")
                    elif overall_pct >= 50:
                        st.info("💪 Good progress! Keep pushing!")
                    else:
                        st.info("🎯 Keep working towards your monthly targets!")
                else:
                    st.info("📝 No targets assigned for this month yet.")
            else:
                st.info("📝 No targets found. Your admin will assign targets soon!")

            st.divider()

        # Staff attendance
        st.markdown('<div class="section-header">👥 Staff Attendance</div>', unsafe_allow_html=True)

        if role.lower() in ["admin", "owner"]:
            try:
                staff_summary = db.get_staff_attendance_summary(gym_id=gym_id)
            except Exception:
                staff_summary = []

            if staff_summary:
                online_count = sum(1 for s in staff_summary if "Online" in s['status'])
                total_staff  = len(staff_summary)
                logins_today = sum(1 for s in staff_summary if s['logins'] > 0)

                sa1, sa2, sa3 = st.columns(3)
                with sa1:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-label">👥 Total Staff</div>
                        <div class="kpi-value">{total_staff}</div>
                    </div>""", unsafe_allow_html=True)
                with sa2:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-label">🟢 Online Now</div>
                        <div class="kpi-value" style="color:#1EB980;">{online_count}</div>
                    </div>""", unsafe_allow_html=True)
                with sa3:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kpi-label">⏳ Today's Logins</div>
                        <div class="kpi-value" style="color:#3B82F6;">{logins_today}</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                staff_data = [{
                    "Name":        s['full_name'],
                    "Role":        s['role'],
                    "Status":      s['status'],
                    "Today":       s['today_status'],
                    "Logins(30d)": s['logins'],
                    "Hours":       f"{s['total_hours']}h",
                } for s in staff_summary]
                st.dataframe(pd.DataFrame(staff_data), use_container_width=True, hide_index=True)
            else:
                st.info("No staff attendance data available.")

        else:
            try:
                my_summary = db.get_my_attendance_summary(username)
                if my_summary:
                    ms1, ms2, ms3, ms4 = st.columns(4)
                    with ms1:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">📅 Today</div>
                            <div class="kpi-value" style="font-size:18px;">{my_summary['today_status']}</div>
                        </div>""", unsafe_allow_html=True)
                    with ms2:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">📊 This Month</div>
                            <div class="kpi-value">{my_summary['total_days']}</div>
                            <div class="kpi-subtext">days</div>
                        </div>""", unsafe_allow_html=True)
                    with ms3:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">⏱️ Total Hours</div>
                            <div class="kpi-value">{my_summary['total_hours']}h</div>
                        </div>""", unsafe_allow_html=True)
                    with ms4:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">🔥 Streak</div>
                            <div class="kpi-value" style="color:#FF6B6B;">{my_summary['current_streak']}</div>
                            <div class="kpi-subtext">days</div>
                        </div>""", unsafe_allow_html=True)
                    if my_summary.get('today_login'):
                        st.caption(f"Logged in at: {my_summary['today_login']}")

                with st.expander("📋 My Attendance History (30 days)", expanded=False):
                    history = db.get_staff_attendance(
                        staff_username=username,
                        date_from=date.today() - timedelta(days=30)
                    )
                    if history:
                        rows = [{
                            "Date":     r.login_time.strftime("%Y-%m-%d"),
                            "Login":    r.login_time.strftime("%I:%M %p"),
                            "Logout":   r.logout_time.strftime("%I:%M %p") if r.logout_time else "—",
                            "Duration": f"{r.session_duration or 0} min",
                            "Status":   "🟢 Online" if r.logout_time is None else "⚫ Offline",
                        } for r in history[:30]]
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("No attendance records found.")
            except Exception as e:
                st.warning(f"Could not load attendance: {e}")
