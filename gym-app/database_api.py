# database_api.py — Safe API summary for AI Coder
# Ye file database.py ka SAFE summary hai — actual DB code nahi.
# AI Coder V12 isse padh kar jaanta hai ke functions kya return karte hain.

"""
DATABASE API REFERENCE
======================
Ye GymPro app ke database.py se export hone wale public functions hain.
AI Coder ko yeh jaanna zaroori hai taake sahi code likhe.

MODELS (SQLAlchemy):
- Gym: id, name, address, phone, email, logo_path, description, amenities,
       rules, mon_fri_start, mon_fri_end, sat_start, sat_end, sun_start,
       sun_end, currency, timezone, ...
- User: id, username, full_name, password_hash, role, gym_id, is_active
- Member: id, gym_id, serial_number, full_name, phone, email, gender, dob,
         photo_path, membership_type, fee_amount, join_date, expiry_date,
         status, notes, face_encoding, whatsapp_sent
- Attendance: id, member_id, gym_id, check_date, status, marked_by
- FeeRecord: id, member_id, gym_id, amount, payment_method, payment_date,
            period_start, period_end, receipt_number, collected_by, notes
- DailyExpense: id, gym_id, amount, category, description, expense_date
- BodyMeasurement: id, member_id, recorded_date, weight_kg, chest_cm, ...
- StockItem: id, gym_id, item_name, category, purchase_price, sale_price, quantity
- Complaint: id, gym_id, member_id, subject, status, priority
- GymPhoto: id, gym_id, path, is_primary
- MembershipPlan: id, gym_id, name, price, duration_days, features
- Exercise, WorkoutPlan, WorkoutSession — AI Voice Trainer

FUNCTIONS (IMPORTANT — return types):
=====================================

# ── Gyms ──
get_all_gyms() -> List[Gym]
get_gym(gym_id) -> Optional[Gym]
add_gym(name, address="", phone="", email="") -> (bool, str)
update_gym(gym_id, name, address="", phone="", email="") -> (bool, str)

# ── Members ──
get_members(gym_id=None, status=None, search=None) -> List[Member]
get_member(member_id) -> Optional[Member]
get_member_by_serial(serial, gym_id=None) -> Optional[Member]
add_member(gym_id, full_name, phone, email, gender, dob,
           membership_type, fee_amount, join_date, expiry_date,
           photo_path, status, notes) -> (bool, str, serial_or_None)
update_member(member_id, **kwargs) -> (bool, str)
delete_member(member_id) -> (bool, str)
get_member_count(gym_id=None) -> int
get_active_member_count(gym_id=None) -> int

# Member model fields commonly accessed:
#   m.id, m.full_name, m.phone, m.email, m.gender, m.dob (str "YYYY-MM-DD"),
#   m.serial_number, m.membership_type, m.fee_amount (float),
#   m.join_date (str), m.expiry_date (str or None), m.status,
#   m.photo_path, m.gym_id, m.notes

# ── Attendance ──
mark_attendance(member_id, gym_id, check_date, status, marked_by) -> (bool, str)
get_attendance(gym_id=None, check_date=None) -> List[Attendance]
get_recent_scans(gym_id=None, limit=10, today_only=True) -> List[dict]
    # Returns: [{"time": "HH:MM:SS", "name": str, "serial": str,
    #            "photo": path, "gym": str, "marked_by": str}]
get_attendance_by_hour(gym_id=None) -> Dict[int, int]  # {hour: count}
get_attendance_trend(gym_id=None, days=30) -> List[dict]
    # Returns: [{"date": "DD Mon", "present": int, "absent": int, "late": int}]
get_member_attendance_rate(member_id, days=30) -> float  # percentage
get_member_streak(member_id) -> int
get_attendance_leaderboard(gym_id=None, limit=10) -> List[dict]
    # Returns: [{"member": Member_obj, "count": int, "streak": int}]
    # NOTE: member is a Member OBJECT, not dict. Access via entry["member"].full_name
get_late_members_summary(gym_id=None, days=30) -> List[dict]
    # Returns: [{"member": Member_obj, "late_count": int}]
get_all_member_last_visits(gym_id=None) -> Dict[int, str]  # {member_id: date_str}
get_active_members(gym_id) -> List[Member]  # NOT present today

# ── Fee Records ──
add_fee_record(member_id, gym_id, amount, payment_method, payment_date,
               period_start, period_end, collected_by, notes="") -> (bool, str)
get_fee_records(gym_id=None, member_id=None, date_from=None, date_to=None,
                limit=None) -> List[FeeRecord]
get_todays_fees(gym_id) -> List[float]  # list of amounts
get_daily_fee_summary(gym_id=None, target_date=None) -> Tuple[float, int, List[FeeRecord]]
    # Returns: (total_amount, count, records)
get_monthly_revenue(gym_id=None, year=None) -> Dict[int, float]
    # Returns: {1: 15000.0, 2: 23000.0, ...} month_number -> amount
    # NOTE: returns DICT, not list
mark_fee_whatsapp_sent(fee_id) -> bool
get_fee_records_created_today(gym_id=None) -> List[FeeRecord]

# ── Expenses ──
add_expense(gym_id, amount, category, description, expense_date, staff_name) -> (bool, str)
get_expenses(gym_id=None, category=None, date_from=None, date_to=None) -> List[DailyExpense]
get_expenses_by_category(gym_id=None) -> List[dict]
    # Returns: [{"category": str, "total": float}]

# ── Expiring / Absent / Birthday ──
get_expiring_members(days=5, gym_id=None) -> List[Tuple[Member, int]]
    # NOTE: Returns list of TUPLES: [(Member_obj, days_left_int), ...]
    # Access: for m, days_left in get_expiring_members(): m.full_name, days_left
get_absent_members(days=3, gym_id=None) -> List[Member]
get_birthday_members(days_ahead=7, gym_id=None) -> List[Tuple[Member, int]]
    # NOTE: Returns list of TUPLES: [(Member_obj, days_until_birthday), ...]
    # Access: for m, days in get_birthday_members(): m.full_name, m.dob

# ── Stats ──
get_stats(gym_id=None) -> Dict:
    # Returns: {"total_members": int, "active_members": int,
    #           "total_revenue": float, "total_expenses": float,
    #           "month_revenue": float, "month_expenses": float,
    #           "net_profit": float, "inventory_revenue": float}

# ── Activity Log ──
log_activity(user, action, details="", gym_id=None, role="", amount=None, record_ref="")
get_activity_logs(gym_id=None, limit=500, date_from=None, date_to=None,
                  user=None, action=None) -> List[ActivityLog]

# ── Users ──
get_user_by_username(username) -> Optional[User]
get_all_users() -> List[User]
add_user(username, full_name, password, role, gym_id=None) -> (bool, str)

# ── Body Measurements ──
add_body_measurement(member_id, recorded_date, weight_kg, chest_cm=None, ...) -> (bool, str)
get_body_measurements(member_id) -> List[BodyMeasurement]

# ── Stock ──
get_stock_items(gym_id=None, low_stock_only=False) -> List[StockItem]
add_stock_item(gym_id, item_name, category, purchase_price, sale_price,
               quantity, min_quantity=5) -> (bool, str)
sell_stock_item(stock_item_id, gym_id, member_id, quantity_sold,
                sale_price, sold_by, sale_date) -> (bool, str)

# ── Complaints ──
add_complaint(gym_id, subject, description, priority, submitted_by, member_id=None) -> (bool, str)
get_complaints(gym_id=None, status=None) -> List[Complaint]

# ── Audit ──
add_audit_entry(...) -> (bool, str)
get_audit_entries(...) -> List[AuditEntry]

# ── Staff ──
get_staff_targets(gym_id=None, staff_username=None, target_month=None) -> List[StaffTarget]
get_staff_progress(staff_username, target_month=None) -> Dict
get_staff_timing(staff_username) -> Optional[dict]
get_all_staff_timings(gym_id) -> List[StaffTiming]
get_staff_attendance_summary(gym_id=None, date_range=30) -> List[dict]
get_my_attendance_summary(staff_username) -> Dict

# ── Gym Plans & Photos ──
get_gym_plans(gym_id) -> List[MembershipPlan]
add_membership_plan(gym_id, name, price, duration_days, features) -> (bool, str)
get_gym_photos(gym_id) -> List[GymPhoto]
save_gym_photo(gym_id, filepath) -> (bool, str)

# ── Announcements ──
get_active_announcement(gym_id=None) -> Optional[Announcement]
add_announcement(gym_id, message, created_by, expires_at=None) -> (bool, str)
get_all_announcements(gym_id=None) -> List[Announcement]

# ── Settings ──
get_setting(key, default="") -> str
set_setting(key, value) -> None

CONSTANTS:
PAYMENT_METHODS = ["Cash", "Bank Transfer", "Card", "Online", "Cheque", "Other"]
MEMBERSHIP_TYPES = ["Monthly", "Quarterly", "Semi-Annual", "Annual", "Day Pass", "Student", "VIP"]
EXPENSE_CATEGORIES = ["Equipment", "Maintenance", "Utilities", "Salaries", ...]
STOCK_CATEGORIES = [...]
COMPLAINT_PRIORITIES = ["Low", "Medium", "High", "Urgent"]
COMPLAINT_STATUSES = ["Open", "In Progress", "Resolved"]

DB MODE: {IS_POSTGRES ? "PostgreSQL (Online)" : "SQLite (Offline)"}
"""

# Ye file sirf documentation hai — koi actual code nahi.
# AI Coder V12 isse padh kar sahi code likhega.
