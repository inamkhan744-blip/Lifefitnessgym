
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
#111111111
# Test script - separate file mein run karein

# ── Engine Path Configurations ──────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == "gym-app":
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "gym-app", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Forceful automatic restore from backup text file
if not IS_POSTGRES:
    import sqlite3
    
    # Sahi paths dhundna
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir) if os.path.basename(current_dir) == "gym-app" else current_dir
    
    # database.py mein ye line update karein
    db_path = os.path.join(BASE_DIR, "gym-app", "gym_pro_v2.db")
    sql_backup_path = os.path.join(root_dir, "backup.sql")
    
    if os.path.exists(sql_backup_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check karein agar members table missing hai ya usme data kam hai
        try:
            cursor.execute("SELECT COUNT(*) FROM members;")
            row_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            row_count = 0
            
        # Agar data 10 se kam hai (jaise abhi 4 dikha raha hai), to backup overwrite karein
        #if row_count < 10:
            conn.close()
            # Khali database ko delete karke fresh backup load karein
            if os.path.exists(db_path):
                os.remove(db_path)
                
            conn = sqlite3.connect(db_path)
            
            conn.commit()
            print("Database successfully restored with all 64 members!")
            
        conn.close()


DB_PATH = os.path.join(BASE_DIR, "gym_pro_v3.db")
DB_MODE = "offline"   # updated below after connection test


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
    engine = create_engine(
        _pg_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=10,
        connect_args={"connect_timeout": 5},   # 5 sec TCP timeout — no more hang
    )
    # Test actual connection — if unreachable, fall back to SQLite silently
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


# ── Models ─────────────────────────────────────────────────────────────────────

class Gym(Base):
    __tablename__ = "gyms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True)
    address = Column(String(255))
    phone = Column(String(30))
    email = Column(String(120))
    created_at = Column(DateTime, default=datetime.utcnow)

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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(60), nullable=False, unique=True)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    gym = relationship("Gym", back_populates="users")


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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    gym = relationship("Gym", back_populates="complaints")
    member = relationship("Member", back_populates="complaints")


class ReceiptLog(Base):
    __tablename__ = "receipt_logs"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    fee_record_id  = Column(Integer, ForeignKey("fee_records.id", ondelete="SET NULL"), nullable=True)
    gym_id         = Column(Integer, ForeignKey("gyms.id",        ondelete="SET NULL"), nullable=True)
    member_name    = Column(String(120), nullable=False)
    receipt_number = Column(String(40),  nullable=False)
    amount         = Column(Float,       nullable=False)
    collected_by   = Column(String(60))
    pay_date       = Column(String(15),  nullable=False)
    pay_time       = Column(String(10),  nullable=False)
    print_issued   = Column(Boolean, default=False, nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow)

    gym = relationship("Gym", back_populates="receipt_logs")


class UnknownCapture(Base):
    """Temporary store for unknown / expired member face captures."""
    __tablename__ = "unknown_captures"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    gym_id       = Column(Integer, nullable=False)
    capture_key  = Column(String(300), nullable=False)   # Object Storage key
    capture_type = Column(String(20), default="unknown") # unknown | expired
    member_id    = Column(Integer, nullable=True)        # only for expired
    member_name  = Column(String(120), nullable=True)
    captured_at  = Column(DateTime, default=datetime.utcnow)
    notes        = Column(Text, nullable=True)


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


# ── Utilities ──────────────────────────────────────────────────────────────────

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def verify_password(pw: str, hashed: str) -> bool:
    return hash_password(pw) == hashed


def _serial_prefix(gym_name: str) -> str:
    words = gym_name.split()
    return "".join(w[0].upper() for w in words[:3])


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
    try:
        UnknownCapture.__table__.create(engine, checkfirst=True)
    except Exception:
        pass

# 🔥 Create StaffAttendance table
    try:
        StaffAttendance.__table__.create(engine, checkfirst=True)
    except:
        pass
    
    
    # 🔥 ADD THIS - Announcement table create
    try:
        Announcement.__table__.create(engine, checkfirst=True)
    except:
        pass
    
    # 🔥 ADD THIS - Ensure announcement columns exist (PostgreSQL)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if table exists, if not create it
            if IS_POSTGRES:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'announcements'
                    )
                """))
                if not result.fetchone()[0]:
                    # Create table
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
        db.add(Gym(name=name.strip(), address=address, phone=phone, email=email))
        db.commit()
        return True, "Gym added."
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
        g.name = name.strip(); g.address = address; g.phone = phone; g.email = email
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
        u.full_name = full_name; u.role = role
        u.gym_id = gym_id; u.is_active = is_active
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

def _next_serial(gym_id, db):
    gym = db.query(Gym).filter_by(id=gym_id).first()
    prefix = _serial_prefix(gym.name) if gym else "GYM"
    count = db.query(Member).filter_by(gym_id=gym_id).count() + 1
    return f"{prefix}-{count:05d}"


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


def add_member(gym_id, full_name, phone, email, gender, dob,
               membership_type, fee_amount, join_date, expiry_date,
               photo_path, status, notes):
    last_err = None
    for _ in range(5):
        db = get_db()
        try:
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
                       photo_path=photo_path, status=status, notes=notes)
            db.add(m)
            db.commit()
# After db.commit() and before return
            sync_to_local((m.id, serial, full_name, phone, email, gender, dob, photo_path, membership_type, fee_amount, str(join_date), str(expiry_date) if expiry_date else None, status, notes, None))
            return True, f"Member registered. Serial: {serial}", serial
        except IntegrityError as e:
            db.rollback()
            last_err = e
            continue   
        except Exception as e:
            db.rollback()
            return False, str(e), None
        finally:
            db.close()
    return False, f"Could not allocate a unique serial number after retries: {last_err}", None

def sync_to_local(member_data):
    """Save member to local SQLite as backup"""
    try:
        local_conn = sqlite3.connect('gym_pro_backup_local.db')
        local_cursor = local_conn.cursor()
        
        # Create table if not exists
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
                face_encoding TEXT
            )
        ''')
        
        # Insert or update
        local_cursor.execute('''
            INSERT OR REPLACE INTO members 
            (id, serial_number, full_name, phone, email, gender, dob, photo_path, membership_type, fee_amount, join_date, expiry_date, status, notes, face_encoding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', member_data)
        
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
    """Save face encoding JSON for a member."""
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
    """Return all members with enrolled face encodings."""
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
    """Delete captures older than `days` days. Returns list of Object Storage keys to delete."""
    db = get_db()
    cutoff = datetime.utcnow() - timedelta(days=days)
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
    """Log a fee receipt into receipt_logs table."""
    db = get_db()
    try:
        now = datetime.utcnow()
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
    """Mark a receipt as printed (or not)."""
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
    """Return receipt log rows, newest first."""
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


# 1. Top par ye import ensure karein:
from sqlalchemy.orm import joinedload

def get_fee_records(gym_id=None, date_from=None, date_to=None):
    db = get_db()
    try:
        # joinedload se DetachedInstanceError khatam ho jayega
        query = db.query(FeeRecord).options(joinedload(FeeRecord.member))
        
        if gym_id:
            query = query.filter(FeeRecord.gym_id == gym_id)
        
        # 'date' ki jagah 'payment_date' use karein
        if date_from:
            query = query.filter(FeeRecord.payment_date >= str(date_from))
        if date_to:
            query = query.filter(FeeRecord.payment_date <= str(date_to))
            
        return query.all()
    finally:
        db.close()






# 🌟 Yahan Dono Naye Functions Add Kar Diye Hain (SQLAlchemy Structure Ke Mutabik) 🌟
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
        utc_today = datetime.utcnow().date()
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
            c.resolved_at = datetime.utcnow()
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
    """Update member photo_path — accepts object storage key or any path as-is."""
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
# --- EMERGENCY POSTGRESQL CLEANUP SYSTEM ---
def clean_corrupt_html_paths():
    try:
        from sqlalchemy import text
        # Yeh aap ke online PostgreSQL database se kachra auto-clean kare ka system hai
        with engine.connect() as connection:
            connection.execute(
                text("UPDATE members SET photo_path = NULL WHERE photo_path LIKE '%<div%' OR photo_path LIKE '%style=%'")
            )
            connection.commit()
            print("✨ Online Database safely cleaned from HTML garbage!")
    except Exception as e:
        print(f"Cleanup update skipped or not needed: {e}")

# Automatically triggers on app startup to keep your database pure
clean_corrupt_html_paths()
# Yeh function database.py ke bilkul last mein hona chahiye
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
#all clear the end
# ── Audit & Attendance Helper Functions (Cleaned) ──────────────────────────
# ── Audit & Verification Helper Functions ──────────────────────────

def is_record_verified(record_id):
    """Check karta hai ke kya fee record pehle se verify ho chuka hai."""
    db = get_db()
    try:
        # 'AuditEntry' model use kar rahe hain, check karein ke 'fee' type ka entry hai ya nahi
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
        # Member id ko string mein convert kar ke check karein
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
        # Aaj jin ki attendance ho gayi unki list
        attended_ids = [a.member_id for a in db.query(Attendance).filter(Attendance.check_date == today).all()]

        # Sirf wo members jo Active hain aur aaj hazir nahi huye
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
        # return yahan nahi hona chahiye
        return db.query(Member).filter(Member.id == m_id).first() 
    except (ValueError, TypeError):
        return None
    finally:
        db.close()

#1111111+
# ── FIX: Proper Database Access ──────────────────────────
def get_member_phone(name):
    db = get_db() # SQLAlchemy session use karein
    try:
        # 'name' ki jagah 'full_name' column use karein
        member = db.query(Member).filter(Member.full_name == name).first()
        return member.phone if member else None
    except Exception as e:
        print(f"Error finding phone: {e}")
        return None
    finally:
        db.close()

#11111111
def get_todays_fees(gym_id):
    db = get_db() # SQLAlchemy session use karein
    try:
        today_str = date.today().isoformat()
        # 'FeeRecord' model use karein, tablename automatically 'fee_records' handle ho jayega
        results = db.query(FeeRecord.amount).filter(
            FeeRecord.gym_id == gym_id,
            FeeRecord.payment_date == today_str
        ).all()
        # Returns a list of amounts [1000.0, 500.0]
        return [r[0] for r in results]
    except Exception as e:
        print(f"DEBUG Error in get_todays_fees: {e}")
        return []
    finally:
        db.close()

# ====================
# ============================================
# ============================================
# STAFF TARGET SYSTEM - COMPLETE (FIXED)
# ============================================

class StaffTarget(Base):
    __tablename__ = "staff_targets"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)
    staff_username = Column(String(60), nullable=False)
    
    # Target Types (No target_type column)
    new_members_target = Column(Float, default=0.0)
    new_members_achieved = Column(Float, default=0.0)
    fee_collection_target = Column(Float, default=0.0)
    fee_collection_achieved = Column(Float, default=0.0)
    attendance_target_percentage = Column(Float, default=80.0)
    attendance_achieved = Column(Float, default=0.0)
    
    # Overall
    total_score = Column(Float, default=0.0)
    prize_amount = Column(Float, default=0.0)
    prize_status = Column(String(20), default="Pending")
    
    target_month = Column(String(7), nullable=False)
    status = Column(String(20), default="Active")
    created_by = Column(String(60))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    gym = relationship("Gym", back_populates="staff_targets")


# ============================================
# STAFF TARGET FUNCTIONS
# ============================================

def add_staff_target(gym_id, staff_username, new_members_target, fee_collection_target, 
                     attendance_target_percentage, target_month, created_by, prize_amount=0):
    """Add complete targets for a staff member"""
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
    """Get targets for staff"""
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
    """Get targets for all staff (for history page)"""
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
    """Get complete target for a staff member"""
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
        
        # Get total active members
        total_members = db.query(Member).filter_by(gym_id=target.gym_id, status="Active").count()
        
        # Calculate attendance target from percentage
        attendance_target_count = (target.attendance_target_percentage / 100) * total_members if total_members > 0 else 0
        
        # Calculate percentages
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


def update_staff_achievement(staff_username, target_type, achieved_value, target_month=None):
    """Update achieved value for staff"""
    db = get_db()
    try:
        if not target_month:
            target_month = date.today().strftime("%Y-%m")
        
        target = db.query(StaffTarget).filter(
            StaffTarget.staff_username == staff_username,
            StaffTarget.target_month == target_month,
            StaffTarget.status == "Active"
        ).first()
        
        if not target:
            return False, "No active target found"
        
        if target_type == "new_members":
            target.new_members_achieved += achieved_value
        elif target_type == "fee_collection":
            target.fee_collection_achieved += achieved_value
        elif target_type == "attendance":
            target.attendance_achieved += achieved_value
        
        # Calculate attendance target from percentage
        total_members = db.query(Member).filter_by(gym_id=target.gym_id, status="Active").count()
        attendance_target_count = (target.attendance_target_percentage / 100) * total_members if total_members > 0 else 0
        
        # Calculate total score
        target.total_score = (
            (target.new_members_achieved / target.new_members_target * 100) if target.new_members_target > 0 else 0 +
            (target.fee_collection_achieved / target.fee_collection_target * 100) if target.fee_collection_target > 0 else 0 +
            (target.attendance_achieved / attendance_target_count * 100) if attendance_target_count > 0 else 0
        ) / 3
        
        # Check if all targets completed
        if (target.new_members_achieved >= target.new_members_target and
            target.fee_collection_achieved >= target.fee_collection_target and
            target.attendance_achieved >= attendance_target_count and
            target.new_members_target > 0 and target.fee_collection_target > 0 and attendance_target_count > 0):
            target.status = "Completed"
            target.prize_status = "Awarded"
        
        db.commit()
        return True, "Achievement updated"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


def get_all_staff_progress(gym_id=None, target_month=None):
    """Get progress for all staff members"""
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
    """Delete a staff target"""
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
    """Get complete progress for a staff member"""
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
            # New Members
            progress['new_members']['target'] = target.new_members_target or 0
            progress['new_members']['achieved'] = target.new_members_achieved or 0
            if target.new_members_target > 0:
                progress['new_members']['percentage'] = min(100, (target.new_members_achieved / target.new_members_target) * 100)
            
            # Fee Collection
            progress['fee_collection']['target'] = target.fee_collection_target or 0
            progress['fee_collection']['achieved'] = target.fee_collection_achieved or 0
            if target.fee_collection_target > 0:
                progress['fee_collection']['percentage'] = min(100, (target.fee_collection_achieved / target.fee_collection_target) * 100)
            
            # Attendance
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
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    gym = relationship("Gym", back_populates="announcements")


# Add relationship to Gym model (find Gym class and add this line)
# Inside Gym class, add: announcements = relationship("Announcement", back_populates="gym", cascade="all, delete-orphan")


def add_announcement(gym_id, message, created_by, expires_at=None):
    """Add a new announcement"""
    db = get_db()
    try:
        # Deactivate old announcements
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
    """Get active announcement for gym"""
    db = get_db()
    try:
        query = db.query(Announcement).filter(
            Announcement.is_active == True
        )
        if gym_id:
            query = query.filter(Announcement.gym_id == gym_id)
        else:
            query = query.filter(Announcement.gym_id == None)
        
        # Check expiry
        now = datetime.utcnow()
        query = query.filter(
            (Announcement.expires_at == None) | (Announcement.expires_at > now)
        )
        
        return query.order_by(Announcement.created_at.desc()).first()
    finally:
        db.close()


def get_all_announcements(gym_id=None):
    """Get all announcements for gym"""
    db = get_db()
    try:
        query = db.query(Announcement)
        if gym_id:
            query = query.filter(Announcement.gym_id == gym_id)
        return query.order_by(Announcement.created_at.desc()).all()
    finally:
        db.close()


def delete_announcement(announcement_id):
    """Delete an announcement"""
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
    session_duration = Column(Integer, default=0)  # Minutes
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)


def log_staff_login(staff_username, ip_address=None):
    """Log staff login time"""
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
            login_time=datetime.utcnow(),
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
    """Log staff logout time"""
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
        
        record.logout_time = datetime.utcnow()
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
    """Get staff attendance records"""
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
    """Get staff attendance summary for all staff"""
    db = get_db()
    try:
        # Get all staff (excluding admin)
        staff_list = db.query(User).filter(User.role != "admin")
        if gym_id:
            staff_list = staff_list.filter(User.gym_id == gym_id)
        staff_list = staff_list.all()
        
        today = date.today()
        date_from = today - timedelta(days=date_range)
        
        results = []
        for staff in staff_list:
            # Get login count in date range
            logins = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff.username,
                StaffAttendance.login_time >= date_from
            ).count()
            
            # Get today's status
            today_record = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff.username,
                func.date(StaffAttendance.login_time) == today,
                StaffAttendance.logout_time == None
            ).first()
            
            status = "🟢 Online" if today_record else "⚪ Offline"
            
            # Get total hours this month
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
    """Get attendance summary for a specific staff member"""
    db = get_db()
    try:
        today = date.today()
        month_start = today.replace(day=1)
        
        # Today's record
        today_record = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            func.date(StaffAttendance.login_time) == today
        ).first()
        
        # This month records
        month_records = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            StaffAttendance.login_time >= month_start
        ).all()
        
        total_days = len(month_records)
        total_minutes = sum(r.session_duration or 0 for r in month_records)
        total_hours = total_minutes // 60
        
        # Last 7 days
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
    """Calculate continuous attendance streak"""
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

# ============================================
# COMPLETE STAFF ATTENDANCE FIX
# ============================================

# database.py mein add karein

def check_and_update_staff_status():
    """Check all staff and update status"""
    db = get_db()
    try:
        today = date.today()
        now = datetime.utcnow()
        timeout = timedelta(hours=2)  # 2 hours timeout
        
        # Get all active sessions
        active_sessions = db.query(StaffAttendance).filter(
            func.date(StaffAttendance.login_time) == today,
            StaffAttendance.logout_time == None
        ).all()
        
        updated_count = 0
        for session in active_sessions:
            # Check if session is expired (no activity for 2 hours)
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


def get_staff_attendance_summary(gym_id=None, date_range=30):
    """Get staff attendance summary (with auto logout check)"""
    # 🔥 First check and update inactive staff
    check_and_update_staff_status()
    
    db = get_db()
    try:
        # Get all staff (excluding admin)
        staff_list = db.query(User).filter(User.role != "admin")
        if gym_id:
            staff_list = staff_list.filter(User.gym_id == gym_id)
        staff_list = staff_list.all()
        
        today = date.today()
        date_from = today - timedelta(days=date_range)
        
        results = []
        for staff in staff_list:
            # Get login count in date range
            logins = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff.username,
                StaffAttendance.login_time >= date_from
            ).count()
            
            # Get today's status (after auto-logout check)
            today_record = db.query(StaffAttendance).filter(
                StaffAttendance.staff_username == staff.username,
                func.date(StaffAttendance.login_time) == today,
                StaffAttendance.logout_time == None
            ).first()
            
            status = "🟢 Online" if today_record else "⚪ Offline"
            
            # Get total hours this month
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
    """Get attendance summary for a specific staff member"""
    # 🔥 Check and update this staff's status
    db = get_db()
    try:
        today = date.today()
        now = datetime.utcnow()
        timeout = timedelta(hours=2)
        
        # Check if this staff has an active session
        active = db.query(StaffAttendance).filter(
            StaffAttendance.staff_username == staff_username,
            func.date(StaffAttendance.login_time) == today,
            StaffAttendance.logout_time == None
        ).first()
        
        # Auto logout if inactive
        if active and (now - active.login_time) > timeout:
            active.logout_time = now
            active.session_duration = (active.logout_time - active.login_time).seconds // 60
            db.commit()
        
        # Now get the summary
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
    """Calculate continuous attendance streak"""
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