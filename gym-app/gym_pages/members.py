import streamlit as st
import pandas as pd
import os
import uuid
from PIL import Image
from datetime import date, timedelta, datetime
import database as db
import styles
from qr_utils import member_qr_png
import object_store
import id_card

# ── 🔥 IMPORT FOR PRINT ──────────────────────────────────────────────────────
try:
    from printer_utils import (
        format_receipt, render_print_preview,
        render_print_component
    )
    HAS_PRINTER = True
except ImportError:
    HAS_PRINTER = False

GENDERS = ["Male", "Female", "Other", "Prefer not to say"]
STATUSES = ["Active", "Inactive", "Suspended", "Frozen"]

# ── Cached DB helpers ──────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _cm(gym_id, status, search):
    return db.get_members(gym_id=gym_id, status=status, search=search)

@st.cache_data(ttl=300, show_spinner=False)
def _ce(gym_id):
    return db.get_expiring_members(days=7, gym_id=gym_id)

@st.cache_data(ttl=300, show_spinner=False)
def _cf(gym_id):
    return db.get_fee_records(gym_id=gym_id)

@st.cache_data(ttl=3600, show_spinner=False)
def _photo_bytes_cached(key: str):
    return object_store.get_photo_bytes(key or "")

@st.cache_data(ttl=300, show_spinner=False)
def _get_all_fee_records(gym_id):
    if gym_id:
        return db.get_fee_records(gym_id=gym_id)
    return []


def save_photo(f, serial: str = "") -> str:
    file_bytes = f.getbuffer()
    key = object_store.upload_photo(bytes(file_bytes), f.name, serial=serial)
    return key


def show_photo(photo_field, w=100):
    photo_bytes = _photo_bytes_cached(photo_field or "")
    size = f"{w}px"
    if photo_bytes:
        import io as _io
        st.image(_io.BytesIO(photo_bytes), width=w)
    else:
        st.markdown(
            f'<div style="width:{size};height:{size};border-radius:10px;'
            f'background:#1E293B;border:1px solid #334155;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:{w // 2}px;color:#94A3B8;">👤</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# PAYMENT STATUS - BULK QUERY
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def _get_member_payment_status_bulk(member_ids_tuple, gym_id):
    if not member_ids_tuple:
        return {}

    all_fee_records = db.get_fee_records(gym_id=gym_id)

    member_fee_map = {}
    for record in all_fee_records:
        mid = record.member_id
        if mid not in member_fee_map:
            member_fee_map[mid] = record
        elif record.payment_date and member_fee_map[mid].payment_date:
            try:
                if record.payment_date > member_fee_map[mid].payment_date:
                    member_fee_map[mid] = record
            except:
                pass

    status_map = {}
    today = date.today()

    for member_id in member_ids_tuple:
        fee_record = member_fee_map.get(member_id)

        if fee_record and hasattr(fee_record, 'period_end') and fee_record.period_end:
            try:
                period_end = pd.to_datetime(fee_record.period_end).date()

                if period_end >= today:
                    days_left = (period_end - today).days
                    if days_left <= 7:
                        status_map[member_id] = ("upcoming", f"🟡 {days_left}d left", "#F59E0B", "#1E293B")
                    else:
                        status_map[member_id] = ("paid", f"✅ Paid ({days_left}d left)", "#10B981", "white")
                else:
                    days_over = (today - period_end).days
                    status_map[member_id] = ("unpaid", f"🔴 Expired ({days_over}d)", "#EF4444", "white")
            except:
                status_map[member_id] = ("unpaid", "⏳ Pending", "#F59E0B", "#1E293B")
        else:
            status_map[member_id] = ("unpaid", "⏳ Pending", "#F59E0B", "#1E293B")

    return status_map


def get_member_payment_status_fast(member, status_cache=None):
    if not member or not hasattr(member, 'id'):
        return "unpaid", "⚠️ No data", "#F59E0B", "#1E293B"

    if status_cache and member.id in status_cache:
        return status_cache[member.id]

    try:
        fee_records = db.get_fee_records(member_id=member.id, limit=1)
        if fee_records:
            latest_fee = fee_records[0]
            if hasattr(latest_fee, 'period_end') and latest_fee.period_end:
                try:
                    period_end = pd.to_datetime(latest_fee.period_end).date()
                    today = date.today()

                    if period_end >= today:
                        days_left = (period_end - today).days
                        if days_left <= 7:
                            return "upcoming", f"🟡 {days_left}d left", "#F59E0B", "#1E293B"
                        else:
                            return "paid", f"✅ Paid ({days_left}d left)", "#10B981", "white"
                    else:
                        days_over = (today - period_end).days
                        return "unpaid", f"🔴 Expired ({days_over}d)", "#EF4444", "white"
                except:
                    pass

        if hasattr(member, 'expiry_date') and member.expiry_date:
            try:
                expiry = pd.to_datetime(member.expiry_date).date()
                today = date.today()
                days_left = (expiry - today).days

                if days_left < 0:
                    return "unpaid", f"🔴 Expired ({abs(days_left)}d)", "#EF4444", "white"
                elif days_left <= 7:
                    return "upcoming", f"🟡 {days_left}d left", "#F59E0B", "#1E293B"
                else:
                    return "paid", f"✅ Paid ({days_left}d left)", "#10B981", "white"
            except:
                pass

        return "unpaid", "⏳ Pending", "#F59E0B", "#1E293B"
    except Exception:
        return "unpaid", "⚠️ Error", "#EF4444", "white"


# ============================================================
# MEMBER ANALYTICS
# ============================================================

def render_member_analytics(members):
    if not members:
        return
    
    st.markdown("#### 📊 Member Analytics")
    
    membership_types = {}
    status_counts = {}
    join_months = {}
    
    for m in members:
        mtype = m.membership_type or "Unknown"
        membership_types[mtype] = membership_types.get(mtype, 0) + 1
        status_counts[m.status] = status_counts.get(m.status, 0) + 1
        
        if m.join_date:
            try:
                join_dt = date.fromisoformat(str(m.join_date))
                month_key = join_dt.strftime("%b %Y")
                join_months[month_key] = join_months.get(month_key, 0) + 1
            except:
                pass
    
    col1, col2 = st.columns(2)
    
    with col1:
        if membership_types:
            df_types = pd.DataFrame({
                "Type": list(membership_types.keys()),
                "Count": list(membership_types.values())
            })
            st.dataframe(df_types, use_container_width=True, hide_index=True)
        else:
            st.info("No membership data")
    
    with col2:
        if status_counts:
            df_status = pd.DataFrame({
                "Status": list(status_counts.keys()),
                "Count": list(status_counts.values())
            })
            st.dataframe(df_status, use_container_width=True, hide_index=True)
        else:
            st.info("No status data")
    
    if join_months:
        st.markdown("#### 📈 Monthly Join Trend")
        df_join = pd.DataFrame({
            "Month": list(join_months.keys()),
            "New Members": list(join_months.values())
        })
        df_join = df_join.sort_values("Month")
        st.dataframe(df_join, use_container_width=True, hide_index=True)


# ============================================================
# QUICK FEE COLLECTION - WITH PRINT SLIP (FIXED)
# ============================================================

def render_quick_fee_collection(member, gym_id):
    """Quick fee collection modal with print receipt - FIXED"""
    st.markdown("#### 💳 Quick Fee Collection")
    
    # ── 🔥 FIX: Ensure gym_id is not None ──────────────────────────────────
    if gym_id is None and member:
        gym_id = member.gym_id
        if gym_id:
            gym = db.get_gym(gym_id)
            if gym:
                st.info(f"📍 Gym: {gym.name}")
    
    if gym_id is None:
        st.error("❌ Gym ID is required. Please select a gym first.")
        return
    
    gym = db.get_gym(gym_id)
    if not gym:
        st.error("❌ Gym not found.")
        return
    gym_name = gym.name
    
    # ── 🔥 Check pending print ──────────────────────────────────────────────
    pending = st.session_state.pop('pending_print_quick', None)
    if pending:
        st.success("✅ Payment recorded! Print dialog should open automatically:")
        if HAS_PRINTER:
            render_print_component(pending['data'], copies=pending['copies'])
        else:
            st.info("📄 Print component not available. Receipt data is ready.")
            st.json(pending['data'])
        st.divider()
    
    with st.form(f"quick_fee_form_{member.id}"):
        col1, col2, col3 = st.columns(3)
        with col1:
            amount = st.number_input(
                "Amount (PKR)", 
                min_value=0, 
                step=500, 
                value=int(member.fee_amount or 0),
                key=f"qf_amount_{member.id}"
            )
        with col2:
            payment_method = st.selectbox(
                "Method", 
                ["Cash", "Bank Transfer", "Card", "Online", "Cheque"],
                key=f"qf_method_{member.id}"
            )
        with col3:
            payment_date = st.date_input(
                "Date", 
                value=date.today(),
                key=f"qf_date_{member.id}"
            )
        
        period_start = st.date_input(
            "Period Start", 
            value=date.today(),
            key=f"qf_start_{member.id}"
        )
        period_end = st.date_input(
            "Period End", 
            value=date.today() + timedelta(days=30),
            key=f"qf_end_{member.id}"  # ✅ FIXED: Added closing }
        )
        notes = st.text_area(
            "Notes", 
            placeholder="Payment notes...",
            key=f"qf_notes_{member.id}"
        )
        
        # ── 🖨️ Print Options ──────────────────────────────────────────────
        st.markdown("---")
        st.subheader("🖨️ Print Options")
        
        col_print1, col_print2 = st.columns(2)
        with col_print1:
            print_receipt = st.checkbox(
                "🖨️ Print Receipt", 
                value=True, 
                key=f"qf_print_{member.id}"
            )
        with col_print2:
            print_copies = st.radio(
                "📄 Copies",
                ["2 (Member + Gym)", "1 (Member only)"],
                index=0,
                key=f"qf_copies_{member.id}"
            )
        
        submitted = st.form_submit_button(
            "💰 Record Payment", 
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if amount <= 0:
                st.error("❌ Amount must be greater than 0")
            else:
                # ── 🔥 Generate receipt number ──────────────────────────────
                receipt_no = f"RCP-{uuid.uuid4().hex[:8].upper()}"
                
                # ── 🔥 FIX: gym_id is now guaranteed not None ──────────────
                ok, msg = db.add_fee_record(
                    member_id=member.id,
                    gym_id=gym_id,  # ✅ Fixed
                    amount=amount,
                    payment_method=payment_method,
                    payment_date=payment_date,
                    period_start=period_start,
                    period_end=period_end,
                    collected_by=st.session_state.get('username', 'Staff'),
                    notes=notes
                )
                
                if ok:
                    # ── 🔥 Update member expiry ──────────────────────────────
                    db.update_member(member.id, expiry_date=str(period_end), status="Active")
                    
                    # ── 🔥 Log activity ──────────────────────────────────────
                    try:
                        db.log_activity(
                            user=st.session_state.get('username', 'Staff'), 
                            action="FEE_COLLECTED_QUICK",
                            details=f"Member: {member.full_name} ({member.serial_number}) | Method: {payment_method} | Period: {period_start} → {period_end}",
                            gym_id=gym_id, 
                            amount=amount,
                            record_ref=receipt_no,
                        )
                    except Exception:
                        pass
                    
                    # ── 🔥 Log receipt ──────────────────────────────────────
                    try:
                        if hasattr(db, 'log_receipt'):
                            db.log_receipt(
                                fee_record_id=None,
                                gym_id=gym_id,
                                member_name=member.full_name,
                                receipt_number=receipt_no,
                                amount=amount,
                                collected_by=st.session_state.get('username', 'Staff'),
                                print_issued=False,
                            )
                    except Exception:
                        pass
                    
                    # ── 🔥 CREATE RECEIPT DATA ──────────────────────────────
                    receipt_data = {
                        'gym_name':     gym_name,
                        'gym_address':  "",
                        'gym_phone':    "",
                        'receipt_no':   receipt_no,
                        'date':         payment_date.strftime('%Y-%m-%d'),
                        'time':         datetime.now().strftime('%I:%M %p'),
                        'collected_by': st.session_state.get('username', 'Staff'),
                        'member_name':  member.full_name,
                        'serial':       member.serial_number,
                        'phone':        member.phone or "N/A",
                        'amount':       amount,
                        'method':       payment_method,
                        'period_start': period_start.strftime('%Y-%m-%d'),
                        'period_end':   period_end.strftime('%Y-%m-%d'),
                    }
                    
                    # ── 🔥 PRINT RECEIPT ────────────────────────────────────
                    if print_receipt:
                        copies = 2 if "2" in print_copies else 1
                        st.session_state['pending_print_quick'] = {
                            'data': receipt_data,
                            'copies': copies,
                        }
                        if hasattr(db, 'update_print_issued'):
                            try:
                                db.update_print_issued(receipt_no, True)
                            except Exception:
                                pass
                    
                    st.success(f"✅ Payment recorded! Receipt: {receipt_no}")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ============================================================
# ⭐ BULK ACTIONS - WITH PERMISSIONS
# ============================================================

def render_bulk_actions(members, gym_id, role):
    """Bulk actions for members - WITH ROLE-BASED PERMISSIONS"""
    if not members:
        return
    
    # ✅ Check if user can perform bulk actions
    can_delete = role in ["admin", "owner"]
    can_update = role in ["admin", "owner", "staff"]
    
    st.markdown("#### 📦 Bulk Actions")
    
    with st.expander("Bulk Actions", expanded=False):
        selected_serials = st.multiselect(
            "Select Members",
            options=[m.serial_number for m in members],
            format_func=lambda x: f"{x} - {next((m.full_name for m in members if m.serial_number == x), '')}"
        )
        
        if selected_serials:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_status = st.selectbox("Change Status to", ["Active", "Inactive", "Suspended", "Frozen"])
                if st.button("🔄 Update Status", use_container_width=True, disabled=not can_update):
                    if can_update:
                        for serial in selected_serials:
                            member = next((m for m in members if m.serial_number == serial), None)
                            if member:
                                db.update_member(member.id, status=new_status)
                        _cm.clear()
                        st.success(f"✅ Updated {len(selected_serials)} members")
                        st.rerun()
                    else:
                        st.error("❌ You don't have permission to update members")
            
            with col2:
                new_expiry = st.date_input("Set Expiry Date", value=date.today() + timedelta(days=30))
                if st.button("📅 Set Expiry", use_container_width=True, disabled=not can_update):
                    if can_update:
                        for serial in selected_serials:
                            member = next((m for m in members if m.serial_number == serial), None)
                            if member:
                                db.update_member(member.id, expiry_date=str(new_expiry))
                        _cm.clear()
                        st.success(f"✅ Updated expiry for {len(selected_serials)} members")
                        st.rerun()
                    else:
                        st.error("❌ You don't have permission to update members")
            
            with col3:
                # ⭐ DELETE BUTTON - ONLY FOR ADMIN/OWNER
                if can_delete:
                    if st.button("🗑️ Delete Selected", use_container_width=True, type="primary"):
                        st.warning(f"⚠️ Delete {len(selected_serials)} members? This cannot be undone!")
                        if st.button("✅ Confirm Delete", key="bulk_confirm_delete"):
                            for serial in selected_serials:
                                member = next((m for m in members if m.serial_number == serial), None)
                                if member:
                                    if member.photo_path:
                                        try:
                                            object_store.delete_photo(member.photo_path)
                                        except:
                                            pass
                                    db.delete_member(member.id)
                            _cm.clear()
                            st.success(f"✅ Deleted {len(selected_serials)} members")
                            st.rerun()
                else:
                    # ⛔ Staff ke liye delete button hide/disable
                    st.info("🔒 Delete members is only available for Admin")
                    st.button("🗑️ Delete Selected", use_container_width=True, disabled=True)


# ============================================================
# FAST PROFESSIONAL TABLE - FIXED WITH FILTERS
# ============================================================

def render_fast_professional_table(members, gym_id=None):
    if not members:
        st.info("📭 No members found.")
        return

    today = date.today()
    member_ids = tuple(m.id for m in members)
    status_cache = _get_member_payment_status_bulk(member_ids, gym_id)

    table_data = []
    for m in members:
        status_type, status_text, _, _ = get_member_payment_status_fast(m, status_cache)

        days_left = None
        expiry_display = "—"
        if m.expiry_date:
            try:
                expiry = date.fromisoformat(str(m.expiry_date))
                days_left = (expiry - today).days
                if days_left < 0:
                    expiry_display = f"🔴 {abs(days_left)}d overdue"
                elif days_left == 0:
                    expiry_display = "🟡 Today!"
                elif days_left <= 7:
                    expiry_display = f"🟡 {days_left}d left"
                else:
                    expiry_display = f"✅ {days_left}d left"
            except:
                expiry_display = "—"

        if status_type == "paid":
            status_display = "✅ Paid"
        elif status_type == "upcoming":
            status_display = "🟡 Upcoming"
        else:
            status_display = "🔴 Unpaid"

        table_data.append({
            "Serial": m.serial_number or "—",
            "Member": m.full_name,
            "Phone": m.phone or "—",
            "Type": m.membership_type or "—",
            "Fee": f"PKR {m.fee_amount:,.0f}",
            "Expiry": expiry_display,
            "Payment": status_display,
            "Status": m.status or "—",
        })

    df = pd.DataFrame(table_data)

    st.markdown(f"""
    <div style="background:#0F172A;border-radius:12px;border:1px solid #1E293B;padding:16px;margin:12px 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:12px;">
            <div style="color:#F8FAFC;font-weight:700;font-size:1rem;">
                👥 Members <span style="background:#7C3AED;color:white;padding:2px 12px;border-radius:999px;font-size:0.75rem;margin-left:8px;">{len(members)}</span>
            </div>
            <div style="display:flex;gap:12px;font-size:0.75rem;">
                <span style="color:#34D399;">🟢 {sum(1 for m in members if m.status == 'Active')} Active</span>
                <span style="color:#F87171;">🔴 {sum(1 for m in members if get_member_payment_status_fast(m, status_cache)[0] == 'unpaid')} Unpaid</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Serial": st.column_config.TextColumn("Serial #", width="small"),
            "Member": st.column_config.TextColumn("Member Name", width="medium"),
            "Phone": st.column_config.TextColumn("Phone", width="small"),
            "Type": st.column_config.TextColumn("Membership", width="small"),
            "Fee": st.column_config.TextColumn("Fee", width="small"),
            "Expiry": st.column_config.TextColumn("Expiry Status", width="small"),
            "Payment": st.column_config.TextColumn("Payment", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
    )

    st.caption(f"🔄 Updated: {datetime.now().strftime('%I:%M %p')} · {len(members)} members")


# ============================================================
# MAIN RENDER FUNCTION - FIXED WITH FILTERS
# ============================================================

def render(gym_id, role):
    styles.page_header("👥", "Members", "Register, search and manage gym members")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym in **Gym Setup** first.")
        return

    # ── Staff gym restriction ─────────────────────────────────────────────────
    if role == "staff":
        user_gym_id = st.session_state.get("user_gym_id")
        if not gym_id and user_gym_id:
            gym_id = user_gym_id
        elif not gym_id:
            gym_id = gyms[0].id if gyms else None
        if not gym_id:
            st.warning("⚠️ Aapka account kisi gym se assign nahi hai. Admin se rabta karein.")
            return

    # ── STATS ──────────────────────────────────────────────────────────────────
    gym_members = _cm(gym_id, "All", "")
    today = date.today()
    total_members  = len(gym_members)
    active_members = sum(1 for m in gym_members if m.status == "Active")
    expired_count  = 0
    for m in gym_members:
        if m.expiry_date:
            try:
                if (date.fromisoformat(str(m.expiry_date)) - today).days < 0:
                    expired_count += 1
            except Exception:
                pass
    expiring_soon  = len(_ce(gym_id))
    gym_fees       = _cf(gym_id)
    total_collected = sum(f.amount for f in gym_fees) if gym_fees else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👥 Total Members",    total_members)
    c2.metric("✅ Active",           active_members)
    c3.metric("🚨 Expired",          expired_count)
    c4.metric("⏳ Expiring (7 days)", expiring_soon)
    c5.metric("💰 Fees Collected",   f"PKR {total_collected:,.0f}")

    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_add, tab_list, tab_analytics = st.tabs([
        "➕ Register New Member", 
        "📋 Members",
        "📊 Analytics"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — REGISTER
    # ══════════════════════════════════════════════════════════════════════════
    with tab_add:
        _register_form(gyms, gym_id, role)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — MEMBER LIST - FIXED WITH FILTERS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_list:
        gym_opts = {g.name: g.id for g in gyms}

        # ── 🔥 FILTERS ──
        f1, f2, f3, f4, f5, f6, f7 = st.columns([1.5, 1.5, 1.5, 1, 1, 1, 1])
        with f1:
            if gym_id or role == "staff":
                chosen_gym_name = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
                st.text_input("🏋️ Gym", value=chosen_gym_name, disabled=True, key="ml_gym_display")
                selected_gid = gym_id
            else:
                opts = {"All Gyms": None} | gym_opts
                chosen = st.selectbox("🏋️ Gym", list(opts.keys()), key="ml_gym")
                selected_gid = opts[chosen]
        with f2:
            search = st.text_input("🔍 Search", placeholder="Name, serial, phone…", key="ml_search")
        with f3:
            status_f = st.selectbox("📊 Status", ["All"] + STATUSES, key="ml_status")
        with f4:
            # ── 🔥 PAYMENT FILTER ──
            payment_filter = st.selectbox(
                "💳 Payment", 
                ["All Members", "Paid", "Unpaid", "Upcoming"],
                key="ml_payment_filter"
            )
        with f5:
            st.write("")
            st.write("")
            st.button("🔄 Refresh", use_container_width=True, key="ml_refresh",
                      on_click=lambda: _cm.clear())
        with f6:
            st.write("")
            st.write("")
            export_btn = st.button("⬇️ Export CSV", use_container_width=True, key="ml_export")
        with f7:
            st.write("")
            st.write("")
            show_bulk = st.button("📦 Bulk Actions", use_container_width=True, key="ml_bulk")

        # ── 🔥 GET MEMBERS WITH PAYMENT FILTER ──
        members = _cm(selected_gid, status_f, search)

        # ── 🔥 APPLY PAYMENT FILTER ──
        if members and payment_filter != "All Members":
            member_ids = tuple(m.id for m in members)
            status_cache = _get_member_payment_status_bulk(member_ids, selected_gid)
            
            filtered_members = []
            for m in members:
                status_type, _, _, _ = get_member_payment_status_fast(m, status_cache)
                if payment_filter == "Paid" and status_type == "paid":
                    filtered_members.append(m)
                elif payment_filter == "Unpaid" and status_type == "unpaid":
                    filtered_members.append(m)
                elif payment_filter == "Upcoming" and status_type == "upcoming":
                    filtered_members.append(m)
            members = filtered_members

        if export_btn and members:
            import io as _io2
            rows = []
            for m in members:
                rows.append({
                    "Serial #": m.serial_number,
                    "Full Name": m.full_name,
                    "Phone": m.phone or "",
                    "Email": m.email or "",
                    "Gender": m.gender or "",
                    "DOB": m.dob or "",
                    "Membership": m.membership_type or "",
                    "Fee (PKR)": m.fee_amount or 0,
                    "Join Date": m.join_date,
                    "Expiry Date": m.expiry_date or "",
                    "Status": m.status,
                    "Notes": m.notes or "",
                })
            csv_buf = _io2.StringIO()
            pd.DataFrame(rows).to_csv(csv_buf, index=False)
            st.download_button("📥 Download CSV", data=csv_buf.getvalue(),
                               file_name="members_export.csv", mime="text/csv",
                               key="ml_csv_dl")

        if not members:
            st.info("📭 No members match your filters.")
        else:
            render_fast_professional_table(members, selected_gid)

            # ⭐ PASS ROLE TO BULK ACTIONS
            if show_bulk:
                render_bulk_actions(members, selected_gid, role)

            st.divider()

            # ── Member Detail View ──────────────────────────────────────────
            st.markdown("#### 👤 Member Details")
            member_options = {m.serial_number: m for m in members}

            def _label(s):
                m = member_options[s]
                badge = ""
                if m.expiry_date:
                    try:
                        d = (date.fromisoformat(str(m.expiry_date)) - today).days
                        if d < 0:
                            badge = " 🔴 EXPIRED"
                        elif d <= 7:
                            badge = f" 🟡 {d}d left"
                    except Exception:
                        pass
                return f"{s} — {m.full_name}{badge}"

            selected_serial = st.selectbox(
                "Select Member for Details",
                list(member_options.keys()),
                format_func=_label,
                key="ml_select_member",
            )
            selected_m = member_options.get(selected_serial)
            if selected_m:
                _member_detail(selected_m, gyms, role, selected_gid)

            # ── Summary Tables ──────────────────────────────────────────────
            member_ids = tuple(m.id for m in members)
            status_cache = _get_member_payment_status_bulk(member_ids, selected_gid)

            active_list   = []
            expired_list  = []
            upcoming_list = []
            unpaid_list   = []

            for m in members:
                expiry_str = str(m.expiry_date) if m.expiry_date else None
                is_expired  = False
                is_upcoming = False
                days_left   = None
                days_over   = None
                if expiry_str:
                    try:
                        exp       = date.fromisoformat(expiry_str)
                        days_left = (exp - today).days
                        if days_left < 0:
                            is_expired = True
                            days_over  = abs(days_left)
                        elif days_left <= 7:
                            is_upcoming = True
                    except Exception:
                        pass

                fee_str = f"PKR {m.fee_amount:,.0f}" if m.fee_amount else "—"
                phone   = m.phone or "—"
                status_type, _, _, _ = get_member_payment_status_fast(m, status_cache)

                if m.status == "Active" and not is_expired:
                    active_list.append({"#": len(active_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Type": m.membership_type or "—",
                        "Fee": fee_str, "Expiry": expiry_str or "—",
                        "Remaining": f"{days_left}d" if days_left is not None else "—"})
                if is_expired or status_type == "unpaid":
                    if is_expired:
                        expired_list.append({"#": len(expired_list)+1, "Serial": m.serial_number or "—",
                            "Name": m.full_name, "Phone": phone, "Type": m.membership_type or "—",
                            "Fee": fee_str, "Expired": expiry_str or "—", "Overdue": f"{days_over}d"})
                    if status_type == "unpaid":
                        unpaid_list.append({"#": len(unpaid_list)+1, "Serial": m.serial_number or "—",
                            "Name": m.full_name, "Phone": phone, "Pending Fee": fee_str,
                            "Since": expiry_str or "—", "Days": f"{days_over}d" if days_over else "—",
                            "_fee": m.fee_amount or 0})
                if is_upcoming and not is_expired:
                    upcoming_list.append({"#": len(upcoming_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Type": m.membership_type or "—",
                        "Fee": fee_str, "Expiry": expiry_str or "—", "Days Left": f"{days_left}d"})
                if not expiry_str and m.status == "Active":
                    unpaid_list.append({"#": len(unpaid_list)+1, "Serial": m.serial_number or "—",
                        "Name": m.full_name, "Phone": phone, "Pending Fee": fee_str,
                        "Since": "Not Set", "Days": "—", "_fee": m.fee_amount or 0})

            seen_serials = set()
            unique_unpaid = []
            for item in unpaid_list:
                if item["Serial"] not in seen_serials:
                    seen_serials.add(item["Serial"])
                    unique_unpaid.append(item)
            unpaid_list = unique_unpaid

            st.markdown("---")
            
            # ── Fee Summary Cards ──────────────────────────────────────────
            paid_members = [m for m in members if get_member_payment_status_fast(m, status_cache)[0] == 'paid']
            unpaid_members = [m for m in members if get_member_payment_status_fast(m, status_cache)[0] == 'unpaid']
            upcoming_members = [m for m in members if get_member_payment_status_fast(m, status_cache)[0] == 'upcoming']
            
            paid_total = sum(m.fee_amount or 0 for m in paid_members)
            unpaid_total = sum(m.fee_amount or 0 for m in unpaid_members)
            upcoming_total = sum(m.fee_amount or 0 for m in upcoming_members)
            
            def fee_to_num(fee_str):
                try:
                    if isinstance(fee_str, (int, float)):
                        return float(fee_str)
                    return float(fee_str.replace("PKR ", "").replace(",", "").strip())
                except:
                    return 0
            
            expired_total = sum(fee_to_num(r["Fee"]) for r in expired_list)

            st.markdown("#### 📊 Fee Summary")
            sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
            
            with sum_col1:
                st.markdown(f"""
                <div style="background:#0F172A;border:1px solid #10B981;border-radius:12px;
                            padding:0.8rem;text-align:center;">
                    <div style="color:#10B981;font-size:0.7rem;font-weight:700;">✅ PAID</div>
                    <div style="color:#FFFFFF;font-size:1.3rem;font-weight:700;">
                        {len(paid_members)}
                    </div>
                    <div style="color:#34D399;font-size:0.9rem;font-weight:600;">
                        PKR {paid_total:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with sum_col2:
                st.markdown(f"""
                <div style="background:#0F172A;border:1px solid #EF4444;border-radius:12px;
                            padding:0.8rem;text-align:center;">
                    <div style="color:#EF4444;font-size:0.7rem;font-weight:700;">⏳ UNPAID</div>
                    <div style="color:#FFFFFF;font-size:1.3rem;font-weight:700;">
                        {len(unpaid_members)}
                    </div>
                    <div style="color:#F87171;font-size:0.9rem;font-weight:600;">
                        PKR {unpaid_total:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with sum_col3:
                st.markdown(f"""
                <div style="background:#0F172A;border:1px solid #F59E0B;border-radius:12px;
                            padding:0.8rem;text-align:center;">
                    <div style="color:#F59E0B;font-size:0.7rem;font-weight:700;">🟡 UPCOMING</div>
                    <div style="color:#FFFFFF;font-size:1.3rem;font-weight:700;">
                        {len(upcoming_members)}
                    </div>
                    <div style="color:#FBBF24;font-size:0.9rem;font-weight:600;">
                        PKR {upcoming_total:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with sum_col4:
                st.markdown(f"""
                <div style="background:#0F172A;border:1px solid #8B5CF6;border-radius:12px;
                            padding:0.8rem;text-align:center;">
                    <div style="color:#8B5CF6;font-size:0.7rem;font-weight:700;">🔴 EXPIRED</div>
                    <div style="color:#FFFFFF;font-size:1.3rem;font-weight:700;">
                        {len(expired_list)}
                    </div>
                    <div style="color:#A78BFA;font-size:0.9rem;font-weight:600;">
                        PKR {expired_total:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            tl1, tl2, tl3, tl4 = st.tabs([
                f"💰 Fees ({len(unpaid_list)}) — PKR {unpaid_total:,.0f}",
                f"🟢 Active ({len(active_list)}) — PKR {paid_total:,.0f}",
                f"🟡 Expiring ({len(upcoming_list)}) — PKR {upcoming_total:,.0f}",
                f"🔴 Expired ({len(expired_list)}) — PKR {expired_total:,.0f}",
            ])

            with tl1:
                if unpaid_list:
                    st.markdown(f"**PKR {unpaid_total:,.0f} pending** — {len(unpaid_list)} members")
                    display = [{k: v for k, v in r.items() if k != "_fee"} for r in unpaid_list]
                    st.dataframe(
                        pd.DataFrame(display),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":           st.column_config.NumberColumn("#", width="small"),
                            "Serial":      st.column_config.TextColumn("Serial #", width="small"),
                            "Name":        st.column_config.TextColumn("Name", width="medium"),
                            "Phone":       st.column_config.TextColumn("Phone", width="small"),
                            "Pending Fee": st.column_config.TextColumn("Fee", width="small"),
                            "Since":       st.column_config.TextColumn("Since", width="small"),
                            "Days":        st.column_config.TextColumn("Days", width="small"),
                        },
                    )
                else:
                    st.success("✅ All fees are up to date!")

            with tl2:
                if active_list:
                    st.markdown(f"**PKR {paid_total:,.0f} total active members' fees** — {len(active_list)} members")
                    st.dataframe(
                        pd.DataFrame(active_list),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":         st.column_config.NumberColumn("#", width="small"),
                            "Serial":    st.column_config.TextColumn("Serial #", width="small"),
                            "Name":      st.column_config.TextColumn("Name", width="medium"),
                            "Phone":     st.column_config.TextColumn("Phone", width="small"),
                            "Type":      st.column_config.TextColumn("Type", width="small"),
                            "Fee":       st.column_config.TextColumn("Fee", width="small"),
                            "Expiry":    st.column_config.TextColumn("Expiry", width="small"),
                            "Remaining": st.column_config.TextColumn("Left", width="small"),
                        },
                    )
                else:
                    st.info("No active members.")

            with tl3:
                if upcoming_list:
                    st.markdown(f"**PKR {upcoming_total:,.0f} total expiring members' fees** — {len(upcoming_list)} members")
                    st.dataframe(
                        pd.DataFrame(upcoming_list),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":         st.column_config.NumberColumn("#", width="small"),
                            "Serial":    st.column_config.TextColumn("Serial #", width="small"),
                            "Name":      st.column_config.TextColumn("Name", width="medium"),
                            "Phone":     st.column_config.TextColumn("Phone", width="small"),
                            "Type":      st.column_config.TextColumn("Type", width="small"),
                            "Fee":       st.column_config.TextColumn("Fee", width="small"),
                            "Expiry":    st.column_config.TextColumn("Expiry", width="small"),
                            "Days Left": st.column_config.TextColumn("Days Left", width="small"),
                        },
                    )
                else:
                    st.info("No members expiring soon.")

            with tl4:
                if expired_list:
                    st.markdown(f"**PKR {expired_total:,.0f} total expired members' fees** — {len(expired_list)} members")
                    st.dataframe(
                        pd.DataFrame(expired_list),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#":       st.column_config.NumberColumn("#", width="small"),
                            "Serial":  st.column_config.TextColumn("Serial #", width="small"),
                            "Name":    st.column_config.TextColumn("Name", width="medium"),
                            "Phone":   st.column_config.TextColumn("Phone", width="small"),
                            "Type":    st.column_config.TextColumn("Type", width="small"),
                            "Fee":     st.column_config.TextColumn("Fee", width="small"),
                            "Expired": st.column_config.TextColumn("Expired", width="small"),
                            "Overdue": st.column_config.TextColumn("Overdue", width="small"),
                        },
                    )
                else:
                    st.success("No expired members.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_analytics:
        st.subheader("📊 Member Analytics")
        
        all_members = _cm(gym_id, "All", "")
        
        if not all_members:
            st.info("No members to analyze")
        else:
            render_member_analytics(all_members)
            
            st.markdown("---")
            st.markdown("#### 🆕 Latest 10 Members")
            
            latest_members = []
            for m in all_members:
                if m.join_date:
                    try:
                        join_dt = date.fromisoformat(str(m.join_date))
                        latest_members.append({
                            "Date": join_dt,
                            "Name": m.full_name,
                            "Serial": m.serial_number,
                            "Phone": m.phone or "-",
                            "Type": m.membership_type or "-"
                        })
                    except:
                        pass
            
            if latest_members:
                latest = sorted(latest_members, key=lambda x: x["Date"], reverse=True)[:10]
                df_latest = pd.DataFrame(latest)
                st.dataframe(df_latest, use_container_width=True, hide_index=True)
            else:
                st.info("No join date data available")


# ============================================================
# MEMBER DETAIL - WITH PERMISSIONS (FIXED)
# ============================================================

def _member_detail(m, gyms, role, gym_id=None):
    today = date.today()
    gym_name = next((g.name for g in gyms if g.id == m.gym_id), "—")

    status_cache = None
    if gym_id:
        member_ids = (m.id,)
        status_cache = _get_member_payment_status_bulk(member_ids, gym_id)

    status_type, status_text, bg_color, text_color = get_member_payment_status_fast(m, status_cache)

    days_left = None
    is_expired = False
    days_display = ""

    if m.expiry_date:
        try:
            expiry = date.fromisoformat(str(m.expiry_date))
            days_left = (expiry - today).days
            is_expired = days_left < 0

            if is_expired:
                days_display = f"🔴 {abs(days_left)}d overdue"
            elif days_left == 0:
                days_display = "🟡 Expires today!"
            elif days_left <= 7:
                days_display = f"🟡 {days_left}d left"
            else:
                days_display = f"✅ {days_left}d remaining"
        except Exception:
            days_display = "⚠️ Invalid date"
    else:
        days_display = "❌ No expiry set"

    status_emoji = {
        "Active": "🟢", 
        "Inactive": "🔴",
        "Suspended": "🟡", 
        "Frozen": "🔵"
    }.get(m.status, "⚪")

    birthday_today = False
    if m.dob:
        try:
            dob = date.fromisoformat(str(m.dob))
            birthday_today = (dob.month == today.month and dob.day == today.day)
        except Exception:
            pass

    st.markdown("---")

    # ── Photo + Info Row ────────────────────────────────────────────────────
    col_photo, col_info = st.columns([1, 3])

    with col_photo:
        show_photo(m.photo_path, w=150)

    with col_info:
        birthday_banner = " 🎂 Birthday Today!" if birthday_today else ""

        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:0.8rem;flex-wrap:wrap;">
                <h3 style="margin:0;color:#F1F5F9;">{status_emoji} {m.full_name}{birthday_banner}</h3>
                <span style="background:{bg_color};color:{text_color};
                            padding:4px 14px;border-radius:9999px;
                            font-size:0.75rem;font-weight:700;">
                    {status_text}
                </span>
                <span style="background:#1E293B;color:#94A3B8;
                            padding:4px 12px;border-radius:9999px;
                            font-size:0.7rem;font-weight:600;
                            border:1px solid #334155;">
                    {days_display}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<p style='margin:2px 0;color:#A78BFA;font-weight:600'>🆔 {m.serial_number} &nbsp;·&nbsp; "
            f"<span style='color:#64748B'>📍 {gym_name}</span></p>",
            unsafe_allow_html=True,
        )

        if is_expired:
            st.error(f"🚨 Membership expired {abs(days_left)} days ago")
        elif days_left is not None and days_left <= 7 and days_left >= 0:
            st.warning(f"⏳ Expires in {days_left} day(s) — {m.expiry_date}")
        elif days_left is not None and days_left > 7:
            st.success(f"✅ Active — {days_left} days remaining (expires {m.expiry_date})")
        elif not m.expiry_date:
            st.info("📅 No expiry date set")

        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown("**📋 Membership**")
            st.write(f"Type: **{m.membership_type or '—'}**")
            st.write(f"Fee: **PKR {m.fee_amount:,.0f}**")
            st.write(f"Joined: **{m.join_date}**")
        with d2:
            st.markdown("**📞 Contact**")
            st.write(f"Phone: **{m.phone or '—'}**")
            st.write(f"Email: **{m.email or '—'}**")
            st.write(f"Gender: **{m.gender or '—'}**")
        with d3:
            st.markdown("**📅 Info**")
            st.write(f"Expiry: **{m.expiry_date or '—'}**")
            st.write(f"DOB: **{m.dob or '—'}**")
            st.write(f"Status: **{m.status}**")

        if m.notes:
            st.info(f"📝 {m.notes}")

    # ── Quick Actions ──────────────────────────────────────────────────────
    st.markdown("#### ⚡ Quick Actions")
    
    qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)

    with qa1:
        if m.phone:
            clean_phone = m.phone.replace(" ", "").replace("-", "").replace("+", "")
            wa_url = f"https://wa.me/{clean_phone}"
            st.link_button("📱 WhatsApp", wa_url, use_container_width=True)
        else:
            st.button("📱 WhatsApp", disabled=True, use_container_width=True, key=f"wa_dis_{m.id}")

    with qa2:
        if st.button("📋 Serial #", use_container_width=True, key=f"copy_{m.id}"):
            st.code(m.serial_number)

    with qa3:
        renew_key = f"renew_active_{m.id}"
        if st.button("📅 Renew", use_container_width=True, key=f"renew_btn_{m.id}"):
            st.session_state[renew_key] = not st.session_state.get(renew_key, False)
            st.rerun()

    with qa4:
        qs_key = f"qs_toggle_{m.id}"
        if st.button("🔄 Change Status", use_container_width=True, key=f"qs_btn_{m.id}"):
            st.session_state[qs_key] = not st.session_state.get(qs_key, False)
            st.rerun()

    with qa5:
        if st.button("📊 Progress", use_container_width=True, key=f"progress_{m.id}"):
            st.session_state["page"] = "Progress Tracker"
            st.rerun()
    
    with qa6:
        fee_key = f"show_quick_fee_{m.id}"
        if st.button("💰 Collect Fee", use_container_width=True, key=f"fee_btn_{m.id}"):
            st.session_state[fee_key] = not st.session_state.get(fee_key, False)
            st.rerun()

    # ── Quick Fee Collection ───────────────────────────────────────────────
    fee_key = f"show_quick_fee_{m.id}"
    if st.session_state.get(fee_key, False):
        with st.container():
            # ── 🔥 FIX: Pass gym_id, if None use member's gym_id ────────────
            effective_gym_id = gym_id if gym_id is not None else m.gym_id
            render_quick_fee_collection(m, effective_gym_id)

    # ── Quick Status Change ────────────────────────────────────────────────
    qs_key = f"qs_toggle_{m.id}"
    if st.session_state.get(qs_key, False):
        with st.container():
            st.markdown("**🔄 Change Status**")
            new_status_cols = st.columns(4)
            for idx, s in enumerate(STATUSES):
                with new_status_cols[idx]:
                    is_cur = m.status == s
                    if st.button(
                        f"{'✅ ' if is_cur else ''}{s}",
                        key=f"qs_{m.id}_{s}",
                        type="primary" if is_cur else "secondary",
                        use_container_width=True,
                    ):
                        db.update_member(m.id, status=s)
                        st.session_state[qs_key] = False
                        _cm.clear()
                        st.success(f"Status updated to **{s}**")
                        st.rerun()

    # ── Renew Panel ────────────────────────────────────────────────────────
    renew_key = f"renew_active_{m.id}"
    if st.session_state.get(renew_key, False):
        with st.container():
            st.markdown("**📅 Renew Membership**")
            st.info(f"Current expiry: **{m.expiry_date or 'Not set'}**")
            try:
                base = date.fromisoformat(str(m.expiry_date)) if m.expiry_date else today
            except Exception:
                base = today

            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                if st.button("1 Month", use_container_width=True, key=f"ren1_{m.id}"):
                    new_exp = base + timedelta(days=30)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()
            with rc2:
                if st.button("3 Months", use_container_width=True, key=f"ren3_{m.id}"):
                    new_exp = base + timedelta(days=90)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()
            with rc3:
                if st.button("6 Months", use_container_width=True, key=f"ren6_{m.id}"):
                    new_exp = base + timedelta(days=180)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()
            with rc4:
                if st.button("1 Year", use_container_width=True, key=f"ren12_{m.id}"):
                    new_exp = base + timedelta(days=365)
                    db.update_member(m.id, expiry_date=str(new_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {new_exp}")
                    st.rerun()

            custom_exp = st.date_input("Or pick custom date",
                                       value=base + timedelta(days=30),
                                       key=f"renew_date_{m.id}")
            rcc1, rcc2 = st.columns(2)
            with rcc1:
                if st.button("✅ Confirm Custom", key=f"renew_confirm_{m.id}", type="primary"):
                    db.update_member(m.id, expiry_date=str(custom_exp), status="Active")
                    st.session_state[renew_key] = False
                    _cm.clear()
                    st.success(f"✅ Renewed until {custom_exp}")
                    st.rerun()
            with rcc2:
                if st.button("❌ Cancel", key=f"renew_cancel_{m.id}"):
                    st.session_state[renew_key] = False
                    st.rerun()

    # ── ID Card & QR ──────────────────────────────────────────────────────
    with st.expander("🪪 ID Card & QR Code"):
        gyms_all = db.get_all_gyms()
        gname = next((g.name for g in gyms_all if g.id == m.gym_id), "GymPro")
        try:
            card_png = id_card.generate_id_card_png(m, gname)
            st.image(card_png, caption="Member ID Card Preview", use_container_width=True)
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("⬇️ Download PNG", data=card_png,
                                   file_name=f"{m.serial_number}_id_card.png", mime="image/png",
                                   key=f"card_png_{m.id}", use_container_width=True)
            with dl2:
                try:
                    card_pdf = id_card.generate_id_card_pdf(m, gname)
                    st.download_button("⬇️ Download PDF", data=card_pdf,
                                       file_name=f"{m.serial_number}_id_card.pdf",
                                       mime="application/pdf", key=f"card_pdf_{m.id}",
                                       use_container_width=True)
                except Exception as e:
                    st.warning(f"PDF: {e}")
            with dl3:
                qr_png = member_qr_png(m.serial_number, box_size=8, border=2)
                st.download_button("⬇️ QR Code", data=qr_png,
                                   file_name=f"{m.serial_number}_qr.png", mime="image/png",
                                   key=f"qr_dl_{m.id}", use_container_width=True)
        except Exception as e:
            st.error(f"ID card error: {e}")
            qr_png = member_qr_png(m.serial_number, box_size=8, border=2)
            st.image(qr_png, width=200, caption=m.serial_number)
            st.download_button("⬇️ QR PNG", data=qr_png,
                               file_name=f"{m.serial_number}_qr.png", mime="image/png",
                               key=f"qr_fb_{m.id}")

    # ── Edit & Delete ─────────────────────────────────────────────────────
    if role in ("admin", "staff"):
        with st.expander("✏️ Edit Member Details", expanded=False):
            _edit_form(m, gyms)

        # ⭐ DELETE - ONLY FOR ADMIN/OWNER
        if role == "admin" or role == "owner":
            st.divider()
            col_del1, _ = st.columns([1, 5])
            with col_del1:
                if st.button("🗑️ Delete Member", key=f"del_m_{m.id}", type="primary"):
                    st.session_state[f"confirm_del_m_{m.id}"] = True
            if st.session_state.get(f"confirm_del_m_{m.id}"):
                st.warning("⚠️ Permanently delete this member? Cannot be undone!")
                cd1, cd2 = st.columns(2)
                if cd1.button("✅ Yes, Delete", key=f"cdy_{m.id}", type="primary"):
                    if m.photo_path:
                        object_store.delete_photo(m.photo_path)
                    db.delete_member(m.id)
                    st.success("✅ Member deleted.")
                    st.session_state.pop(f"confirm_del_m_{m.id}", None)
                    _cm.clear()
                    st.rerun()
                if cd2.button("❌ Cancel", key=f"cdn_{m.id}"):
                    st.session_state.pop(f"confirm_del_m_{m.id}", None)
                    st.rerun()
        else:
            # ⛔ Staff ke liye delete button nahi dikhana
            st.info("🔒 Delete member option is only available for Admin")


# ============================================================
# REGISTER FORM
# ============================================================

def _register_form(gyms, gym_id, role):
    st.subheader("➕ Register New Member")
    st.caption("Fill in the details below to add a new member")

    gym_opts = {g.name: g.id for g in gyms}
    default_name = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)

    with st.form("reg_member_form", clear_on_submit=True):
        st.markdown("#### 📋 Personal Information")

        c1, c2 = st.columns(2)
        with c1:
            if role == "staff":
                gym_sel = default_name
                st.text_input("🏋️ Gym", value=default_name, disabled=True, key="reg_gym_display")
            else:
                gym_sel = st.selectbox("🏋️ Gym *", list(gym_opts.keys()),
                                       index=list(gym_opts.keys()).index(default_name),
                                       key="reg_gym_sel")
            full_name = st.text_input("👤 Full Name *", key="reg_full_name", placeholder="e.g., Muhammad Ali")
            phone = st.text_input("📞 Phone", placeholder="+92 300-0000000", key="reg_phone")
            email = st.text_input("📧 Email", key="reg_email", placeholder="example@email.com")
            gender = st.selectbox("⚥ Gender", GENDERS, key="reg_gender")
            dob = st.date_input("🎂 Date of Birth", value=None,
                                min_value=date(1920, 1, 1), max_value=date.today(),
                                key="reg_dob")
        with c2:
            mem_type = st.selectbox("📋 Membership Type *", db.MEMBERSHIP_TYPES, key="reg_mem_type")
            fee_amount = st.number_input("💰 Monthly Fee (PKR)", min_value=0.0, step=5.0, format="%.2f", key="reg_fee")
            join_date = st.date_input("📅 Join Date *", value=date.today(), key="reg_join")
            expiry_date = st.date_input("📅 Expiry Date", value=date.today() + timedelta(days=30), key="reg_expiry")
            status = st.selectbox("📊 Status", STATUSES, key="reg_status")
            notes = st.text_area("📝 Notes", height=60, key="reg_notes", placeholder="Any remarks about this member...")
            photo = st.file_uploader("📷 Member Photo", type=["jpg", "jpeg", "png", "webp"],
                                     key="reg_photo")

        if photo:
            st.image(photo, width=120, caption="📸 Preview")

        st.markdown("---")
        if st.form_submit_button("✅ Register Member", type="primary", use_container_width=True):
            if not full_name.strip():
                st.error("❌ Full name is required!")
            else:
                photo_path = save_photo(photo) if photo else None
                ok, msg, serial = db.add_member(
                    gym_id=gym_opts[gym_sel],
                    full_name=full_name, phone=phone, email=email,
                    gender=gender, dob=str(dob) if dob else "",
                    membership_type=mem_type, fee_amount=fee_amount,
                    join_date=str(join_date),
                    expiry_date=str(expiry_date) if expiry_date else None,
                    photo_path=photo_path, status=status, notes=notes,
                )
                if ok:
                    if photo_path and serial:
                        new_key = f"member_photos/{serial}.jpg"
                        if object_store.rename_photo(photo_path, new_key):
                            member = db.get_member_by_serial(serial)
                            if member and not photo_path.startswith("http"):
                                db.update_member_photo_path(member.id, new_key)
                    st.success(f"🎉 {msg}")
                    st.balloons()
                else:
                    st.error(f"❌ {msg}")


# ============================================================
# EDIT FORM
# ============================================================

def _edit_form(m, gyms):
    gym_opts = {g.name: g.id for g in gyms}
    cur_gym = next((g.name for g in gyms if g.id == m.gym_id), gyms[0].name)

    with st.form(f"edit_member_form_{m.id}"):
        st.markdown("#### ✏️ Edit Member Details")

        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("👤 Full Name *", value=m.full_name, key=f"ef_name_{m.id}")
            phone = st.text_input("📞 Phone", value=m.phone or "", key=f"ef_phone_{m.id}")
            email = st.text_input("📧 Email", value=m.email or "", key=f"ef_email_{m.id}")
            gender_i = GENDERS.index(m.gender) if m.gender in GENDERS else 0
            gender = st.selectbox("⚥ Gender", GENDERS, index=gender_i, key=f"ef_gender_{m.id}")
            dob_val = None
            if m.dob:
                try:
                    dob_val = date.fromisoformat(m.dob)
                except Exception:
                    pass
            dob = st.date_input("🎂 DOB", value=dob_val, min_value=date(1920, 1, 1),
                                max_value=date.today(), key=f"ef_dob_{m.id}")
        with c2:
            mi = db.MEMBERSHIP_TYPES.index(m.membership_type) if m.membership_type in db.MEMBERSHIP_TYPES else 0
            mem_type = st.selectbox("📋 Membership Type *", db.MEMBERSHIP_TYPES, index=mi, key=f"ef_mtype_{m.id}")
            fee_amount = st.number_input("💰 Fee (PKR)", value=float(m.fee_amount or 0),
                                         min_value=0.0, step=5.0, key=f"ef_fee_{m.id}")
            join_date = st.date_input("📅 Join Date *", value=date.fromisoformat(m.join_date),
                                      key=f"ef_join_{m.id}")
            exp_val = date.fromisoformat(m.expiry_date) if m.expiry_date else date.today() + timedelta(days=30)
            expiry_date = st.date_input("📅 Expiry Date", value=exp_val, key=f"ef_expiry_{m.id}")
            si = STATUSES.index(m.status) if m.status in STATUSES else 0
            status = st.selectbox("📊 Status", STATUSES, index=si, key=f"ef_status_{m.id}")
            notes = st.text_area("📝 Notes", value=m.notes or "", height=60, key=f"ef_notes_{m.id}")
            photo = st.file_uploader("📷 Replace Photo", type=["jpg", "jpeg", "png", "webp"],
                                     key=f"ef_photo_{m.id}")

        if photo:
            st.image(photo, width=100, caption="📸 New Photo Preview")

        st.markdown("---")
        col_s, col_c = st.columns(2)
        save = col_s.form_submit_button("💾 Save Changes", type="primary")
        cancel = col_c.form_submit_button("❌ Cancel")

        if cancel:
            st.rerun()
        if save:
            photo_path = m.photo_path
            if photo:
                photo_bytes = photo.getbuffer()
                uploaded_key = object_store.upload_photo(bytes(photo_bytes), photo.name, serial=m.serial_number)
                if m.photo_path and m.photo_path != uploaded_key:
                    try:
                        object_store.delete_photo(m.photo_path)
                    except Exception:
                        pass
                photo_path = uploaded_key
                object_store.get_photo_bytes.clear()
                st.session_state.photo_cache = {}
            ok, msg = db.update_member(
                m.id, full_name=full_name, phone=phone, email=email,
                gender=gender, dob=str(dob) if dob else "",
                membership_type=mem_type, fee_amount=fee_amount,
                join_date=str(join_date), expiry_date=str(expiry_date),
                photo_path=photo_path, status=status, notes=notes,
            )
            if ok:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")