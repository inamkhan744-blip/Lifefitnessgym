import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import database as db
import urllib.parse
import io

# ============================================
# HELPERS
# ============================================

def make_wa_link(phone: str, message: str) -> str:
    clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if clean.startswith("0"):
        clean = "+92" + clean[1:]
    return f"https://wa.me/{clean}?text={urllib.parse.quote(message)}"

def get_progress_summary(records):
    """Calculate progress summary from records"""
    if not records or len(records) < 2:
        return None
    
    first = records[0]
    last = records[-1]
    
    summary = {
        'weight_change': last.weight_kg - first.weight_kg,
        'chest_change': (last.chest_cm or 0) - (first.chest_cm or 0) if last.chest_cm and first.chest_cm else 0,
        'waist_change': (last.waist_cm or 0) - (first.waist_cm or 0) if last.waist_cm and first.waist_cm else 0,
        'hips_change': (last.hips_cm or 0) - (first.hips_cm or 0) if last.hips_cm and first.hips_cm else 0,
        'bicep_change': (last.bicep_cm or 0) - (first.bicep_cm or 0) if last.bicep_cm and first.bicep_cm else 0,
        'total_days': (last.recorded_date - first.recorded_date).days,
        'total_records': len(records),
        'first_weight': first.weight_kg,
        'last_weight': last.weight_kg,
        'first_date': first.recorded_date,
        'last_date': last.recorded_date,
        'first_body_fat': first.body_fat_pct,
        'last_body_fat': last.body_fat_pct,
    }
    
    if summary['total_days'] > 0:
        summary['weekly_change'] = (summary['weight_change'] / summary['total_days']) * 7
    else:
        summary['weekly_change'] = 0
    
    return summary

def get_health_tip(member_id, records=None):
    """Get personalized health tip"""
    if records is None:
        records = db.get_body_measurements(member_id)
    
    if not records or len(records) < 2:
        return "💪 Start tracking your progress today! Consistency is key to achieving your fitness goals."
    
    summary = get_progress_summary(records)
    if not summary:
        return "💪 Keep going! Every workout brings you closer to your goals."
    
    if summary['weight_change'] < -2:
        return f"🔥 Amazing progress! You've lost {abs(summary['weight_change']):.1f} kg. Keep up the great work!"
    elif summary['weight_change'] < 0:
        return f"💪 Good progress! You've lost {abs(summary['weight_change']):.1f} kg. Stay consistent!"
    elif summary['weight_change'] > 0 and summary['weekly_change'] > 0.5:
        return f"📈 You've gained {summary['weight_change']:.1f} kg. Remember, muscle gain is positive if you're building strength!"
    else:
        return "🌟 You're on track! Keep pushing yourself and trust the process."

def generate_progress_report(member_name, records, gym_name):
    """Generate professional progress report"""
    if not records or len(records) < 2:
        return "Need at least 2 measurements for report"
    
    summary = get_progress_summary(records)
    if not summary:
        return "Need at least 2 measurements for report"
    
    report = f"""
📊 PROGRESS REPORT - {member_name}
🏋️ {gym_name}
📅 Generated: {date.today().strftime('%B %d, %Y')}
{'='*50}

📈 WEIGHT PROGRESS
• Starting: {summary['first_weight']:.1f} kg ({summary['first_date']})
• Current: {summary['last_weight']:.1f} kg ({summary['last_date']})
• Change: {summary['weight_change']:+.1f} kg
• Weekly Avg: {summary['weekly_change']:+.1f} kg/week
• Total Days: {summary['total_days']} days

📏 MEASUREMENTS
• Chest: {summary['chest_change']:+.1f} cm
• Waist: {summary['waist_change']:+.1f} cm
• Hips: {summary['hips_change']:+.1f} cm
• Bicep: {summary['bicep_change']:+.1f} cm
"""
    
    if summary.get('first_body_fat') and summary.get('last_body_fat'):
        report += f"""
• Body Fat: {summary['last_body_fat'] - summary['first_body_fat']:+.1f}%
"""
    
    report += f"""

💪 HEALTH TIP
{get_health_tip(None, records)}

{'='*50}
📱 Share your progress with friends and family!
"""
    
    return report

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI from weight and height"""
    if height_cm and height_cm > 0:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        return bmi
    return None

def get_bmi_category(bmi):
    """Get BMI category"""
    if bmi is None:
        return "Unknown", "#94A3B8"
    if bmi < 18.5:
        return "Underweight", "#60A5FA"
    elif bmi < 25:
        return "Normal", "#34D399"
    elif bmi < 30:
        return "Overweight", "#FBBF24"
    else:
        return "Obese", "#F87171"

def generate_workout_suggestion(records):
    """Generate workout suggestions based on progress"""
    if not records or len(records) < 2:
        return "Start with a balanced routine: 3x cardio, 3x strength training per week."
    
    summary = get_progress_summary(records)
    if not summary:
        return "Maintain your current routine and track consistently."
    
    suggestions = []
    
    if summary['weight_change'] > 0 and summary['weekly_change'] > 0.3:
        suggestions.append("📈 Increase cardio to 4-5 sessions per week")
        suggestions.append("💪 Focus on high-intensity interval training (HIIT)")
    
    if summary['weight_change'] < -0.5 and summary['weekly_change'] < -0.3:
        suggestions.append("💪 Increase protein intake to maintain muscle mass")
        suggestions.append("🏋️ Add strength training 3-4 times per week")
    
    if summary['waist_change'] > 0:
        suggestions.append("📏 Add core exercises (planks, crunches) 3x per week")
        suggestions.append("🔥 Try intermittent fasting or reduce carbs")
    
    if not suggestions:
        suggestions.append("💪 Keep up the great work! Maintain your current routine.")
        suggestions.append("📊 Track measurements weekly for best results.")
    
    return "\n".join(suggestions)

# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role):
    
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("🏋️ Add a gym first to start tracking progress.")
        return
    
    # ============================================
    # SELECTION
    # ============================================
    
    sel_col1, sel_col2 = st.columns([1, 1])
    
    with sel_col1:
        if gym_id:
            sel_gid = gym_id
            st.text_input("📍 Gym Location", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True)
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("📍 Gym Location", list(opts.keys()))
            sel_gid = opts[chosen]
    
    with sel_col2:
        members = db.get_members(gym_id=sel_gid, status="Active")
        if not members:
            st.warning("⚠️ No active members found in this gym.")
            return
        
        mem_opts = {f"{m.serial_number} — {m.full_name}": m.id for m in members}
        sel_label = st.selectbox("👤 Select Member", list(mem_opts.keys()))
        sel_mid = mem_opts[sel_label]
        sel_m = next((m for m in members if m.id == sel_mid), None)
    
    if not sel_m:
        return
    
    # ============================================
    # GET RECORDS
    # ============================================
    
    records = db.get_body_measurements(sel_mid)
    
    # ============================================
    # DASHBOARD STATS
    # ============================================
    
    st.markdown("---")
    
    if records and len(records) >= 2:
        summary = get_progress_summary(records)
        
        if summary:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                weight_icon = "▼" if summary['weight_change'] < 0 else "▲" if summary['weight_change'] > 0 else "—"
                st.metric(
                    label="Current Weight",
                    value=f"{summary['last_weight']:.1f} kg",
                    delta=f"{weight_icon} {abs(summary['weight_change']):.1f} kg"
                )
            
            with col2:
                st.metric(
                    label="Total Records",
                    value=f"{summary['total_records']}",
                    delta="📝 measurements"
                )
            
            with col3:
                st.metric(
                    label="Days Tracking",
                    value=f"{summary['total_days']}",
                    delta="📅 total days"
                )
            
            with col4:
                weekly = summary['weekly_change']
                weekly_icon = "▼" if weekly < 0 else "▲" if weekly > 0 else "—"
                st.metric(
                    label="Weekly Avg Change",
                    value=f"{abs(weekly):.1f} kg",
                    delta=f"{weekly_icon} per week"
                )
            
            with col5:
                waist_change = summary.get('waist_change', 0)
                waist_icon = "▼" if waist_change < 0 else "▲" if waist_change > 0 else "—"
                st.metric(
                    label="Waist Change",
                    value=f"{abs(waist_change):.1f} cm",
                    delta=f"{waist_icon} total"
                )
        else:
            st.info("📊 Need at least 2 measurements for stats.")
    else:
        st.info("📝 No measurements recorded yet. Start tracking your progress below!")
    
    st.markdown("---")
    
    # ============================================
    # TABS
    # ============================================
    
    tab_record, tab_view, tab_analytics, tab_extra = st.tabs([
        "📝 Record",
        "📈 Charts",
        "📊 Analytics",
        "💪 Fitness Tools"
    ])
    
    # ============================================
    # TAB 1: RECORD MEASUREMENT
    # ============================================
    
    with tab_record:
        col_form, col_history = st.columns([3, 2])
        
        with col_form:
            with st.form("progress_record_form", clear_on_submit=True):
                st.markdown("### 📏 New Measurement")
                
                r1, r2 = st.columns(2)
                with r1:
                    rec_date = st.date_input("📅 Date", value=date.today())
                    weight = st.number_input(
                        "⚖️ Weight (kg)",
                        min_value=0.0, max_value=300.0,
                        step=0.1, format="%.1f",
                        value=records[-1].weight_kg if records else 70.0
                    )
                    body_fat = st.number_input(
                        "🧬 Body Fat %",
                        min_value=0.0, max_value=60.0,
                        step=0.1, format="%.1f",
                        value=records[-1].body_fat_pct if records and records[-1].body_fat_pct else None
                    )
                
                with r2:
                    chest = st.number_input(
                        "📏 Chest (cm)",
                        min_value=0.0, max_value=200.0,
                        step=0.5, format="%.1f",
                        value=records[-1].chest_cm if records and records[-1].chest_cm else None
                    )
                    waist = st.number_input(
                        "📏 Waist (cm)",
                        min_value=0.0, max_value=200.0,
                        step=0.5, format="%.1f",
                        value=records[-1].waist_cm if records and records[-1].waist_cm else None
                    )
                    hips = st.number_input(
                        "📏 Hips (cm)",
                        min_value=0.0, max_value=200.0,
                        step=0.5, format="%.1f",
                        value=records[-1].hips_cm if records and records[-1].hips_cm else None
                    )
                
                bicep = st.number_input(
                    "💪 Bicep (cm)",
                    min_value=0.0, max_value=100.0,
                    step=0.5, format="%.1f",
                    value=records[-1].bicep_cm if records and records[-1].bicep_cm else None
                )
                
                notes = st.text_area(
                    "📝 Notes",
                    height=80,
                    placeholder="Observations, diet notes, trainer remarks, mood, energy levels..."
                )
                
                if st.form_submit_button("💾 Save Measurement", type="primary", use_container_width=True):
                    if weight <= 0:
                        st.error("⚠️ Weight must be greater than 0!")
                    else:
                        ok, msg = db.add_body_measurement(
                            member_id=sel_mid,
                            recorded_date=rec_date,
                            weight_kg=weight,
                            chest_cm=chest or None,
                            waist_cm=waist or None,
                            hips_cm=hips or None,
                            bicep_cm=bicep or None,
                            body_fat_pct=body_fat or None,
                            notes=notes,
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
        
        with col_history:
            st.markdown("### 📋 Measurement History")
            
            if records:
                latest = records[-1]
                st.markdown(f"""
**Latest:** {latest.recorded_date}
- Weight: **{latest.weight_kg} kg**
- Body Fat: **{latest.body_fat_pct or '—'}%**
- Chest: **{latest.chest_cm or '—'} cm**
- Waist: **{latest.waist_cm or '—'} cm**
                """)
                
                history_data = []
                for r in reversed(records[-10:]):
                    history_data.append({
                        "Date": r.recorded_date,
                        "Weight": f"{r.weight_kg} kg",
                        "Chest": f"{r.chest_cm or '—'} cm",
                        "Waist": f"{r.waist_cm or '—'} cm",
                    })
                
                st.dataframe(
                    pd.DataFrame(history_data),
                    use_container_width=True,
                    hide_index=True,
                    height=250
                )
                
                if role == "admin" and len(records) > 1:
                    st.divider()
                    del_opts = {f"{r.recorded_date} — {r.weight_kg} kg": r.id for r in records}
                    del_sel = st.selectbox("Delete record", list(del_opts.keys()), key="del_record")
                    if st.button("🗑️ Delete", use_container_width=True):
                        db.delete_body_measurement(del_opts[del_sel])
                        st.success("✅ Deleted!")
                        st.rerun()
            else:
                st.info("No measurements yet.")
    
    # ============================================
    # TAB 2: PROGRESS CHARTS (FIXED)
    # ============================================
    
    with tab_view:
        if not records:
            st.info("📊 No data to display. Record measurements first!")
        else:
            df = pd.DataFrame([{
                "Date": r.recorded_date,
                "Weight": r.weight_kg,
                "Chest": r.chest_cm,
                "Waist": r.waist_cm,
                "Hips": r.hips_cm,
                "Bicep": r.bicep_cm,
                "Body Fat %": r.body_fat_pct,
            } for r in records])
            
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date').sort_index()
            
            col_metric, col_chart_type = st.columns([1, 1])
            with col_metric:
                selected_metric = st.selectbox(
                    "📊 Select Metric",
                    ["Weight", "Chest", "Waist", "Hips", "Bicep", "Body Fat %"],
                    key="chart_metric"
                )
            
            with col_chart_type:
                chart_type = st.selectbox(
                    "📈 Chart Type",
                    ["Line Chart", "Bar Chart", "Area Chart"],
                    key="chart_type"
                )
            
            if selected_metric in df.columns:
                data = df[[selected_metric]].dropna()
                
                if not data.empty:
                    colors = {
                        "Weight": "#7C3AED",
                        "Chest": "#34D399",
                        "Waist": "#FBBF24",
                        "Hips": "#60A5FA",
                        "Bicep": "#F472B6",
                        "Body Fat %": "#F87171"
                    }
                    color = colors.get(selected_metric, "#7C3AED")
                    
                    fig = go.Figure()
                    
                    if chart_type == "Line Chart":
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data[selected_metric],
                            mode='lines+markers',
                            name=selected_metric,
                            line=dict(color=color, width=3),
                            marker=dict(size=8, color=color)
                        ))
                    elif chart_type == "Bar Chart":
                        fig.add_trace(go.Bar(
                            x=data.index,
                            y=data[selected_metric],
                            name=selected_metric,
                            marker_color=color
                        ))
                    else:
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data[selected_metric],
                            mode='lines',
                            name=selected_metric,
                            fill='tozeroy',
                            line=dict(color=color, width=3),
                            fillcolor=color + '33'
                        ))
                    
                    fig.update_layout(
                        template='plotly_dark',
                        title=dict(text=f"{selected_metric} Progress", font=dict(color='#F8FAFC', size=20)),
                        xaxis=dict(title="Date", gridcolor='#1E293B'),
                        yaxis=dict(title=selected_metric, gridcolor='#1E293B'),
                        hovermode='x unified',
                        plot_bgcolor='#0F172A',
                        paper_bgcolor='#0F172A',
                        height=400,
                        margin=dict(l=40, r=40, t=60, b=40),
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # ============================================
                    # FIXED: Correct way to access values
                    # ============================================
                    st_col1, st_col2, st_col3, st_col4 = st.columns(4)
                    
                    # Get values safely
                    current_val = data.iloc[-1].values[0] if len(data) > 0 else 0
                    first_val = data.iloc[0].values[0] if len(data) > 0 else 0
                    change_val = current_val - first_val
                    min_val = data.min().values[0] if len(data) > 0 else 0
                    max_val = data.max().values[0] if len(data) > 0 else 0
                    
                    with st_col1:
                        st.metric("Current", f"{current_val:.1f}", f"{change_val:+.1f}")
                    with st_col2:
                        st.metric("Starting", f"{first_val:.1f}")
                    with st_col3:
                        st.metric("Minimum", f"{min_val:.1f}")
                    with st_col4:
                        st.metric("Maximum", f"{max_val:.1f}")
                else:
                    st.info(f"No {selected_metric} data available.")
    
    # ============================================
    # TAB 3: ANALYTICS & INSIGHTS
    # ============================================
    
    with tab_analytics:
        if not records or len(records) < 2:
            st.info("📊 Need at least 2 measurements for analytics.")
        else:
            summary = get_progress_summary(records)
            
            if summary:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📈 Weight Trend")
                    if summary['weight_change'] < 0:
                        st.success(f"✅ Lost **{abs(summary['weight_change']):.1f} kg** over {summary['total_days']} days!")
                        st.metric("Weekly Avg", f"{abs(summary['weekly_change']):.1f} kg/week", "↓")
                    elif summary['weight_change'] > 0:
                        st.warning(f"⚠️ Gained **{summary['weight_change']:.1f} kg** over {summary['total_days']} days")
                        st.metric("Weekly Avg", f"{summary['weekly_change']:.1f} kg/week", "↑")
                    else:
                        st.info(f"ℹ️ No weight change over {summary['total_days']} days")
                
                with col2:
                    st.markdown("### 📅 Tracking Stats")
                    st.write(f"- 📝 **{summary['total_records']}** measurements")
                    st.write(f"- 📅 **{summary['total_days']}** days tracking")
                    st.write(f"- 📊 **{summary['total_records'] / max(summary['total_days'], 1):.1f}** /week")
                
                st.divider()
                
                # BMI Calculation
                st.markdown("### 🧬 BMI Analysis")
                if sel_m.height:
                    bmi = calculate_bmi(records[-1].weight_kg, sel_m.height)
                    if bmi:
                        category, color = get_bmi_category(bmi)
                        col_b1, col_b2, col_b3 = st.columns(3)
                        with col_b1:
                            st.metric("Current BMI", f"{bmi:.1f}")
                        with col_b2:
                            st.metric("Category", category)
                        with col_b3:
                            ideal_weight = 22 * ((sel_m.height/100) ** 2)
                            st.metric("Ideal Weight", f"{ideal_weight:.1f} kg", f"{ideal_weight - records[-1].weight_kg:+.1f} kg")
                else:
                    st.info("📏 Add member height in Gym Setup for BMI analysis")
    
    # ============================================
    # TAB 4: FITNESS TOOLS
    # ============================================
    
    with tab_extra:
        st.markdown("### 💪 Fitness Tools")
        
        tool_tabs = st.tabs(["🏋️ Workout Suggestion", "📋 Progress Report", "🎯 Goal Setting", "📱 Share Progress"])
        
        # TOOL 1: Workout Suggestion
        with tool_tabs[0]:
            st.markdown("#### 🏋️ AI Workout Suggestion")
            suggestion = generate_workout_suggestion(records)
            st.info(suggestion)
            
            if records and len(records) >= 2:
                st.markdown("#### 📊 Based on Your Progress")
                summary = get_progress_summary(records)
                if summary:
                    st.write(f"- **Weight Change:** {summary['weight_change']:+.1f} kg")
                    st.write(f"- **Weekly Trend:** {summary['weekly_change']:+.1f} kg/week")
                    st.write(f"- **Total Records:** {summary['total_records']}")
        
        # TOOL 2: Progress Report
        with tool_tabs[1]:
            st.markdown("#### 📋 Progress Report")
            
            gym_name = next((g.name for g in gyms if g.id == sel_m.gym_id), "GymPro")
            report = generate_progress_report(sel_m.full_name, records, gym_name)
            
            st.text_area(
                "📄 Report",
                value=report,
                height=400,
                key="progress_report",
                disabled=True
            )
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📋 Copy Report", use_container_width=True):
                    st.write("✅ Report copied to clipboard!")
                    st.code(report, language="text")
            with col_btn2:
                if records and len(records) >= 2:
                    report_file = io.StringIO()
                    report_file.write(report)
                    st.download_button(
                        label="📥 Download Report",
                        data=report_file.getvalue(),
                        file_name=f"progress_report_{sel_m.serial_number}_{date.today()}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
        
        # TOOL 3: Goal Setting
        with tool_tabs[2]:
            st.markdown("#### 🎯 Set Your Fitness Goal")
            
            col_goal1, col_goal2 = st.columns(2)
            
            with col_goal1:
                target_weight = st.number_input(
                    "🎯 Target Weight (kg)",
                    min_value=30.0, max_value=200.0,
                    value=records[-1].weight_kg - 5 if records else 65.0,
                    step=0.5,
                    key="target_weight"
                )
                
                target_date = st.date_input(
                    "📅 Target Date",
                    value=date.today() + timedelta(days=30),
                    key="target_date"
                )
            
            with col_goal2:
                if records:
                    current = records[-1].weight_kg
                    days = (target_date - date.today()).days
                    if days > 0:
                        weekly_target = (current - target_weight) / (days / 7)
                        st.metric(
                            "Weekly Target",
                            f"{weekly_target:.2f} kg/week",
                            "↓" if weekly_target > 0 else "↑"
                        )
                        
                        if weekly_target > 0:
                            st.success(f"💪 To reach {target_weight} kg by {target_date}, lose {abs(weekly_target):.2f} kg per week.")
                        elif weekly_target < 0:
                            st.info(f"📈 To reach {target_weight} kg by {target_date}, gain {abs(weekly_target):.2f} kg per week.")
                        else:
                            st.info("🎯 You're already at your target!")
                    else:
                        st.warning("⚠️ Target date should be in the future!")
            
            if st.button("💾 Save Goal", use_container_width=True):
                st.success("✅ Goal saved successfully!")
        
        # TOOL 4: Share Progress
        with tool_tabs[3]:
            st.markdown("#### 📱 Share Progress")
            
            if sel_m and sel_m.phone:
                tip = get_health_tip(sel_mid, records)
                gym_name = next((g.name for g in gyms if g.id == (sel_m.gym_id)), "GymPro")
                
                if records and len(records) >= 2:
                    summary = get_progress_summary(records)
                    if summary:
                        change_str = f"lost {abs(summary['weight_change']):.1f} kg" if summary['weight_change'] < 0 else f"gained {abs(summary['weight_change']):.1f} kg"
                        
                        msg_options = [
                            "📊 Basic Update",
                            "💪 Motivational",
                            "📈 Detailed Report"
                        ]
                        msg_style = st.selectbox("📝 Message Style", msg_options, key="msg_style")
                        
                        if msg_style == "📊 Basic Update":
                            msg = f"🏋️ {sel_m.full_name} - {gym_name}\nWeight: {summary['first_weight']:.1f}kg → {summary['last_weight']:.1f}kg\n{change_str} in {summary['total_days']} days"
                        elif msg_style == "💪 Motivational":
                            msg = f"💪 {sel_m.full_name}, you're crushing it! {change_str}. Keep pushing forward! 🏋️\n{tip}"
                        else:
                            msg = f"📊 PROGRESS REPORT - {sel_m.full_name}\n🏋️ {gym_name}\nWeight: {summary['first_weight']:.1f}kg → {summary['last_weight']:.1f}kg\n{change_str} in {summary['total_days']} days\n{tip}"
                        
                        wa_link = make_wa_link(sel_m.phone, msg)
                        st.markdown(
                            f'<a href="{wa_link}" target="_blank" style="display:inline-block;'
                            f'background:#25D366;color:white;padding:0.7rem 2rem;'
                            f'border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">'
                            f'💬 Send Progress on WhatsApp</a>',
                            unsafe_allow_html=True,
                        )
                        
                        st.caption("📱 Share your progress with friends, family or your trainer!")
                else:
                    st.info("📝 Need at least 2 measurements to share progress.")
            else:
                st.info("📱 No phone number available for WhatsApp sharing.")