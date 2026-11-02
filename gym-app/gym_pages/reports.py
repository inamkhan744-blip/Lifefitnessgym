import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
import database as db
import styles
import io
import base64

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

def init_session_state():
    if 'report_photo_cache' not in st.session_state:
        st.session_state.report_photo_cache = {}
    if 'report_refresh' not in st.session_state:
        st.session_state.report_refresh = False

init_session_state()

# ============================================
# ── ★★★ EXPORT FUNCTIONS ★★★ ──
# ============================================

def export_to_csv(df, filename):
    """Export DataFrame to CSV"""
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        f"📥 Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        key=f"csv_export_{filename}_{datetime.now().timestamp()}"
    )

def export_to_excel(df, filename):
    """Export DataFrame to Excel"""
    try:
        import openpyxl
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        excel_data = output.getvalue()
        st.download_button(
            f"📥 Download Excel",
            data=excel_data,
            file_name=filename.replace('.csv', '.xlsx'),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"excel_export_{filename}_{datetime.now().timestamp()}"
        )
    except ImportError:
        st.warning("⚠️ openpyxl not installed. Install with: pip install openpyxl")

def export_to_pdf(df, filename, title="Report"):
    """Export DataFrame to PDF"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(letter))
        elements = []
        
        # Title
        styles_pdf = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles_pdf['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#7C3AED')
        )
        elements.append(Paragraph(f"<b>{title}</b>", title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles_pdf['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Table data
        table_data = [df.columns.tolist()] + df.values.tolist()
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#334155')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0F172A'), colors.HexColor('#1E293B')]),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        pdf_data = output.getvalue()
        st.download_button(
            f"📥 Download PDF",
            data=pdf_data,
            file_name=filename.replace('.csv', '.pdf'),
            mime="application/pdf",
            key=f"pdf_export_{filename}_{datetime.now().timestamp()}"
        )
    except ImportError:
        st.warning("⚠️ reportlab not installed. Install with: pip install reportlab")

def render_export_buttons(df, title="Report", filename=None):
    """Render all export buttons for a DataFrame"""
    if filename is None:
        filename = f"{title}_{date.today().strftime('%Y-%m-%d')}.csv"
    
    st.markdown("#### 📤 Export Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_to_csv(df, filename)
    
    with col2:
        export_to_excel(df, filename)
    
    with col3:
        export_to_pdf(df, filename, title)
    
    st.caption(f"📊 {len(df)} rows exported")


# ============================================
# 3D CSS STYLES
# ============================================

st.markdown("""
<style>
    /* 3D Card Effect */
    .card-3d {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 
            0 10px 30px rgba(0,0,0,0.5),
            0 4px 10px rgba(0,0,0,0.3),
            inset 0 -2px 0 rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .card-3d:hover {
        transform: translateY(-5px);
        box-shadow: 
            0 20px 40px rgba(0,0,0,0.6),
            0 8px 20px rgba(0,0,0,0.4),
            inset 0 -2px 0 rgba(255,255,255,0.08);
    }
    
    .card-3d::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #7C3AED, #A78BFA, #7C3AED);
        box-shadow: 0 0 20px rgba(124,58,237,0.3);
    }
    
    .card-3d .icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .card-3d .value {
        font-size: 2rem;
        font-weight: 800;
        color:var(--gp-text);
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .card-3d .label {
        font-size: 0.8rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }
    
    .card-3d .change {
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.3rem;
    }
    
    .card-3d .change.positive {
        color: #34D399;
    }
    
    .card-3d .change.negative {
        color: #F87171;
    }
    
    .card-3d .change.neutral {
        color: #FBBF24;
    }
    
    .card-3d.glow-purple {
        border-color: rgba(124,58,237,0.3);
    }
    
    .card-3d.glow-green {
        border-color: rgba(52,211,153,0.3);
    }
    
    .card-3d.glow-red {
        border-color: rgba(248,113,113,0.3);
    }
    
    .card-3d.glow-yellow {
        border-color: rgba(251,191,36,0.3);
    }
    
    .card-3d.glow-blue {
        border-color: rgba(96,165,250,0.3);
    }
    
    /* Staff Card */
    .staff-card {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .staff-card:hover {
        transform: translateY(-3px);
        border-color: #7C3AED;
        box-shadow: 0 8px 25px rgba(124,58,237,0.2);
    }
    
    .staff-card .staff-name {
        font-size: 1.1rem;
        font-weight: 700;
        color:var(--gp-text);
    }
    
    .staff-card .staff-role {
        font-size: 0.8rem;
        color: #94A3B8;
    }
    
    .staff-card .staff-stats {
        font-size: 0.85rem;
        color: #34D399;
        font-weight: 600;
        margin-top: 0.3rem;
    }
    
    /* Tab Navigation */
    .report-tab {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .report-tab.active {
        background: #7C3AED;
        color: white;
    }
    
    .report-tab:hover {
        background: rgba(124,58,237,0.2);
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# MONTHLY GYM SUMMARY REPORT
# ============================================

def render_monthly_gym_summary(gym_id, date_from, date_to):
    """Render monthly gym-wise summary report"""
    st.subheader("🏋️ Monthly Gym Summary")
    st.caption("Har gym ka month-wise collection, expenses aur profit")
    
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("No gyms found")
        return
    
    # ── Get all months in range ──────────────────────────────────────────
    months = []
    current = date_from
    while current <= date_to:
        months.append(current.strftime("%Y-%m"))
        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    # ── Collect data for each gym ──────────────────────────────────────
    all_data = []
    
    for gym in gyms:
        # Filter if specific gym selected
        if gym_id and gym.id != gym_id:
            continue
            
        gym_total_collection = 0
        gym_total_expenses = 0
        gym_total_profit = 0
        gym_total_members = 0
        
        for month in months:
            month_start = datetime.strptime(month, "%Y-%m").date()
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            # Collection
            fees = db.get_fee_records(
                gym_id=gym.id,
                date_from=month_start,
                date_to=month_end
            )
            collection = sum(f.amount for f in fees) if fees else 0
            payments = len(fees) if fees else 0
            members = len(set(f.member_id for f in fees)) if fees else 0
            
            # Expenses
            expenses = db.get_expenses(
                gym_id=gym.id,
                date_from=month_start,
                date_to=month_end
            )
            total_expenses = sum(e.amount for e in expenses) if expenses else 0
            
            profit = collection - total_expenses
            
            all_data.append({
                "Gym": gym.name,
                "Month": month,
                "Collection": collection,
                "Expenses": total_expenses,
                "Profit": profit,
                "Members": members,
                "Payments": payments,
            })
            
            gym_total_collection += collection
            gym_total_expenses += total_expenses
            gym_total_profit += profit
            gym_total_members += members
        
        # ── Gym Summary Card ──────────────────────────────────────────────
        if gym_id and gym.id == gym_id:
            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                        border:1px solid #7C3AED;
                        border-radius:16px;
                        padding:1.2rem;
                        margin-bottom:1rem;
                        box-shadow:0 4px 25px rgba(124,58,237,0.15);">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                    <div>
                        <div style="font-size:1.3rem;font-weight:800;color:#FFFFFF;">🏋️ {gym.name}</div>
                        <div style="color:#94A3B8;font-size:0.85rem;">{len(months)} months</div>
                    </div>
                    <div style="display:flex;gap:1rem;flex-wrap:wrap;">
                        <div style="text-align:center;">
                            <div style="color:#94A3B8;font-size:0.65rem;">Total Collection</div>
                            <div style="color:#34D399;font-size:1.2rem;font-weight:700;">PKR {gym_total_collection:,.0f}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="color:#94A3B8;font-size:0.65rem;">Total Expenses</div>
                            <div style="color:#F87171;font-size:1.2rem;font-weight:700;">PKR {gym_total_expenses:,.0f}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="color:#94A3B8;font-size:0.65rem;">Net Profit</div>
                            <div style="color:{"#34D399" if gym_total_profit >= 0 else "#F87171"};font-size:1.2rem;font-weight:700;">
                                PKR {gym_total_profit:,.0f}
                            </div>
                        </div>
                        <div style="text-align:center;">
                            <div style="color:#94A3B8;font-size:0.65rem;">Total Members</div>
                            <div style="color:#60A5FA;font-size:1.2rem;font-weight:700;">{gym_total_members}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if not all_data:
        st.info("No data found for the selected period")
        return
    
    df = pd.DataFrame(all_data)
    
    # ── Summary Cards ──────────────────────────────────────────────────────
    total_collection = df['Collection'].sum()
    total_expenses = df['Expenses'].sum()
    total_profit = df['Profit'].sum()
    total_members = df['Members'].sum()
    total_payments = df['Payments'].sum()
    
    st.markdown("### 📊 Overall Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Total Collection", f"PKR {total_collection:,.0f}")
    with col2:
        st.metric("💸 Total Expenses", f"PKR {total_expenses:,.0f}")
    with col3:
        profit_color = "normal" if total_profit >= 0 else "inverse"
        st.metric("📈 Net Profit", f"PKR {total_profit:,.0f}", delta_color=profit_color)
    with col4:
        st.metric("👥 Total Members", f"{total_members}")
    with col5:
        st.metric("📋 Total Payments", f"{total_payments}")
    
    st.divider()
    
    # ── Month Filter ──────────────────────────────────────────────────────
    months_available = sorted(df['Month'].unique(), reverse=True)
    selected_month = st.selectbox("📅 Select Month", months_available, key="monthly_gym_month")
    
    month_df = df[df['Month'] == selected_month]
    
    if not month_df.empty:
        st.subheader(f"📊 {selected_month} — Gym-wise Breakdown")
        
        # Gym comparison chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=month_df['Gym'],
            y=month_df['Collection'],
            name='Collection',
            marker=dict(color='#34D399'),
            text=[f'PKR {c:,.0f}' for c in month_df['Collection']],
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            x=month_df['Gym'],
            y=month_df['Expenses'],
            name='Expenses',
            marker=dict(color='#F87171'),
            text=[f'PKR {c:,.0f}' for c in month_df['Expenses']],
            textposition='outside'
        ))
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350,
            margin=dict(l=40, r=20, t=30, b=40),
            xaxis=dict(gridcolor='#1E293B'),
            yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            barmode='group',
        )
        st.plotly_chart(fig, width="stretch", key="monthly_gym_chart_1")
    
    st.divider()
    
    # ── Monthly Trend for Selected Gym ──────────────────────────────────
    if gym_id:
        gym_name = next((g.name for g in gyms if g.id == gym_id), "Selected Gym")
        st.subheader(f"📈 Monthly Trend — {gym_name}")
        gym_df = df[df['Gym'] == gym_name]
        
        if not gym_df.empty:
            fig3 = go.Figure()
            
            fig3.add_trace(go.Scatter(
                x=gym_df['Month'],
                y=gym_df['Collection'],
                mode='lines+markers',
                name='Collection',
                line=dict(color='#34D399', width=3),
                marker=dict(size=8, color='#34D399'),
                fill='tozeroy',
                fillcolor='rgba(52,211,153,0.15)'
            ))
            
            fig3.add_trace(go.Scatter(
                x=gym_df['Month'],
                y=gym_df['Expenses'],
                mode='lines+markers',
                name='Expenses',
                line=dict(color='#F87171', width=3),
                marker=dict(size=8, color='#F87171'),
                fill='tozeroy',
                fillcolor='rgba(248,113,113,0.15)'
            ))
            
            fig3.add_trace(go.Scatter(
                x=gym_df['Month'],
                y=gym_df['Profit'],
                mode='lines+markers',
                name='Profit',
                line=dict(color='#FFC947', width=3),
                marker=dict(size=8, color='#FFC947'),
            ))
            
            fig3.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                margin=dict(l=40, r=20, t=30, b=40),
                xaxis=dict(gridcolor='#1E293B'),
                yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig3, width="stretch", key="monthly_gym_trend")
    
    # ── All Months Table ──────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 All Months Data")
    
    all_df = df.copy()
    all_df['Collection'] = all_df['Collection'].apply(lambda x: f"PKR {x:,.0f}")
    all_df['Expenses'] = all_df['Expenses'].apply(lambda x: f"PKR {x:,.0f}")
    all_df['Profit'] = all_df['Profit'].apply(lambda x: f"PKR {x:,.0f}")
    
    st.dataframe(
        all_df[['Gym', 'Month', 'Collection', 'Expenses', 'Profit', 'Members', 'Payments']],
        width="stretch",
        hide_index=True
    )
    
    # ── Export ──────────────────────────────────────────────────────────────
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Monthly Gym Summary CSV",
        data=csv,
        file_name=f"monthly_gym_summary_{date.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
        key="monthly_gym_csv_download"
    )


# ============================================
# GYM COMPARISON DASHBOARD
# ============================================

def render_gym_comparison_dashboard(gym_id, date_from, date_to):
    """Render gym comparison dashboard"""
    st.subheader("🏋️ Gym Comparison Dashboard")
    
    gyms = db.get_all_gyms()
    if not gyms or len(gyms) < 2:
        st.info("Need at least 2 gyms for comparison")
        return
    
    # ── Get data for all gyms ────────────────────────────────────────────
    gym_data = []
    
    for gym in gyms:
        if gym_id and gym.id != gym_id:
            continue
            
        fees = db.get_fee_records(gym_id=gym.id, date_from=date_from, date_to=date_to)
        expenses = db.get_expenses(gym_id=gym.id, date_from=date_from, date_to=date_to)
        
        collection = sum(f.amount for f in fees) if fees else 0
        total_expenses = sum(e.amount for e in expenses) if expenses else 0
        profit = collection - total_expenses
        members = len(set(f.member_id for f in fees)) if fees else 0
        payments = len(fees) if fees else 0
        
        gym_data.append({
            "Gym": gym.name,
            "Collection": collection,
            "Expenses": total_expenses,
            "Profit": profit,
            "Members": members,
            "Payments": payments,
            "Avg Payment": collection / payments if payments > 0 else 0,
        })
    
    if not gym_data:
        st.info("No data found")
        return
    
    df = pd.DataFrame(gym_data)
    df = df.sort_values('Collection', ascending=False)
    
    # ── Summary Cards ──────────────────────────────────────────────────────
    total_collection = df['Collection'].sum()
    total_expenses = df['Expenses'].sum()
    total_profit = df['Profit'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Collection", f"PKR {total_collection:,.0f}")
    with col2:
        st.metric("💸 Total Expenses", f"PKR {total_expenses:,.0f}")
    with col3:
        profit_color = "normal" if total_profit >= 0 else "inverse"
        st.metric("📈 Net Profit", f"PKR {total_profit:,.0f}", delta_color=profit_color)
    
    st.divider()
    
    # ── Comparison Charts ────────────────────────────────────────────────
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=df['Gym'],
        y=df['Collection'],
        name='Collection',
        marker=dict(color='#34D399'),
        text=[f'PKR {c:,.0f}' for c in df['Collection']],
        textposition='outside'
    ))
    
    fig1.add_trace(go.Bar(
        x=df['Gym'],
        y=df['Expenses'],
        name='Expenses',
        marker=dict(color='#F87171'),
        text=[f'PKR {c:,.0f}' for c in df['Expenses']],
        textposition='outside'
    ))
    
    fig1.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(gridcolor='#1E293B'),
        yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode='group',
    )
    st.plotly_chart(fig1, width="stretch", key="gym_compare_chart_1")
    
    # ── Profit Chart ──────────────────────────────────────────────────────
    fig2 = go.Figure()
    
    colors = ['#34D399' if p >= 0 else '#F87171' for p in df['Profit']]
    
    fig2.add_trace(go.Bar(
        x=df['Gym'],
        y=df['Profit'],
        name='Profit/Loss',
        marker=dict(color=colors),
        text=[f'PKR {p:,.0f}' for p in df['Profit']],
        textposition='outside'
    ))
    
    fig2.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=250,
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis=dict(gridcolor='#1E293B'),
        yaxis=dict(gridcolor='#1E293B', title='Profit/Loss (PKR)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig2, width="stretch", key="gym_compare_chart_2")
    
    # ── Ranking ──────────────────────────────────────────────────────────
    st.subheader("🏆 Gym Ranking")
    
    for i, row in df.iterrows():
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        profit_color = "#34D399" if row['Profit'] >= 0 else "#F87171"
        
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    background:#0F172A;border:1px solid #1E293B;
                    border-radius:12px;padding:0.8rem 1.2rem;
                    margin-bottom:0.5rem;">
            <div style="display:flex;align-items:center;gap:1rem;">
                <span style="font-size:1.5rem;">{medal}</span>
                <div>
                    <div style="font-weight:700;color:#FFFFFF;font-size:1.1rem;">{row['Gym']}</div>
                    <div style="color:#94A3B8;font-size:0.8rem;">{row['Members']} members · {row['Payments']} payments</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#FFC947;font-weight:700;">PKR {row['Collection']:,.0f}</div>
                <div style="color:{profit_color};font-weight:600;">Profit: PKR {row['Profit']:,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ── Export ──────────────────────────────────────────────────────────────
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Gym Comparison CSV",
        data=csv,
        file_name=f"gym_comparison_{date.today().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
        key="gym_compare_csv_download"
    )


# ============================================
# MEMBER REPORTS
# ============================================

def render_member_reports(gym_id, date_from, date_to):
    """Render member analytics reports"""
    st.subheader("👥 Member Reports")
    
    members = db.get_members(gym_id=gym_id)
    
    if not members:
        st.info("No members found")
        return
    
    # Member stats
    total_members = len(members)
    active_members = sum(1 for m in members if m.status == "Active")
    inactive_members = sum(1 for m in members if m.status == "Inactive")
    expired_members = sum(1 for m in members if m.status == "Expired")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Members", total_members)
    with col2:
        st.metric("✅ Active", active_members)
    with col3:
        st.metric("❌ Inactive", inactive_members)
    with col4:
        st.metric("⏰ Expired", expired_members)
    
    st.divider()
    
    # Membership type distribution
    st.markdown("#### 📊 Membership Type Distribution")
    types = {}
    for m in members:
        mtype = m.membership_type or "Unknown"
        types[mtype] = types.get(mtype, 0) + 1
    
    if types:
        df_types = pd.DataFrame({
            "Type": list(types.keys()),
            "Count": list(types.values())
        })
        
        fig = px.pie(df_types, values="Count", names="Type", title="Membership Types",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, width="stretch", key="member_types_pie")
    
    # Member growth trend
    st.markdown("#### 📈 Member Growth Trend")
    join_dates = []
    for m in members:
        if m.join_date:
            try:
                join_dates.append(datetime.strptime(m.join_date, "%Y-%m-%d").date())
            except:
                pass
    
    if join_dates:
        df_join = pd.DataFrame({"Date": join_dates})
        df_join["Count"] = 1
        df_join = df_join.groupby("Date").sum().reset_index()
        df_join["Cumulative"] = df_join["Count"].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_join["Date"],
            y=df_join["Cumulative"],
            mode='lines+markers',
            name='Total Members',
            line=dict(color='#7C3AED', width=3),
            marker=dict(size=8, color='#A78BFA'),
            fill='tozeroy',
            fillcolor='rgba(124,58,237,0.15)'
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis=dict(gridcolor='#1E293B'),
            yaxis=dict(gridcolor='#1E293B', title="Members")
        )
        st.plotly_chart(fig, width="stretch", key="member_growth_chart")
    
    # Latest members
    st.markdown("#### 🆕 Latest 10 Members")
    latest = sorted(join_dates, reverse=True)[:10] if join_dates else []
    if latest:
        latest_members = []
        for d in latest:
            for m in members:
                if m.join_date == str(d):
                    latest_members.append({
                        "Name": m.full_name,
                        "Serial": m.serial_number,
                        "Join Date": m.join_date,
                        "Type": m.membership_type or "-",
                        "Status": m.status
                    })
                    break
        df_latest = pd.DataFrame(latest_members[:10])
        st.dataframe(df_latest, width="stretch", hide_index=True)


# ============================================
# REVENUE REPORTS
# ============================================

def render_revenue_reports(gym_id, date_from, date_to):
    """Render revenue analytics reports"""
    st.subheader("💰 Revenue Reports")
    
    # Get fee records
    fees = db.get_fee_records(gym_id=gym_id, date_from=date_from, date_to=date_to)
    
    if not fees:
        st.info("No revenue data found")
        return
    
    # Revenue stats
    total_revenue = sum(f.amount for f in fees)
    total_transactions = len(fees)
    avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Revenue", f"PKR {total_revenue:,.0f}")
    with col2:
        st.metric("📊 Transactions", total_transactions)
    with col3:
        st.metric("📈 Avg Transaction", f"PKR {avg_transaction:,.0f}")
    
    st.divider()
    
    # Daily revenue trend
    st.markdown("#### 📈 Daily Revenue Trend")
    df = pd.DataFrame([{
        "Date": f.payment_date,
        "Amount": f.amount
    } for f in fees])
    df["Date"] = pd.to_datetime(df["Date"])
    daily = df.groupby("Date")["Amount"].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["Date"],
        y=daily["Amount"],
        marker=dict(color='#10B981'),
        text=[f'PKR {a:,.0f}' for a in daily["Amount"]],
        textposition='outside',
        textfont=dict(color='white', size=10)
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor='#1E293B'),
        yaxis=dict(gridcolor='#1E293B', title="Amount (PKR)")
    )
    st.plotly_chart(fig, width="stretch", key="revenue_daily_chart")
    
    # Payment method distribution
    st.markdown("#### 💳 Payment Method Distribution")
    methods = {}
    for f in fees:
        method = f.payment_method or "Cash"
        methods[method] = methods.get(method, 0) + f.amount
    
    if methods:
        df_methods = pd.DataFrame({
            "Method": list(methods.keys()),
            "Amount": list(methods.values())
        })
        
        fig = px.pie(df_methods, values="Amount", names="Method", title="Payment Methods",
                     color_discrete_sequence=['#7C3AED', '#34D399', '#FBBF24', '#F87171', '#60A5FA'])
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, width="stretch", key="revenue_method_pie")


# ============================================
# EXPENSE REPORTS
# ============================================

def render_expense_reports(gym_id, date_from, date_to):
    """Render expense analytics reports"""
    st.subheader("💳 Expense Reports")
    
    expenses = db.get_expenses(gym_id=gym_id, date_from=date_from, date_to=date_to)
    
    if not expenses:
        st.info("No expense data found")
        return
    
    # Expense stats
    total_expenses = sum(e.amount for e in expenses)
    total_entries = len(expenses)
    avg_expense = total_expenses / total_entries if total_entries > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💳 Total Expenses", f"PKR {total_expenses:,.0f}")
    with col2:
        st.metric("📊 Entries", total_entries)
    with col3:
        st.metric("📈 Avg Expense", f"PKR {avg_expense:,.0f}")
    
    st.divider()
    
    # Category breakdown
    st.markdown("#### 📊 Expense by Category")
    categories = {}
    for e in expenses:
        cat = e.category or "Other"
        categories[cat] = categories.get(cat, 0) + e.amount
    
    if categories:
        df_cat = pd.DataFrame({
            "Category": list(categories.keys()),
            "Amount": list(categories.values())
        })
        
        fig = px.pie(df_cat, values="Amount", names="Category", title="Expense Categories",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, width="stretch", key="expense_category_pie")
    
    # Daily expense trend
    st.markdown("#### 📉 Daily Expense Trend")
    df = pd.DataFrame([{
        "Date": e.expense_date,
        "Amount": e.amount
    } for e in expenses])
    df["Date"] = pd.to_datetime(df["Date"])
    daily = df.groupby("Date")["Amount"].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["Date"],
        y=daily["Amount"],
        mode='lines+markers',
        name='Expenses',
        line=dict(color='#EF4444', width=3),
        marker=dict(size=8, color='#F87171'),
        fill='tozeroy',
        fillcolor='rgba(239,68,68,0.15)'
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor='#1E293B'),
        yaxis=dict(gridcolor='#1E293B', title="Amount (PKR)")
    )
    st.plotly_chart(fig, width="stretch", key="expense_daily_chart")


# ============================================
# ATTENDANCE REPORTS
# ============================================

def render_attendance_reports(gym_id, date_from, date_to):
    """Render attendance analytics reports"""
    st.subheader("📅 Attendance Reports")
    
    attendance = db.get_attendance_range(gym_id=gym_id, from_date=date_from, to_date=date_to)
    
    if not attendance:
        st.info("No attendance data found")
        return
    
    # Attendance stats
    total = len(attendance)
    present = sum(1 for a in attendance if a.status == "Present")
    absent = sum(1 for a in attendance if a.status == "Absent")
    late = sum(1 for a in attendance if a.status == "Late")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Records", total)
    with col2:
        st.metric("✅ Present", present)
    with col3:
        st.metric("❌ Absent", absent)
    with col4:
        st.metric("🕐 Late", late)
    
    # Attendance rate
    rate = (present / total * 100) if total > 0 else 0
    st.metric("📈 Attendance Rate", f"{rate:.1f}%")
    
    st.divider()
    
    # Daily attendance trend
    st.markdown("#### 📈 Daily Attendance Trend")
    df = pd.DataFrame([{
        "Date": a.check_date,
        "Status": a.status
    } for a in attendance])
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Count by date and status
    pivot = df.groupby(["Date", "Status"]).size().unstack(fill_value=0)
    
    fig = go.Figure()
    for status in ["Present", "Late", "Absent"]:
        if status in pivot.columns:
            color = {"Present": "#10B981", "Late": "#FBBF24", "Absent": "#EF4444"}
            fig.add_trace(go.Bar(
                x=pivot.index,
                y=pivot[status],
                name=status,
                marker_color=color.get(status, "#94A3B8")
            ))
    
    fig.update_layout(
        barmode="stack",
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(gridcolor='#1E293B'),
        yaxis=dict(gridcolor='#1E293B', title="Count"),
        legend=dict(orientation="h", y=1.02, x=0.5)
    )
    st.plotly_chart(fig, width="stretch", key="attendance_daily_chart")


# ============================================
# FINANCIAL SUMMARY
# ============================================

def render_financial_summary(gym_id, date_from, date_to):
    """Render financial summary report"""
    st.subheader("📊 Financial Summary")
    
    # Get data
    fees = db.get_fee_records(gym_id=gym_id, date_from=date_from, date_to=date_to)
    expenses = db.get_expenses(gym_id=gym_id, date_from=date_from, date_to=date_to)
    
    total_revenue = sum(f.amount for f in fees) if fees else 0
    total_expenses = sum(e.amount for e in expenses) if expenses else 0
    net_profit = total_revenue - total_expenses
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        color = "#34D399" if net_profit >= 0 else "#EF4444"
        st.markdown(f"""
        <div class="card-3d glow-{'green' if net_profit >= 0 else 'red'}" style="text-align:center;padding:0.8rem;">
            <span class="icon">{'📈' if net_profit >= 0 else '📉'}</span>
            <div class="value" style="color:{color};">PKR {net_profit:,.0f}</div>
            <div class="label">Net Profit / Loss</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="card-3d glow-green" style="text-align:center;padding:0.8rem;">
            <span class="icon">💰</span>
            <div class="value">PKR {total_revenue:,.0f}</div>
            <div class="label">Total Revenue</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="card-3d glow-red" style="text-align:center;padding:0.8rem;">
            <span class="icon">💳</span>
            <div class="value">PKR {total_expenses:,.0f}</div>
            <div class="label">Total Expenses</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.markdown(f"""
        <div class="card-3d glow-yellow" style="text-align:center;padding:0.8rem;">
            <span class="icon">📊</span>
            <div class="value">{margin:.1f}%</div>
            <div class="label">Profit Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Revenue vs Expenses chart
    st.markdown("#### 📊 Revenue vs Expenses")
    
    # Get monthly data
    monthly_data = {}
    for f in fees:
        if f.payment_date:
            month = f.payment_date[:7]
            monthly_data[month] = monthly_data.get(month, {"revenue": 0, "expenses": 0})
            monthly_data[month]["revenue"] += f.amount
    
    for e in expenses:
        if e.expense_date:
            month = e.expense_date[:7]
            if month not in monthly_data:
                monthly_data[month] = {"revenue": 0, "expenses": 0}
            monthly_data[month]["expenses"] += e.amount
    
    if monthly_data:
        months = sorted(monthly_data.keys())
        revenue_data = [monthly_data[m]["revenue"] for m in months]
        expense_data = [monthly_data[m]["expenses"] for m in months]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months,
            y=revenue_data,
            name='Revenue',
            marker_color='#10B981'
        ))
        fig.add_trace(go.Bar(
            x=months,
            y=expense_data,
            name='Expenses',
            marker_color='#EF4444'
        ))
        fig.update_layout(
            barmode='group',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis=dict(gridcolor='#1E293B'),
            yaxis=dict(gridcolor='#1E293B', title="Amount (PKR)")
        )
        st.plotly_chart(fig, width="stretch", key="financial_rev_exp_chart")


# ============================================
# TOP MEMBERS REPORT
# ============================================

def render_top_members_report(gym_id, date_from, date_to):
    """Render top paying members report"""
    st.subheader("🏆 Top Paying Members")
    
    fees = db.get_fee_records(gym_id=gym_id, date_from=date_from, date_to=date_to)
    
    if not fees:
        st.info("No payment data found")
        return
    
    # Aggregate by member
    member_data = {}
    for f in fees:
        mid = f.member_id
        if mid not in member_data:
            member_data[mid] = {"total": 0, "count": 0, "name": "", "serial": ""}
        member_data[mid]["total"] += f.amount
        member_data[mid]["count"] += 1
    
    # Get member names
    for mid in member_data:
        member = db.get_member(mid)
        if member:
            member_data[mid]["name"] = member.full_name
            member_data[mid]["serial"] = member.serial_number
    
    # Sort by total
    sorted_members = sorted(member_data.items(), key=lambda x: x[1]["total"], reverse=True)
    
    if sorted_members:
        data = []
        for idx, (mid, info) in enumerate(sorted_members[:20], 1):
            data.append({
                "Rank": idx,
                "Member": info["name"] or "Unknown",
                "Serial": info["serial"] or "-",
                "Total Paid": f"PKR {info['total']:,.0f}",
                "Transactions": info["count"],
                "Avg": f"PKR {info['total']/info['count']:,.0f}" if info["count"] > 0 else "0"
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, width="stretch", hide_index=True)
        
        # Export
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Top Members Report",
            data=csv,
            file_name=f"top_members_{date.today()}.csv",
            mime="text/csv",
            key="top_members_csv_download"
        )
    else:
        st.info("No member data available")


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_staff_reports(gym_id=None, staff_name=None, date_from=None, date_to=None):
    """Get comprehensive staff reports"""
    
    reports = {
        'staff_info': {},
        'attendance': {},
        'fee_collection': {},
        'expenses': {},
        'inventory_sales': {},
        'summary': {}
    }
    
    # Get all staff (users)
    all_users = db.get_all_users()
    
    # Filter by gym if needed
    if gym_id:
        all_users = [u for u in all_users if u.gym_id == gym_id]
    
    # Filter by staff name if needed
    if staff_name:
        all_users = [u for u in all_users if u.full_name == staff_name]
    
    for user in all_users:
        staff_data = {
            'name': user.full_name,
            'role': user.role,
            'username': user.username,
            'gym_id': user.gym_id,
            'is_active': user.is_active,
        }
        
        # Get attendance records by this staff
        attendance_count = 0
        fee_count = 0
        fee_amount = 0
        expense_count = 0
        expense_amount = 0
        sale_count = 0
        sale_amount = 0
        
        # Attendance
        try:
            db_session = db.get_db()
            att_records = db_session.query(db.Attendance).filter(
                db.Attendance.marked_by == user.username
            )
            if date_from:
                att_records = att_records.filter(db.Attendance.check_date >= str(date_from))
            if date_to:
                att_records = att_records.filter(db.Attendance.check_date <= str(date_to))
            attendance_count = att_records.count()
        except:
            pass
        
        # Fee Collection
        try:
            fee_records = db.get_fee_records(gym_id=gym_id)
            fee_records = [r for r in fee_records if r.collected_by == user.username]
            if date_from:
                fee_records = [r for r in fee_records if r.payment_date and pd.to_datetime(r.payment_date).date() >= date_from]
            if date_to:
                fee_records = [r for r in fee_records if r.payment_date and pd.to_datetime(r.payment_date).date() <= date_to]
            fee_count = len(fee_records)
            fee_amount = sum(r.amount for r in fee_records)
        except:
            pass
        
        # Expenses
        try:
            expense_records = db.get_expenses(gym_id=gym_id)
            expense_records = [r for r in expense_records if r.staff_name == user.full_name]
            if date_from:
                expense_records = [r for r in expense_records if r.expense_date and pd.to_datetime(r.expense_date).date() >= date_from]
            if date_to:
                expense_records = [r for r in expense_records if r.expense_date and pd.to_datetime(r.expense_date).date() <= date_to]
            expense_count = len(expense_records)
            expense_amount = sum(r.amount for r in expense_records)
        except:
            pass
        
        # Inventory Sales
        try:
            sale_records = db.get_stock_sales(gym_id=gym_id)
            sale_records = [r for r in sale_records if r.sold_by == user.username]
            if date_from:
                sale_records = [r for r in sale_records if r.sale_date and pd.to_datetime(r.sale_date).date() >= date_from]
            if date_to:
                sale_records = [r for r in sale_records if r.sale_date and pd.to_datetime(r.sale_date).date() <= date_to]
            sale_count = len(sale_records)
            sale_amount = sum(r.total_amount for r in sale_records)
        except:
            pass
        
        staff_data['attendance_count'] = attendance_count
        staff_data['fee_count'] = fee_count
        staff_data['fee_amount'] = fee_amount
        staff_data['expense_count'] = expense_count
        staff_data['expense_amount'] = expense_amount
        staff_data['sale_count'] = sale_count
        staff_data['sale_amount'] = sale_amount
        
        reports['staff_info'][user.username] = staff_data
    
    return reports


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role, username):
    
    styles.page_header("📊", "Reports & Analytics",
                       "Comprehensive reports for staff, finances, members, and performance")
    
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    # ============================================
    # FILTERS
    # ============================================
    
    st.markdown("""
    <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                border:1px solid #334155;
                border-radius:12px;
                padding:1rem;
                margin-bottom:1rem;
                box-shadow:0 4px 15px rgba(0,0,0,0.3);">
    """, unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1])
    
    with col_f1:
        if gym_id:
            sel_gid = gym_id
            st.text_input("🏋️ Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True)
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("🏋️ Gym", list(opts.keys()))
            sel_gid = opts[chosen]
    
    with col_f2:
        date_from = st.date_input("📅 From", value=date.today().replace(day=1))
    
    with col_f3:
        date_to = st.date_input("📅 To", value=date.today())
    
    with col_f4:
        st.write("")
        st.write("")
        if st.button("🔄 Generate Reports", width='stretch'):
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TABS
    # ============================================
    
    tab_staff, tab_members, tab_revenue, tab_expenses, tab_attendance, tab_financial, tab_top, tab_monthly, tab_gym_compare = st.tabs([
        "👥 Staff", "👤 Members", "💰 Revenue", "💳 Expenses", 
        "📅 Attendance", "📊 Financial", "🏆 Top Members",
        "📆 Monthly Gym", "🏋️ Gym Compare"
    ])
    
    # ── TAB 1: STAFF REPORTS ──────────────────────────────────────────────
    with tab_staff:
        reports_data = get_staff_reports(gym_id=sel_gid, date_from=date_from, date_to=date_to)
        staff_list = list(reports_data['staff_info'].values())
        
        if staff_list:
            total_staff = len(staff_list)
            total_fees = sum(s['fee_amount'] for s in staff_list)
            total_expenses = sum(s['expense_amount'] for s in staff_list)
            total_sales = sum(s['sale_amount'] for s in staff_list)
            total_attendance = sum(s['attendance_count'] for s in staff_list)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f"""
                <div class="card-3d glow-purple" style="text-align:center;padding:0.8rem;">
                    <span class="icon">👥</span>
                    <div class="value">{total_staff}</div>
                    <div class="label">Total Staff</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="card-3d glow-green" style="text-align:center;padding:0.8rem;">
                    <span class="icon">💰</span>
                    <div class="value">PKR {total_fees:,.0f}</div>
                    <div class="label">Total Fees Collected</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="card-3d glow-red" style="text-align:center;padding:0.8rem;">
                    <span class="icon">💳</span>
                    <div class="value">PKR {total_expenses:,.0f}</div>
                    <div class="label">Total Expenses</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="card-3d glow-yellow" style="text-align:center;padding:0.8rem;">
                    <span class="icon">📦</span>
                    <div class="value">PKR {total_sales:,.0f}</div>
                    <div class="label">Inventory Sales</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                st.markdown(f"""
                <div class="card-3d glow-blue" style="text-align:center;padding:0.8rem;">
                    <span class="icon">✅</span>
                    <div class="value">{total_attendance}</div>
                    <div class="label">Total Attendances</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Net Profit/Loss
            net = total_fees + total_sales - total_expenses
            net_color = "positive" if net >= 0 else "negative"
            net_icon = "📈" if net >= 0 else "📉"
            
            st.markdown(f"""
            <div style="margin-top:0.5rem;text-align:center;">
                <div class="card-3d glow-{'green' if net >= 0 else 'red'}" style="padding:0.8rem;display:inline-block;width:auto;min-width:300px;">
                    <span class="icon">{net_icon}</span>
                    <div class="value" style="color:{'#34D399' if net >= 0 else '#F87171'};">PKR {net:,.0f}</div>
                    <div class="label">Net Profit / Loss</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Staff grid
            st.subheader("👥 Staff Performance")
            
            cols = st.columns(3)
            for idx, staff in enumerate(staff_list):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="staff-card">
                        <div class="staff-name">{staff['name']}</div>
                        <div class="staff-role">👤 {staff['role']}</div>
                        <div class="staff-stats">
                            💰 PKR {staff['fee_amount']:,.0f} Fees
                        </div>
                        <div style="display:flex;justify-content:space-around;margin-top:0.5rem;font-size:0.75rem;color:#94A3B8;">
                            <span>✅ {staff['attendance_count']}</span>
                            <span>📦 {staff['sale_count']}</span>
                            <span>💳 {staff['expense_count']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # ── STAFF EXPORT ──
            st.divider()
            df_staff = pd.DataFrame(staff_list)
            render_export_buttons(df_staff, "Staff Performance Report", f"staff_report_{date.today()}.csv")
            
        else:
            st.info("📭 No staff members found for the selected filters.")
    
    # ── TAB 2: MEMBER REPORTS ─────────────────────────────────────────────
    with tab_members:
        # Get member data for export
        members = db.get_members(gym_id=sel_gid)
        if members:
            member_data = []
            for m in members:
                member_data.append({
                    "Name": m.full_name,
                    "Serial": m.serial_number,
                    "Phone": m.phone,
                    "Membership Type": m.membership_type,
                    "Status": m.status,
                    "Join Date": m.join_date,
                    "Expiry Date": m.expiry_date,
                    "Fee Amount": m.fee_amount,
                })
            df_members = pd.DataFrame(member_data)
            render_export_buttons(df_members, "Members Report", f"members_report_{date.today()}.csv")
        
        render_member_reports(sel_gid, date_from, date_to)
    
    # ── TAB 3: REVENUE REPORTS ────────────────────────────────────────────
    with tab_revenue:
        fees = db.get_fee_records(gym_id=sel_gid, date_from=date_from, date_to=date_to)
        if fees:
            revenue_data = []
            for f in fees:
                member = db.get_member(f.member_id)
                revenue_data.append({
                    "Date": f.payment_date,
                    "Member": member.full_name if member else "Unknown",
                    "Amount": f.amount,
                    "Method": f.payment_method or "Cash",
                    "Collected By": f.collected_by or "-",
                    "Receipt": f.receipt_number or "-",
                })
            df_revenue = pd.DataFrame(revenue_data)
            render_export_buttons(df_revenue, "Revenue Report", f"revenue_report_{date.today()}.csv")
        
        render_revenue_reports(sel_gid, date_from, date_to)
    
    # ── TAB 4: EXPENSE REPORTS ────────────────────────────────────────────
    with tab_expenses:
        expenses = db.get_expenses(gym_id=sel_gid, date_from=date_from, date_to=date_to)
        if expenses:
            expense_data = []
            for e in expenses:
                expense_data.append({
                    "Date": e.expense_date,
                    "Category": e.category,
                    "Description": e.description,
                    "Amount": e.amount,
                    "Staff": e.staff_name or "-",
                })
            df_expenses = pd.DataFrame(expense_data)
            render_export_buttons(df_expenses, "Expense Report", f"expense_report_{date.today()}.csv")
        
        render_expense_reports(sel_gid, date_from, date_to)
    
    # ── TAB 5: ATTENDANCE REPORTS ─────────────────────────────────────────
    with tab_attendance:
        attendance = db.get_attendance_range(gym_id=sel_gid, from_date=date_from, to_date=date_to)
        if attendance:
            att_data = []
            for a in attendance:
                member = db.get_member(a.member_id)
                # FIXED: check_time error fixed - using hasattr to check attribute exists
                check_time_value = getattr(a, 'check_time', getattr(a, 'check_in_time', getattr(a, 'time', '-')))
                att_data.append({
                    "Date": a.check_date,
                    "Member": member.full_name if member else "Unknown",
                    "Status": a.status,
                    "Time": check_time_value,
                    "Marked By": a.marked_by or "-",
                })
            df_attendance = pd.DataFrame(att_data)
            render_export_buttons(df_attendance, "Attendance Report", f"attendance_report_{date.today()}.csv")
        
        render_attendance_reports(sel_gid, date_from, date_to)
    
    # ── TAB 6: FINANCIAL SUMMARY ─────────────────────────────────────────
    with tab_financial:
        fees = db.get_fee_records(gym_id=sel_gid, date_from=date_from, date_to=date_to)
        expenses = db.get_expenses(gym_id=sel_gid, date_from=date_from, date_to=date_to)
        
        if fees or expenses:
            fin_data = []
            total_revenue = sum(f.amount for f in fees) if fees else 0
            total_expenses = sum(e.amount for e in expenses) if expenses else 0
            
            fin_data.append({
                "Metric": "Total Revenue",
                "Amount": total_revenue
            })
            fin_data.append({
                "Metric": "Total Expenses",
                "Amount": total_expenses
            })
            fin_data.append({
                "Metric": "Net Profit/Loss",
                "Amount": total_revenue - total_expenses
            })
            fin_data.append({
                "Metric": "Profit Margin",
                "Amount": f"{(total_revenue - total_expenses) / total_revenue * 100:.1f}%" if total_revenue > 0 else "0%"
            })
            df_financial = pd.DataFrame(fin_data)
            render_export_buttons(df_financial, "Financial Summary", f"financial_report_{date.today()}.csv")
        
        render_financial_summary(sel_gid, date_from, date_to)
    
    # ── TAB 7: TOP MEMBERS ────────────────────────────────────────────────
    with tab_top:
        render_top_members_report(sel_gid, date_from, date_to)
    
    # ── TAB 8: MONTHLY GYM SUMMARY ────────────────────────────────────────
    with tab_monthly:
        render_monthly_gym_summary(sel_gid, date_from, date_to)
    
    # ── TAB 9: GYM COMPARISON ──────────────────────────────────────────────
    with tab_gym_compare:
        render_gym_comparison_dashboard(sel_gid, date_from, date_to)

    # ============================================
    # EXPORT ALL REPORTS
    # ============================================
    
    st.divider()
    st.subheader("📥 Export All Reports")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        if st.button("📋 Export All Reports (CSV)", width='stretch'):
            staff_data = get_staff_reports(gym_id=sel_gid, date_from=date_from, date_to=date_to)
            staff_list = list(staff_data['staff_info'].values())
            
            if staff_list:
                df = pd.DataFrame(staff_list)
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download All CSV",
                    data=csv,
                    file_name=f"all_reports_{date.today()}.csv",
                    mime="text/csv",
                    key="all_reports_csv_download"
                )
            else:
                st.warning("No data to export.")
    
    with col_exp2:
        if st.button("📊 Export Financial Summary (Excel)", width='stretch'):
            fees = db.get_fee_records(gym_id=sel_gid, date_from=date_from, date_to=date_to)
            expenses = db.get_expenses(gym_id=sel_gid, date_from=date_from, date_to=date_to)
            
            if fees or expenses:
                try:
                    import openpyxl
                    from openpyxl import Workbook
                    wb = Workbook()
                    
                    ws1 = wb.active
                    ws1.title = "Revenue"
                    ws1.append(["Date", "Member", "Amount", "Method"])
                    for f in fees:
                        member = db.get_member(f.member_id)
                        ws1.append([f.payment_date, member.full_name if member else "Unknown", f.amount, f.payment_method or "Cash"])
                    
                    ws2 = wb.create_sheet("Expenses")
                    ws2.append(["Date", "Category", "Description", "Amount"])
                    for e in expenses:
                        ws2.append([e.expense_date, e.category, e.description, e.amount])
                    
                    output = io.BytesIO()
                    wb.save(output)
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        "📥 Download Financial Report",
                        data=excel_data,
                        file_name=f"financial_report_{date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="financial_excel_download"
                    )
                except ImportError:
                    st.warning("⚠️ openpyxl not installed. Install with: pip install openpyxl")
            else:
                st.warning("No data to export.")
    
    with col_exp3:
        if st.button("🔄 Refresh All Data", width='stretch'):
            st.rerun()