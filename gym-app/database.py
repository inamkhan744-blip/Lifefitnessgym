# database.py - COMPLETE FIXED VERSION
# With proper serial number handling, no duplicates, and all functions working

import os
import hashlib
import uuid
import sqlite3
from datetime import datetime, date, timedelta
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date,
    DateTime, Boolean, Text, ForeignKey, func, text as sa_text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from typing import Optional, List, Dict, Any, Tuple
# ── Engine Path Configurations ──────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == "gym-app":
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "gym-app", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not IS_POSTGRES:
    import sqlite3
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir) if os.path.basename(current_dir) == "gym-app" else current_dir
    
    db_path = os.path.join(BASE_DIR, "gym-app", "gym_pro_v2.db")
    sql_backup_path = os.path.join(root_dir, "backup.sql")
    
    if os.path.exists(sql_backup_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM members;")
            row_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            row_count = 0
            
        conn.close()

DB_PATH = os.path.join(BASE_DIR, "gym_pro_v3.db")
DB_MODE = "offline"

def _make_sqlite_engine():
    eng = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
    )
    @event.listens_for(eng, "connect")
    def _set_pragma(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
    return eng

if IS_POSTGRES:
    _pg_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    if "sslmode" not in _pg_url:
        _sep = "&" if "?" in _pg_url else "?"
        _pg_url += f"{_sep}sslmode=require"
    engine = create_engine(
        _pg_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 15},
    )
    try:
        with engine.connect() as _c:
            _c.execute(sa_text("SELECT 1"))
        DB_MODE = "online"
    except Exception:
        engine.dispose()
        engine = _make_sqlite_engine()
        IS_POSTGRES = False
        DB_MODE = "offline"
else:
    engine = _make_sqlite_engine()
    DB_MODE = "offline"

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

def get_db() -> Session:
    return SessionLocal()

# ============================================
# GYM PHOTO MODEL
# ============================================

class GymPhoto(Base):
    __tablename__ = "gym_photos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(500), nullable=False)
    is_primary = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.now)
    
    gym = relationship("Gym", back_populates="gym_photos")

# ============================================
# MEMBERSHIP PLAN MODEL
# ============================================

class MembershipPlan(Base):
    __tablename__ = "membership_plans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    duration_days = Column(Integer, nullable=False)
    features = Column(Text)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    
    gym = relationship("Gym", back_populates="membership_plans")

# ── Models ─────────────────────────────────────────────────────────────────────

class Gym(Base):
    __tablename__ = "gyms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True)
    address = Column(String(255))
    phone = Column(String(30))
    email = Column(String(120))
    created_at = Column(DateTime, default=datetime.now)
    
    # 🔥 NEW: Serial number tracking per gym
    next_serial = Column(Integer, default=1)
    
    # Other fields
    description = Column(Text)
    amenities = Column(Text)
    rules = Column(Text)
    status = Column(String(20), default="active")
    
    # Working hours
    mon_fri_start = Column(String(10), default="06:00")
    mon_fri_end = Column(String(10), default="22:00")
    sat_start = Column(String(10), default="08:00")
    sat_end = Column(String(10), default="20:00")
    sun_start = Column(String(10), default="08:00")
    sun_end = Column(String(10), default="18:00")
    holiday_mode = Column(Integer, default=0)
    
    # Social links
    facebook = Column(String(255))
    instagram = Column(String(255))
    youtube = Column(String(255))
    twitter = Column(String(255))
    linkedin = Column(String(255))
    website = Column(String(255))
    
    # Bank details
    bank_name = Column(String(255))
    account_title = Column(String(255))
    account_number = Column(String(100))
    iban = Column(String(100))
    
    # Other settings
    expense_categories = Column(Text)
    logo_path = Column(Text)
    max_members = Column(Integer, default=0)
    checkin_required = Column(Integer, default=0)
    reminder_days = Column(Integer, default=7)
    allow_online_payments = Column(Integer, default=0)
    currency = Column(String(10), default="PKR")
    timezone = Column(String(50), default="Asia/Karachi")

    members = relationship("Member", back_populates="gym", cascade="all, delete-orphan")
    users = relationship("User", back_populates="gym")
    expenses = relationship("DailyExpense", back_populates="gym", cascade="all, delete-orphan")
    fee_records = relationship("FeeRecord", back_populates="gym", cascade="all, delete-orphan")
    audit_entries = relationship("AuditEntry", back_populates="gym", cascade="all, delete-orphan")
    stock_items = relationship("StockItem", back_populates="gym", cascade="all, delete-orphan")
    stock_sales = relationship("StockSale", back_populates="gym", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="gym", cascade="all, delete-orphan")
    receipt_logs = relationship("ReceiptLog", back_populates="gym", cascade="all, delete-orphan")
    staff_targets = relationship("StaffTarget", back_populates="gym", cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="gym", cascade="all, delete-orphan")
    activity_logs  = relationship("ActivityLog",  back_populates="gym", cascade="all, delete-orphan")
    shift_sessions = relationship("ShiftSession", back_populates="gym", cascade="all, delete-orphan")
    gym_photos = relationship("GymPhoto", back_populates="gym", cascade="all, delete-orphan")
    membership_plans = relationship("MembershipPlan", back_populates="gym", cascade="all, delete-orphan")
    staff_timings = relationship("StaffTiming", back_populates="gym", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(60), nullable=False, unique=True)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="users")

# ============================================
# 🔥 MEMBER MODEL - UPDATED WITH created_by_staff
# ============================================

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    serial_number = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    phone = Column(String(30))
    email = Column(String(120))
    gender = Column(String(20))
    dob = Column(String(15))
    photo_path = Column(String(255))
    membership_type = Column(String(40), nullable=False)
    fee_amount = Column(Float, default=0.0)
    join_date = Column(String(15), nullable=False)
    expiry_date = Column(String(15))
    status = Column(String(20), default="Active")
    notes = Column(Text)
    face_encoding = Column(Text, nullable=True)
    whatsapp_sent = Column(Boolean, default=False, nullable=False)
    created_by_staff = Column(String(60), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="members")
    attendances = relationship("Attendance", back_populates="member", cascade="all, delete-orphan")
    fee_records = relationship("FeeRecord", back_populates="member", cascade="all, delete-orphan")
    body_measurements = relationship("BodyMeasurement", back_populates="member", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="member")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    check_date = Column(String(15), nullable=False)
    status = Column(String(20), default="Present")
    marked_by = Column(String(60))
    created_at = Column(DateTime, default=datetime.now)

    member = relationship("Member", back_populates="attendances")

class FeeRecord(Base):
    __tablename__ = "fee_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(40), default="Cash")
    payment_date = Column(String(15), nullable=False)
    period_start = Column(String(15))
    period_end = Column(String(15))
    receipt_number = Column(String(30))
    collected_by = Column(String(60))
    notes = Column(Text)
    whatsapp_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    member = relationship("Member", back_populates="fee_records")
    gym = relationship("Gym", back_populates="fee_records")

class DailyExpense(Base):
    __tablename__ = "daily_expenses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(60), nullable=False)
    description = Column(Text)
    expense_date = Column(String(15), nullable=False)
    staff_name = Column(String(60))
    created_at = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="expenses")

class AuditEntry(Base):
    __tablename__ = "audit_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    entry_type = Column(String(20), nullable=False)
    reference_id = Column(Integer, nullable=True)
    expected_amount = Column(Float)
    actual_amount = Column(Float)
    description = Column(Text)
    entry_date = Column(String(15), nullable=False)
    verified_by = Column(String(60))
    status = Column(String(20), default="Pending")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="audit_entries")

class BodyMeasurement(Base):
    __tablename__ = "body_measurements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    recorded_date = Column(String(15), nullable=False)
    weight_kg = Column(Float, default=0.0)
    chest_cm = Column(Float)
    waist_cm = Column(Float)
    hips_cm = Column(Float)
    bicep_cm = Column(Float)
    body_fat_pct = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    member = relationship("Member", back_populates="body_measurements")

class StockItem(Base):
    __tablename__ = "stock_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String(120), nullable=False)
    category = Column(String(60), default="Supplement")
    purchase_price = Column(Float, default=0.0)
    sale_price = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="stock_items")
    sales = relationship("StockSale", back_populates="stock_item", cascade="all, delete-orphan")

class StockSale(Base):
    __tablename__ = "stock_sales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_item_id = Column(Integer, ForeignKey("stock_items.id", ondelete="CASCADE"), nullable=False)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    quantity_sold = Column(Integer, default=1)
    sale_price = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    sold_by = Column(String(60))
    sale_date = Column(String(15), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    stock_item = relationship("StockItem", back_populates="sales")
    gym = relationship("Gym", back_populates="stock_sales")

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="Open")   
    priority = Column(String(20), default="Medium")  
    submitted_by = Column(String(60))
    resolved_by = Column(String(60))
    wa_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime)

    gym = relationship("Gym", back_populates="complaints")
    member = relationship("Member", back_populates="complaints")

class ReceiptLog(Base):
    __tablename__ = "receipt_logs"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    fee_record_id  = Column(Integer, ForeignKey("fee_records.id", ondelete="SET NULL"), nullable=True)
    gym_id         = Column(Integer, ForeignKey("gyms.id", ondelete="SET NULL"), nullable=True)
    member_name    = Column(String(120), nullable=False)
    receipt_number = Column(String(40),  nullable=False)
    amount         = Column(Float,       nullable=False)
    collected_by   = Column(String(60))
    pay_date       = Column(String(15),  nullable=False)
    pay_time       = Column(String(10),  nullable=False)
    print_issued   = Column(Boolean, default=False, nullable=False)
    created_at     = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="receipt_logs")

class UnknownCapture(Base):
    __tablename__ = "unknown_captures"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    gym_id       = Column(Integer, nullable=False)
    capture_key  = Column(String(300), nullable=False)
    capture_type = Column(String(20), default="unknown")
    member_id    = Column(Integer, nullable=True)
    member_name  = Column(String(120), nullable=True)
    captured_at  = Column(DateTime, default=datetime.now)
    notes        = Column(Text, nullable=True)

class AppSetting(Base):
    __tablename__ = "app_settings"
    key   = Column(String(120), primary_key=True)
    value = Column(Text, nullable=True)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    gym_id     = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=True)
    user       = Column(String(80), nullable=False)
    role       = Column(String(20))
    action     = Column(String(60), nullable=False)
    details    = Column(Text)
    amount     = Column(Float, nullable=True)
    record_ref = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="activity_logs")

class ShiftSession(Base):
    __tablename__ = "shift_sessions"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    gym_id         = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    staff_user     = Column(String(80), nullable=False)
    role           = Column(String(20))
    opened_at      = Column(DateTime, default=datetime.now)
    closed_at      = Column(DateTime, nullable=True)
    opening_cash   = Column(Float, default=0.0)
    expected_cash  = Column(Float, nullable=True)
    closing_cash   = Column(Float, nullable=True)
    discrepancy    = Column(Float, nullable=True)
    status         = Column(String(20), default="open")

    gym = relationship("Gym", back_populates="shift_sessions")

# ── Constants ──────────────────────────────────────────────────────────────────

PAYMENT_METHODS   = ["Cash", "Bank Transfer", "Card", "Online", "Cheque", "Other"]
MEMBERSHIP_TYPES  = ["Monthly", "Quarterly", "Semi-Annual", "Annual", "Day Pass", "Student", "VIP"]
EXPENSE_CATEGORIES = ["Equipment", "Maintenance", "Utilities", "Salaries", "Marketing",
                       "Rent", "Supplies", "Cleaning", "Other"]
STOCK_CATEGORIES  = ["Supplement", "Protein", "Equipment", "Apparel", "Drink/Water",
                     "Snack", "Medicine", "Accessory", "Other"]
COMPLAINT_PRIORITIES = ["Low", "Medium", "High", "Urgent"]
COMPLAINT_STATUSES   = ["Open", "In Progress", "Resolved"]

HEALTH_TIPS = [
    "💪 Tip: Drink at least 3 liters of water daily to stay hydrated during workouts.",
    "🥗 Tip: Eat a protein-rich meal within 30 minutes after your workout for faster recovery.",
    "😴 Tip: Sleep 7-8 hours a night — muscle grows while you rest, not just during exercise.",
    "🧘 Tip: Stretching 10 minutes after each session reduces injury risk significantly.",
    "🔥 Tip: High-intensity intervals (HIIT) burn fat faster than steady-state cardio.",
    "🥛 Tip: 20-40g of protein post-workout accelerates muscle synthesis.",
    "🚶 Tip: A 10-minute walk after meals improves digestion and lowers blood sugar.",
    "🧠 Tip: Consistency beats intensity — showing up daily matters more than one great session.",
    "🍌 Tip: Bananas are the perfect pre-workout snack — natural sugar + potassium for muscles.",
    "⏱️ Tip: Rest 48 hours between training the same muscle group for optimal growth.",
    "🏋️ Tip: Compound lifts (squat, deadlift, bench) give the most return per workout minute.",
    "🌿 Tip: Add leafy greens to every meal — they reduce inflammation and speed recovery.",
    "☀️ Tip: Morning workouts boost metabolism and energy for the entire day.",
    "🫀 Tip: 30 minutes of cardio 3x per week dramatically improves heart health.",
    "🍳 Tip: Eggs are a complete protein source — perfect breakfast before training.",
]

def get_health_tip(seed: int = 0) -> str:
    return HEALTH_TIPS[seed % len(HEALTH_TIPS)]

# ── App Settings ────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    try:
        with SessionLocal() as s:
            row = s.get(AppSetting, key)
            return row.value if row and row.value is not None else default
    except Exception:
        return default

def set_setting(key: str, value: str) -> None:
    try:
        with SessionLocal() as s:
            row = s.get(AppSetting, key)
            if row:
                row.value = value
            else:
                s.add(AppSetting(key=key, value=value))
            s.commit()
    except Exception:
        pass

# ── Utilities ──────────────────────────────────────────────────────────────────

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(pw: str, hashed: str) -> bool:
    return hash_password(pw) == hashed

def _serial_prefix(gym_name: str) -> str:
    words = gym_name.split()
    if len(words) >= 2:
        return "".join(w[0].upper() for w in words[:2])
    return gym_name[:3].upper() if gym_name else "PF"

def _ensure_column(table: str, column: str, ddl: str):
    with engine.begin() as conn:
        if IS_POSTGRES:
            cols = [row[0] for row in conn.exec_driver_sql(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s", (table,)).fetchall()]
        else:
            cols = [row[1] for row in conn.exec_driver_sql(
                f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            ddl_pg = ddl.replace("BOOLEAN NOT NULL DEFAULT 0",
                                 "BOOLEAN NOT NULL DEFAULT FALSE") \
                        .replace("BOOLEAN NOT NULL DEFAULT 1",
                                 "BOOLEAN NOT NULL DEFAULT TRUE")
            sql_ddl = ddl_pg if IS_POSTGRES else ddl
            conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {sql_ddl}")

def init_db():
    Base.metadata.create_all(engine)
    _ensure_column("members", "whatsapp_sent",
                   "whatsapp_sent BOOLEAN NOT NULL DEFAULT 0")
    _ensure_column("fee_records", "whatsapp_sent",
                   "whatsapp_sent BOOLEAN NOT NULL DEFAULT 0")
    _ensure_column("members", "face_encoding", "face_encoding TEXT")
    _ensure_column("members", "created_by_staff", "created_by_staff VARCHAR(60)")
    _ensure_column("gyms", "next_serial", "next_serial INTEGER DEFAULT 1")
    
    # Add all gym columns
    add_gym_columns()
    
    try:
        UnknownCapture.__table__.create(engine, checkfirst=True)
    except Exception:
        pass

    try:
        StaffAttendance.__table__.create(engine, checkfirst=True)
    except:
        pass
    
    try:
        Announcement.__table__.create(engine, checkfirst=True)
    except:
        pass
    
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            if IS_POSTGRES:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'announcements'
                    )
                """))
                if not result.fetchone()[0]:
                    conn.execute(text("""
                        CREATE TABLE announcements (
                            id SERIAL PRIMARY KEY,
                            gym_id INTEGER REFERENCES gyms(id) ON DELETE CASCADE,
                            message TEXT NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_by VARCHAR(60),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP
                        )
                    """))
                    conn.commit()
                    print("✅ Announcements table created")
    except Exception as e:
        print(f"⚠️ Announcement table creation error: {e}")

    seeds = [
        ("admin",   "Administrator", "admin",   "ADMIN_DEFAULT_PASSWORD",   "admin123"),
        ("staff",   "Staff Member",  "staff",   "STAFF_DEFAULT_PASSWORD",   "staff123"),
        ("auditor", "Auditor",       "auditor", "AUDITOR_DEFAULT_PASSWORD", "auditor123"),
    ]
    for username, full_name, role, env_key, dev_default in seeds:
        db = get_db()
        try:
            if db.query(User).filter_by(username=username).first():
                continue
            password = os.environ.get(env_key) or dev_default
            db.add(User(username=username, full_name=full_name,
                        password_hash=hash_password(password), role=role,
                        gym_id=None, is_active=True))
            db.commit()
        except IntegrityError:
            db.rollback()  
        finally:
            db.close()

    clean_corrupt_html_paths()

# ── Gym CRUD ───────────────────────────────────────────────────────────────────

def get_all_gyms():
    db = get_db()
    try:
        return db.query(Gym).order_by(Gym.name).all()
    finally:
        db.close()

def get_gym(gym_id):
    db = get_db()
    try:
        return db.query(Gym).filter_by(id=gym_id).first()
    finally:
        db.close()

def add_gym(name, address="", phone="", email=""):
    db = get_db()
    try:
        if db.query(Gym).filter(func.lower(Gym.name) == name.strip().lower()).first():
            return False, "A gym with this name already exists."
        gym = Gym(name=name.strip(), address=address, phone=phone, email=email)
        db.add(gym)
        db.commit()
        db.refresh(gym)
        return True, f"Gym '{name}' added successfully."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_gym(gym_id, name, address="", phone="", email=""):
    db = get_db()
    try:
        g = db.query(Gym).filter_by(id=gym_id).first()
        if not g:
            return False, "Gym not found."
        dup = db.query(Gym).filter(func.lower(Gym.name) == name.strip().lower(), Gym.id != gym_id).first()
        if dup:
            return False, "Name already taken."
        g.name = name.strip()
        g.address = address
        g.phone = phone
        g.email = email
        db.commit()
        return True, "Gym updated."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def delete_gym(gym_id):
    db = get_db()
    try:
        g = db.query(Gym).filter_by(id=gym_id).first()
        if g:
            db.delete(g)
            db.commit()
        return True, "Gym deleted."
    finally:
        db.close()

# ============================================
# 🔥 SERIAL NUMBER FUNCTIONS - FIXED
# ============================================

def get_gym_prefix(gym_id: int) -> str:
    """Get gym prefix for serial numbers."""
    gym = get_gym(gym_id)
    if gym:
        return _serial_prefix(gym.name)
    return "PF"

def get_next_member_serial(gym_id: int) -> int:
    """Get the next available serial number for a gym - FIXED."""
    try:
        db = get_db()
        # Get current gym's next_serial
        gym = db.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            db.close()
            return 1
        
        next_serial = gym.next_serial or 1
        
        # Check if this serial is already used
        prefix = get_gym_prefix(gym_id)
        serial_str = f"{prefix}-{str(next_serial).zfill(5)}"
        
        existing = db.query(Member).filter(
            Member.gym_id == gym_id,
            Member.serial_number == serial_str
        ).first()
        
        # If serial already exists, find next available
        retry_count = 0
        while existing and retry_count < 20:
            next_serial += 1
            serial_str = f"{prefix}-{str(next_serial).zfill(5)}"
            existing = db.query(Member).filter(
                Member.gym_id == gym_id,
                Member.serial_number == serial_str
            ).first()
            retry_count += 1
        
        db.close()
        return next_serial
        
    except Exception as e:
        print(f"Error getting next serial: {e}")
        return 1

def update_gym_next_serial(gym_id: int, new_serial: int) -> Tuple[bool, str]:
    """Update the next serial number for a gym."""
    try:
        db = get_db()
        gym = db.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            db.close()
            return False, "Gym not found"
        
        # Check if the new serial is already used
        prefix = get_gym_prefix(gym_id)
        serial_str = f"{prefix}-{str(new_serial).zfill(5)}"
        
        existing = db.query(Member).filter(
            Member.gym_id == gym_id,
            Member.serial_number == serial_str
        ).first()
        
        if existing:
            db.close()
            return False, f"Serial {serial_str} already exists!"
        
        gym.next_serial = new_serial
        db.commit()
        db.close()
        return True, "Serial number updated successfully"
        
    except Exception as e:
        return False, str(e)

# ── User CRUD ──────────────────────────────────────────────────────────────────

def get_user_by_username(username):
    db = get_db()
    try:
        return db.query(User).filter_by(username=username).first()
    finally:
        db.close()

def get_all_users():
    db = get_db()
    try:
        return db.query(User).order_by(User.role, User.full_name).all()
    finally:
        db.close()

def add_user(username, full_name, password, role, gym_id=None):
    db = get_db()
    try:
        if db.query(User).filter_by(username=username).first():
            return False, "Username already exists."
        db.add(User(username=username, full_name=full_name,
                    password_hash=hash_password(password), role=role, gym_id=gym_id))
        db.commit()
        return True, "User created."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_user(user_id, full_name, role, gym_id, is_active, new_password=None):
    db = get_db()
    try:
        u = db.query(User).filter_by(id=user_id).first()
        if not u:
            return False, "User not found."
        u.full_name = full_name
        u.role = role
        u.gym_id = gym_id
        u.is_active = is_active
        if new_password:
            u.password_hash = hash_password(new_password)
        db.commit()
        return True, "User updated."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def delete_user(user_id):
    db = get_db()
    try:
        u = db.query(User).filter_by(id=user_id).first()
        if u:
            db.delete(u)
            db.commit()
        return True, "User deleted."
    finally:
        db.close()

# ── Member CRUD ────────────────────────────────────────────────────────────────

# ============================================
# 🔥 FIXED: _next_serial() - Serial number generate karne ka sahi tareeqa
# ============================================

def _next_serial(gym_id, db):
    """Generate next serial number - FIXED to avoid duplicates"""
    gym = db.query(Gym).filter_by(id=gym_id).first()
    prefix = _serial_prefix(gym.name) if gym else "PF"
    
    # Use gym's next_serial field
    next_num = gym.next_serial if gym and gym.next_serial else 1
    
    # Check if this serial already exists
    serial_str = f"{prefix}-{str(next_num).zfill(5)}"
    existing = db.query(Member).filter(
        Member.gym_id == gym_id,
        Member.serial_number == serial_str
    ).first()
    
    # If exists, find next available
    retry_count = 0
    while existing and retry_count < 20:
        next_num += 1
        serial_str = f"{prefix}-{str(next_num).zfill(5)}"
        existing = db.query(Member).filter(
            Member.gym_id == gym_id,
            Member.serial_number == serial_str
        ).first()
        retry_count += 1
    
    # Update gym's next_serial
    if gym:
        gym.next_serial = next_num + 1
        db.commit()
    
    return serial_str

def get_members(gym_id=None, status=None, search=None):
    db = get_db()
    try:
        q = db.query(Member)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if status and status != "All":
            q = q.filter_by(status=status)
        if search:
            s = f"%{search}%"
            q = q.filter(
                Member.full_name.ilike(s) |
                Member.serial_number.ilike(s) |
                Member.phone.ilike(s) |
                Member.email.ilike(s)
            )
        return q.order_by(Member.created_at.desc()).all()
    finally:
        db.close()

def get_member(member_id):
    db = get_db()
    try:
        return db.query(Member).filter_by(id=member_id).first()
    finally:
        db.close()

def get_member_by_serial(serial: str, gym_id=None):
    if not serial:
        return None
    db = get_db()
    try:
        q = db.query(Member).filter(Member.serial_number == serial.strip())
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        return q.first()
    finally:
        db.close()

# ============================================
# 🔥 FIXED: add_member() - Retry logic with duplicate detection
# ============================================

def add_member(gym_id, full_name, phone, email, gender, dob,
               membership_type, fee_amount, join_date, expiry_date,
               photo_path, status, notes):
    last_err = None
    max_retries = 10
    
    for attempt in range(max_retries):
        db = get_db()
        try:
            # ── STAFF USERNAME CAPTURE ──
            try:
                from streamlit import session_state
                staff_username = session_state.get("username", "unknown")
            except:
                staff_username = "unknown"

            if phone and phone.strip():
                existing_phone = db.query(Member).filter(
                    Member.phone == phone.strip()
                ).first()
                if existing_phone:
                    return False, "⚠️ This phone number is already registered with another member.", None

            serial = _next_serial(gym_id, db)
            m = Member(gym_id=gym_id, serial_number=serial, full_name=full_name.strip(),
                       phone=phone.strip() if phone else None,
                       email=email, gender=gender, dob=dob,
                       membership_type=membership_type, fee_amount=fee_amount,
                       join_date=str(join_date),
                       expiry_date=str(expiry_date) if expiry_date else None,
                       photo_path=photo_path, status=status, notes=notes,
                       created_by_staff=staff_username)
            db.add(m)
            db.commit()
            
            # ── WHATSAPP AUTO-ADD TRIGGER ──
            try:
                from gym_pages.whatsapp import add_member_to_staff_group
                if phone and phone.strip() and staff_username != "unknown":
                    import threading
                    threading.Thread(
                        target=add_member_to_staff_group,
                        args=(phone.strip(), staff_username, full_name.strip(), serial)
                    ).start()
                    print(f"✅ WhatsApp auto-add triggered for {full_name} by {staff_username}")
            except Exception as wa_error:
                print(f"⚠️ WhatsApp auto-add failed: {wa_error}")
            
            sync_to_local((m.id, serial, full_name, phone, email, gender, dob, photo_path, membership_type, fee_amount, str(join_date), str(expiry_date) if expiry_date else None, status, notes, None))
            return True, f"Member registered. Serial: {serial}", serial
            
        except IntegrityError as e:
            db.rollback()
            last_err = e
            # 🔥 Check if it's a duplicate serial number error
            error_msg = str(e).lower()
            if "duplicate key" in error_msg and "serial_number" in error_msg:
                print(f"⚠️ Serial {serial} already exists, retrying... (attempt {attempt + 1}/{max_retries})")
                # Update gym next_serial
                try:
                    gym = db.query(Gym).filter_by(id=gym_id).first()
                    if gym:
                        gym.next_serial = gym.next_serial + 1
                        db.commit()
                except:
                    pass
                continue
            else:
                return False, str(e), None
                
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()
            
    return False, f"Could not allocate a unique serial number after {max_retries} retries: {last_err}", None

def sync_to_local(member_data):
    """Save member to local SQLite as backup"""
    try:
        local_conn = sqlite3.connect('gym_pro_backup_local.db')
        local_cursor = local_conn.cursor()
        
        local_cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY,
                serial_number TEXT,
                full_name TEXT,
                phone TEXT,
                email TEXT,
                gender TEXT,
                dob TEXT,
                photo_path TEXT,
                membership_type TEXT,
                fee_amount REAL,
                join_date TEXT,
                expiry_date TEXT,
                status TEXT,
                notes TEXT,
                face_encoding TEXT,
                created_by_staff TEXT
            )
        ''')
        
        local_cursor.execute('''
            INSERT OR REPLACE INTO members 
            (id, serial_number, full_name, phone, email, gender, dob, photo_path, membership_type, fee_amount, join_date, expiry_date, status, notes, face_encoding, created_by_staff)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', member_data + (None,))
        
        local_conn.commit()
        local_conn.close()
        return True
    except Exception as e:
        print(f"Local sync error: {e}")
        return False

def update_member(member_id, **kwargs):
    db = get_db()
    try:
        m = db.query(Member).filter_by(id=member_id).first()
        if not m:
            return False, "Member not found."

        new_phone = kwargs.get("phone", "").strip() if kwargs.get("phone") else ""
        if new_phone and new_phone != (m.phone or ""):
            dup = db.query(Member).filter(
                Member.phone == new_phone,
                Member.id != member_id
            ).first()
            if dup:
                return False, "⚠️ This phone number is already registered with another member."

        for k, v in kwargs.items():
            setattr(m, k, v)
        db.commit()
        return True, "Member updated."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

# ── Face Encoding CRUD ────────────────────────────────────────────────────────

def save_face_encoding(member_id: int, encoding_json: str) -> tuple[bool, str]:
    db = get_db()
    try:
        m = db.query(Member).filter_by(id=member_id).first()
        if not m:
            return False, "Member not found"
        m.face_encoding = encoding_json
        db.commit()
        return True, "Face enrolled"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_face_encodings(gym_id=None) -> list[dict]:
    db = get_db()
    try:
        q = db.query(Member).filter(Member.face_encoding.isnot(None))
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        return [
            {
                "id": m.id,
                "gym_id": m.gym_id,
                "serial_number": m.serial_number,
                "full_name": m.full_name,
                "photo_path": m.photo_path,
                "status": m.status or "Active",
                "expiry_date": m.expiry_date,
                "encoding_json": m.face_encoding,
            }
            for m in q.all()
        ]
    finally:
        db.close()

# ── Unknown / Expired Capture CRUD ────────────────────────────────────────────

def add_unknown_capture(gym_id: int, capture_key: str,
                        capture_type: str = "unknown",
                        member_id: int | None = None,
                        member_name: str | None = None,
                        notes: str | None = None) -> int | None:
    db = get_db()
    try:
        cap = UnknownCapture(
            gym_id=gym_id,
            capture_key=capture_key,
            capture_type=capture_type,
            member_id=member_id,
            member_name=member_name,
            notes=notes,
        )
        db.add(cap)
        db.commit()
        db.refresh(cap)
        return cap.id
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()

def get_unknown_captures(gym_id: int | None = None, limit: int = 100) -> list:
    db = get_db()
    try:
        q = db.query(UnknownCapture).order_by(UnknownCapture.captured_at.desc())
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        return q.limit(limit).all()
    finally:
        db.close()

def delete_unknown_capture_record(capture_id: int) -> bool:
    db = get_db()
    try:
        cap = db.query(UnknownCapture).filter_by(id=capture_id).first()
        if cap:
            db.delete(cap)
            db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def cleanup_old_captures(days: int = 3) -> list[str]:
    db = get_db()
    cutoff = datetime.now() - timedelta(days=days)
    try:
        old = db.query(UnknownCapture).filter(UnknownCapture.captured_at < cutoff).all()
        keys = [c.capture_key for c in old]
        for c in old:
            db.delete(c)
        db.commit()
        return keys
    except Exception:
        db.rollback()
        return []
    finally:
        db.close()

def delete_member(member_id):
    db = get_db()
    try:
        m = db.query(Member).filter_by(id=member_id).first()
        if m:
            if m.photo_path:
                full_path = m.photo_path if os.path.isabs(m.photo_path) else os.path.join(UPLOAD_FOLDER, os.path.basename(m.photo_path))
                if os.path.exists(full_path):
                    os.remove(full_path)
            db.delete(m)
            db.commit()
        return True, "Member deleted."
    finally:
        db.close()

def get_expiring_members(days=5, gym_id=None):
    db = get_db()
    try:
        today = date.today()
        threshold = today + timedelta(days=days)
        q = db.query(Member).filter(
            Member.status == "Active",
            Member.expiry_date.isnot(None),
            Member.expiry_date != "",
        )
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        results = []
        for m in q.all():
            try:
                exp = date.fromisoformat(m.expiry_date)
                if today <= exp <= threshold:
                    results.append((m, (exp - today).days))
            except Exception:
                pass
        return results
    finally:
        db.close()

def get_absent_members(days=3, gym_id=None):
    db = get_db()
    try:
        today = date.today()
        cutoff = str(today - timedelta(days=days))
        q = db.query(Member).filter_by(status="Active")
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        results = []
        for m in q.all():
            recent = db.query(Attendance).filter(
                Attendance.member_id == m.id,
                Attendance.status == "Present",
                Attendance.check_date >= cutoff,
            ).first()
            if not recent:
                results.append(m)
        return results
    finally:
        db.close()

def get_birthday_members(days_ahead=7, gym_id=None):
    db = get_db()
    try:
        today = date.today()
        q = db.query(Member).filter(
            Member.status == "Active",
            Member.dob.isnot(None),
            Member.dob != "",
        )
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        results = []
        for m in q.all():
            try:
                dob = date.fromisoformat(m.dob)
                bday_this_year = dob.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = dob.replace(year=today.year + 1)
                delta = (bday_this_year - today).days
                if 0 <= delta <= days_ahead:
                    results.append((m, delta))
            except Exception:
                pass
        return sorted(results, key=lambda x: x[1])
    finally:
        db.close()

def get_member_streak(member_id):
    db = get_db()
    try:
        today = date.today()
        streak = 0
        check = today
        for _ in range(365):
            rec = db.query(Attendance).filter_by(
                member_id=member_id, check_date=str(check), status="Present"
            ).first()
            if rec:
                streak += 1
                check -= timedelta(days=1)
            else:
                break
        return streak
    finally:
        db.close()

def get_attendance_leaderboard(gym_id=None, limit=10):
    db = get_db()
    try:
        today = date.today()
        month_start = str(today.replace(day=1))
        q = db.query(
            Attendance.member_id,
            func.count(Attendance.id).label("count")
        ).filter(
            Attendance.status == "Present",
            Attendance.check_date >= month_start,
        )
        if gym_id:
            q = q.filter(Attendance.gym_id == gym_id)
        rows = q.group_by(Attendance.member_id).order_by(func.count(Attendance.id).desc()).limit(limit).all()
        results = []
        for row in rows:
            m = db.query(Member).filter_by(id=row.member_id).first()
            if m:
                results.append({"member": m, "count": row.count,
                                 "streak": get_member_streak(m.id)})
        return results
    finally:
        db.close()

# ── Attendance ─────────────────────────────────────────────────────────────────

def mark_attendance(member_id, gym_id, check_date, status, marked_by):
    db = get_db()
    try:
        existing = db.query(Attendance).filter_by(
            member_id=member_id, check_date=str(check_date)
        ).first()
        if existing:
            existing.status = status
            existing.marked_by = marked_by
        else:
            db.add(Attendance(member_id=member_id, gym_id=gym_id,
                              check_date=str(check_date), status=status, marked_by=marked_by))
        db.commit()
        return True, "Attendance marked."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_attendance(gym_id=None, check_date=None):
    db = get_db()
    try:
        q = db.query(Attendance)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if check_date:
            q = q.filter_by(check_date=str(check_date))
        return q.order_by(Attendance.created_at.desc()).all()
    finally:
        db.close()

def get_recent_scans(gym_id=None, limit: int = 10, today_only: bool = True):
    db = get_db()
    try:
        q = db.query(Attendance).filter(Attendance.status == "Present")
        if gym_id:
            q = q.filter(Attendance.gym_id == gym_id)
        if today_only:
            q = q.filter(Attendance.check_date == str(date.today()))
        rows = q.order_by(Attendance.created_at.desc()).limit(limit).all()
        results = []
        for a in rows:
            m = db.query(Member).filter_by(id=a.member_id).first()
            g = db.query(Gym).filter_by(id=a.gym_id).first()
            results.append({
                "time":    a.created_at.strftime("%H:%M:%S") if a.created_at else "—",
                "name":    m.full_name if m else "—",
                "serial":  m.serial_number if m else "—",
                "photo":   m.photo_path if m else None,
                "gym":     g.name if g else "—",
                "marked_by": a.marked_by or "—",
            })
        return results
    finally:
        db.close()

def get_attendance_by_hour(gym_id=None):
    db = get_db()
    try:
        q = db.query(Attendance).filter(
            Attendance.status == "Present",
            Attendance.created_at.isnot(None),
        )
        if gym_id:
            q = q.filter(Attendance.gym_id == gym_id)
        hours = {i: 0 for i in range(24)}
        for a in q.all():
            if a.created_at:
                hours[a.created_at.hour] += 1
        return hours
    finally:
        db.close()

def get_attendance_trend(gym_id=None, days=30):
    session = get_db()
    try:
        today = date.today()
        results = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            base = session.query(Attendance).filter(Attendance.check_date == str(d))
            if gym_id:
                base = base.filter(Attendance.gym_id == gym_id)
            recs = base.all()
            results.append({
                "date":    d.strftime("%d %b"),
                "present": sum(1 for r in recs if r.status == "Present"),
                "absent":  sum(1 for r in recs if r.status == "Absent"),
                "late":    sum(1 for r in recs if r.status == "Late"),
            })
        return results
    finally:
        session.close()

def get_all_member_last_visits(gym_id=None):
    session = get_db()
    try:
        q = session.query(
            Attendance.member_id,
            func.max(Attendance.check_date).label("last_date")
        ).filter(Attendance.status == "Present")
        if gym_id:
            q = q.filter(Attendance.gym_id == gym_id)
        rows = q.group_by(Attendance.member_id).all()
        return {r.member_id: r.last_date for r in rows}
    finally:
        session.close()

def get_member_attendance_rate(member_id, days=30):
    session = get_db()
    try:
        today = date.today()
        cutoff = str(today - timedelta(days=days))
        present = session.query(func.count(Attendance.id)).filter(
            Attendance.member_id == member_id,
            Attendance.check_date >= cutoff,
            Attendance.status == "Present"
        ).scalar() or 0
        return round(present / days * 100, 1)
    finally:
        session.close()

def get_late_members_summary(gym_id=None, days=30):
    session = get_db()
    try:
        today = date.today()
        cutoff = str(today - timedelta(days=days))
        q = session.query(
            Attendance.member_id,
            func.count(Attendance.id).label("late_count")
        ).filter(
            Attendance.status == "Late",
            Attendance.check_date >= cutoff
        )
        if gym_id:
            q = q.filter(Attendance.gym_id == gym_id)
        rows = q.group_by(Attendance.member_id).order_by(
            func.count(Attendance.id).desc()
        ).limit(10).all()
        results = []
        for row in rows:
            m = session.query(Member).filter_by(id=row.member_id).first()
            if m:
                results.append({"member": m, "late_count": row.late_count})
        return results
    finally:
        session.close()

def get_attendance_range(gym_id=None, from_date=None, to_date=None, status_filter=None):
    session = get_db()
    try:
        q = session.query(Attendance)
        if gym_id:
            q = q.filter(Attendance.gym_id == gym_id)
        if from_date:
            q = q.filter(Attendance.check_date >= str(from_date))
        if to_date:
            q = q.filter(Attendance.check_date <= str(to_date))
        if status_filter and status_filter != "All":
            q = q.filter(Attendance.status == status_filter)
        return q.order_by(Attendance.check_date.desc(), Attendance.created_at.desc()).all()
    finally:
        session.close()

# ── Fee Records ────────────────────────────────────────────────────────────────

def add_fee_record(member_id, gym_id, amount, payment_method, payment_date,
                   period_start, period_end, collected_by, notes=""):
    db = get_db()
    try:
        receipt = f"RCP-{uuid.uuid4().hex[:8].upper()}"
        db.add(FeeRecord(member_id=member_id, gym_id=gym_id, amount=amount,
                         payment_method=payment_method, payment_date=str(payment_date),
                         period_start=str(period_start) if period_start else None,
                         period_end=str(period_end) if period_end else None,
                         receipt_number=receipt, collected_by=collected_by, notes=notes))
        db.commit()
        return True, f"Fee recorded. Receipt: {receipt}"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def log_receipt(fee_record_id, gym_id, member_name, receipt_number, amount,
                collected_by, print_issued=False):
    db = get_db()
    try:
        now = datetime.now()
        db.add(ReceiptLog(
            fee_record_id  = fee_record_id,
            gym_id         = gym_id,
            member_name    = str(member_name),
            receipt_number = str(receipt_number),
            amount         = float(amount),
            collected_by   = str(collected_by),
            pay_date       = now.strftime("%Y-%m-%d"),
            pay_time       = now.strftime("%H:%M"),
            print_issued   = print_issued,
        ))
        db.commit()
        return True, "Receipt logged."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_print_issued(receipt_number: str, issued: bool = True):
    db = get_db()
    try:
        db.query(ReceiptLog)\
          .filter(ReceiptLog.receipt_number == receipt_number)\
          .update({"print_issued": issued})
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def get_receipt_logs(gym_id=None, limit=500):
    db = get_db()
    try:
        q = db.query(ReceiptLog)
        if gym_id:
            q = q.filter(ReceiptLog.gym_id == gym_id)
        rows = q.order_by(ReceiptLog.created_at.desc()).limit(limit).all()
        result = []
        for r in rows:
            result.append({
                "id":             r.id,
                "receipt_number": r.receipt_number,
                "member_name":    r.member_name,
                "amount":         r.amount,
                "collected_by":   r.collected_by or "",
                "pay_date":       r.pay_date,
                "pay_time":       r.pay_time,
                "print_issued":   r.print_issued,
                "created_at":     r.created_at,
            })
        return result
    except Exception as e:
        return []
    finally:
        db.close()

from sqlalchemy.orm import joinedload

def get_fee_records(gym_id=None, member_id=None, date_from=None, date_to=None, limit=None):
    db = get_db()
    try:
        query = db.query(FeeRecord).options(joinedload(FeeRecord.member))
        
        if gym_id:
            query = query.filter(FeeRecord.gym_id == gym_id)
        
        if member_id:
            query = query.filter(FeeRecord.member_id == member_id)
        
        if date_from:
            query = query.filter(FeeRecord.payment_date >= str(date_from))
        if date_to:
            query = query.filter(FeeRecord.payment_date <= str(date_to))
        
        query = query.order_by(FeeRecord.payment_date.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    finally:
        db.close()

def update_fee_record(record_id, amount, payment_method, period_start, period_end, notes):
    db = get_db()
    try:
        record = db.query(FeeRecord).filter(FeeRecord.id == record_id).first()
        if record:
            record.amount = float(amount)
            record.payment_method = payment_method
            record.period_start = str(period_start) if period_start else None
            record.period_end = str(period_end) if period_end else None
            record.notes = notes
            db.commit()
            return True, "Record updated successfully."
        return False, "Record not found."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def delete_fee_record(record_id):
    db = get_db()
    try:
        record = db.query(FeeRecord).filter(FeeRecord.id == record_id).first()
        if record:
            db.delete(record)
            db.commit()
            return True, "Record deleted successfully."
        return False, "Record not found."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def mark_member_whatsapp_sent(member_id: int) -> bool:
    db = get_db()
    try:
        n = (db.query(Member)
               .filter(Member.id == member_id, Member.whatsapp_sent == False)
               .update({Member.whatsapp_sent: True}, synchronize_session=False))
        db.commit()
        return n == 1
    finally:
        db.close()

def mark_fee_whatsapp_sent(fee_id: int) -> bool:
    db = get_db()
    try:
        n = (db.query(FeeRecord)
               .filter(FeeRecord.id == fee_id, FeeRecord.whatsapp_sent == False)
               .update({FeeRecord.whatsapp_sent: True}, synchronize_session=False))
        db.commit()
        return n == 1
    finally:
        db.close()

def get_fee_records_created_today(gym_id=None):
    db = get_db()
    try:
        utc_today = datetime.now().date()
        start = datetime.combine(utc_today, datetime.min.time())
        end   = start + timedelta(days=1)
        q = db.query(FeeRecord).filter(
            FeeRecord.created_at >= start,
            FeeRecord.created_at <  end,
            FeeRecord.whatsapp_sent == False,  
        )
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        return q.order_by(FeeRecord.created_at.desc()).all()
    finally:
        db.close()

def get_monthly_revenue(gym_id=None, year=None):
    year = year or date.today().year
    records = get_fee_records(gym_id=gym_id)
    monthly = {i: 0.0 for i in range(1, 13)}
    for r in records:
        try:
            d = date.fromisoformat(r.payment_date)
            if d.year == year:
                monthly[d.month] += r.amount
        except Exception:
            pass
    return monthly

# ── Expenses ───────────────────────────────────────────────────────────────────

def add_expense(gym_id, amount, category, description, expense_date, staff_name):
    db = get_db()
    try:
        db.add(DailyExpense(gym_id=gym_id, amount=amount, category=category,
                            description=description, expense_date=str(expense_date),
                            staff_name=staff_name))
        db.commit()
        return True, "Expense recorded."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_expenses(gym_id=None, category=None, date_from=None, date_to=None):
    db = get_db()
    try:
        q = db.query(DailyExpense)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if category and category != "All":
            q = q.filter_by(category=category)
        if date_from:
            q = q.filter(DailyExpense.expense_date >= str(date_from))
        if date_to:
            q = q.filter(DailyExpense.expense_date <= str(date_to))
        return q.order_by(DailyExpense.expense_date.desc()).all()
    finally:
        db.close()

def delete_expense(expense_id):
    db = get_db()
    try:
        e = db.query(DailyExpense).filter_by(id=expense_id).first()
        if e:
            db.delete(e)
            db.commit()
        return True, "Deleted."
    finally:
        db.close()

# ── Audit ──────────────────────────────────────────────────────────────────────

def add_audit_entry(gym_id, entry_type, reference_id, expected_amount, actual_amount,
                    description, entry_date, verified_by, notes=""):
    db = get_db()
    try:
        status = "Verified" if abs(expected_amount - actual_amount) < 0.01 else "Discrepancy"
        db.add(AuditEntry(gym_id=gym_id, entry_type=entry_type, reference_id=reference_id,
                          expected_amount=expected_amount, actual_amount=actual_amount,
                          description=description, entry_date=str(entry_date),
                          verified_by=verified_by, status=status, notes=notes))
        db.commit()
        return True, f"Audit entry saved. Status: {status}"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_audit_entries(gym_id=None, status=None, date_from=None, date_to=None):
    db = get_db()
    try:
        q = db.query(AuditEntry)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if status and status != "All":
            q = q.filter_by(status=status)
        if date_from:
            q = q.filter(AuditEntry.entry_date >= str(date_from))
        if date_to:
            q = q.filter(AuditEntry.entry_date <= str(date_to))
        return q.order_by(AuditEntry.entry_date.desc()).all()
    finally:
        db.close()

# ── Activity Log (Anti-Theft) ───────────────────────────────────────────────────

def log_activity(user, action, details="", gym_id=None, role="", amount=None, record_ref=""):
    db = get_db()
    try:
        db.add(ActivityLog(
            gym_id=gym_id,
            user=str(user),
            role=str(role),
            action=str(action),
            details=str(details),
            amount=amount,
            record_ref=str(record_ref),
        ))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()

def get_activity_logs(gym_id=None, limit=500, date_from=None, date_to=None, user=None, action=None):
    db = get_db()
    try:
        q = db.query(ActivityLog)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if user:
            q = q.filter(ActivityLog.user == user)
        if action:
            q = q.filter(ActivityLog.action == action)
        if date_from:
            q = q.filter(ActivityLog.created_at >= datetime.combine(date_from, datetime.min.time())
                         if hasattr(date_from, 'year') else ActivityLog.created_at >= date_from)
        if date_to:
            q = q.filter(ActivityLog.created_at <= datetime.combine(date_to, datetime.max.time())
                         if hasattr(date_to, 'year') else ActivityLog.created_at <= date_to)
        return q.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    finally:
        db.close()


def get_member_portal_usage(gym_id=None, active_minutes=15, limit=500):
    """Return member portal usage aggregated by member.

    Portal activity is stored in ActivityLog so this works with both the
    PostgreSQL and SQLite database modes without a schema migration.
    """
    db = get_db()
    try:
        actions = ("MEMBER_PORTAL_LOGIN", "MEMBER_PORTAL_ACTIVE")
        q = db.query(ActivityLog).filter(ActivityLog.action.in_(actions))
        if gym_id:
            q = q.filter(ActivityLog.gym_id == gym_id)
        logs = q.order_by(ActivityLog.created_at.desc()).limit(limit).all()

        grouped = {}
        for log in logs:
            serial = str(log.user or "").strip()
            if not serial:
                continue
            item = grouped.setdefault(serial, {
                "serial": serial,
                "name": "",
                "gym_id": log.gym_id,
                "last_seen": log.created_at,
                "last_login": None,
                "visits": 0,
                "active_events": 0,
            })
            item["visits"] += 1
            if log.action == "MEMBER_PORTAL_ACTIVE":
                item["active_events"] += 1
            else:
                if item["last_login"] is None:
                    item["last_login"] = log.created_at
            if log.created_at and (
                item["last_seen"] is None or log.created_at > item["last_seen"]
            ):
                item["last_seen"] = log.created_at
            if not item["name"] and log.details:
                details = str(log.details)
                # Details are written as "Member: Name | ..." by the portal.
                if details.startswith("Member: "):
                    item["name"] = details.split("Member: ", 1)[1].split(" | ", 1)[0]

        now = datetime.now()
        for item in grouped.values():
            if not item["name"]:
                member = db.query(Member).filter(Member.serial_number == item["serial"]).first()
                if member:
                    item["name"] = member.full_name
                    item["gym_id"] = member.gym_id
            last_seen = item["last_seen"]
            item["is_active"] = bool(
                last_seen and (now - last_seen).total_seconds() <= active_minutes * 60
            )
            item["last_seen_text"] = (
                last_seen.strftime("%d %b %Y, %I:%M %p") if last_seen else "—"
            )
        return sorted(
            grouped.values(),
            key=lambda x: x["last_seen"] or datetime.min,
            reverse=True,
        )
    finally:
        db.close()


def get_daily_fee_summary(gym_id=None, target_date=None):
    db = get_db()
    try:
        date_str = str(target_date or datetime.now().date())
        q = db.query(FeeRecord).filter(FeeRecord.payment_date == date_str)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        records = q.all()
        total = sum(r.amount or 0 for r in records)
        return total, len(records), records
    finally:
        db.close()

# ── Shift Session Functions ─────────────────────────────────────────────────────

def open_shift(gym_id, staff_user, role, opening_cash=0.0):
    db = get_db()
    try:
        existing = db.query(ShiftSession).filter_by(
            gym_id=gym_id, staff_user=staff_user, status="open"
        ).first()
        if existing:
            return False, "Aapki pehle se ek shift open hai. Pehle band karein."
        s = ShiftSession(
            gym_id=gym_id, staff_user=staff_user, role=role,
            opening_cash=float(opening_cash), status="open"
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        log_activity(user=staff_user, action="SHIFT_OPENED",
                     details=f"Opening cash: PKR {opening_cash:,.0f}",
                     gym_id=gym_id, role=role, amount=opening_cash)
        return True, s.id
    except Exception as e:
        try: db.rollback()
        except: pass
        return False, str(e)
    finally:
        db.close()

def close_shift(shift_id, closing_cash):
    db = get_db()
    try:
        shift = db.query(ShiftSession).filter_by(id=shift_id).first()
        if not shift:
            return False, "Shift nahi mili."
        if shift.status != "open":
            return False, "Yeh shift already band hai."

        opened_str = shift.opened_at.strftime("%Y-%m-%d")
        recs = db.query(FeeRecord).filter(
            FeeRecord.gym_id == shift.gym_id,
            FeeRecord.collected_by == shift.staff_user,
            FeeRecord.payment_date >= opened_str,
        ).all()
        shift_collections = [r for r in recs if r.created_at and r.created_at >= shift.opened_at]
        collected = sum(r.amount or 0 for r in shift_collections)

        expected = (shift.opening_cash or 0) + collected
        discrepancy = float(closing_cash) - expected
        status = "flagged" if discrepancy < -1 else "closed"

        shift.closed_at     = datetime.now()
        shift.expected_cash = expected
        shift.closing_cash  = float(closing_cash)
        shift.discrepancy   = discrepancy
        shift.status        = status
        db.commit()

        log_activity(
            user=shift.staff_user, action="SHIFT_CLOSED",
            details=f"Opening: PKR {shift.opening_cash:,.0f} | Collected: PKR {collected:,.0f} | Expected: PKR {expected:,.0f} | Submitted: PKR {closing_cash:,.0f} | Diff: PKR {discrepancy:,.0f}",
            gym_id=shift.gym_id, role=shift.role, amount=discrepancy,
            record_ref="FLAGGED" if status == "flagged" else "OK"
        )
        return True, {"expected": expected, "closing": closing_cash, "discrepancy": discrepancy, "status": status}
    except Exception as e:
        try: db.rollback()
        except: pass
        return False, str(e)
    finally:
        db.close()

def get_active_shift(gym_id, staff_user):
    db = get_db()
    try:
        return db.query(ShiftSession).filter_by(
            gym_id=gym_id, staff_user=staff_user, status="open"
        ).first()
    finally:
        db.close()

def get_staff_today_metrics(username: str, gym_id=None) -> dict:
    from datetime import date as _date
    today      = _date.today()
    today_str  = str(today)
    today_start = datetime.combine(today, datetime.min.time())
    db = get_db()
    try:
        fq = db.query(FeeRecord).filter(
            FeeRecord.collected_by == username,
            FeeRecord.payment_date == today_str,
        )
        if gym_id:
            fq = fq.filter(FeeRecord.gym_id == gym_id)
        fees      = fq.all()
        fee_total = sum(r.amount or 0 for r in fees)
        fee_count = len(fees)

        aq = db.query(Attendance).filter(
            Attendance.marked_by == username,
            Attendance.check_date == today_str,
        )
        if gym_id:
            aq = aq.filter(Attendance.gym_id == gym_id)
        att_count = aq.count()

        mq = db.query(Member).filter(Member.status == "active")
        if gym_id:
            mq = mq.filter(Member.gym_id == gym_id)
        total_active = mq.count()

        sq = db.query(ShiftSession).filter_by(staff_user=username, status="open")
        if gym_id:
            sq = sq.filter(ShiftSession.gym_id == gym_id)
        active_shift  = sq.first()
        shift_open    = active_shift is not None
        shift_id      = active_shift.id if active_shift else None
        shift_opening = active_shift.opening_cash if active_shift else 0.0
        shift_opened_at = active_shift.opened_at.strftime("%H:%M") if active_shift else None

        sq2 = db.query(ShiftSession).filter(
            ShiftSession.staff_user == username,
            ShiftSession.opened_at >= today_start,
        )
        if gym_id:
            sq2 = sq2.filter(ShiftSession.gym_id == gym_id)
        shifts_today = sq2.count()

        lq = db.query(ActivityLog).filter(
            ActivityLog.user == username,
            ActivityLog.created_at >= today_start,
        )
        if gym_id:
            lq = lq.filter(ActivityLog.gym_id == gym_id)
        logs = lq.order_by(ActivityLog.created_at.desc()).all()

        deletions    = [l for l in logs if "DELETE" in (l.action or "").upper()]
        new_members  = [l for l in logs if l.action in ("MEMBER_ADDED", "MEMBER_REGISTERED")]
        last_log     = logs[0] if logs else None

        return {
            "fee_total":           fee_total,
            "fee_count":           fee_count,
            "att_count":           att_count,
            "total_active_members":total_active,
            "shift_open":          shift_open,
            "shift_id":            shift_id,
            "shift_opening_cash":  shift_opening,
            "shift_opened_at":     shift_opened_at,
            "shifts_today":        shifts_today,
            "activity_count":      len(logs),
            "deletions_today":     len(deletions),
            "new_members_today":   len(new_members),
            "last_action":         last_log.action if last_log else None,
            "last_action_time":    last_log.created_at.strftime("%H:%M") if last_log else None,
        }
    except Exception as e:
        return {
            "fee_total": 0, "fee_count": 0, "att_count": 0,
            "total_active_members": 0, "shift_open": False,
            "shift_id": None, "shift_opening_cash": 0,
            "shift_opened_at": None, "shifts_today": 0,
            "activity_count": 0, "deletions_today": 0,
            "new_members_today": 0, "last_action": None, "last_action_time": None,
        }
    finally:
        db.close()

def get_today_shifts(gym_id=None):
    db = get_db()
    try:
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        q = db.query(ShiftSession).filter(ShiftSession.opened_at >= today_start)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        return q.order_by(ShiftSession.opened_at.desc()).all()
    finally:
        db.close()

def check_fraud_alerts(gym_id=None, target_date=None):
    from collections import defaultdict
    alerts = []
    check_date = target_date or datetime.now().date()
    date_str = str(check_date)
    today_start = datetime.combine(check_date, datetime.min.time())
    today_end   = datetime.combine(check_date, datetime.max.time())

    dbs = get_db()
    try:
        delete_logs = dbs.query(ActivityLog).filter(
            ActivityLog.action == "FEE_DELETED",
            ActivityLog.created_at >= today_start,
            ActivityLog.created_at <= today_end,
        )
        if gym_id:
            delete_logs = delete_logs.filter_by(gym_id=gym_id)
        del_by = defaultdict(list)
        for lg in delete_logs.all():
            del_by[lg.user].append(lg)
        for user, entries in del_by.items():
            n = len(entries)
            total_deleted = sum(e.amount or 0 for e in entries)
            if n >= 4:
                alerts.append({
                    "severity": "critical",
                    "icon": "🚨",
                    "title": f"{user} ne aaj {n} fee records DELETE kiye!",
                    "detail": f"Deleted amount: PKR {total_deleted:,.0f} — Fori jaanch karein!"
                })
            elif n >= 2:
                alerts.append({
                    "severity": "warning",
                    "icon": "⚠️",
                    "title": f"{user} ne aaj {n} fee records delete kiye",
                    "detail": f"Deleted amount: PKR {total_deleted:,.0f}"
                })

        edit_logs = dbs.query(ActivityLog).filter(
            ActivityLog.action == "FEE_EDITED",
            ActivityLog.created_at >= today_start,
            ActivityLog.created_at <= today_end,
        )
        if gym_id:
            edit_logs = edit_logs.filter_by(gym_id=gym_id)
        edit_by = defaultdict(int)
        for lg in edit_logs.all():
            edit_by[lg.user] += 1
        for user, n in edit_by.items():
            if n >= 3:
                alerts.append({
                    "severity": "warning",
                    "icon": "✏️",
                    "title": f"{user} ne aaj {n} baar fee records EDIT kiye",
                    "detail": "Zyada edits amount manipulation ki nishani ho sakti hai."
                })

        off_q = dbs.query(ActivityLog).filter(
            ActivityLog.action == "FEE_COLLECTED",
            ActivityLog.created_at >= today_start,
            ActivityLog.created_at <= today_end,
        )
        if gym_id:
            off_q = off_q.filter_by(gym_id=gym_id)
        off_hours = []
        for lg in off_q.all():
            if lg.created_at:
                h = lg.created_at.hour
                if h < 7 or h >= 22:
                    off_hours.append(lg)
        if off_hours:
            names = list({e.user for e in off_hours})
            alerts.append({
                "severity": "warning",
                "icon": "🌙",
                "title": f"Off-hours fee collection ({len(off_hours)} transactions)",
                "detail": f"Staff: {', '.join(names)} — Normal hours se bahar fees collect ki gayi."
            })

        flagged_shifts = dbs.query(ShiftSession).filter(
            ShiftSession.status == "flagged",
            ShiftSession.closed_at >= today_start,
        )
        if gym_id:
            flagged_shifts = flagged_shifts.filter_by(gym_id=gym_id)
        for s in flagged_shifts.all():
            alerts.append({
                "severity": "critical",
                "icon": "💸",
                "title": f"{s.staff_user} ki shift mein cash short!",
                "detail": f"Expected: PKR {s.expected_cash:,.0f} | Submitted: PKR {s.closing_cash:,.0f} | Short: PKR {abs(s.discrepancy):,.0f}"
            })

        big_del = dbs.query(ActivityLog).filter(
            ActivityLog.action == "FEE_DELETED",
            ActivityLog.amount >= 3000,
            ActivityLog.created_at >= today_start,
            ActivityLog.created_at <= today_end,
        )
        if gym_id:
            big_del = big_del.filter_by(gym_id=gym_id)
        for lg in big_del.all():
            alerts.append({
                "severity": "critical",
                "icon": "💰",
                "title": f"Bara amount delete kiya — PKR {(lg.amount or 0):,.0f}",
                "detail": f"Staff: {lg.user} | Receipt: {lg.record_ref or '—'} | Time: {lg.created_at.strftime('%H:%M') if lg.created_at else '—'}"
            })

        return alerts
    except Exception:
        return []
    finally:
        dbs.close()

# ── Body Measurements ──────────────────────────────────────────────────────────

def add_body_measurement(member_id, recorded_date, weight_kg, chest_cm=None,
                         waist_cm=None, hips_cm=None, bicep_cm=None,
                         body_fat_pct=None, notes=""):
    db = get_db()
    try:
        db.add(BodyMeasurement(
            member_id=member_id,
            recorded_date=str(recorded_date),
            weight_kg=weight_kg,
            chest_cm=chest_cm,
            waist_cm=waist_cm,
            hips_cm=hips_cm,
            bicep_cm=bicep_cm,
            body_fat_pct=body_fat_pct,
            notes=notes,
        ))
        db.commit()
        return True, "Measurements recorded."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_body_measurements(member_id):
    db = get_db()
    try:
        return (db.query(BodyMeasurement)
                .filter_by(member_id=member_id)
                .order_by(BodyMeasurement.recorded_date.asc())
                .all())
    finally:
        db.close()

def delete_body_measurement(measurement_id):
    db = get_db()
    try:
        r = db.query(BodyMeasurement).filter_by(id=measurement_id).first()
        if r:
            db.delete(r)
            db.commit()
        return True, "Deleted."
    finally:
        db.close()

# ── Stock & Inventory ──────────────────────────────────────────────────────────

def add_stock_item(gym_id, item_name, category, purchase_price, sale_price,
                   quantity, min_quantity=5):
    db = get_db()
    try:
        db.add(StockItem(gym_id=gym_id, item_name=item_name.strip(),
                         category=category, purchase_price=purchase_price,
                         sale_price=sale_price, quantity=quantity,
                         min_quantity=min_quantity))
        db.commit()
        return True, "Item added to inventory."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_stock_items(gym_id=None, low_stock_only=False):
    db = get_db()
    try:
        q = db.query(StockItem)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if low_stock_only:
            q = q.filter(StockItem.quantity <= StockItem.min_quantity)
        return q.order_by(StockItem.item_name).all()
    finally:
        db.close()

def update_stock_item(item_id, **kwargs):
    db = get_db()
    try:
        item = db.query(StockItem).filter_by(id=item_id).first()
        if not item:
            return False, "Item not found."
        for k, v in kwargs.items():
            setattr(item, k, v)
        db.commit()
        return True, "Item updated."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def delete_stock_item(item_id):
    db = get_db()
    try:
        item = db.query(StockItem).filter_by(id=item_id).first()
        if item:
            db.delete(item)
            db.commit()
        return True, "Item deleted."
    finally:
        db.close()

def sell_stock_item(stock_item_id, gym_id, member_id, quantity_sold,
                    sale_price, sold_by, sale_date):
    db = get_db()
    try:
        item = db.query(StockItem).filter_by(id=stock_item_id).first()
        if not item:
            return False, "Item not found."
        if item.quantity < quantity_sold:
            return False, f"Insufficient stock. Available: {item.quantity}"
        item.quantity -= quantity_sold
        total = quantity_sold * sale_price
        db.add(StockSale(
            stock_item_id=stock_item_id, gym_id=gym_id, member_id=member_id,
            quantity_sold=quantity_sold, sale_price=sale_price,
            total_amount=total, sold_by=sold_by, sale_date=str(sale_date),
        ))
        db.commit()
        return True, f"Sold {quantity_sold}x {item.item_name} for PKR {total:,.2f}"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_stock_sales(gym_id=None, date_from=None, date_to=None):
    db = get_db()
    try:
        q = db.query(StockSale)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if date_from:
            q = q.filter(StockSale.sale_date >= str(date_from))
        if date_to:
            q = q.filter(StockSale.sale_date <= str(date_to))
        return q.order_by(StockSale.sale_date.desc()).all()
    finally:
        db.close()

# ── Complaints ─────────────────────────────────────────────────────────────────

def add_complaint(gym_id, subject, description, priority, submitted_by, member_id=None):
    db = get_db()
    try:
        db.add(Complaint(
            gym_id=gym_id, member_id=member_id, subject=subject.strip(),
            description=description, priority=priority,
            submitted_by=submitted_by, status="Open",
        ))
        db.commit()
        return True, "Complaint submitted."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_complaints(gym_id=None, status=None):
    db = get_db()
    try:
        q = db.query(Complaint)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        if status and status != "All":
            q = q.filter_by(status=status)
        return q.order_by(Complaint.created_at.desc()).all()
    finally:
        db.close()

def update_complaint_status(complaint_id, status, resolved_by=None):
    db = get_db()
    try:
        c = db.query(Complaint).filter_by(id=complaint_id).first()
        if not c:
            return False, "Complaint not found."
        c.status = status
        if status == "Resolved":
            c.resolved_by = resolved_by
            c.resolved_at = datetime.now()
        db.commit()
        return True, f"Status updated to {status}."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

# ── Analytics helpers ──────────────────────────────────────────────────────────

def get_member_count(gym_id=None):
    db = get_db()
    try:
        q = db.query(Member)
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        return q.count()
    finally:
        db.close()

def get_active_member_count(gym_id=None):
    db = get_db()
    try:
        q = db.query(Member).filter_by(status="Active")
        if gym_id:
            q = q.filter_by(gym_id=gym_id)
        return q.count()
    finally:
        db.close()

def get_expenses_by_category(gym_id=None):
    db = get_db()
    try:
        q = db.query(DailyExpense.category,
                     func.coalesce(func.sum(DailyExpense.amount), 0).label("total"))
        if gym_id:
            q = q.filter(DailyExpense.gym_id == gym_id)
        rows = q.group_by(DailyExpense.category).order_by(func.sum(DailyExpense.amount).desc()).all()
        return [{"category": r.category, "total": float(r.total)} for r in rows]
    finally:
        db.close()

def get_stats(gym_id=None):
    db = get_db()
    try:
        mq = db.query(Member)
        fq = db.query(FeeRecord)
        eq = db.query(DailyExpense)
        if gym_id:
            mq = mq.filter_by(gym_id=gym_id)
            fq = fq.filter_by(gym_id=gym_id)
            eq = eq.filter_by(gym_id=gym_id)
        total_members  = mq.count()
        active_members = mq.filter_by(status="Active").count()
        total_revenue  = db.query(func.coalesce(func.sum(FeeRecord.amount), 0)).filter(
            *([FeeRecord.gym_id == gym_id] if gym_id else [])
        ).scalar()
        total_expenses = db.query(func.coalesce(func.sum(DailyExpense.amount), 0)).filter(
            *([DailyExpense.gym_id == gym_id] if gym_id else [])
        ).scalar()
        today = date.today()
        month_fees = db.query(func.coalesce(func.sum(FeeRecord.amount), 0)).filter(
            FeeRecord.payment_date >= str(today.replace(day=1)),
            *([FeeRecord.gym_id == gym_id] if gym_id else [])
        ).scalar()
        month_exp = db.query(func.coalesce(func.sum(DailyExpense.amount), 0)).filter(
            DailyExpense.expense_date >= str(today.replace(day=1)),
            *([DailyExpense.gym_id == gym_id] if gym_id else [])
        ).scalar()
        inv_rev = db.query(func.coalesce(func.sum(StockSale.total_amount), 0)).filter(
            *([StockSale.gym_id == gym_id] if gym_id else [])
        ).scalar()
        return {
            "total_members":   total_members,
            "active_members":  active_members,
            "total_revenue":   float(total_revenue or 0),
            "total_expenses":  float(total_expenses or 0),
            "month_revenue":   float(month_fees or 0),
            "month_expenses":  float(month_exp or 0),
            "net_profit":      float((total_revenue or 0) - (total_expenses or 0)),
            "inventory_revenue": float(inv_rev or 0),
        }
    finally:
        db.close()

def update_member_photo_path(member_id, photo_path):
    db = SessionLocal()
    try:
        member = db.query(Member).filter(Member.id == member_id).first()
        if member:
            member.photo_path = photo_path
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating member photo path: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def clean_corrupt_html_paths():
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(
                text("UPDATE members SET photo_path = NULL WHERE photo_path LIKE '%<div%' OR photo_path LIKE '%style=%'")
            )
            connection.commit()
            print("✨ Online Database safely cleaned from HTML garbage!")
    except Exception as e:
        print(f"Cleanup update skipped or not needed: {e}")

def is_verified(reference_id):
    try:
        conn = sqlite3.connect("gym-app/gym_pro_v3.db")
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM audit_entries WHERE reference_id = ? AND entry_type = 'fee'", (str(reference_id),))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error in is_verified: {e}")
        return False

# ── Audit & Attendance Helper Functions ──────────────────────────────────────

def is_record_verified(record_id):
    db = get_db()
    try:
        log = db.query(AuditEntry).filter(
            AuditEntry.reference_id == str(record_id), 
            AuditEntry.entry_type == 'fee'
        ).first()
        return log is not None
    except Exception as e:
        print(f"Error checking verification: {e}")
        return False
    finally:
        db.close()

def update_audit_by_member(member_id, new_status):
    db = get_db()
    try:
        entry = db.query(AuditEntry).filter(
            AuditEntry.reference_id == str(member_id), 
            AuditEntry.status == "Discrepancy"
        ).first()
        if entry:
            entry.status = new_status
            db.commit()
    finally:
        db.close()

def get_active_members(gym_id):
    db = get_db()
    try:
        today = str(date.today())
        attended_ids = [a.member_id for a in db.query(Attendance).filter(Attendance.check_date == today).all()]

        members = db.query(Member).filter(
            Member.gym_id == gym_id, 
            Member.status == 'Active',
            ~Member.id.in_(attended_ids)
        ).all()
        return members
    finally:
        db.close()

def mark_member_present(member_id, gym_id, attendance_date):
    db = get_db()
    try:
        new_attendance = Attendance(
            member_id=member_id, 
            gym_id=gym_id, 
            check_date=str(attendance_date), 
            status="Present",
            marked_by="Auditor"
        )
        db.add(new_attendance)
        db.commit()
        return True, "Success"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_audit_status(entry_id, new_status):
    db = get_db()
    try:
        entry = db.query(AuditEntry).filter_by(id=entry_id).first()
        if entry:
            entry.status = new_status
            db.commit()
    finally:
        db.close()

def get_member_by_id(member_id):
    db = get_db()
    try:
        m_id = int(member_id)
        return db.query(Member).filter(Member.id == m_id).first() 
    except (ValueError, TypeError):
        return None
    finally:
        db.close()

def get_member_phone(name):
    db = get_db()
    try:
        member = db.query(Member).filter(Member.full_name == name).first()
        return member.phone if member else None
    except Exception as e:
        print(f"Error finding phone: {e}")
        return None
    finally:
        db.close()

def get_todays_fees(gym_id):
    db = get_db()
    try:
        today_str = date.today().isoformat()
        results = db.query(FeeRecord.amount).filter(
            FeeRecord.gym_id == gym_id,
            FeeRecord.payment_date == today_str
        ).all()
        return [r[0] for r in results]
    except Exception as e:
        print(f"DEBUG Error in get_todays_fees: {e}")
        return []
    finally:
        db.close()

# ============================================
# STAFF TARGET SYSTEM
# ============================================

class StaffTarget(Base):
    __tablename__ = "staff_targets"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    staff_username = Column(String(60), nullable=False)
    
    new_members_target = Column(Float, default=0.0)
    new_members_achieved = Column(Float, default=0.0)
    fee_collection_target = Column(Float, default=0.0)
    fee_collection_achieved = Column(Float, default=0.0)
    attendance_target_percentage = Column(Float, default=80.0)
    attendance_achieved = Column(Float, default=0.0)
    
    total_score = Column(Float, default=0.0)
    prize_amount = Column(Float, default=0.0)
    prize_status = Column(String(20), default="Pending")
    
    target_month = Column(String(7), nullable=False)
    status = Column(String(20), default="Active")
    created_by = Column(String(60))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    gym = relationship("Gym", back_populates="staff_targets")

def add_staff_target(gym_id, staff_username, new_members_target, fee_collection_target, 
                     attendance_target_percentage, target_month, created_by, prize_amount=0):
    db = get_db()
    try:
        existing = db.query(StaffTarget).filter(
            StaffTarget.gym_id == gym_id,
            StaffTarget.staff_username == staff_username,
            StaffTarget.target_month == target_month
        ).first()
        
        if existing:
            return False, f"Target already exists for {staff_username} this month"
        
        target = StaffTarget(
            gym_id=gym_id,
            staff_username=staff_username,
            new_members_target=new_members_target,
            fee_collection_target=fee_collection_target,
            attendance_target_percentage=attendance_target_percentage,
            target_month=target_month,
            created_by=created_by,
            prize_amount=prize_amount,
            status="Active"
        )
        db.add(target)
        db.commit()
        return True, "Targets added successfully"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_staff_targets(gym_id=None, staff_username=None, target_month=None):
    db = get_db()
    try:
        query = db.query(StaffTarget)
        if gym_id:
            query = query.filter(StaffTarget.gym_id == gym_id)
        if staff_username:
            query = query.filter(StaffTarget.staff_username == staff_username)
        if target_month:
            query = query.filter(StaffTarget.target_month == target_month)
        return query.order_by(StaffTarget.created_at.desc()).all()
    finally:
        db.close()

def get_all_staff_targets(gym_id=None, target_month=None):
    db = get_db()
    try:
        query = db.query(StaffTarget)
        if gym_id:
            query = query.filter(StaffTarget.gym_id == gym_id)
        if target_month:
            query = query.filter(StaffTarget.target_month == target_month)
        return query.order_by(StaffTarget.created_at.desc()).all()
    finally:
        db.close()

def get_staff_target(staff_username, target_month=None):
    if not target_month:
        target_month = date.today().strftime("%Y-%m")
    
    db = get_db()
    try:
        target = db.query(StaffTarget).filter(
            StaffTarget.staff_username == staff_username,
            StaffTarget.target_month == target_month
        ).first()
        
        if not target:
            return None
        
        total_members = db.query(Member).filter_by(gym_id=target.gym_id, status="Active").count()
        attendance_target_count = (target.attendance_target_percentage / 100) * total_members if total_members > 0 else 0
        
        new_members_pct = (target.new_members_achieved / target.new_members_target * 100) if target.new_members_target > 0 else 0
        fee_pct = (target.fee_collection_achieved / target.fee_collection_target * 100) if target.fee_collection_target > 0 else 0
        attendance_pct = (target.attendance_achieved / attendance_target_count * 100) if attendance_target_count > 0 else 0
        
        overall_pct = (new_members_pct + fee_pct + attendance_pct) / 3
        
        return {
            'target': target,
            'total_members': total_members,
            'attendance_target_percentage': target.attendance_target_percentage,
            'attendance_target_count': attendance_target_count,
            'new_members': {'target': target.new_members_target, 'achieved': target.new_members_achieved, 'percentage': min(100, new_members_pct)},
            'fee_collection': {'target': target.fee_collection_target, 'achieved': target.fee_collection_achieved, 'percentage': min(100, fee_pct)},
            'attendance': {'target': attendance_target_count, 'achieved': target.attendance_achieved, 'percentage': min(100, attendance_pct)},
            'overall': min(100, overall_pct),
            'total_score': target.total_score,
            'prize_amount': target.prize_amount,
            'prize_status': target.prize_status,
            'status': target.status,
        }
    finally:
        db.close()

def update_staff_achievements(staff_username, target_month=None):
    if not target_month:
        target_month = date.today().strftime("%Y-%m")
    
    db_session = get_db()
    try:
        target = db_session.query(StaffTarget).filter(
            StaffTarget.staff_username == staff_username,
            StaffTarget.target_month == target_month,
            StaffTarget.status == "Active"
        ).first()
        
        if not target:
            return False, "No active target found"
        
        gym_id = target.gym_id
        members_this_month = db_session.query(Member).filter(
            Member.gym_id == gym_id,
            func.strftime("%Y-%m", Member.created_at) == target_month
        ).count()
        target.new_members_achieved = members_this_month
        
        fees_this_month = db_session.query(func.sum(FeeRecord.amount)).filter(
            FeeRecord.gym_id == gym_id,
            FeeRecord.collected_by == staff_username,
            func.strftime("%Y-%m", FeeRecord.created_at) == target_month
        ).scalar() or 0
        target.fee_collection_achieved = fees_this_month
        
        total_members = db_session.query(Member).filter_by(gym_id=gym_id, status="Active").count()
        attendance_target_count = (target.attendance_target_percentage / 100) * total_members if total_members > 0 else 0
        
        attendance_marked = db_session.query(Attendance).filter(
            Attendance.gym_id == gym_id,
            Attendance.marked_by == staff_username,
            func.strftime("%Y-%m", Attendance.check_date) == target_month,
            Attendance.status == "Present"
        ).count()
        target.attendance_achieved = attendance_marked
        
        new_pct = (target.new_members_achieved / target.new_members_target * 100) if target.new_members_target > 0 else 0
        fee_pct = (target.fee_collection_achieved / target.fee_collection_target * 100) if target.fee_collection_target > 0 else 0
        att_pct = (target.attendance_achieved / attendance_target_count * 100) if attendance_target_count > 0 else 0
        
        target.total_score = (new_pct + fee_pct + att_pct) / 3
        
        if (target.new_members_achieved >= target.new_members_target and
            target.fee_collection_achieved >= target.fee_collection_target and
            target.attendance_achieved >= attendance_target_count and
            target.new_members_target > 0 and target.fee_collection_target > 0 and attendance_target_count > 0):
            target.status = "Completed"
            target.prize_status = "Awarded"
        
        db_session.commit()
        return True, "Achievements updated"
        
    except Exception as e:
        db_session.rollback()
        return False, str(e)
    finally:
        db_session.close()

def get_all_staff_progress(gym_id=None, target_month=None):
    if not target_month:
        target_month = date.today().strftime("%Y-%m")
    
    all_users = get_all_users()
    if gym_id:
        all_users = [u for u in all_users if u.gym_id == gym_id]
    
    results = []
    for user in all_users:
        if user.role.lower() == "admin":
            continue
        progress = get_staff_target(user.username, target_month)
        
        if progress:
            results.append({
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'progress': progress,
                'is_active': user.is_active
            })
        else:
            results.append({
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'progress': None,
                'is_active': user.is_active
            })
    
    return results

def delete_staff_target(target_id):
    db = get_db()
    try:
        target = db.query(StaffTarget).filter(StaffTarget.id == target_id).first()
        if target:
            db.delete(target)
            db.commit()
            return True, "Target deleted"
        return False, "Target not found"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_staff_progress(staff_username, target_month=None):
    if not target_month:
        target_month = date.today().strftime("%Y-%m")
    
    db_session = get_db()
    try:
        target = db_session.query(StaffTarget).filter(
            StaffTarget.staff_username == staff_username,
            StaffTarget.target_month == target_month
        ).first()
        
        progress = {
            'new_members': {'target': 0, 'achieved': 0, 'percentage': 0},
            'fee_collection': {'target': 0, 'achieved': 0, 'percentage': 0},
            'attendance': {'target': 0, 'achieved': 0, 'percentage': 0},
            'overall': 0,
            'total_targets': 0,
            'completed_targets': 0,
            'prize_amount': 0,
            'prize_status': 'Pending',
            'status': 'Active',
            'attendance_target_percentage': 80,
            'attendance_target_count': 0,
            'total_members': 0,
        }
        
        if target:
            progress['new_members']['target'] = target.new_members_target or 0
            progress['new_members']['achieved'] = target.new_members_achieved or 0
            if target.new_members_target > 0:
                progress['new_members']['percentage'] = min(100, (target.new_members_achieved / target.new_members_target) * 100)
            
            progress['fee_collection']['target'] = target.fee_collection_target or 0
            progress['fee_collection']['achieved'] = target.fee_collection_achieved or 0
            if target.fee_collection_target > 0:
                progress['fee_collection']['percentage'] = min(100, (target.fee_collection_achieved / target.fee_collection_target) * 100)
            
            progress['attendance_target_percentage'] = target.attendance_target_percentage or 80
            progress['attendance']['achieved'] = target.attendance_achieved or 0
            
            total_members = db_session.query(Member).filter_by(gym_id=target.gym_id, status="Active").count()
            progress['total_members'] = total_members
            attendance_target_count = (target.attendance_target_percentage / 100) * total_members if total_members > 0 else 0
            progress['attendance']['target'] = attendance_target_count
            progress['attendance_target_count'] = attendance_target_count
            
            if attendance_target_count > 0:
                progress['attendance']['percentage'] = min(100, (target.attendance_achieved / attendance_target_count) * 100)
            
            progress['total_targets'] = 3
            if target.status == "Completed":
                progress['completed_targets'] = 3
            
            progress['prize_amount'] = target.prize_amount or 0
            progress['prize_status'] = target.prize_status or 'Pending'
            progress['status'] = target.status or 'Active'
            
            total_pct = progress['new_members']['percentage'] + progress['fee_collection']['percentage'] + progress['attendance']['percentage']
            progress['overall'] = total_pct / 3
        
        return progress
    finally:
        db_session.close()

# ============================================
# ANNOUNCEMENT SYSTEM
# ============================================

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=True)
    message = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(60))
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)

    gym = relationship("Gym", back_populates="announcements")

def add_announcement(gym_id, message, created_by, expires_at=None):
    db = get_db()
    try:
        db.query(Announcement).filter(
            Announcement.gym_id == gym_id,
            Announcement.is_active == True
        ).update({Announcement.is_active: False})
        
        announcement = Announcement(
            gym_id=gym_id,
            message=message,
            created_by=created_by,
            expires_at=expires_at,
            is_active=True
        )
        db.add(announcement)
        db.commit()
        return True, "Announcement added successfully"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_active_announcement(gym_id=None):
    db = get_db()
    try:
        query = db.query(Announcement).filter(
            Announcement.is_active == True
        )
        if gym_id:
            query = query.filter(Announcement.gym_id == gym_id)
        else:
            query = query.filter(Announcement.gym_id == None)
        
        now = datetime.now()
        query = query.filter(
            (Announcement.expires_at == None) | (Announcement.expires_at > now)
        )
        
        return query.order_by(Announcement.created_at.desc()).first()
    finally:
        db.close()

def get_all_announcements(gym_id=None):
    db = get_db()
    try:
        query = db.query(Announcement)
        if gym_id:
            query = query.filter(Announcement.gym_id == gym_id)
        return query.order_by(Announcement.created_at.desc()).all()
    finally:
        db.close()

def delete_announcement(announcement_id):
    db = get_db()
    try:
        announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if announcement:
            db.delete(announcement)
            db.commit()
            return True, "Announcement deleted"
        return False, "Announcement not found"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

# ============================================
# STAFF ATTENDANCE TRACKING
# ============================================

class StaffAttendance(Base):
    __tablename__ = "staff_attendance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_username = Column(String(60), nullable=False)
    login_time = Column(DateTime, nullable=False)
    logout_time = Column(DateTime, nullable=True)
    session_duration = Column(Integer, default=0)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.now)

def log_staff_login(staff_username, ip_address=None):
    db = get_db()
    try:
        today = date.today()
        existing = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            func.date(StaffAttendance.login_time) == today,
            StaffAttendance.logout_time == None
        ).first()
        
        if existing:
            return False, "Staff already logged in today"
        
        attendance = StaffAttendance(
            staff_username=staff_username,
            login_time=datetime.now(),
            ip_address=ip_address
        )
        db.add(attendance)
        db.commit()
        return True, "Login recorded"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def log_staff_logout(staff_username):
    db = get_db()
    try:
        today = date.today()
        record = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            func.date(StaffAttendance.login_time) == today,
            StaffAttendance.logout_time == None
        ).order_by(StaffAttendance.login_time.desc()).first()
        
        if not record:
            return False, "No active session found"
        
        record.logout_time = datetime.now()
        duration = (record.logout_time - record.login_time).seconds // 60
        record.session_duration = duration
        db.commit()
        return True, f"Logout recorded (Duration: {duration} minutes)"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_staff_attendance(staff_username=None, date_from=None, date_to=None):
    db = get_db()
    try:
        query = db.query(StaffAttendance)
        if staff_username:
            query = query.filter(StaffAttendance.staff_username == staff_username)
        if date_from:
            query = query.filter(StaffAttendance.login_time >= date_from)
        if date_to:
            query = query.filter(StaffAttendance.login_time <= date_to)
        return query.order_by(StaffAttendance.login_time.desc()).all()
    finally:
        db.close()

def get_staff_attendance_summary(gym_id=None, date_range=30):
    check_and_update_staff_status()
    
    db = get_db()
    try:
        staff_list = db.query(User).filter(User.role != "admin")
        if gym_id:
            staff_list = staff_list.filter(User.gym_id == gym_id)
        staff_list = staff_list.all()
        
        today = date.today()
        date_from = today - timedelta(days=date_range)
        
        results = []
        for staff in staff_list:
            logins = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff.username,
                StaffAttendance.login_time >= date_from
            ).count()
            
            today_record = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff.username,
                func.date(StaffAttendance.login_time) == today,
                StaffAttendance.logout_time == None
            ).first()
            
            status = "🟢 Online" if today_record else "⚪ Offline"
            
            month_start = today.replace(day=1)
            month_records = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff.username,
                StaffAttendance.login_time >= month_start,
                StaffAttendance.logout_time != None
            ).all()
            
            total_minutes = sum(r.session_duration or 0 for r in month_records)
            total_hours = total_minutes // 60
            
            results.append({
                'username': staff.username,
                'full_name': staff.full_name,
                'role': staff.role,
                'logins': logins,
                'status': status,
                'total_hours': total_hours,
                'today_status': "✅ Logged In" if today_record else "⏳ Not Logged In"
            })
        
        return results
    finally:
        db.close()

def get_my_attendance_summary(staff_username):
    db = get_db()
    try:
        today = date.today()
        now = datetime.now()
        timeout = timedelta(hours=2)
        
        active = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            func.date(StaffAttendance.login_time) == today,
            StaffAttendance.logout_time == None
        ).first()
        
        if active and (now - active.login_time) > timeout:
            active.logout_time = now
            active.session_duration = (active.logout_time - active.login_time).seconds // 60
            db.commit()
        
        month_start = today.replace(day=1)
        
        today_record = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            func.date(StaffAttendance.login_time) == today
        ).first()
        
        month_records = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            StaffAttendance.login_time >= month_start
        ).all()
        
        total_days = len(month_records)
        total_minutes = sum(r.session_duration or 0 for r in month_records)
        total_hours = total_minutes // 60
        
        week_start = today - timedelta(days=7)
        week_records = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            StaffAttendance.login_time >= week_start
        ).all()
        
        return {
            'today_status': "✅ Logged In" if today_record and today_record.logout_time is None else "⏳ Not Logged In",
            'today_login': today_record.login_time.strftime('%I:%M %p') if today_record else None,
            'total_days': total_days,
            'total_hours': total_hours,
            'week_days': len(week_records),
            'current_streak': _get_attendance_streak(staff_username)
        }
    finally:
        db.close()

def _get_attendance_streak(staff_username):
    db = get_db()
    try:
        streak = 0
        check_date = date.today()
        
        for _ in range(365):
            record = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff_username,
                func.date(StaffAttendance.login_time) == check_date
            ).first()
            
            if record:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return streak
    finally:
        db.close()

def check_and_update_staff_status():
    db = get_db()
    try:
        today = date.today()
        now = datetime.now()
        timeout = timedelta(hours=2)
        
        active_sessions = db.query(StaffAttendance).filter(
            func.date(StaffAttendance.login_time) == today,
            StaffAttendance.logout_time == None
        ).all()
        
        updated_count = 0
        for session in active_sessions:
            if (now - session.login_time) > timeout:
                session.logout_time = now
                session.session_duration = (session.logout_time - session.login_time).seconds // 60
                updated_count += 1
        
        db.commit()
        return updated_count
    except Exception as e:
        db.rollback()
        return 0
    finally:
        db.close()

# ============================================
# GYM MEMBERSHIP PLANS FUNCTIONS
# ============================================

def add_membership_plan(gym_id, name, price, duration_days, features):
    db = get_db()
    try:
        existing = db.query(MembershipPlan).filter(
            MembershipPlan.gym_id == gym_id,
            MembershipPlan.name == name,
            MembershipPlan.is_active == 1
        ).first()
        
        if existing:
            return False, "A plan with this name already exists"
        
        plan = MembershipPlan(
            gym_id=gym_id,
            name=name,
            price=price,
            duration_days=duration_days,
            features=features,
            is_active=1
        )
        db.add(plan)
        db.commit()
        return True, "Plan added successfully!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_gym_plans(gym_id):
    db = get_db()
    try:
        return db.query(MembershipPlan).filter(
            MembershipPlan.gym_id == gym_id,
            MembershipPlan.is_active == 1
        ).order_by(MembershipPlan.price).all()
    finally:
        db.close()

def delete_plan(plan_id):
    db = get_db()
    try:
        plan = db.query(MembershipPlan).filter_by(id=plan_id).first()
        if plan:
            plan.is_active = 0
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def update_plan(plan_id, name, price, duration_days, features):
    db = get_db()
    try:
        plan = db.query(MembershipPlan).filter_by(id=plan_id).first()
        if plan:
            plan.name = name
            plan.price = price
            plan.duration_days = duration_days
            plan.features = features
            db.commit()
            return True, "Plan updated successfully!"
        return False, "Plan not found"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

# ============================================
# GYM PHOTOS FUNCTIONS
# ============================================

def save_gym_photo(gym_id, filepath):
    db = get_db()
    try:
        existing = db.query(GymPhoto).filter_by(gym_id=gym_id).count()
        
        photo = GymPhoto(
            gym_id=gym_id,
            path=filepath,
            is_primary=1 if existing == 0 else 0
        )
        db.add(photo)
        db.commit()
        return True, "Photo saved successfully!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_gym_photos(gym_id):
    db = get_db()
    try:
        return db.query(GymPhoto).filter_by(gym_id=gym_id).order_by(
            GymPhoto.is_primary.desc(), GymPhoto.uploaded_at.desc()
        ).all()
    finally:
        db.close()

def delete_gym_photo(photo_id):
    db = get_db()
    try:
        photo = db.query(GymPhoto).filter_by(id=photo_id).first()
        if photo:
            if os.path.exists(photo.path):
                try:
                    os.remove(photo.path)
                except:
                    pass
            db.delete(photo)
            db.commit()
        return True, "Photo deleted"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def set_primary_photo(photo_id):
    db = get_db()
    try:
        photo = db.query(GymPhoto).filter_by(id=photo_id).first()
        if photo:
            db.query(GymPhoto).filter_by(gym_id=photo.gym_id).update({"is_primary": 0})
            photo.is_primary = 1
            db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

# ============================================
# GYM TIMINGS FUNCTIONS
# ============================================

def update_gym_timings(gym_id, mon_fri_start, mon_fri_end, sat_start, sat_end, sun_start, sun_end):
    db = get_db()
    try:
        gym = db.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return False, "Gym not found"
        
        gym.mon_fri_start = mon_fri_start
        gym.mon_fri_end = mon_fri_end
        gym.sat_start = sat_start
        gym.sat_end = sat_end
        gym.sun_start = sun_start
        gym.sun_end = sun_end
        db.commit()
        return True, "Timings updated successfully!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_gym_amenities(gym_id, amenities):
    db = get_db()
    try:
        gym = db.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return False, "Gym not found"
        
        gym.amenities = amenities
        db.commit()
        return True, "Amenities updated successfully!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_gym_info(gym_id, description, website, social_media, bank_account, tax_id):
    db = get_db()
    try:
        gym = db.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return False, "Gym not found"
        
        gym.description = description
        gym.website = website
        gym.social_media = social_media
        gym.bank_account = bank_account
        gym.tax_id = tax_id
        db.commit()
        return True, "Information updated successfully!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_gym_status(gym_id, status):
    db = get_db()
    try:
        gym = db.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return False, "Gym not found"
        
        gym.status = status
        db.commit()
        return True, f"Status updated to {status}!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_gym_settings(gym_id, max_members, checkin_required, reminder_days, allow_online_payments):
    db = get_db()
    try:
        gym = db.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return False, "Gym not found"
        
        gym.max_members = max_members
        gym.checkin_required = 1 if checkin_required else 0
        gym.reminder_days = reminder_days
        gym.allow_online_payments = 1 if allow_online_payments else 0
        db.commit()
        return True, "Settings updated successfully!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def add_gym_columns():
    db = get_db()
    try:
        from sqlalchemy import inspect, text
        
        inspector = inspect(engine)
        
        if 'gyms' not in inspector.get_table_names():
            return
        
        columns = [c['name'] for c in inspector.get_columns('gyms')]
        
        new_columns = {
            'next_serial': 'INTEGER DEFAULT 1',
            'description': 'TEXT',
            'website': 'VARCHAR(255)',
            'social_media': 'VARCHAR(255)',
            'bank_account': 'VARCHAR(255)',
            'tax_id': 'VARCHAR(100)',
            'status': "VARCHAR(20) DEFAULT 'active'",
            'max_members': 'INTEGER DEFAULT 0',
            'checkin_required': 'INTEGER DEFAULT 0',
            'reminder_days': 'INTEGER DEFAULT 7',
            'allow_online_payments': 'INTEGER DEFAULT 0',
            'mon_fri_start': 'VARCHAR(10)',
            'mon_fri_end': 'VARCHAR(10)',
            'sat_start': 'VARCHAR(10)',
            'sat_end': 'VARCHAR(10)',
            'sun_start': 'VARCHAR(10)',
            'sun_end': 'VARCHAR(10)',
            'amenities': 'TEXT',
            'currency': "VARCHAR(10) DEFAULT 'PKR'",
            'timezone': "VARCHAR(50) DEFAULT 'Asia/Karachi'",
            'logo_path': 'TEXT',
            'facebook': 'VARCHAR(255)',
            'instagram': 'VARCHAR(255)',
            'youtube': 'VARCHAR(255)',
            'twitter': 'VARCHAR(255)',
            'linkedin': 'VARCHAR(255)',
            'bank_name': 'VARCHAR(255)',
            'account_title': 'VARCHAR(255)',
            'account_number': 'VARCHAR(100)',
            'iban': 'VARCHAR(100)',
            'rules': 'TEXT',
            'expense_categories': 'TEXT',
            'holiday_mode': 'INTEGER DEFAULT 0'
        }
        
        for col, col_type in new_columns.items():
            if col not in columns:
                try:
                    if IS_POSTGRES:
                        db.execute(text(f'ALTER TABLE gyms ADD COLUMN {col} {col_type}'))
                    else:
                        db.execute(text(f'ALTER TABLE gyms ADD COLUMN {col} {col_type}'))
                    print(f"✅ Added column: {col}")
                except Exception as e:
                    print(f"⚠️ Could not add {col}: {e}")
        
        db.commit()
    except Exception as e:
        print(f"⚠️ Column migration error: {e}")
        db.rollback()
    finally:
        db.close()

def get_member_by_id(member_id):
    db = get_db()
    try:
        return db.query(Member).filter_by(id=member_id).first()
    finally:
        db.close()

# ── STAFF TIMINGS TABLE ─────────────────────────────────────────────

class StaffTiming(Base):
    __tablename__ = "staff_timings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    staff_username = Column(String(60), nullable=False, unique=True)
    check_in_time = Column(String(10), nullable=False)
    check_out_time = Column(String(10), nullable=False)
    grace_minutes = Column(Integer, default=15)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    gym = relationship("Gym", back_populates="staff_timings")

def get_staff_timing(staff_username: str) -> dict | None:
    db = get_db()
    try:
        timing = db.query(StaffTiming).filter_by(staff_username=staff_username).first()
        if timing:
            return {
                "check_in_time": timing.check_in_time,
                "check_out_time": timing.check_out_time,
                "grace_minutes": timing.grace_minutes,
                "gym_id": timing.gym_id
            }
        return None
    finally:
        db.close()

def set_staff_timing(gym_id: int, staff_username: str, check_in_time: str, check_out_time: str, grace_minutes: int = 15):
    db = get_db()
    try:
        existing = db.query(StaffTiming).filter_by(staff_username=staff_username).first()
        if existing:
            existing.check_in_time = check_in_time
            existing.check_out_time = check_out_time
            existing.grace_minutes = grace_minutes
            existing.gym_id = gym_id
        else:
            timing = StaffTiming(
                gym_id=gym_id,
                staff_username=staff_username,
                check_in_time=check_in_time,
                check_out_time=check_out_time,
                grace_minutes=grace_minutes
            )
            db.add(timing)
        db.commit()
        return True, "Staff timing updated successfully!"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def get_all_staff_timings(gym_id: int):
    db = get_db()
    try:
        return db.query(StaffTiming).filter_by(gym_id=gym_id).all()
    finally:
        db.close()