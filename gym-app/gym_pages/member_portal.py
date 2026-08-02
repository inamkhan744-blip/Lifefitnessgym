"""
GymPro Member Portal
Member apni serial number + phone se login karein aur sab kuch dekh sakein:
- Profile & fee status
- Attendance mark karna + calendar
- Progress charts
- AI Diet Plan
- AI Exercise Coach
"""

import streamlit as st
import database as db
import os
import re
import hashlib
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _mp_member():
    """Return the logged-in portal member object, or None."""
    mid = st.session_state.get("portal_member_id")
    if not mid:
        return None
    return db.get_member(mid)


def _mp_logout():
    for k in ["portal_member_id", "portal_member_serial", "mp_chat", "mp_diet_plan",
              "mp_workout_plan", "mp_exercise_input", "mp_diet_done"]:
        st.session_state.pop(k, None)
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# AI HELPER  (Groq)
# ─────────────────────────────────────────────────────────────────────────────

def _groq(messages: list, temperature=0.7, max_tokens=1800) -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return "⚠️ GROQ_API_KEY set nahi hai — AI features unavailable."
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama3-8b-8192", "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            timeout=30,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ AI error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE CODE  (deterministic daily code — member shows to staff)
# ─────────────────────────────────────────────────────────────────────────────

def _daily_code(member_id: int) -> str:
    seed = f"{member_id}-{date.today().isoformat()}-GYMPRO"
    h = hashlib.sha256(seed.encode()).hexdigest()
    return h[:6].upper()


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

PORTAL_CSS = """
<style>
/* ── Base ─────────────────────────────────────────────────────── */
.mp-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.mp-stat {
    background: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    margin-bottom: 0.5rem;
}
.mp-stat-val { font-size: 2rem; font-weight: 800; margin: 0; }
.mp-stat-lbl { font-size: 0.75rem; color: #94A3B8; margin: 0; text-transform: uppercase; letter-spacing: 1px; }

/* ── Status badges ────────────────────────────────────────────── */
.badge-active   { background:#064e3b; color:#34d399; padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; display:inline-block; }
.badge-expired  { background:#450a0a; color:#f87171; padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; display:inline-block; }
.badge-inactive { background:#1e1b4b; color:#a78bfa; padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; display:inline-block; }
.badge-frozen   { background:#0c1a2e; color:#60a5fa; padding:4px 14px; border-radius:20px; font-size:0.8rem; font-weight:700; display:inline-block; }

/* ── Profile header ───────────────────────────────────────────── */
.mp-profile-name { font-size: 1.6rem; font-weight: 800; color: #F1F5F9; }
.mp-profile-serial { font-size: 0.85rem; color: #7C3AED; font-weight: 700; letter-spacing: 1px; }

/* ── Fee countdown ────────────────────────────────────────────── */
.fee-ok   { color: #34d399; }
.fee-warn { color: #fbbf24; }
.fee-due  { color: #f87171; }

/* ── Attendance code ──────────────────────────────────────────── */
.att-code {
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: 12px;
    text-align: center;
    color: #7C3AED;
    background: #0F172A;
    border: 2px solid #7C3AED;
    border-radius: 12px;
    padding: 1rem 0;
    font-family: monospace;
}

/* ── AI chat bubbles ──────────────────────────────────────────── */
.chat-user {
    background: #312e81;
    border-radius: 16px 16px 4px 16px;
    padding: 0.7rem 1rem;
    margin: 0.3rem 0;
    text-align: right;
    color: #e0e7ff;
}
.chat-ai {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 16px 16px 16px 4px;
    padding: 0.7rem 1rem;
    margin: 0.3rem 0;
    color: #E2E8F0;
}

/* ── Section title ────────────────────────────────────────────── */
.mp-section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #7C3AED;
    border-bottom: 2px solid #7C3AED33;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}

/* ── Login box ────────────────────────────────────────────────── */
.mp-login-box {
    max-width: 440px;
    margin: 3rem auto;
    padding: 2.5rem;
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 20px;
    box-shadow: 0 25px 50px rgba(0,0,0,0.6);
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

def _login_page():
    st.markdown(PORTAL_CSS, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:3rem;">🏋️</div>
            <div style="font-size:1.8rem; font-weight:800; color:#7C3AED;">Member Portal</div>
            <div style="color:#94A3B8; font-size:0.9rem;">Apna profile, attendance aur progress yahan dekhein</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("mp_login"):
            serial = st.text_input("🪪 Serial Number", placeholder="e.g. PF-00001",
                                   help="Membership card pe likha serial number")
            phone_last4 = st.text_input("📱 Phone ke akhri 4 digits",
                                        placeholder="e.g. 5678", max_chars=4,
                                        help="Apne registered phone number ke akhri 4 digits")
            submit = st.form_submit_button("🔓 Login karo", type="primary", use_container_width=True)

        if submit:
            if not serial or not phone_last4:
                st.error("Serial number aur phone digits dono zaruri hain.")
                return

            member = db.get_member_by_serial(serial.strip().upper())
            if not member:
                st.error("❌ Serial number nahi mila. Dobara check karein.")
                return

            phone = (member.phone or "").replace(" ", "").replace("-", "")
            if not phone.endswith(phone_last4.strip()):
                st.error("❌ Phone digits galat hain. Dobara check karein.")
                return

            # Success
            st.session_state["portal_member_id"] = member.id
            st.session_state["portal_member_serial"] = member.serial_number
            if "mp_chat" not in st.session_state:
                st.session_state["mp_chat"] = []
            st.rerun()

        st.markdown("---")
        st.markdown(
            "<div style='text-align:center; color:#64748B; font-size:0.8rem;'>"
            "Serial number apni membership card pe hoga<br>"
            "Mushkil ho toh gym staff se madad lein"
            "</div>",
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE TAB
# ─────────────────────────────────────────────────────────────────────────────

def _tab_profile(m, gym):
    today = date.today()

    # ── Photo + basic info ────────────────────────────────────────
    c_photo, c_info = st.columns([1, 2])
    with c_photo:
        if m.photo_path and os.path.exists(m.photo_path):
            st.image(m.photo_path, width=160)
        else:
            st.markdown(
                "<div style='width:160px;height:160px;border-radius:12px;"
                "background:#1E293B;display:flex;align-items:center;"
                "justify-content:center;font-size:4rem;'>👤</div>",
                unsafe_allow_html=True
            )

    with c_info:
        badge_map = {"Active": "active", "Expired": "expired",
                     "Inactive": "inactive", "Frozen": "frozen", "Suspended": "inactive"}
        b = badge_map.get(m.status, "inactive")
        st.markdown(f"""
        <div class="mp-profile-name">{m.full_name}</div>
        <div class="mp-profile-serial">#{m.serial_number}</div>
        <span class="badge-{b}">{m.status}</span>
        <br><br>
        <div style="color:#94A3B8; font-size:0.88rem; line-height:1.9;">
        🏋️ <b style='color:#E2E8F0'>{gym.name if gym else 'N/A'}</b><br>
        🎫 <b style='color:#E2E8F0'>{m.membership_type}</b><br>
        📱 {m.phone or '—'}<br>
        📧 {m.email or '—'}<br>
        🚻 {m.gender or '—'} &nbsp;|&nbsp; 🎂 {m.dob or '—'}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Dates & fee countdown ─────────────────────────────────────
    st.markdown('<div class="mp-section-title">💳 Membership Status</div>', unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)

    join = m.join_date or "—"
    expiry = m.expiry_date

    if expiry:
        try:
            exp_date = date.fromisoformat(expiry)
            days_left = (exp_date - today).days
            if days_left > 7:
                countdown_html = f'<div class="mp-stat-val fee-ok">{days_left}</div>'
                countdown_lbl = "Days Left"
            elif days_left >= 0:
                countdown_html = f'<div class="mp-stat-val fee-warn">{days_left}</div>'
                countdown_lbl = "⚠️ Days Left"
            else:
                countdown_html = f'<div class="mp-stat-val fee-due">{abs(days_left)}</div>'
                countdown_lbl = "🔴 Days Overdue"
        except Exception:
            countdown_html = '<div class="mp-stat-val">—</div>'
            countdown_lbl = "Days Left"
    else:
        countdown_html = '<div class="mp-stat-val">—</div>'
        countdown_lbl = "Days Left"

    with d1:
        st.markdown(f'<div class="mp-stat"><div class="mp-stat-val">{join}</div><div class="mp-stat-lbl">Join Date</div></div>', unsafe_allow_html=True)
    with d2:
        st.markdown(f'<div class="mp-stat"><div class="mp-stat-val">{expiry or "—"}</div><div class="mp-stat-lbl">Expiry Date</div></div>', unsafe_allow_html=True)
    with d3:
        st.markdown(f'<div class="mp-stat">{countdown_html}<div class="mp-stat-lbl">{countdown_lbl}</div></div>', unsafe_allow_html=True)
    with d4:
        fee = m.fee_amount or 0
        st.markdown(f'<div class="mp-stat"><div class="mp-stat-val" style="color:#7C3AED;">PKR {fee:,.0f}</div><div class="mp-stat-lbl">Monthly Fee</div></div>', unsafe_allow_html=True)

    # ── Fee history ───────────────────────────────────────────────
    st.markdown('<div class="mp-section-title" style="margin-top:1.5rem">💰 Fee History</div>', unsafe_allow_html=True)
    fee_recs = db.get_fee_records(member_id=m.id, limit=12)
    if fee_recs:
        rows = []
        for f in sorted(fee_recs, key=lambda x: x.payment_date, reverse=True):
            rows.append({
                "Date": f.payment_date,
                "Amount": f"PKR {f.amount:,.0f}",
                "Method": f.payment_method or "—",
                "Period": f"{f.period_start or '—'} → {f.period_end or '—'}",
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        # Revenue chart
        months = {}
        for f in fee_recs:
            mo = (f.payment_date or "")[:7]
            if mo:
                months[mo] = months.get(mo, 0) + (f.amount or 0)
        if months:
            df_m = pd.DataFrame({"Month": list(months.keys()), "Amount": list(months.values())}).sort_values("Month")
            fig = px.bar(df_m, x="Month", y="Amount", title="Fee Payments History",
                         color_discrete_sequence=["#7C3AED"])
            fig.update_layout(plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
                              font_color="#E2E8F0", title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Abhi tak koi fee record nahi hai.")


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE TAB
# ─────────────────────────────────────────────────────────────────────────────

def _tab_attendance(m):
    today = date.today()

    st.markdown('<div class="mp-section-title">📅 Aaj ki Attendance</div>', unsafe_allow_html=True)

    # Check already marked?
    att_recs = db.get_attendance(check_date=str(today))
    today_att = next((a for a in att_recs if a.member_id == m.id), None)

    col_code, col_action = st.columns([1, 1])

    with col_code:
        code = _daily_code(m.id)
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:0.5rem;">
            <div style="color:#94A3B8; font-size:0.8rem; margin-bottom:0.4rem;">📲 Apna Daily Code — staff ko dikhao</div>
            <div class="att-code">{code}</div>
            <div style="color:#64748B; font-size:0.72rem; margin-top:0.4rem;">Yeh code sirf aaj valid hai</div>
        </div>
        """, unsafe_allow_html=True)

    with col_action:
        if today_att:
            status_icon = "✅" if today_att.status == "Present" else "⚠️"
            st.success(f"{status_icon} Aaj ka attendance mark ho gaya: **{today_att.status}**")
        else:
            st.warning("⏰ Aaj ka attendance abhi mark nahi hua")

        if st.button("✅ Aaj Present Mark Karo", type="primary", use_container_width=True,
                     disabled=(today_att is not None)):
            ok, msg = db.mark_attendance(m.id, m.gym_id, today, "Present", "member-self")
            if ok:
                st.success("✅ Attendance mark ho gayi!")
                st.rerun()
            else:
                st.error(f"Error: {msg}")

    st.divider()

    # ── Stats ─────────────────────────────────────────────────────
    st.markdown('<div class="mp-section-title">📊 Attendance Stats</div>', unsafe_allow_html=True)
    streak = db.get_member_streak(m.id)
    rate_30 = db.get_member_attendance_rate(m.id, days=30)
    rate_7  = db.get_member_attendance_rate(m.id, days=7)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f'<div class="mp-stat"><div class="mp-stat-val" style="color:#f59e0b;">🔥 {streak}</div><div class="mp-stat-lbl">Day Streak</div></div>', unsafe_allow_html=True)
    with s2:
        color = "#34d399" if rate_30 >= 70 else "#fbbf24" if rate_30 >= 40 else "#f87171"
        st.markdown(f'<div class="mp-stat"><div class="mp-stat-val" style="color:{color};">{rate_30:.0f}%</div><div class="mp-stat-lbl">30-Day Rate</div></div>', unsafe_allow_html=True)
    with s3:
        color7 = "#34d399" if rate_7 >= 70 else "#fbbf24" if rate_7 >= 40 else "#f87171"
        st.markdown(f'<div class="mp-stat"><div class="mp-stat-val" style="color:{color7};">{rate_7:.0f}%</div><div class="mp-stat-lbl">7-Day Rate</div></div>', unsafe_allow_html=True)

    # ── 30-day calendar chart ─────────────────────────────────────
    st.markdown('<div class="mp-section-title" style="margin-top:1.2rem">📆 30 Din ki History</div>', unsafe_allow_html=True)

    days_30 = [today - timedelta(days=i) for i in range(29, -1, -1)]
    all_att = db.get_attendance(check_date=None)
    my_att = {a.check_date: a.status for a in all_att if a.member_id == m.id}

    cal_rows = []
    for d in days_30:
        ds = str(d)
        s = my_att.get(ds, "Absent")
        cal_rows.append({"Date": d.strftime("%d %b"), "Status": s,
                         "Val": 1 if s == "Present" else 0,
                         "Color": "#34d399" if s == "Present" else "#f87171" if s == "Absent" else "#fbbf24"})

    df_cal = pd.DataFrame(cal_rows)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_cal["Date"],
        y=df_cal["Val"],
        marker_color=[r["Color"] for r in cal_rows],
        hovertemplate="%{x}<br>%{customdata}<extra></extra>",
        customdata=df_cal["Status"],
    ))
    fig.update_layout(
        plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
        font_color="#E2E8F0", title_x=0.5,
        yaxis=dict(showticklabels=False, range=[0, 1.2]),
        xaxis=dict(tickangle=-45),
        height=200, margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🟢 Present  🔴 Absent  🟡 Late")


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS TAB
# ─────────────────────────────────────────────────────────────────────────────

def _tab_progress(m):
    records = db.get_body_measurements(m.id)

    st.markdown('<div class="mp-section-title">📏 Measurements Add Karo</div>', unsafe_allow_html=True)
    with st.form("mp_meas"):
        c1, c2, c3 = st.columns(3)
        with c1:
            weight = st.number_input("⚖️ Weight (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.5)
            chest  = st.number_input("Chest (cm)", min_value=0.0, max_value=200.0, value=0.0, step=0.5)
        with c2:
            waist  = st.number_input("Waist (cm)", min_value=0.0, max_value=200.0, value=0.0, step=0.5)
            hips   = st.number_input("Hips (cm)",  min_value=0.0, max_value=200.0, value=0.0, step=0.5)
        with c3:
            bicep  = st.number_input("Bicep (cm)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            body_fat = st.number_input("Body Fat %", min_value=0.0, max_value=60.0, value=0.0, step=0.5)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("💾 Save karo", type="primary"):
            ok, msg = db.add_body_measurement(
                m.id, date.today(), weight,
                chest or None, waist or None, hips or None, bicep or None,
                body_fat or None, notes
            )
            if ok:
                st.success("✅ Measurements save ho gayi!")
                st.rerun()
            else:
                st.error(msg)

    if not records:
        st.info("Abhi tak koi measurement nahi hai. Upar add karo!")
        return

    st.divider()
    st.markdown('<div class="mp-section-title">📈 Progress Charts</div>', unsafe_allow_html=True)

    dates  = [r.recorded_date for r in records]
    weights = [r.weight_kg for r in records]

    # Weight chart
    fig_w = go.Figure()
    fig_w.add_trace(go.Scatter(
        x=dates, y=weights, mode="lines+markers",
        line=dict(color="#7C3AED", width=3),
        marker=dict(size=8, color="#7C3AED"),
        fill="tozeroy", fillcolor="rgba(124,58,237,0.1)",
        name="Weight (kg)"
    ))
    fig_w.update_layout(
        title="Weight Progress (kg)",
        plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
        font_color="#E2E8F0", title_x=0.5,
        yaxis_title="kg", xaxis_title="",
        height=280, margin=dict(t=40, b=20, l=40, r=10)
    )
    st.plotly_chart(fig_w, use_container_width=True)

    # BMI
    latest = records[-1]
    gym = db.get_gym(m.gym_id)
    height_cm = None  # Member model mein height nahi, agar future mein add karein

    # Measurements chart (if data exists)
    meas_data = {}
    for field, label in [("chest_cm", "Chest"), ("waist_cm", "Waist"),
                          ("hips_cm", "Hips"), ("bicep_cm", "Bicep")]:
        vals = [getattr(r, field) for r in records]
        if any(v for v in vals):
            meas_data[label] = vals

    if meas_data:
        fig_m = go.Figure()
        colors = ["#34d399", "#f87171", "#fbbf24", "#60a5fa"]
        for i, (label, vals) in enumerate(meas_data.items()):
            fig_m.add_trace(go.Scatter(
                x=dates, y=vals, mode="lines+markers",
                name=f"{label} (cm)",
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6),
            ))
        fig_m.update_layout(
            title="Body Measurements (cm)",
            plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
            font_color="#E2E8F0", title_x=0.5,
            yaxis_title="cm", xaxis_title="",
            height=280, margin=dict(t=40, b=20, l=40, r=10)
        )
        st.plotly_chart(fig_m, use_container_width=True)

    # Summary stats
    if len(records) >= 2:
        first = records[0]
        last = records[-1]
        st.markdown('<div class="mp-section-title" style="margin-top:0.5rem">📋 Summary</div>', unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        wc = last.weight_kg - first.weight_kg
        wcolor = "#34d399" if wc <= 0 else "#f87171"
        with s1:
            st.markdown(f'<div class="mp-stat"><div class="mp-stat-val" style="color:{wcolor};">{wc:+.1f} kg</div><div class="mp-stat-lbl">Weight Change</div></div>', unsafe_allow_html=True)
        with s2:
            days = (date.fromisoformat(str(last.recorded_date)) - date.fromisoformat(str(first.recorded_date))).days
            st.markdown(f'<div class="mp-stat"><div class="mp-stat-val">{days}</div><div class="mp-stat-lbl">Days Tracked</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="mp-stat"><div class="mp-stat-val">{len(records)}</div><div class="mp-stat-lbl">Records</div></div>', unsafe_allow_html=True)
        with s4:
            if days > 0:
                wkly = (wc / days) * 7
                st.markdown(f'<div class="mp-stat"><div class="mp-stat-val" style="font-size:1.3rem;">{wkly:+.2f}</div><div class="mp-stat-lbl">kg/week avg</div></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# AI DIET PLAN TAB
# ─────────────────────────────────────────────────────────────────────────────

def _tab_diet(m):
    st.markdown('<div class="mp-section-title">🥗 AI Personalized Diet Plan</div>', unsafe_allow_html=True)

    records = db.get_body_measurements(m.id)
    latest = records[-1] if records else None

    # Goal selector
    goal = st.selectbox("🎯 Aap ka goal kya hai?", [
        "Weight Loss (wazan kam karna)",
        "Muscle Gain (muscle banana)",
        "Weight Maintenance (wazan qaim rakhna)",
        "Endurance & Fitness (stamina badhana)",
        "Healthy Eating (sehat mand khana)",
    ])

    c1, c2 = st.columns(2)
    with c1:
        custom_weight = st.number_input("⚖️ Current Weight (kg)", min_value=30.0, max_value=300.0,
                                         value=float(latest.weight_kg) if latest else 70.0, step=0.5)
        height_cm = st.number_input("📏 Apni height (cm)", min_value=100, max_value=250, value=170)
    with c2:
        activity = st.selectbox("🏃 Activity level", [
            "Sedentary (zyada baith ke kaam)",
            "Lightly active (thoda walk wagera)",
            "Moderately active (gym 3-4x/week)",
            "Very active (gym 5-6x/week)",
            "Extremely active (heavy training daily)",
        ])
        diet_pref = st.selectbox("🍽️ Diet preference", [
            "No restriction",
            "Vegetarian",
            "No pork",
            "Halal only",
            "Low carb",
            "High protein",
        ])

    allergies = st.text_input("⚠️ Koi allergy ya avoid karna chahte ho? (optional)", placeholder="e.g. dairy, nuts")

    if st.button("🤖 Mera Diet Plan Banao", type="primary", use_container_width=True):
        with st.spinner("AI diet plan bana raha hai..."):
            prompt = f"""You are a professional nutritionist and fitness coach.
Create a detailed, personalized 7-day diet plan for this member.

Member profile:
- Name: {m.full_name}
- Gender: {m.gender or 'Not specified'}
- Weight: {custom_weight} kg
- Height: {height_cm} cm
- Goal: {goal}
- Activity level: {activity}
- Diet preference: {diet_pref}
- Allergies/Avoid: {allergies or 'None'}

Instructions:
- Write in Roman Urdu (mix with English food names)
- Give specific meal times (Sehri/Breakfast, Mid-morning, Lunch, Evening snack, Dinner)
- Include Pakistani/South Asian foods where appropriate
- Give portion sizes
- Calculate approximate daily calories
- Add 5 practical tips at the end
- Make it realistic and sustainable

Format: Day 1 through Day 7, clear sections, easy to follow."""

            plan = _groq([
                {"role": "system", "content": "You are a professional nutritionist. Always respond in Roman Urdu mixed with English."},
                {"role": "user", "content": prompt}
            ], max_tokens=2500)

            st.session_state["mp_diet_plan"] = plan
            st.session_state["mp_diet_done"] = True

    if st.session_state.get("mp_diet_plan"):
        st.divider()
        st.markdown("### 📋 Aap ka Personalized Diet Plan")
        st.markdown(st.session_state["mp_diet_plan"])

        # Download button
        st.download_button(
            "⬇️ Download Diet Plan",
            data=st.session_state["mp_diet_plan"],
            file_name=f"diet_plan_{m.serial_number}_{date.today()}.txt",
            mime="text/plain",
        )


# ─────────────────────────────────────────────────────────────────────────────
# AI EXERCISE COACH TAB
# ─────────────────────────────────────────────────────────────────────────────

def _tab_exercise(m):
    st.markdown('<div class="mp-section-title">💪 AI Exercise Coach</div>', unsafe_allow_html=True)

    records = db.get_body_measurements(m.id)
    latest = records[-1] if records else None

    # ── Today's Workout Plan ──────────────────────────────────────
    st.markdown("#### 🗓️ Aaj ka Workout Plan Generate Karo")
    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        focus = st.selectbox("Aaj kya karna hai?", [
            "Full Body",
            "Chest & Triceps",
            "Back & Biceps",
            "Legs & Glutes",
            "Shoulders & Abs",
            "Cardio & HIIT",
            "Core & Flexibility",
            "Rest & Recovery",
        ])
    with wc2:
        level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
    with wc3:
        duration = st.selectbox("Duration", ["30 mins", "45 mins", "60 mins", "90 mins"])

    equipment = st.multiselect("Equipment available", [
        "Dumbbells", "Barbell", "Cable Machine", "Bench",
        "Pull-up Bar", "Resistance Bands", "Treadmill", "No Equipment (bodyweight)"
    ], default=["Dumbbells"])

    if st.button("⚡ Aaj ka Workout Generate Karo", type="primary", use_container_width=True):
        with st.spinner("AI workout plan bana raha hai..."):
            equip_str = ", ".join(equipment) if equipment else "bodyweight only"
            weight_info = f"{latest.weight_kg} kg" if latest else "not specified"

            workout_prompt = f"""You are an expert personal trainer.
Create a detailed workout plan for today.

Member: {m.full_name} ({m.gender or 'N/A'})
Focus: {focus}
Level: {level}
Duration: {duration}
Equipment: {equip_str}
Current Weight: {weight_info}

Instructions:
- Write in Roman Urdu + English
- List every exercise with: sets x reps, rest time, pro tip
- Include warm-up (5 min) and cool-down (5 min)
- Add a motivation line at the end
- Keep it practical for a Pakistani gym

Also create a simple table at the end showing:
Exercise | Sets | Reps | Rest | Muscle Group"""

            plan = _groq([
                {"role": "system", "content": "You are an expert personal trainer. Respond in Roman Urdu mixed with English."},
                {"role": "user", "content": workout_prompt}
            ], max_tokens=2000)

            st.session_state["mp_workout_plan"] = plan

    if st.session_state.get("mp_workout_plan"):
        st.divider()
        st.markdown("#### 📋 Aaj ka Workout Plan")
        st.markdown(st.session_state["mp_workout_plan"])

        # Exercise progress chart
        st.divider()
        st.markdown("#### 📊 Weekly Training Chart")
        att_recs_7 = []
        for i in range(7):
            d = date.today() - timedelta(days=6-i)
            recs = db.get_attendance(check_date=str(d))
            present = any(a.member_id == m.id and a.status == "Present" for a in recs)
            att_recs_7.append({"Day": d.strftime("%a\n%d %b"), "Present": 1 if present else 0})

        df_week = pd.DataFrame(att_recs_7)
        fig_w = go.Figure(go.Bar(
            x=df_week["Day"],
            y=df_week["Present"],
            marker_color=["#7C3AED" if v else "#1E293B" for v in df_week["Present"]],
            text=["✅" if v else "❌" for v in df_week["Present"]],
            textposition="outside",
        ))
        fig_w.update_layout(
            title="Is Hafte ki Training",
            plot_bgcolor="#0F172A", paper_bgcolor="#0F172A",
            font_color="#E2E8F0", title_x=0.5,
            yaxis=dict(showticklabels=False, range=[0, 1.5]),
            height=220, margin=dict(t=40, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_w, use_container_width=True)

        st.download_button(
            "⬇️ Download Workout Plan",
            data=st.session_state["mp_workout_plan"],
            file_name=f"workout_{m.serial_number}_{date.today()}.txt",
            mime="text/plain",
        )

    # ── AI Chat ───────────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="mp-section-title">💬 AI se Exercise ke bare mein pocho</div>', unsafe_allow_html=True)

    if "mp_chat" not in st.session_state:
        st.session_state["mp_chat"] = []

    # Show chat history
    for msg in st.session_state["mp_chat"]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    user_q = st.chat_input("Exercise, diet ya fitness ke bare mein kuch bhi pocho...")
    if user_q:
        st.session_state["mp_chat"].append({"role": "user", "content": user_q})

        # Build messages for API
        system_msg = {
            "role": "system",
            "content": (
                f"You are GymPro AI Coach for {m.full_name}. "
                f"They are a gym member (membership: {m.membership_type}). "
                "You help with exercises, workout plans, fitness tips, nutrition advice. "
                "Always respond in Roman Urdu mixed with English. "
                "Be encouraging, specific, and practical. "
                "If they ask for an exercise chart or plan, format it clearly with tables or bullet points."
            )
        }
        api_msgs = [system_msg] + [
            {"role": m2["role"], "content": m2["content"]}
            for m2 in st.session_state["mp_chat"][-12:]  # last 6 exchanges
        ]

        with st.spinner("AI soch raha hai..."):
            reply = _groq(api_msgs, max_tokens=1200)

        st.session_state["mp_chat"].append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state["mp_chat"] and st.button("🗑️ Chat Clear karo"):
        st.session_state["mp_chat"] = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render():
    st.markdown(PORTAL_CSS, unsafe_allow_html=True)

    # ── Login check ───────────────────────────────────────────────
    m = _mp_member()
    if not m:
        _login_page()
        return

    gym = db.get_gym(m.gym_id)

    # ── Header ────────────────────────────────────────────────────
    h1, h2 = st.columns([5, 1])
    with h1:
        st.markdown(
            f"<div style='font-size:1.4rem; font-weight:800; color:#7C3AED;'>🏋️ Member Portal</div>"
            f"<div style='color:#94A3B8; font-size:0.85rem;'>Ahlan {m.full_name}! — {gym.name if gym else ''}</div>",
            unsafe_allow_html=True
        )
    with h2:
        if st.button("🚪 Logout", use_container_width=True):
            _mp_logout()

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────
    tabs = st.tabs(["👤 Profile & Fees", "📅 Attendance", "📈 Progress", "🥗 Diet Plan", "💪 Exercise Coach"])

    with tabs[0]:
        _tab_profile(m, gym)

    with tabs[1]:
        _tab_attendance(m)

    with tabs[2]:
        _tab_progress(m)

    with tabs[3]:
        _tab_diet(m)

    with tabs[4]:
        _tab_exercise(m)
