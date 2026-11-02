import sqlite3
import os
from sqlalchemy import text
import database as db

# 1. Replit ki local SQLite file dhoondein
sqlite_paths = ["gym_pro_v3.db", "gym-app/gym_pro_v3.db", "gym_pro_backup_local.db"]
sqlite_path = None
for p in sqlite_paths:
    if os.path.exists(p):
        sqlite_path = p
        break

if not sqlite_path:
    print("❌ Local SQLite file nahi mili!")
    exit()

print(f"🔄 Replit ki Local File ({sqlite_path}) se data Neon mein bhej rahe hain...")

sqlite_conn = sqlite3.connect(sqlite_path)
sqlite_conn.row_factory = sqlite3.Row
cursor = sqlite_conn.cursor()

# 2. Neon session start karein
neon_session = db.SessionLocal()

# --- MEMBERS SYNC ---
cursor.execute("SELECT * FROM members")
members = cursor.fetchall()
member_count = 0

for m in members:
    # Check karein ke member pehle se Neon mein hai ya nahi
    exists = neon_session.query(db.Member).filter_by(serial_number=m['serial_number']).first()
    if not exists:
        new_m = db.Member(
            gym_id=m['gym_id'],
            serial_number=m['serial_number'],
            full_name=m['full_name'],
            phone=m['phone'],
            email=m['email'],
            gender=m['gender'],
            dob=m['dob'],
            photo_path=m['photo_path'],
            membership_type=m['membership_type'],
            fee_amount=m['fee_amount'],
            join_date=m['join_date'],
            expiry_date=m['expiry_date'],
            status=m['status'],
            notes=m['notes'],
            whatsapp_sent=bool(m['whatsapp_sent']) if 'whatsapp_sent' in m.keys() else False,
            created_by_staff=m['created_by_staff'] if 'created_by_staff' in m.keys() else None
        )
        neon_session.add(new_m)
        member_count += 1

neon_session.commit()
print(f"✅ {member_count} naye Members Neon mein add ho gaye.")

# --- FEES SYNC ---
try:
    cursor.execute("SELECT * FROM fee_records")
    fees = cursor.fetchall()
    fee_count = 0
    for f in fees:
        exists = neon_session.query(db.FeeRecord).filter_by(id=f['id']).first()
        if not exists:
            # Check karein ke member Neon mein mojood hai
            member_exists = neon_session.query(db.Member).filter_by(serial_number=f['receipt_number']).first() # Fallback logic
            # ID se match karein
            new_f = db.FeeRecord(
                id=f['id'],
                member_id=f['member_id'],
                gym_id=f['gym_id'],
                amount=f['amount'],
                payment_method=f['payment_method'],
                payment_date=f['payment_date'],
                period_start=f['period_start'],
                period_end=f['period_end'],
                receipt_number=f['receipt_number'],
                collected_by=f['collected_by'],
                notes=f['notes']
            )
            neon_session.add(new_f)
            fee_count += 1
    neon_session.commit()
    print(f"✅ {fee_count} naye Fee Records Neon mein add ho gaye.")
except Exception as e:
    print(f"⚠️ Fee records sync mein error: {e}")

# --- ATTENDANCE SYNC ---
try:
    cursor.execute("SELECT * FROM attendance")
    atts = cursor.fetchall()
    att_count = 0
    for a in atts:
        exists = neon_session.query(db.Attendance).filter_by(id=a['id']).first()
        if not exists:
            new_a = db.Attendance(
                id=a['id'],
                member_id=a['member_id'],
                gym_id=a['gym_id'],
                check_date=a['check_date'],
                status=a['status'],
                marked_by=a['marked_by']
            )
            neon_session.add(new_a)
            att_count += 1
    neon_session.commit()
    print(f"✅ {att_count} naye Attendance Records Neon mein add ho gaye.")
except Exception as e:
    print(f"⚠️ Attendance sync mein error: {e}")

# --- IDs ko reset karein taake naya data aage se sahi ID le ---
try:
    neon_session.execute(text("SELECT setval(pg_get_serial_sequence('members', 'id'), coalesce(max(id),1)) FROM members;"))
    neon_session.execute(text("SELECT setval(pg_get_serial_sequence('fee_records', 'id'), coalesce(max(id),1)) FROM fee_records;"))
    neon_session.execute(text("SELECT setval(pg_get_serial_sequence('attendance', 'id'), coalesce(max(id),1)) FROM attendance;"))
    neon_session.commit()
    print("🔄 Database IDs reset ho gayi hain.")
except Exception as e:
    print(f"⚠️ ID reset error: {e}")

neon_session.close()
sqlite_conn.close()

print("🎉 MUBARAK HO! Replit ka saara data Neon (Cloud) mein transfer ho gaya hai.")
print("Ab aap Streamlit Cloud par wapas jayein aur 'Reboot app' dabayein.")
