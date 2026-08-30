import streamlit as st
import pandas as pd
import io
from datetime import date, datetime, timedelta
import database as db
import styles
import plotly.graph_objects as go
import plotly.express as px

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

def init_session_state():
    if 'inventory_photo_cache' not in st.session_state:
        st.session_state.inventory_photo_cache = {}
    if 'inventory_edit_id' not in st.session_state:
        st.session_state.inventory_edit_id = None

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
    
    /* 3D Table Effect */
    .table-3d {
        background: #0F172A;
        border: 1px solid #334155;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(0,0,0,0.4);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HELPERS
# ============================================

def get_stock_status(item):
    """Get stock status with color"""
    if not item:
        return "Unknown", "#94A3B8"
    ratio = item.quantity / item.min_quantity if item.min_quantity > 0 else 1
    if ratio <= 0:
        return "🔴 Out of Stock", "#EF4444"
    elif ratio <= 1:
        return "🔴 Low Stock", "#EF4444"
    elif ratio <= 2:
        return "🟡 Warning", "#F59E0B"
    else:
        return "🟢 In Stock", "#10B981"

# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render(gym_id, role):
    
    # ============================================
    # HEADER
    # ============================================
    
    styles.page_header("📦", "Stock & Inventory", 
                       "Manage supplements, equipment & daily sales with 3D insights")
    
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("🏋️ Add a gym first to start managing inventory.")
        return

    # ============================================
    # GYM SELECTOR
    # ============================================
    
    def gym_selector(key_suffix):
        if gym_id:
            st.text_input("🏋️ Gym", value=next((g.name for g in gyms if g.id == gym_id), ""),
                          disabled=True, key=f"inv_gym_display_{key_suffix}")
            return gym_id
        else:
            opts = {g.name: g.id for g in gyms}
            chosen = st.selectbox("🏋️ Select Gym", list(opts.keys()), key=f"inv_gym_{key_suffix}")
            return opts[chosen]

    # ============================================
    # TABS
    # ============================================
    
    tab_stock, tab_pos, tab_reports, tab_add = st.tabs([
        "📋 Stock Management",
        "🛒 Point of Sale",
        "📊 Sales Analytics",
        "➕ Add Item"
    ])

    # ============================================
    # TAB 1: STOCK MANAGEMENT
    # ============================================
    
    with tab_stock:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            sel_gid = gym_selector("stock")
        with sc2:
            st.write("")
            st.write("")
            low_only = st.checkbox("⚠️ Low Stock Only", key="inv_low_only")

        items = db.get_stock_items(gym_id=sel_gid, low_stock_only=low_only)

        if not items:
            st.info("📭 No inventory items found. Add items in the 'Add Item' tab.")
        else:
            # ============================================
            # STATS CARDS
            # ============================================
            
            low_count = sum(1 for i in items if i.quantity <= i.min_quantity)
            out_of_stock = sum(1 for i in items if i.quantity <= 0)
            total_stock_val = sum(i.purchase_price * i.quantity for i in items)
            total_potential = sum(i.sale_price * i.quantity for i in items)
            total_profit = total_potential - total_stock_val
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f"""
                <div class="card-3d glow-purple" style="text-align:center;">
                    <span class="icon">📦</span>
                    <div class="value">{len(items)}</div>
                    <div class="label">Total Items</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="card-3d glow-red" style="text-align:center;">
                    <span class="icon">🔴</span>
                    <div class="value">{low_count}</div>
                    <div class="label">Low Stock Alerts</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="card-3d glow-yellow" style="text-align:center;">
                    <span class="icon">💰</span>
                    <div class="value">PKR {total_stock_val:,.0f}</div>
                    <div class="label">Stock Value</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="card-3d glow-green" style="text-align:center;">
                    <span class="icon">📈</span>
                    <div class="value">PKR {total_potential:,.0f}</div>
                    <div class="label">Potential Revenue</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                profit_margin = (total_profit / total_potential * 100) if total_potential > 0 else 0
                st.markdown(f"""
                <div class="card-3d glow-blue" style="text-align:center;">
                    <span class="icon">💹</span>
                    <div class="value" style="font-size:1.5rem;">{profit_margin:.1f}%</div>
                    <div class="label">Profit Margin</div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            
            # ============================================
            # STOCK TABLE
            # ============================================
            
            rows = []
            for i in items:
                status, status_color = get_stock_status(i)
                gname = next((g.name for g in gyms if g.id == i.gym_id), "—")
                profit = i.sale_price - i.purchase_price
                rows.append({
                    "ID": i.id,
                    "Item": i.item_name,
                    "Category": i.category,
                    "Gym": gname,
                    "Purchase": i.purchase_price,
                    "Sale": i.sale_price,
                    "Profit": profit,
                    "Qty": i.quantity,
                    "Min": i.min_quantity,
                    "Status": status,
                    "Status Color": status_color,
                })
            df = pd.DataFrame(rows)
            
            # Display with formatting
            display_df = df.copy()
            display_df["Purchase"] = display_df["Purchase"].apply(lambda x: f"PKR {x:,.2f}")
            display_df["Sale"] = display_df["Sale"].apply(lambda x: f"PKR {x:,.2f}")
            display_df["Profit"] = display_df["Profit"].apply(lambda x: f"PKR {x:,.2f}")
            
            st.dataframe(
                display_df[["Item", "Category", "Qty", "Min", "Purchase", "Sale", "Profit", "Status"]],
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "Item": st.column_config.TextColumn("Item", width="medium"),
                    "Category": st.column_config.TextColumn("Category", width="small"),
                    "Qty": st.column_config.NumberColumn("Qty", width="small"),
                    "Min": st.column_config.NumberColumn("Min", width="small"),
                    "Purchase": st.column_config.TextColumn("Purchase", width="small"),
                    "Sale": st.column_config.TextColumn("Sale", width="small"),
                    "Profit": st.column_config.TextColumn("Profit", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="medium"),
                }
            )

            # ============================================
            # ADMIN: EDIT/DELETE
            # ============================================
            
            if role == "admin":
                st.divider()
                st.subheader("🔐 Admin Actions")
                st.caption("Edit or delete stock items")
                
                item_opts = {f"{i.item_name} (Qty: {i.quantity})": i.id for i in items}
                sel_item_label = st.selectbox("Select Item to Manage", list(item_opts.keys()), key="inv_edit_sel")
                sel_item = next((i for i in items if i.id == item_opts[sel_item_label]), None)
                
                if sel_item:
                    col_edit, col_delete = st.columns(2)
                    
                    # Edit
                    with col_edit:
                        with st.expander("✏️ Edit Item", expanded=False):
                            with st.form(f"edit_stock_{sel_item.id}"):
                                ec1, ec2 = st.columns(2)
                                with ec1:
                                    new_name = st.text_input("Item Name", value=sel_item.item_name, key=f"es_name_{sel_item.id}")
                                    new_cat = st.selectbox("Category", db.STOCK_CATEGORIES,
                                                           index=db.STOCK_CATEGORIES.index(sel_item.category) if sel_item.category in db.STOCK_CATEGORIES else 0,
                                                           key=f"es_cat_{sel_item.id}")
                                    new_buy = st.number_input("Purchase Price (PKR)", value=float(sel_item.purchase_price), min_value=0.0, step=1.0, key=f"es_buy_{sel_item.id}")
                                with ec2:
                                    new_sell = st.number_input("Sale Price (PKR)", value=float(sel_item.sale_price), min_value=0.0, step=1.0, key=f"es_sell_{sel_item.id}")
                                    new_qty = st.number_input("Quantity", value=int(sel_item.quantity), min_value=0, step=1, key=f"es_qty_{sel_item.id}")
                                    new_min = st.number_input("Min Alert Qty", value=int(sel_item.min_quantity), min_value=0, step=1, key=f"es_min_{sel_item.id}")
                                
                                if st.form_submit_button("💾 Update Item", type="primary", use_container_width=True):
                                    db.update_stock_item(sel_item.id, item_name=new_name, category=new_cat,
                                                        purchase_price=new_buy, sale_price=new_sell,
                                                        quantity=new_qty, min_quantity=new_min)
                                    st.success("✅ Item updated successfully!")
                                    st.rerun()
                    
                    # Delete
                    with col_delete:
                        with st.expander("🗑️ Delete Item", expanded=False):
                            st.warning(f"⚠️ Delete **{sel_item.item_name}**?")
                            st.caption("This cannot be undone!")
                            if st.button("🚨 Confirm Delete", type="primary", use_container_width=True):
                                db.delete_stock_item(sel_item.id)
                                st.success("✅ Item deleted!")
                                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 2: POINT OF SALE
    # ============================================
    
    with tab_pos:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.subheader("🛒 Point of Sale")
        st.caption("Sell items to members or walk-in customers")
        
        sel_gid_pos = gym_selector("pos")
        items_pos = db.get_stock_items(gym_id=sel_gid_pos)
        
        if not items_pos:
            st.info("📭 No stock items available. Add items first!")
        else:
            with st.form("pos_form", clear_on_submit=True):
                pc1, pc2 = st.columns(2)
                
                with pc1:
                    item_opts_pos = {f"{i.item_name} — PKR {i.sale_price:.0f} (Qty: {i.quantity})": i.id
                                     for i in items_pos if i.quantity > 0}
                    if not item_opts_pos:
                        st.warning("⚠️ All items are out of stock!")
                        st.stop()
                    
                    sel_pos_label = st.selectbox("🛒 Select Item *", list(item_opts_pos.keys()), key="pos_item_sel")
                    sel_pos_id = item_opts_pos[sel_pos_label]
                    sel_pos_item = next((i for i in items_pos if i.id == sel_pos_id), None)
                    
                    qty_to_sell = st.number_input("📦 Quantity", min_value=1,
                                                   max_value=sel_pos_item.quantity if sel_pos_item else 1,
                                                   step=1, value=1, key="pos_qty")
                    custom_price = st.number_input(
                        "💰 Sale Price (PKR)",
                        value=float(sel_pos_item.sale_price) if sel_pos_item else 0.0,
                        min_value=0.0, step=1.0, key="pos_price",
                    )
                
                with pc2:
                    members_pos = db.get_members(gym_id=sel_gid_pos, status="Active")
                    mem_opts_pos = {"👤 Walk-in (No Member)": None} | {
                        f"{m.serial_number} — {m.full_name}": m.id for m in members_pos
                    }
                    mem_sel_pos = st.selectbox("👤 Member", list(mem_opts_pos.keys()), key="pos_member_sel")
                    pos_member_id = mem_opts_pos[mem_sel_pos]
                    sale_date_pos = st.date_input("📅 Sale Date", value=date.today(), key="pos_date")
                    pos_notes = st.text_input("📝 Notes", placeholder="Any remarks...", key="pos_notes")
                
                if sel_pos_item:
                    total_preview = qty_to_sell * custom_price
                    st.info(f"💰 **Total: PKR {total_preview:,.2f}** ({qty_to_sell} × PKR {custom_price:.2f})")
                    
                    # Show stock after sale
                    remaining = sel_pos_item.quantity - qty_to_sell
                    if remaining < 0:
                        st.error(f"❌ Only {sel_pos_item.quantity} items available!")
                    elif remaining <= sel_pos_item.min_quantity:
                        st.warning(f"⚠️ After sale, only {remaining} items left (Min: {sel_pos_item.min_quantity})")
                
                if st.form_submit_button("✅ Process Sale", type="primary", use_container_width=True):
                    current_user = st.session_state.get("username", "staff")
                    ok, msg = db.sell_stock_item(
                        stock_item_id=sel_pos_id,
                        gym_id=sel_gid_pos,
                        member_id=pos_member_id,
                        quantity_sold=qty_to_sell,
                        sale_price=custom_price,
                        sold_by=current_user,
                        sale_date=sale_date_pos,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 3: SALES ANALYTICS
    # ============================================
    
    with tab_reports:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.subheader("📊 Sales Analytics")
        st.caption("Track inventory revenue and performance")
        
        rc1, rc2, rc3 = st.columns([2, 1, 1])
        with rc1:
            sel_gid_rep = gym_selector("rep")
        with rc2:
            rep_from = st.date_input("📅 From", value=date.today().replace(day=1), key="inv_from")
        with rc3:
            rep_to = st.date_input("📅 To", value=date.today(), key="inv_to")
        
        sales = db.get_stock_sales(gym_id=sel_gid_rep, date_from=rep_from, date_to=rep_to)
        
        if not sales:
            st.info("📭 No sales in this period.")
        else:
            # ============================================
            # STATS CARDS
            # ============================================
            
            total_revenue = sum(s.total_amount for s in sales)
            items_map = {i.id: i for i in db.get_stock_items()}
            members_map = {m.id: m for m in db.get_members()}
            
            total_profit = 0.0
            total_items_sold = 0
            
            for s in sales:
                item = items_map.get(s.stock_item_id)
                profit = (s.sale_price - (item.purchase_price if item else 0)) * s.quantity_sold
                total_profit += profit
                total_items_sold += s.quantity_sold
            
            margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="card-3d glow-green" style="text-align:center;">
                    <span class="icon">💰</span>
                    <div class="value">PKR {total_revenue:,.0f}</div>
                    <div class="label">Total Revenue</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="card-3d glow-blue" style="text-align:center;">
                    <span class="icon">📈</span>
                    <div class="value">PKR {total_profit:,.0f}</div>
                    <div class="label">Total Profit</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="card-3d glow-purple" style="text-align:center;">
                    <span class="icon">📊</span>
                    <div class="value" style="font-size:1.5rem;">{margin:.1f}%</div>
                    <div class="label">Profit Margin</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="card-3d glow-yellow" style="text-align:center;">
                    <span class="icon">📦</span>
                    <div class="value">{total_items_sold}</div>
                    <div class="label">Items Sold</div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            
            # ============================================
            # SALES TABLE
            # ============================================
            
            rows = []
            for s in sales:
                item = items_map.get(s.stock_item_id)
                mem = members_map.get(s.member_id) if s.member_id else None
                profit = (s.sale_price - (item.purchase_price if item else 0)) * s.quantity_sold
                rows.append({
                    "Date": s.sale_date,
                    "Item": item.item_name if item else "—",
                    "Category": item.category if item else "—",
                    "Qty": s.quantity_sold,
                    "Sale Price": s.sale_price,
                    "Total": s.total_amount,
                    "Profit": profit,
                    "Member": mem.full_name if mem else "Walk-in",
                    "Sold By": s.sold_by or "—",
                })
            df_sales = pd.DataFrame(rows)
            
            display_df = df_sales.copy()
            display_df["Sale Price"] = display_df["Sale Price"].apply(lambda x: f"PKR {x:,.2f}")
            display_df["Total"] = display_df["Total"].apply(lambda x: f"PKR {x:,.2f}")
            display_df["Profit"] = display_df["Profit"].apply(lambda x: f"PKR {x:,.2f}")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=350,
                column_config={
                    "Date": st.column_config.DateColumn("Date", width="small"),
                    "Item": st.column_config.TextColumn("Item", width="medium"),
                    "Category": st.column_config.TextColumn("Category", width="small"),
                    "Qty": st.column_config.NumberColumn("Qty", width="small"),
                    "Sale Price": st.column_config.TextColumn("Sale Price", width="small"),
                    "Total": st.column_config.TextColumn("Total", width="small"),
                    "Profit": st.column_config.TextColumn("Profit", width="small"),
                    "Member": st.column_config.TextColumn("Member", width="medium"),
                    "Sold By": st.column_config.TextColumn("Sold By", width="small"),
                }
            )
            
            # ============================================
            # EXPORT
            # ============================================
            
            col_exp1, col_exp2 = st.columns([1, 5])
            with col_exp1:
                if st.button("⬇️ Export CSV", use_container_width=True):
                    buf = io.StringIO()
                    df_sales.to_csv(buf, index=False)
                    st.download_button(
                        "📥 Download", 
                        data=buf.getvalue().encode(),
                        file_name=f"inventory_sales_{rep_from}_{rep_to}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ============================================
    # TAB 4: ADD ITEM
    # ============================================
    
    with tab_add:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#1E293B,#0F172A);
                    border:1px solid #334155;
                    border-radius:12px;
                    padding:1.5rem;
                    box-shadow:0 8px 25px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        st.subheader("➕ Add New Stock Item")
        st.caption("Add a new item to your inventory")
        
        sel_gid_add = gym_selector("add")

        with st.form("add_stock_form", clear_on_submit=True):
            ac1, ac2 = st.columns(2)
            with ac1:
                item_name = st.text_input("📦 Item Name *", placeholder="e.g., Whey Protein 1kg", key="as_name")
                category = st.selectbox("📂 Category *", db.STOCK_CATEGORIES, key="as_category")
                purchase_price = st.number_input("💰 Purchase Price (PKR) *", min_value=0.0, step=1.0, key="as_buy")
            with ac2:
                sale_price = st.number_input("💰 Sale Price (PKR) *", min_value=0.0, step=1.0, key="as_sell")
                quantity = st.number_input("📦 Initial Quantity *", min_value=0, step=1, key="as_qty")
                min_qty = st.number_input("⚠️ Low Stock Alert Threshold", min_value=0, step=1, value=5, key="as_min")
            
            # Show profit preview
            if sale_price > 0 and purchase_price > 0:
                profit_per_unit = sale_price - purchase_price
                total_profit = profit_per_unit * quantity
                st.info(f"💹 **Profit per unit:** PKR {profit_per_unit:,.2f} | **Total potential profit:** PKR {total_profit:,.2f}")
            
            if st.form_submit_button("✅ Add to Inventory", type="primary", use_container_width=True):
                if not item_name.strip():
                    st.error("❌ Item name is required!")
                elif sale_price < purchase_price:
                    st.warning("⚠️ Sale price is less than purchase price — you'll be selling at a loss!")
                    ok, msg = db.add_stock_item(sel_gid_add, item_name, category,
                                                purchase_price, sale_price, quantity, min_qty)
                    st.success(msg) if ok else st.error(msg)
                else:
                    ok, msg = db.add_stock_item(sel_gid_add, item_name, category,
                                                purchase_price, sale_price, quantity, min_qty)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        
        st.markdown("</div>", unsafe_allow_html=True)