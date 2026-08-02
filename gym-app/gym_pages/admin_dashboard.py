import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db
import styles
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# PROFESSIONAL DATA TABLE CSS
# ============================================================
PROFESSIONAL_TABLE_CSS = """
<style>
    .pro-table-container {
        background: #0F172A;
        border-radius: 16px;
        border: 1px solid #1E293B;
        overflow: hidden;
        padding: 0;
        margin: 12px 0;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    .pro-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 0.85rem;
    }
    .pro-table thead {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        border-bottom: 2px solid #7C3AED;
    }
    .pro-table thead th {
        padding: 12px 16px;
        text-align: left;
        color: #94A3B8;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        white-space: nowrap;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .pro-table tbody tr {
        border-bottom: 1px solid #1E293B;
        transition: all 0.2s ease;
        cursor: default;
    }
    .pro-table tbody tr:hover {
        background: rgba(124, 58, 237, 0.08);
        transform: scale(1.002);
    }
    .pro-table tbody tr:last-child {
        border-bottom: none;
    }
    .pro-table tbody td {
        padding: 10px 16px;
        color: #E2E8F0;
        vertical-align: middle;
        font-size: 0.82rem;
    }
    .pro-badge {
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
    }
    .pro-badge-paid { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.2); }
    .pro-badge-unpaid { background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.2); }
    .pro-badge-partial { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.2); }
    .pro-badge-none { background: rgba(100, 116, 139, 0.15); color: #94A3B8; border: 1px solid rgba(100, 116, 139, 0.2); }
    .pro-expiry-critical { color: #EF4444; }
    .pro-expiry-urgent { color: #F59E0B; }
    .pro-expiry-good { color: #10B981; }
    .pro-expiry-normal { color: #94A3B8; }
    .pro-amount { font-weight: 700; font-size: 0.85rem; }
    .pro-amount-paid { color: #34D399; }
    .pro-amount-unpaid { color: #F87171; }
    .pro-name { font-weight: 600; color: #F8FAFC; font-size: 0.9rem; }
    .pro-serial { font-size: 0.7rem; color: #64748B; font-weight: 500; }
    .pro-table-footer {
        background: #0F172A;
        border-top: 1px solid #1E293B;
        padding: 10px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8rem;
        color: #94A3B8;
    }
    .pro-table-footer .count { color: #F8FAFC; font-weight: 600; }
    .pro-table-scroll {
        overflow-x: auto;
        max-height: 600px;
        overflow-y: auto;
    }
    .pro-table-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .pro-table-scroll::-webkit-scrollbar-track { background: #0F172A; }
    .pro-table-scroll::-webkit-scrollbar-thumb { background: #7C3AED; border-radius: 10px; }
    @media (max-width: 768px) {
        .pro-table thead th, .pro-table tbody td { padding: 6px 8px; font-size: 0.7rem; }
    }
</style>
"""


def render_professional_table(data, columns_config=None, title="Members List"):
    """Render a professional data table with HTML/CSS"""
    if not data:
        st.info("No data available")
        return
    
    if columns_config is None:
        columns_config = {}
    
    html = f"""
    <div class="pro-table-container">
        <div class="pro-table-scroll">
        <table class="pro-table">
            <thead><tr>
    """
    for col in data[0].keys():
        if col.startswith("_"):
            continue
        label = columns_config.get(col, col.replace("_", " ").title())
        html += f'<th>{label}</th>'
    html += "</tr></thead><tbody>"
    
    for row in data:
        html += '<tr>'
        for key, value in row.items():
            if key.startswith("_"):
                continue
            if key == "Status" and isinstance(value, str):
                if "PAID" in value.upper():
                    badge_class = "pro-badge-paid"
                elif "UNPAID" in value.upper():
                    badge_class = "pro-badge-unpaid"
                elif "PARTIAL" in value.upper():
                    badge_class = "pro-badge-partial"
                else:
                    badge_class = "pro-badge-none"
                html += f'<td><span class="pro-badge {badge_class}">{value}</span></td>'
            elif key == "Expiry" and isinstance(value, str):
                if "overdue" in value.lower():
                    html += f'<td><span class="pro-expiry pro-expiry-critical">{value}</span></td>'
                elif "left" in value.lower() and "🟡" in value:
                    html += f'<td><span class="pro-expiry pro-expiry-urgent">{value}</span></td>'
                elif "left" in value.lower() and "✅" in value:
                    html += f'<td><span class="pro-expiry pro-expiry-good">{value}</span></td>'
                else:
                    html += f'<td><span class="pro-expiry pro-expiry-normal">{value}</span></td>'
            elif "Fee" in key or "Amount" in key or "Paid" in key or "Pending" in key:
                html += f'<td><span class="pro-amount">{value}</span></td>'
            elif key == "Name" and isinstance(value, str):
                html += f'<td><span class="pro-name">{value}</span></td>'
            else:
                html += f'<td>{value}</td>'
        html += '</tr>'
    
    html += f"""
            </tbody>
        </table>
        </div>
        <div class="pro-table-footer">
            <span>Showing <span class="count">{len(data)}</span> records</span>
            <span>Updated: {datetime.now().strftime('%I:%M %p')}</span>
        </div>
    </div>
    """
    st.markdown(PROFESSIONAL_TABLE_CSS, unsafe_allow_html=True)
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# AI COACH - SIMPLIFIED VERSION
# ============================================================

def get_ai_suggestion(username, gym_id):
    """Get AI suggestion without external module"""
    try:
        shift_open = False
        try:
            shift_open = db.get_active_shift(gym_id=gym_id, staff_user=username) is not None
        except:
            pass
        
        metrics = {}
        try:
            metrics = db.get_staff_today_metrics(username, gym_id)
        except:
            pass
        
        fee_today = metrics.get('fee_total', 0) if metrics else 0
        att_count = metrics.get('att_count', 0) if metrics else 0
        
        if not shift_open:
            return {
                "message": "🚀 Shift abhi band hai! Pehle 'Open Shift' karein, phir fees collect karein. 💪",
                "actions": ["Open Shift", "Collect Fee", "Mark Attendance"]
            }
        elif fee_today == 0 and att_count == 0:
            return {
                "message": "📋 Aaj abhi tak koi fee collect nahi ki aur na hi attendance mark ki. Aaj ka target poora karein! 🎯",
                "actions": ["Collect Fee", "Mark Attendance", "Check Members"]
            }
        elif fee_today > 0 and att_count > 0:
            return {
                "message": f"🔥 Shandaar! Aaj PKR {fee_today:,.0f} fees collect ki aur {att_count} attendance mark ki. Isi tarah continue karein! 🏆",
                "actions": ["Collect More Fee", "Mark More Attendance", "View Report"]
            }
        else:
            return {
                "message": f"💪 Aaj PKR {fee_today:,.0f} fees collect ki. Attendance bhi mark karein! 📊",
                "actions": ["Mark Attendance", "Collect Fee", "Check Members"]
            }
    except Exception as e:
        return {
            "message": "Assalam-o-Alaikum! 👋 Main aapka AI Coach hoon. Aaj ki shift start karein aur apna best dein! 💪",
            "actions": ["Open Shift", "Collect Fee", "Mark Attendance"]
        }


# ============================================================
# REVENUE TREND CHART
# ============================================================

def render_revenue_trend_chart(gym_id):
    try:
        monthly = db.get_monthly_revenue(gym_id=gym_id)
        if monthly and any(monthly.values()):
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            values = [monthly.get(i, 0) for i in range(1, 13)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=months,
                y=values,
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#FFC947', width=3),
                marker=dict(size=8, color='#FFC947'),
                fill='tozeroy',
                fillcolor='rgba(255,201,71,0.15)'
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=250,
                margin=dict(l=0, r=0, t=20, b=20),
                xaxis=dict(gridcolor='#1E293B'),
                yaxis=dict(gridcolor='#1E293B', title='Revenue (PKR)')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            return True
    except Exception as e:
        print(f"Revenue trend error: {e}")
    return False


# ============================================================
# MEMBER GROWTH CHART
# ============================================================

def render_member_growth_chart(gym_id):
    try:
        members = db.get_members(gym_id=gym_id)
        if members:
            join_dates = []
            for m in members:
                if m.join_date:
                    try:
                        join_dates.append(datetime.strptime(m.join_date, "%Y-%m-%d").date())
                    except:
                        pass
            
            if join_dates:
                df = pd.DataFrame({"Date": join_dates})
                df["Count"] = 1
                df = df.groupby("Date").sum().reset_index()
                df["Cumulative"] = df["Count"].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["Date"],
                    y=df["Cumulative"],
                    mode='lines+markers',
                    name='Total Members',
                    line=dict(color='#A78BFA', width=3),
                    marker=dict(size=6, color='#A78BFA'),
                    fill='tozeroy',
                    fillcolor='rgba(139,92,246,0.15)'
                ))
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=250,
                    margin=dict(l=0, r=0, t=20, b=20),
                    xaxis=dict(gridcolor='#1E293B'),
                    yaxis=dict(gridcolor='#1E293B', title='Members')
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                return True
    except Exception as e:
        print(f"Member growth error: {e}")
    return False


# ============================================================
# EXPENSE BREAKDOWN CHART
# ============================================================

def render_expense_breakdown_chart(gym_id):
    try:
        expenses = db.get_expenses_by_category(gym_id=gym_id)
        if expenses:
            categories = [e['category'] for e in expenses]
            amounts = [e['total'] for e in expenses]
            
            colors = ['#EF4444', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6', '#EC4899', '#06B6D4']
            
            fig = go.Figure(data=[go.Pie(
                labels=categories,
                values=amounts,
                hole=0.4,
                marker=dict(colors=colors[:len(categories)]),
                textinfo='label+percent',
                textfont=dict(color='white', size=11)
            )])
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=280,
                margin=dict(l=0, r=0, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            return True
    except Exception as e:
        print(f"Expense breakdown error: {e}")
    return False


# ============================================================
# ATTENDANCE CHART
# ============================================================

def render_attendance_chart(gym_id):
    try:
        data = db.get_attendance_trend(gym_id=gym_id, days=30)
        if data:
            df = pd.DataFrame(data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['present'],
                mode='lines+markers',
                name='Present',
                line=dict(color='#34D399', width=3),
                marker=dict(size=6)
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=250,
                margin=dict(l=0, r=0, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(gridcolor='#1E293B'),
                yaxis=dict(gridcolor='#1E293B')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            return True
    except Exception as e:
        print(f"Chart error: {e}")
    return False


# ============================================================
# FEE CHART
# ============================================================

def render_fee_chart(gym_id):
    try:
        today = date.today()
        month_start = today.replace(day=1)
        fees = db.get_fee_records(gym_id=gym_id, date_from=month_start, date_to=today)
        
        if fees:
            df = pd.DataFrame([{
                'date': f.payment_date,
                'amount': f.amount
            } for f in fees if f.payment_date])
            df['date'] = pd.to_datetime(df['date'])
            df = df.groupby('date')['amount'].sum().reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['date'],
                y=df['amount'],
                marker=dict(color='#FFC947'),
                text=[f'PKR {a:,.0f}' for a in df['amount']],
                textposition='outside',
                textfont=dict(color='white', size=10)
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=250,
                margin=dict(l=0, r=0, t=30, b=20),
                xaxis=dict(gridcolor='#1E293B'),
                yaxis=dict(gridcolor='#1E293B')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            return True
    except Exception as e:
        print(f"Fee chart error: {e}")
    return False


# ============================================================
# MEMBERSHIP PIE CHART
# ============================================================

def render_membership_pie_chart(gym_id):
    try:
        members = db.get_members(gym_id=gym_id)
        if members:
            df = pd.DataFrame([{
                'type': m.membership_type or 'Unknown',
                'count': 1
            } for m in members])
            df = df.groupby('type')['count'].sum().reset_index()
            
            colors = ['#7C3AED', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
            
            fig = go.Figure(data=[go.Pie(
                labels=df['type'],
                values=df['count'],
                hole=0.4,
                marker=dict(colors=colors[:len(df)]),
                textinfo='label+percent',
                textfont=dict(color='white', size=12)
            )])
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=280,
                margin=dict(l=0, r=0, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            return True
    except Exception as e:
        print(f"Pie chart error: {e}")
    return False


# ============================================================
# PERFORMANCE COMPARISON FUNCTIONS
# ============================================================

def get_performance_data(gym_id=None):
    today = date.today()
    month_start = today.replace(day=1)
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_month_end = today.replace(day=1) - timedelta(days=1)
    
    current_month_fees = db.get_fee_records(gym_id=gym_id, date_from=month_start, date_to=today)
    current_month_total = sum(f.amount for f in current_month_fees) if current_month_fees else 0
    current_month_count = len(current_month_fees) if current_month_fees else 0
    
    last_month_fees = db.get_fee_records(gym_id=gym_id, date_from=last_month_start, date_to=last_month_end)
    last_month_total = sum(f.amount for f in last_month_fees) if last_month_fees else 0
    last_month_count = len(last_month_fees) if last_month_fees else 0
    
    today_fees = db.get_fee_records(gym_id=gym_id, date_from=today, date_to=today)
    today_total = sum(f.amount for f in today_fees) if today_fees else 0
    today_count = len(today_fees) if today_fees else 0
    
    same_day_last_month = today - timedelta(days=30)
    same_day_fees = db.get_fee_records(gym_id=gym_id, date_from=same_day_last_month, date_to=same_day_last_month)
    same_day_total = sum(f.amount for f in same_day_fees) if same_day_fees else 0
    same_day_count = len(same_day_fees) if same_day_fees else 0
    
    return {
        'current_month': {'total': current_month_total, 'count': current_month_count},
        'last_month': {'total': last_month_total, 'count': last_month_count},
        'today': {'total': today_total, 'count': today_count},
        'same_day_last_month': {'total': same_day_total, 'count': same_day_count},
        'month_start': month_start,
        'last_month_start': last_month_start,
        'today_date': today,
        'same_day_last_month_date': same_day_last_month,
    }


def render_performance_comparison(performance_data, gym_id=None):
    data = performance_data
    
    month_diff = data['current_month']['total'] - data['last_month']['total']
    month_pct = (month_diff / data['last_month']['total'] * 100) if data['last_month']['total'] > 0 else 0
    
    today_diff = data['today']['total'] - data['same_day_last_month']['total']
    today_pct = (today_diff / data['same_day_last_month']['total'] * 100) if data['same_day_last_month']['total'] > 0 else 0
    
    st.markdown("### 📊 Performance Comparison")
    st.caption(f"Comparing: {data['month_start'].strftime('%d %b %Y')} to {data['today_date'].strftime('%d %b %Y')}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        color = "#34D399" if month_diff >= 0 else "#EF4444"
        arrow = "↑" if month_diff >= 0 else "↓"
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:1rem;">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📅 THIS MONTH</div>
            <div style="color:#FFFFFF;font-size:1.5rem;font-weight:700;">PKR {data['current_month']['total']:,.0f}</div>
            <div style="color:#64748B;font-size:0.8rem;">{data['current_month']['count']} transactions</div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:{color};font-weight:600;">{arrow} PKR {abs(month_diff):,.0f}</span>
                <span style="color:#94A3B8;font-size:0.7rem;margin-left:0.5rem;">({month_pct:.1f}% vs last month)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:1rem;">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📆 LAST MONTH</div>
            <div style="color:#94A3B8;font-size:1.5rem;font-weight:700;">PKR {data['last_month']['total']:,.0f}</div>
            <div style="color:#64748B;font-size:0.8rem;">{data['last_month']['count']} transactions</div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.7rem;">
                    {data['last_month_start'].strftime('%d %b')} - {(data['today_date'] - timedelta(days=1)).strftime('%d %b')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:1rem;">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📈 GROWTH</div>
            <div style="color:{'#34D399' if month_pct >= 0 else '#EF4444'};font-size:1.8rem;font-weight:800;">
                {month_pct:.1f}%
            </div>
            <div style="color:#64748B;font-size:0.8rem;">
                {'📈 Increase' if month_pct >= 0 else '📉 Decrease'}
            </div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.7rem;">
                    {data['month_start'].strftime('%d %b')} - {data['today_date'].strftime('%d %b')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col4, col5, col6 = st.columns([1, 1, 1])
    
    with col4:
        color = "#34D399" if today_diff >= 0 else "#EF4444"
        arrow = "↑" if today_diff >= 0 else "↓"
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:1rem;">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📅 TODAY</div>
            <div style="color:#FFC947;font-size:1.5rem;font-weight:700;">PKR {data['today']['total']:,.0f}</div>
            <div style="color:#64748B;font-size:0.8rem;">{data['today']['count']} transactions</div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:{color};font-weight:600;">{arrow} PKR {abs(today_diff):,.0f}</span>
                <span style="color:#94A3B8;font-size:0.7rem;margin-left:0.5rem;">({today_pct:.1f}% vs same day last month)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:1rem;">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📆 SAME DAY LAST MONTH</div>
            <div style="color:#94A3B8;font-size:1.5rem;font-weight:700;">PKR {data['same_day_last_month']['total']:,.0f}</div>
            <div style="color:#64748B;font-size:0.8rem;">{data['same_day_last_month']['count']} transactions</div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.7rem;">
                    {data['same_day_last_month_date'].strftime('%d %b %Y')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div style="background:#0F172A;border:1px solid #1E293B;border-radius:12px;padding:1rem;">
            <div style="color:#94A3B8;font-size:0.7rem;font-weight:600;">📊 TODAY VS LAST MONTH</div>
            <div style="color:{'#34D399' if today_pct >= 0 else '#EF4444'};font-size:1.8rem;font-weight:800;">
                {today_pct:.1f}%
            </div>
            <div style="color:#64748B;font-size:0.8rem;">
                {'📈 Better than last month' if today_pct >= 0 else '📉 Lower than last month'}
            </div>
            <div style="margin-top:0.5rem;border-top:1px solid #1E293B;padding-top:0.5rem;">
                <span style="color:#94A3B8;font-size:0.7rem;">
                    Today: {data['today_date'].strftime('%d %b')} vs {data['same_day_last_month_date'].strftime('%d %b')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 🔥 FIXED: DAILY PERFORMANCE CHART
# ============================================================

def render_daily_performance_chart(gym_id=None):
    """Render daily performance chart for current month - FIXED"""
    today = date.today()
    month_start = today.replace(day=1)
    
    days_in_month = []
    current_date = month_start
    while current_date <= today:
        days_in_month.append(current_date)
        current_date += timedelta(days=1)
    
    daily_data = []
    for d in days_in_month:
        day_fees = db.get_fee_records(gym_id=gym_id, date_from=d, date_to=d)
        total = sum(f.amount for f in day_fees) if day_fees else 0
        count = len(day_fees) if day_fees else 0
        daily_data.append({
            'date': d,
            'amount': total,
            'count': count
        })
    
    if not daily_data or all(d['amount'] == 0 for d in daily_data):
        return False
    
    df = pd.DataFrame(daily_data)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['amount'],
        name='Daily Collection',
        marker=dict(
            color=df['amount'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Amount (PKR)")
        ),
        text=[f'PKR {a:,.0f}' for a in df['amount']],
        textposition='outside',
        textfont=dict(color='white', size=9)
    ))
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['amount'],
        mode='lines+markers',
        name='Trend',
        line=dict(color='#FF6B6B', width=2, dash='dash'),
        marker=dict(size=6, color='#FF6B6B')
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=0, r=0, t=30, b=20),
        xaxis=dict(gridcolor='#1E293B', tickangle=45),
        yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    total = df['amount'].sum()
    avg = df['amount'].mean()
    max_day = df.loc[df['amount'].idxmax()]
    
    # 🔥 FIX: Check if min_day is not None and amount is valid
    min_day = None
    if df['amount'].min() > 0:
        min_day = df.loc[df['amount'].idxmin()]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Month", f"PKR {total:,.0f}")
    c2.metric("📊 Daily Average", f"PKR {avg:,.0f}")
    c3.metric("📈 Best Day", f"{max_day['date'].strftime('%d %b')} (PKR {max_day['amount']:,.0f})")
    
    # 🔥 FIX: Check if min_day is a valid Series/DataFrame, not None
    if min_day is not None:
        c4.metric("📉 Lowest Day", f"{min_day['date'].strftime('%d %b')} (PKR {min_day['amount']:,.0f})")
    else:
        c4.metric("📉 Lowest Day", "No data")
    
    return True


def render_gym_performance_comparison(gyms, date_from, date_to):
    if not gyms or len(gyms) < 2:
        return
    
    st.markdown("### 🏋️ Gym Performance Comparison")
    
    gym_data = []
    for g in gyms:
        records = db.get_fee_records(gym_id=g.id, date_from=date_from, date_to=date_to)
        total = sum(r.amount for r in records) if records else 0
        count = len(records) if records else 0
        avg = total / count if count > 0 else 0
        gym_data.append({
            "Gym": g.name,
            "Collection": total,
            "Transactions": count,
            "Avg": avg
        })
    
    df_gym = pd.DataFrame(gym_data)
    df_gym = df_gym.sort_values('Collection', ascending=False)
    
    colors = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#EF4444', '#06B6D4']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_gym['Gym'],
        y=df_gym['Collection'],
        marker=dict(color=colors[:len(df_gym)]),
        text=[f'PKR {c:,.0f}' for c in df_gym['Collection']],
        textposition='outside',
        textfont=dict(color='white', size=11)
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=250,
        margin=dict(l=0, r=0, t=30, b=20),
        xaxis=dict(gridcolor='#1E293B'),
        yaxis=dict(gridcolor='#1E293B', title='Amount (PKR)'),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("#### 🏆 Gym Ranking")
    for i, row in df_gym.iterrows():
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    background:#0F172A;border:1px solid #1E293B;border-radius:8px;
                    padding:0.5rem 1rem;margin-bottom:0.3rem;">
            <div>
                <span style="font-size:1.2rem;margin-right:0.5rem;">{medal}</span>
                <span style="color:#F8FAFC;font-weight:600;">{row['Gym']}</span>
            </div>
            <div>
                <span style="color:#FFC947;font-weight:700;">PKR {row['Collection']:,.0f}</span>
                <span style="color:#94A3B8;font-size:0.7rem;margin-left:0.5rem;">({row['Transactions']} transactions)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# AI COACH MODERN
# ============================================================

def render_ai_coach_modern(username, role, gym_id):
    suggestion = get_ai_suggestion(username, gym_id)
    
    shift_open = False
    try:
        shift_open = db.get_active_shift(gym_id=gym_id, staff_user=username) is not None
    except:
        shift_open = False
    
    perf_score = 0
    perf_label = "No Data"
    perf_color = "#64748B"
    today_total = 0
    tasks_done = 0
    total_tasks = 7
    
    try:
        metrics = db.get_staff_today_metrics(username, gym_id)
        if metrics:
            fee_score = min(100, (metrics.get('fee_total', 0) / 5000) * 100)
            att_score = min(100, (metrics.get('att_count', 0) / 10) * 100)
            new_member_score = min(100, (metrics.get('new_members_today', 0) / 5) * 100)
            
            perf_score = int((fee_score + att_score + new_member_score) / 3)
            today_total = metrics.get('fee_total', 0)
            tasks_done = min(7, metrics.get('activity_count', 0))
            
            if perf_score >= 80:
                perf_label = "Excellent 🏆"
                perf_color = "#34D399"
            elif perf_score >= 60:
                perf_label = "Good 👍"
                perf_color = "#FBBF24"
            elif perf_score >= 40:
                perf_label = "Average 📊"
                perf_color = "#F59E0B"
            else:
                perf_label = "Needs Work ⚠️"
                perf_color = "#EF4444"
    except:
        perf_score = 0
        perf_label = "No Data"
        perf_color = "#64748B"
    
    st.markdown("""
    <style>
        .ai-coach-card {
            background: linear-gradient(145deg, rgba(20,20,30,0.92), rgba(10,10,20,0.96));
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,201,71,0.12);
            border-radius: 20px;
            padding: 22px 24px;
            margin: 12px 0 20px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 60px rgba(124,58,237,0.04);
            position: relative;
            overflow: hidden;
        }
        .ai-coach-card::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(124,58,237,0.06), transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }
        .ai-avatar {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            background: linear-gradient(135deg, #7C3AED, #4F46E5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 20px rgba(124,58,237,0.25);
            flex-shrink: 0;
        }
        .ai-badge {
            background: rgba(16,185,129,0.12);
            color: #34D399;
            padding: 2px 12px;
            border-radius: 9999px;
            font-size: 10px;
            font-weight: 700;
            border: 1px solid rgba(16,185,129,0.15);
            letter-spacing: 0.5px;
        }
        .ai-score-ring {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .ai-score-inner {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: #0F172A;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .ai-score-number {
            font-size: 18px;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1;
        }
        .ai-score-label {
            font-size: 7px;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .ai-message-text {
            font-size: 14px;
            line-height: 1.6;
            color: #CBD5E1;
            padding: 8px 0 4px 0;
        }
        .ai-divider {
            border: none;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin: 12px 0;
        }
        .ai-status-badge {
            padding: 4px 14px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .ai-footer-tip {
            font-size: 11px;
            color: #64748B;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .ai-footer-date {
            font-size: 11px;
            color: #64748B;
        }
        .ai-stats-mini {
            background: rgba(20,20,30,0.5);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 12px;
            padding: 10px 16px;
            flex: 1;
            min-width: 100px;
            text-align: center;
        }
        .ai-stats-mini .label {
            font-size: 9px;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        .ai-stats-mini .value {
            font-size: 16px;
            font-weight: 700;
            margin-top: 2px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    score_style = f"""
    <style>
        .ai-score-ring {{
            background: conic-gradient({perf_color} {perf_score}%, #1E293B {perf_score}% 100%) !important;
        }}
    </style>
    """
    st.markdown(score_style, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1.5])
    
    with col1:
        st.markdown('<div class="ai-avatar">🤖</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                <span style="font-size:17px;font-weight:800;color:#FFFFFF;">AI Performance Coach</span>
                <span class="ai-badge">● LIVE</span>
                <span style="font-size:11px;color:#64748B;font-weight:500;">{datetime.now().strftime('%I:%M %p')}</span>
            </div>
            <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:2px;">
                <span style="font-size:12px;color:#94A3B8;">👤 {username}</span>
                <span style="font-size:12px;color:#94A3B8;">•</span>
                <span style="font-size:12px;color:#94A3B8;">Shift: {'🟢 Open' if shift_open else '🔴 Closed'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="ai-score-ring">
            <div class="ai-score-inner">
                <span class="ai-score-number">{perf_score}</span>
                <span class="ai-score-label">Score</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr class="ai-divider">', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="ai-message-text">
        {suggestion.get('message', 'Assalam-o-Alaikum! 👋 Aaj ka din shuru karein! 💪')}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">
        <span class="ai-status-badge" style="background:rgba(239,68,68,0.1);color:{perf_color};border:1px solid rgba(239,68,68,0.1);">
            {perf_label}
        </span>
        <span class="ai-status-badge" style="background:rgba(59,130,246,0.1);color:#60A5FA;border:1px solid rgba(59,130,246,0.1);">
            📊 Today: PKR {today_total:,.0f}
        </span>
        <span class="ai-status-badge" style="background:rgba(245,158,11,0.1);color:#FBBF24;border:1px solid rgba(245,158,11,0.1);">
            🎯 {tasks_done}/{total_tasks} tasks
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top:14px;">', unsafe_allow_html=True)
    
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    
    with btn_col1:
        if st.button("🚀 Open Shift", use_container_width=True, key="ai_open_shift"):
            st.session_state["page"] = "Fee Collection"
            st.rerun()
    
    with btn_col2:
        if st.button("💰 Collect Fee", use_container_width=True, key="ai_collect_fee"):
            st.session_state["page"] = "Fee Collection"
            st.rerun()
    
    with btn_col3:
        if st.button("✅ Mark Attendance", use_container_width=True, key="ai_mark_attendance"):
            st.session_state["page"] = "Attendance"
            st.rerun()
    
    with btn_col4:
        if st.button("📋 Checklist", use_container_width=True, key="ai_checklist"):
            st.session_state["page"] = "Attendance"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr class="ai-divider">', unsafe_allow_html=True)
    
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    with stats_col1:
        st.markdown(f"""
        <div class="ai-stats-mini">
            <div class="label">Pending</div>
            <div class="value" style="color:#F87171;">{max(0, total_tasks - tasks_done)} tasks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col2:
        st.markdown(f"""
        <div class="ai-stats-mini">
            <div class="label">Completed</div>
            <div class="value" style="color:#34D399;">{tasks_done} tasks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col3:
        st.markdown(f"""
        <div class="ai-stats-mini">
            <div class="label">Efficiency</div>
            <div class="value" style="color:#60A5FA;">{min(100, int(tasks_done/total_tasks*100))}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stats_col4:
        st.markdown(f"""
        <div class="ai-stats-mini">
            <div class="label">Today's Date</div>
            <div class="value" style="color:#94A3B8;font-size:13px;">{date.today().strftime('%d %b')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-top:10px;">
        <span class="ai-footer-tip">💡 Tip: Pehle shift kholen, phir fees collect karein</span>
        <span class="ai-footer-date">{date.today().strftime('%A, %d %B %Y')}</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# MAIN RENDER FUNCTION
# ============================================================

def render(gym_id, role, username):
    gyms = db.get_all_gyms()
    
    if role.lower() == "staff":
        user = db.get_user_by_username(username)
        if user and user.gym_id:
            gym_id = user.gym_id
            st.session_state["gym_id"] = gym_id
        else:
            st.warning("⚠️ Aapka account kisi gym se assign nahi hai.")
            return

    # ── CSS ──────────────────────────────────────────────────────────────
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
        
        .export-btn {
            background: linear-gradient(135deg, #7C3AED, #6D28D9) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            cursor: pointer !important;
            font-weight: 600 !important;
            font-size: 0.8rem !important;
            transition: all 0.3s ease !important;
        }
        .export-btn:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 20px rgba(124,58,237,0.4) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── Export Button ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;justify-content:flex-end;margin-bottom:0.5rem;">
        <button onclick="window.print()" class="export-btn">
            🖨️ Export Dashboard
        </button>
    </div>
    """, unsafe_allow_html=True)

    # ── Fraud Alert Banner ──────────────────────────────────────────────
    if role.lower() in ["admin", "owner"]:
        try:
            alerts = db.check_fraud_alerts(gym_id=gym_id)
            if alerts:
                critical = [a for a in alerts if a["severity"] == "critical"]
                warnings = [a for a in alerts if a["severity"] == "warning"]
                
                header_color = "#7F1D1D" if critical else "#78350F"
                border_color = "#EF4444" if critical else "#F59E0B"
                title_color = "#FCA5A5" if critical else "#FCD34D"
                
                if critical:
                    title_text = f"🚨 {len(critical)} CRITICAL ALERT{'S' if len(critical)!=1 else ''} — Fori Attention Chahiye!"
                else:
                    title_text = f"⚠️ {len(warnings)} Suspicious Activity Alert{'s' if len(warnings)!=1 else ''} Aaj"
                
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

    # ── Staff AI Coach ──────────────────────────────────────────────────
    if role.lower() == "staff":
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0F172A,#1E1B4B);
                    border:1px solid #3B82F6;border-radius:14px;
                    padding:0.75rem 1rem;margin-bottom:0.75rem;">
            <span style="color:#60A5FA;font-weight:700;font-size:1rem;">🤖 AI Performance Coach</span>
            <span style="color:#94A3B8;font-size:0.8rem;"> — Aaj aapki performance ka live analysis</span>
        </div>
        """, unsafe_allow_html=True)
        
        render_ai_coach_modern(username=username, role=role, gym_id=gym_id)
        st.divider()

    # ── Hero Greeting Banner ────────────────────────────────────────────
    now = datetime.now()
    hour = now.hour
    if hour < 12:    greeting, g_emoji = "Assalam-o-Alaikum", "🌅"
    elif hour < 17:  greeting, g_emoji = "Good Afternoon",    "☀️"
    else:            greeting, g_emoji = "Good Evening",      "🌙"

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

    # ── Active Announcement ──────────────────────────────────────────────
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

    # ── Get Data ──────────────────────────────────────────────────────────
    stats = db.get_stats(gym_id)

    try:
        today = date.today()
        month_start = today.replace(day=1)
        month_fees = db.get_fee_records(gym_id=gym_id, date_from=month_start, date_to=today)
        month_fees_total = sum(f.amount for f in month_fees) if month_fees else 0
    except Exception as e:
        print(f"Error getting month fees: {e}")
        month_fees_total = 0

    try:
        today = date.today()
        today_fees = db.get_fee_records(gym_id=gym_id, date_from=today, date_to=today)
        fees_today = sum(f.amount for f in today_fees) if today_fees else 0
    except Exception as e:
        print(f"Error getting today's fees: {e}")
        fees_today = 0

    inactive = stats.get('total_members', 0) - stats.get('active_members', 0)
    month_expenses = stats.get('month_expenses', 0)
    net = month_fees_total - month_expenses
    net_color = "#1EB980" if net >= 0 else "#FF5A5A"
    inv_rev = stats.get('inventory_revenue', 0)

    # ── KPI Cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:1.5rem;">👥</div>
            <div class="kpi-label">Total</div>
            <div class="kpi-value" style="font-size:28px;">{stats.get('total_members', 0)}</div>
            <div class="kpi-subtext">{inactive} inactive</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:1.5rem;">✅</div>
            <div class="kpi-label">Active</div>
            <div class="kpi-value" style="font-size:28px;color:#10B981;">{stats.get('active_members', 0)}</div>
            <div class="kpi-subtext">Active members</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:1.5rem;">💰</div>
            <div class="kpi-label">Month Revenue</div>
            <div class="kpi-value" style="font-size:20px;">PKR {month_fees_total:,.0f}</div>
            <div class="kpi-subtext">This month's collection</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:1.5rem;">📈</div>
            <div class="kpi-label">Net P/L</div>
            <div class="kpi-value" style="font-size:20px;color:{net_color};">PKR {net:,.0f}</div>
            <div class="kpi-subtext">Exp: PKR {month_expenses:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    with c5:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:1.5rem;">💵</div>
            <div class="kpi-label">Today's Fees</div>
            <div class="kpi-value" style="font-size:20px;color:#FFC947;">PKR {fees_today:,.0f}</div>
            <div class="kpi-subtext">Today's collection</div>
        </div>""", unsafe_allow_html=True)

    with c6:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:1.5rem;">📅</div>
            <div class="kpi-label">Month Fees</div>
            <div class="kpi-value" style="font-size:20px;color:#34D399;">PKR {month_fees_total:,.0f}</div>
            <div class="kpi-subtext">This month's fees</div>
        </div>""", unsafe_allow_html=True)

    with c7:
        st.markdown(f"""<div class="kpi-card">
            <div style="font-size:1.5rem;">📦</div>
            <div class="kpi-label">Inventory</div>
            <div class="kpi-value" style="font-size:20px;color:#6EE7B7;">PKR {inv_rev:,.0f}</div>
            <div class="kpi-subtext">From POS</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Performance Comparison ────────────────────────────────────────────
    performance_data = get_performance_data(gym_id)
    render_performance_comparison(performance_data, gym_id)
    
    st.markdown("---")
    
    # ── Daily Performance Chart ──────────────────────────────────────────
    st.markdown("### 📅 Daily Performance - Current Month")
    render_daily_performance_chart(gym_id)
    
    st.markdown("---")

    # ── Charts Row ──────────────────────────────────────────────────────────
    chart_col1, chart_col2, chart_col3 = st.columns([2, 1, 1])
    
    with chart_col1:
        st.markdown("#### 📈 Revenue Trend")
        render_revenue_trend_chart(gym_id)
    
    with chart_col2:
        st.markdown("#### 📊 Attendance Trend")
        render_attendance_chart(gym_id)
    
    with chart_col3:
        st.markdown("#### 📊 Membership Types")
        render_membership_pie_chart(gym_id)
    
    chart_col4, chart_col5, chart_col6 = st.columns([2, 1, 1])
    
    with chart_col4:
        st.markdown("#### 📈 Member Growth")
        render_member_growth_chart(gym_id)
    
    with chart_col5:
        st.markdown("#### 💰 Fee Collection")
        render_fee_chart(gym_id)
    
    with chart_col6:
        st.markdown("#### 💳 Expense Breakdown")
        render_expense_breakdown_chart(gym_id)

    # ── Gym Performance Comparison ────────────────────────────────────────
    if gym_id is None and gyms and len(gyms) > 1:
        today = date.today()
        month_start = today.replace(day=1)
        render_gym_performance_comparison(gyms, month_start, today)

    # ── Today's Snapshot ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">📅 Today\'s Snapshot</div>', unsafe_allow_html=True)
    
    try:
        att_today = db.get_attendance(gym_id=gym_id, check_date=date.today())
        present_today = sum(1 for a in att_today if a.status == "Present") if att_today else 0
    except Exception:
        present_today = 0
    
    att_pct = round(present_today / stats.get('active_members', 1) * 100) if stats.get('active_members', 0) > 0 else 0
    
    try:
        exp3_count = len(db.get_expiring_members(days=3, gym_id=gym_id)) if hasattr(db, 'get_expiring_members') else 0
        absent3_count = len(db.get_absent_members(days=3, gym_id=gym_id)) if hasattr(db, 'get_absent_members') else 0
    except Exception:
        exp3_count = absent3_count = 0

    sn1, sn2, sn3, sn4, sn5 = st.columns(5)
    
    with sn1:
        st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #10B981;">
            <div style="font-size:1.3rem;">🏃</div>
            <div class="kpi-label">Attendance Today</div>
            <div class="kpi-value" style="font-size:28px;color:#10B981;">{present_today}</div>
            <div class="kpi-subtext">{att_pct}% checked in</div>
        </div>""", unsafe_allow_html=True)
    
    with sn2:
        st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #FFC947;">
            <div style="font-size:1.3rem;">💵</div>
            <div class="kpi-label">Fees Today</div>
            <div class="kpi-value" style="font-size:20px;color:#FFC947;">PKR {fees_today:,.0f}</div>
            <div class="kpi-subtext">Today's collection</div>
        </div>""", unsafe_allow_html=True)
    
    with sn3:
        st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #EF4444;">
            <div style="font-size:1.3rem;">⏰</div>
            <div class="kpi-label">Expiring (3d)</div>
            <div class="kpi-value" style="font-size:28px;color:#EF4444;">{exp3_count}</div>
            <div class="kpi-subtext">Need renewal now</div>
        </div>""", unsafe_allow_html=True)
    
    with sn4:
        st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #3B82F6;">
            <div style="font-size:1.3rem;">🚨</div>
            <div class="kpi-label">Absent 3+ Days</div>
            <div class="kpi-value" style="font-size:28px;color:#3B82F6;">{absent3_count}</div>
            <div class="kpi-subtext">At-risk members</div>
        </div>""", unsafe_allow_html=True)
    
    with sn5:
        try:
            bday_count = len(db.get_birthday_members(days_ahead=7, gym_id=gym_id)) if hasattr(db, 'get_birthday_members') else 0
        except Exception:
            bday_count = 0
        st.markdown(f"""<div class="kpi-card" style="border-top:3px solid #8B5CF6;">
            <div style="font-size:1.3rem;">🎂</div>
            <div class="kpi-label">Birthdays Soon</div>
            <div class="kpi-value" style="font-size:28px;color:#8B5CF6;">{bday_count}</div>
            <div class="kpi-subtext">Within 7 days</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick Actions ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚡ Quick Actions</div>', unsafe_allow_html=True)
    
    qa1, qa2, qa3, qa4, qa5 = st.columns(5)
    
    with qa1:
        if st.button("➕ Add Member", use_container_width=True, type="primary"):
            st.session_state["page"] = "Members"
            st.rerun()
    
    with qa2:
        if st.button("💰 Collect Fee", use_container_width=True):
            st.session_state["page"] = "Fee Collection"
            st.rerun()
    
    with qa3:
        if st.button("📊 Attendance", use_container_width=True):
            st.session_state["page"] = "Attendance"
            st.rerun()
    
    with qa4:
        if st.button("📝 Expense", use_container_width=True):
            st.session_state["page"] = "Expenses"
            st.rerun()
    
    with qa5:
        if st.button("📦 Inventory", use_container_width=True):
            st.session_state["page"] = "Inventory"
            st.rerun()

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_home, tab_alerts, tab_members, tab_activity, tab_staff = st.tabs([
        "🏠 Overview", "🚨 Alerts", "👥 Members", "📊 Activity", "👔 Staff"
    ])

    # ── TAB 1: Overview ──────────────────────────────────────────────────
    with tab_home:
        st.info("📊 Dashboard overview is displayed above. Scroll up to see all KPIs and charts.")

    # ── TAB 2: Alerts ────────────────────────────────────────────────────
    with tab_alerts:
        try:
            bday_members = db.get_birthday_members(days_ahead=7, gym_id=gym_id) if hasattr(db, 'get_birthday_members') else []
        except Exception:
            bday_members = []
        try:
            expiring = db.get_expiring_members(days=7, gym_id=gym_id) if hasattr(db, 'get_expiring_members') else []
        except Exception:
            expiring = []
        try:
            absent_alert = db.get_absent_members(days=3, gym_id=gym_id) if hasattr(db, 'get_absent_members') else []
        except Exception:
            absent_alert = []
        try:
            low_stock = db.get_stock_items(gym_id=gym_id, low_stock_only=True) if hasattr(db, 'get_stock_items') else []
        except Exception:
            low_stock = []

        crit_count = sum(1 for _, d in expiring if d <= 1) if expiring else 0
        urgent_count = sum(1 for _, d in expiring if 2 <= d <= 3) if expiring else 0

        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #EF4444;">
                <div class="kpi-label">🔴 Critical Expiry</div>
                <div class="kpi-value" style="font-size:28px;color:#EF4444;">{crit_count}</div>
                <div class="kpi-subtext">0–1 days</div>
            </div>""", unsafe_allow_html=True)
        with a2:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #F59E0B;">
                <div class="kpi-label">🟠 Urgent Expiry</div>
                <div class="kpi-value" style="font-size:28px;color:#F59E0B;">{urgent_count}</div>
                <div class="kpi-subtext">2–3 days</div>
            </div>""", unsafe_allow_html=True)
        with a3:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #3B82F6;">
                <div class="kpi-label">🔵 Absent 3+ Days</div>
                <div class="kpi-value" style="font-size:28px;color:#3B82F6;">{len(absent_alert)}</div>
                <div class="kpi-subtext">At-risk members</div>
            </div>""", unsafe_allow_html=True)
        with a4:
            st.markdown(f"""<div class="kpi-card" style="border-left:4px solid #8B5CF6;">
                <div class="kpi-label">🎂 Birthdays Soon</div>
                <div class="kpi-value" style="font-size:28px;color:#8B5CF6;">{len(bday_members)}</div>
                <div class="kpi-subtext">Within 7 days</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

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
        else:
            st.success("✅ No memberships expiring in the next 7 days!")

        st.divider()

        if absent_alert:
            st.markdown(f'<div class="section-header">🚨 {len(absent_alert)} Members Absent 3+ Days</div>', unsafe_allow_html=True)
            for m in absent_alert[:15]:
                st.markdown(f"""
                <div style="background:#0A0A1A;border-left:4px solid #3B82F6;border-radius:10px;padding:10px 16px;margin-bottom:6px;
                     display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:600;color:#F8FAFC;">{m.full_name}</div>
                    <div style="color:#94A3B8;font-size:0.8rem;">🆔 {m.serial_number} &nbsp;·&nbsp; 📞 {m.phone or '—'}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.success("✅ No members absent for 3+ consecutive days!")

        if role.lower() in ["admin", "owner"] and gyms:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📢 Post Announcement", expanded=False):
                with st.form("announcement_form", clear_on_submit=True):
                    if gym_id:
                        sel_gid = gym_id
                        _gnm = next((g.name for g in gyms if g.id == gym_id), "")
                        st.text_input("🏋️ Gym", value=_gnm, disabled=True)
                    else:
                        _opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
                        _chosen = st.selectbox("🏋️ Gym", list(_opts.keys()))
                        sel_gid = _opts[_chosen]
                    message = st.text_area("📝 Message", placeholder="Type announcement here...", height=70)
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        set_expiry = st.checkbox("Set Expiry Date")
                    with ce2:
                        expiry_date = st.date_input("Expiry", value=date.today() + timedelta(days=7)) if set_expiry else None
                    if st.form_submit_button("📢 Post", type="primary", use_container_width=True):
                        if not message.strip():
                            st.error("❌ Please enter a message!")
                        else:
                            expires_at = datetime.combine(expiry_date, datetime.min.time()) if expiry_date else None
                            ok, msg = db.add_announcement(sel_gid, message, username, expires_at)
                            if ok:
                                st.success("✅ Posted!")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")

    # ── TAB 3: Members ──────────────────────────────────────────────────
    with tab_members:
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
                status_badge = "⚪ NO FEE"
                status_key = "none"
            elif paid >= expected_fee and expected_fee > 0:
                status_badge = "🟢 PAID"
                status_key = "paid"
            elif paid > 0:
                status_badge = "🟡 PARTIAL"
                status_key = "partial"
            else:
                status_badge = "🔴 UNPAID"
                status_key = "unpaid"

            days_left = "—"
            if m.expiry_date:
                try:
                    exp = date.fromisoformat(str(m.expiry_date))
                    days = (exp - date.today()).days
                    if days < 0:
                        days_left = f"🔴 {abs(days)}d overdue"
                    elif days == 0:
                        days_left = "🟡 Today!"
                    elif days <= 7:
                        days_left = f"🟡 {days}d left"
                    else:
                        days_left = f"✅ {days}d left"
                except:
                    days_left = "—"

            unified_rows.append({
                "Serial":  m.serial_number or "—",
                "Name":    m.full_name,
                "Phone":   m.phone or "—",
                "Type":    m.membership_type or "—",
                "Fee":     f"PKR {expected_fee:,.0f}",
                "Paid":    f"PKR {paid:,.0f}",
                "Pending": f"PKR {pending:,.0f}",
                "Expiry":  days_left,
                "Status":  status_badge,
                "_status_key": status_key,
            })

        total_count = len(unified_rows)
        paid_count = sum(1 for r in unified_rows if r["_status_key"] == "paid")
        unpaid_count = sum(1 for r in unified_rows if r["_status_key"] == "unpaid")
        partial_count = sum(1 for r in unified_rows if r["_status_key"] == "partial")

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">👥 Total</div>
                <div class="kpi-value">{total_count}</div></div>""", unsafe_allow_html=True)
        with s2:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">🟢 Paid</div>
                <div class="kpi-value" style="color:#1EB980;">{paid_count}</div></div>""", unsafe_allow_html=True)
        with s3:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">🟡 Partial</div>
                <div class="kpi-value" style="color:#FFC947;">{partial_count}</div></div>""", unsafe_allow_html=True)
        with s4:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">🔴 Unpaid</div>
                <div class="kpi-value" style="color:#FF5A5A;">{unpaid_count}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

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

        search_query = st.text_input("🔍 Search by Name / Serial", placeholder="Type to search...", key="dash_mem_search")

        filtered_rows = [r for r in unified_rows
                         if st.session_state.fee_filter == "all" or r["_status_key"] == st.session_state.fee_filter]
        if search_query:
            q = search_query.lower()
            filtered_rows = [r for r in filtered_rows if q in r["Name"].lower() or q in r["Serial"].lower()]

        if filtered_rows:
            table_data = []
            for r in filtered_rows[:50]:
                table_data.append({
                    "Serial": r["Serial"],
                    "Name": r["Name"],
                    "Phone": r["Phone"],
                    "Type": r["Type"],
                    "Fee": r["Fee"],
                    "Paid": r["Paid"],
                    "Pending": r["Pending"],
                    "Expiry": r["Expiry"],
                    "Status": r["Status"],
                })
            
            columns_config = {
                "Serial": "Serial #",
                "Name": "Member Name",
                "Phone": "Phone",
                "Type": "Membership",
                "Fee": "Fee",
                "Paid": "Paid",
                "Pending": "Pending",
                "Expiry": "Expiry Status",
                "Status": "Status"
            }
            
            render_professional_table(table_data, columns_config=columns_config)
            st.caption(f"📋 Showing {len(table_data)} of {len(filtered_rows)} members")
        else:
            st.info("No members found matching your filter.")

    # ── TAB 4: Activity ──────────────────────────────────────────────────
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
                peak_hour = max(hour_data, key=lambda h: hour_data[h])
                peak_count = hour_data[peak_hour]
                am_pm = "AM" if peak_hour < 12 else "PM"
                hour_12 = peak_hour % 12 or 12
                total_att = sum(hour_data.values())
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;padding:32px 20px;">
                    <div style="font-size:48px;font-weight:900;
                         background:linear-gradient(135deg,#FFC947,#FF6B6B);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                        {hour_12}:00 {am_pm}
                    </div>
                    <div style="font-size:14px;color:#8A8A8A;margin:10px 0;">🔥 Peak — {peak_count} check-ins</div>
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
                "Time": s["time"],
                "Member": s["name"],
                "Serial": s["serial"],
                "Marked By": s["marked_by"],
            } for s in scans])
            st.dataframe(scan_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No check-ins yet today.")

    # ── TAB 5: Staff ────────────────────────────────────────────────────
    with tab_staff:
        if role.lower() not in ["admin", "owner"]:
            st.markdown('<div class="section-header">🎯 My Performance Targets</div>', unsafe_allow_html=True)
            current_month = date.today().strftime("%Y-%m")
            try:
                progress = db.get_staff_progress(username, current_month) if hasattr(db, 'get_staff_progress') else None
            except Exception:
                progress = None

            if progress:
                targets_exist = any([
                    progress.get('new_members', {}).get('target', 0) > 0,
                    progress.get('fee_collection', {}).get('target', 0) > 0,
                    progress.get('attendance', {}).get('target', 0) > 0,
                ])
                if targets_exist:
                    overall_pct = progress.get('overall', 0)
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
                            {progress.get('completed_targets', 0)}/{progress.get('total_targets', 0)} targets completed
                        </div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**📈 Target Progress**")
                    
                    new_pct = min(100, progress.get('new_members', {}).get('percentage', 0))
                    st.progress(new_pct / 100, text=f"👤 New Members: {new_pct:.0f}%")
                    
                    fee_pct = min(100, progress.get('fee_collection', {}).get('percentage', 0))
                    st.progress(fee_pct / 100, text=f"💰 Fee Collection: {fee_pct:.0f}%")
                    
                    att_pct = min(100, progress.get('attendance', {}).get('percentage', 0))
                    st.progress(att_pct / 100, text=f"✅ Attendance: {att_pct:.0f}%")

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

        st.markdown('<div class="section-header">👥 Staff Attendance</div>', unsafe_allow_html=True)

        if role.lower() in ["admin", "owner"]:
            try:
                staff_summary = db.get_staff_attendance_summary(gym_id=gym_id) if hasattr(db, 'get_staff_attendance_summary') else []
            except Exception:
                staff_summary = []

            if staff_summary:
                online_count = sum(1 for s in staff_summary if "Online" in s.get('status', ''))
                total_staff = len(staff_summary)
                logins_today = sum(1 for s in staff_summary if s.get('logins', 0) > 0)

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
                    "Name": s.get('full_name', ''),
                    "Role": s.get('role', ''),
                    "Status": s.get('status', ''),
                    "Today": s.get('today_status', ''),
                    "Logins(30d)": s.get('logins', 0),
                    "Hours": f"{s.get('total_hours', 0)}h",
                } for s in staff_summary]
                st.dataframe(pd.DataFrame(staff_data), use_container_width=True, hide_index=True)
            else:
                st.info("No staff attendance data available.")

        else:
            try:
                my_summary = db.get_my_attendance_summary(username) if hasattr(db, 'get_my_attendance_summary') else None
                if my_summary:
                    ms1, ms2, ms3, ms4 = st.columns(4)
                    with ms1:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">📅 Today</div>
                            <div class="kpi-value" style="font-size:18px;">{my_summary.get('today_status', '—')}</div>
                        </div>""", unsafe_allow_html=True)
                    with ms2:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">📊 This Month</div>
                            <div class="kpi-value">{my_summary.get('total_days', 0)}</div>
                            <div class="kpi-subtext">days</div>
                        </div>""", unsafe_allow_html=True)
                    with ms3:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">⏱️ Total Hours</div>
                            <div class="kpi-value">{my_summary.get('total_hours', 0)}h</div>
                        </div>""", unsafe_allow_html=True)
                    with ms4:
                        st.markdown(f"""<div class="kpi-card">
                            <div class="kpi-label">🔥 Streak</div>
                            <div class="kpi-value" style="color:#FF6B6B;">{my_summary.get('current_streak', 0)}</div>
                            <div class="kpi-subtext">days</div>
                        </div>""", unsafe_allow_html=True)
                    if my_summary.get('today_login'):
                        st.caption(f"Logged in at: {my_summary['today_login']}")

                with st.expander("📋 My Attendance History (30 days)", expanded=False):
                    history = db.get_staff_attendance(
                        staff_username=username,
                        date_from=date.today() - timedelta(days=30)
                    ) if hasattr(db, 'get_staff_attendance') else []
                    if history:
                        rows = [{
                            "Date": r.login_time.strftime("%Y-%m-%d"),
                            "Login": r.login_time.strftime("%I:%M %p"),
                            "Logout": r.logout_time.strftime("%I:%M %p") if r.logout_time else "—",
                            "Duration": f"{r.session_duration or 0} min",
                            "Status": "🟢 Online" if r.logout_time is None else "⚫ Offline",
                        } for r in history[:30]]
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("No attendance records found.")
            except Exception as e:
                st.warning(f"Could not load attendance: {e}")