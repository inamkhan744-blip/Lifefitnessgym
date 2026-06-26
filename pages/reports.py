import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
import database as db
import styles
import io

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
        color: #F8FAFC;
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
        color: #F8FAFC;
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
</style>
""", unsafe_allow_html=True)

# ============================================
# HELPERS
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
            # Get all attendance marked by this staff
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
# MAIN RENDER FUNCTION - FIXED
# ============================================

def render(gym_id, role, username):
    
    styles.page_header("📊", "Reports & Analytics",
                       "Comprehensive reports for staff, finances, and performance")
    
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
        if st.button("🔄 Generate Reports", use_container_width=True):
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # GET REPORTS DATA
    # ============================================
    
    reports_data = get_staff_reports(gym_id=sel_gid, date_from=date_from, date_to=date_to)
    staff_list = list(reports_data['staff_info'].values())
    
    # ============================================
    # OVERVIEW STATS
    # ============================================
    
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
    
    # ============================================
    # STAFF REPORTS
    # ============================================
    
    st.subheader("👥 Staff Performance Reports")
    st.caption("Each staff member's detailed performance metrics")
    
    if staff_list:
        # Create tabs for each staff or show all
        staff_names = [s['name'] for s in staff_list]
        selected_staff_tab = st.selectbox("Select Staff Member to View Details", ["All Staff"] + staff_names)
        
        if selected_staff_tab == "All Staff":
            # Show all staff in grid
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
        else:
            # Show selected staff detailed report
            selected_staff = next((s for s in staff_list if s['name'] == selected_staff_tab), None)
            if selected_staff:
                st.markdown("---")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="card-3d glow-green" style="text-align:center;padding:0.8rem;">
                        <div class="value">PKR {selected_staff['fee_amount']:,.0f}</div>
                        <div class="label">💰 Fees Collected</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="card-3d glow-blue" style="text-align:center;padding:0.8rem;">
                        <div class="value">{selected_staff['attendance_count']}</div>
                        <div class="label">✅ Attendances</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="card-3d glow-yellow" style="text-align:center;padding:0.8rem;">
                        <div class="value">PKR {selected_staff['sale_amount']:,.0f}</div>
                        <div class="label">📦 Inventory Sales</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="card-3d glow-red" style="text-align:center;padding:0.8rem;">
                        <div class="value">PKR {selected_staff['expense_amount']:,.0f}</div>
                        <div class="label">💳 Expenses</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Staff details table
                st.divider()
                st.markdown(f"#### 📋 {selected_staff['name']} - Detailed Report")
                
                detail_data = {
                    "Metric": [
                        "Staff Name",
                        "Role",
                        "Status",
                        "Fees Collected (Count)",
                        "Fees Collected (Amount)",
                        "Attendance Marked",
                        "Inventory Sales (Count)",
                        "Inventory Sales (Amount)",
                        "Expenses (Count)",
                        "Expenses (Amount)"
                    ],
                    "Value": [
                        selected_staff['name'],
                        selected_staff['role'],
                        "✅ Active" if selected_staff.get('is_active', True) else "❌ Inactive",
                        selected_staff['fee_count'],
                        f"PKR {selected_staff['fee_amount']:,.2f}",
                        selected_staff['attendance_count'],
                        selected_staff['sale_count'],
                        f"PKR {selected_staff['sale_amount']:,.2f}",
                        selected_staff['expense_count'],
                        f"PKR {selected_staff['expense_amount']:,.2f}"
                    ]
                }
                
                st.dataframe(pd.DataFrame(detail_data), use_container_width=True, hide_index=True)
    else:
        st.info("📭 No staff members found for the selected filters.")
    
    st.divider()
    
    # ============================================
    # CHARTS
    # ============================================
    
    st.subheader("📊 Visual Analytics")
    
    if staff_list:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            # Fee Collection Chart
            st.markdown("#### 💰 Fee Collection by Staff")
            
            staff_names = [s['name'] for s in staff_list if s['fee_amount'] > 0]
            staff_fees = [s['fee_amount'] for s in staff_list if s['fee_amount'] > 0]
            
            if staff_names and staff_fees:
                fig = go.Figure(data=[
                    go.Bar(
                        x=staff_names,
                        y=staff_fees,
                        marker_color='#7C3AED',
                        marker_line_color='#A78BFA',
                        marker_line_width=1,
                        hovertemplate='%{x}<br>PKR %{y:,.2f}<extra></extra>'
                    )
                ])
                
                fig.update_layout(
                    template='plotly_dark',
                    title=dict(text="Fees Collected", font=dict(color='#F8FAFC', size=16)),
                    xaxis=dict(title="Staff", gridcolor='#1E293B'),
                    yaxis=dict(title="Amount (PKR)", gridcolor='#1E293B'),
                    plot_bgcolor='#0F172A',
                    paper_bgcolor='#0F172A',
                    height=300,
                    margin=dict(l=40, r=20, t=40, b=40),
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No fee collection data available.")
        
        with col_c2:
            # Attendance Chart
            st.markdown("#### ✅ Attendance Marked by Staff")
            
            staff_att = [s['name'] for s in staff_list if s['attendance_count'] > 0]
            att_counts = [s['attendance_count'] for s in staff_list if s['attendance_count'] > 0]
            
            if staff_att and att_counts:
                fig = go.Figure(data=[
                    go.Pie(
                        labels=staff_att,
                        values=att_counts,
                        marker=dict(colors=['#7C3AED', '#34D399', '#FBBF24', '#F87171', '#60A5FA']),
                        textinfo='label+percent',
                        textposition='auto',
                        hole=0.3,
                    )
                ])
                
                fig.update_layout(
                    template='plotly_dark',
                    title=dict(text="Attendance Distribution", font=dict(color='#F8FAFC', size=16)),
                    plot_bgcolor='#0F172A',
                    paper_bgcolor='#0F172A',
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No attendance data available.")
        
        # Additional charts
        col_c3, col_c4 = st.columns(2)
        
        with col_c3:
            # Inventory Sales Chart
            st.markdown("#### 📦 Inventory Sales by Staff")
            
            staff_sales = [s['name'] for s in staff_list if s['sale_amount'] > 0]
            sales_amounts = [s['sale_amount'] for s in staff_list if s['sale_amount'] > 0]
            
            if staff_sales and sales_amounts:
                fig = go.Figure(data=[
                    go.Bar(
                        x=staff_sales,
                        y=sales_amounts,
                        marker_color='#F59E0B',
                        marker_line_color='#FBBF24',
                        marker_line_width=1,
                        hovertemplate='%{x}<br>PKR %{y:,.2f}<extra></extra>'
                    )
                ])
                
                fig.update_layout(
                    template='plotly_dark',
                    title=dict(text="Inventory Sales", font=dict(color='#F8FAFC', size=16)),
                    xaxis=dict(title="Staff", gridcolor='#1E293B'),
                    yaxis=dict(title="Amount (PKR)", gridcolor='#1E293B'),
                    plot_bgcolor='#0F172A',
                    paper_bgcolor='#0F172A',
                    height=300,
                    margin=dict(l=40, r=20, t=40, b=40),
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No inventory sales data available.")
        
        with col_c4:
            # Expenses Chart
            st.markdown("#### 💳 Expenses by Staff")
            
            staff_exp = [s['name'] for s in staff_list if s['expense_amount'] > 0]
            exp_amounts = [s['expense_amount'] for s in staff_list if s['expense_amount'] > 0]
            
            if staff_exp and exp_amounts:
                fig = go.Figure(data=[
                    go.Bar(
                        x=staff_exp,
                        y=exp_amounts,
                        marker_color='#EF4444',
                        marker_line_color='#F87171',
                        marker_line_width=1,
                        hovertemplate='%{x}<br>PKR %{y:,.2f}<extra></extra>'
                    )
                ])
                
                fig.update_layout(
                    template='plotly_dark',
                    title=dict(text="Expenses", font=dict(color='#F8FAFC', size=16)),
                    xaxis=dict(title="Staff", gridcolor='#1E293B'),
                    yaxis=dict(title="Amount (PKR)", gridcolor='#1E293B'),
                    plot_bgcolor='#0F172A',
                    paper_bgcolor='#0F172A',
                    height=300,
                    margin=dict(l=40, r=20, t=40, b=40),
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expense data available.")
    else:
        st.info("📊 No data available for charts.")

    # ============================================
    # EXPORT REPORTS
    # ============================================
    
    st.divider()
    st.subheader("📥 Export Reports")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        if st.button("📋 Export Staff Report (CSV)", use_container_width=True):
            if staff_list:
                df = pd.DataFrame(staff_list)
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    data=csv,
                    file_name=f"staff_report_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("No data to export.")
    
    with col_exp2:
        if st.button("📄 Generate Summary Report", use_container_width=True):
            if staff_list:
                total_fees = sum(s['fee_amount'] for s in staff_list)
                total_expenses = sum(s['expense_amount'] for s in staff_list)
                total_sales = sum(s['sale_amount'] for s in staff_list)
                net = total_fees + total_sales - total_expenses
                
                report = f"""
📊 GYMPRO - STAFF PERFORMANCE REPORT
📅 Date: {date.today().strftime('%B %d, %Y')}
{'='*60}

📈 OVERVIEW
• Total Staff: {len(staff_list)}
• Total Fees Collected: PKR {total_fees:,.2f}
• Total Expenses: PKR {total_expenses:,.2f}
• Total Inventory Sales: PKR {total_sales:,.2f}
• Net Profit/Loss: PKR {net:,.2f}

{'='*60}
👥 STAFF DETAILS
"""
                for s in staff_list:
                    report += f"""
{'-'*40}
• Name: {s['name']}
• Role: {s['role']}
• Fees Collected: PKR {s['fee_amount']:,.2f} ({s['fee_count']} transactions)
• Attendance Marked: {s['attendance_count']}
• Inventory Sales: PKR {s['sale_amount']:,.2f} ({s['sale_count']} sales)
• Expenses: PKR {s['expense_amount']:,.2f} ({s['expense_count']} entries)
"""
                
                st.code(report, language="text")
                st.success("✅ Report generated! Copy it from above.")
            else:
                st.warning("No data to generate report.")
    
    with col_exp3:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.rerun()