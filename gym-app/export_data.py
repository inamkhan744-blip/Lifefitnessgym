"""
Data Export Script — Replit se Supabase ke liye
Run: python3 export_data.py
Output: gym_export.sql (Supabase mein paste karein)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import database as db
from sqlalchemy.orm import Session
from database import (
    engine, Gym, Member, User, DailyExpense, Attendance, UnknownCapture
)
from datetime import datetime

db.init_db()

lines = []
lines.append("-- GymPro Data Export")
lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append("-- Supabase SQL Editor mein yeh paste karein\n")

def esc(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"

with Session(engine) as s:
    # ── GYMS ─────────────────────────────────────────────────
    gyms = s.query(Gym).all()
    lines.append(f"-- GYMS ({len(gyms)})")
    lines.append("INSERT INTO gyms (id,name,address,phone,email) VALUES")
    rows = []
    for g in gyms:
        rows.append(f"  ({esc(g.id)},{esc(g.name)},{esc(g.address)},{esc(g.phone)},{esc(g.email)})")
    lines.append(",\n".join(rows) + "\nON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name;\n")

    # ── USERS ─────────────────────────────────────────────────
    users = s.query(User).all()
    lines.append(f"-- USERS ({len(users)})")
    lines.append("INSERT INTO users (id,username,full_name,password_hash,role,gym_id,is_active) VALUES")
    rows = []
    for u in users:
        rows.append(
            f"  ({esc(u.id)},{esc(u.username)},{esc(u.full_name)},"
            f"{esc(u.password_hash)},{esc(u.role)},{esc(u.gym_id)},{esc(u.is_active)})"
        )
    lines.append(",\n".join(rows) + "\nON CONFLICT (id) DO UPDATE SET username=EXCLUDED.username;\n")

    # ── MEMBERS ───────────────────────────────────────────────
    members = s.query(Member).all()
    lines.append(f"-- MEMBERS ({len(members)})")
    lines.append(
        "INSERT INTO members "
        "(id,gym_id,serial_number,full_name,phone,email,gender,dob,"
        "membership_type,join_date,expiry_date,status,photo_path,face_encoding) VALUES"
    )
    rows = []
    for m in members:
        rows.append(
            f"  ({esc(m.id)},{esc(m.gym_id)},{esc(m.serial_number)},"
            f"{esc(m.full_name)},{esc(m.phone)},{esc(m.email)},"
            f"{esc(m.gender)},{esc(m.dob)},{esc(m.membership_type)},"
            f"{esc(m.join_date)},{esc(m.expiry_date)},{esc(m.status)},"
            f"{esc(m.photo_path)},{esc(m.face_encoding)})"
        )
    lines.append(",\n".join(rows) + "\nON CONFLICT (id) DO UPDATE SET full_name=EXCLUDED.full_name;\n")

    # ── EXPENSES ──────────────────────────────────────────────
    try:
        expenses = s.query(DailyExpense).all()
        if expenses:
            lines.append(f"-- EXPENSES ({len(expenses)})")
            lines.append(
                "INSERT INTO daily_expenses (id,gym_id,amount,category,description,expense_date,added_by) VALUES"
            )
            rows = []
            for e in expenses:
                rows.append(
                    f"  ({esc(e.id)},{esc(e.gym_id)},{esc(e.amount)},"
                    f"{esc(e.category)},{esc(e.description)},"
                    f"{esc(e.expense_date)},{esc(getattr(e,'added_by',None))})"
                )
            lines.append(",\n".join(rows) + "\nON CONFLICT (id) DO UPDATE SET amount=EXCLUDED.amount;\n")
    except Exception as ex:
        lines.append(f"-- Expenses skip: {ex}\n")

    # ── ATTENDANCE ────────────────────────────────────────────
    try:
        att = s.query(Attendance).all()
        if att:
            lines.append(f"-- ATTENDANCE ({len(att)})")
            lines.append(
                "INSERT INTO attendance (id,member_id,gym_id,check_date,status,marked_by) VALUES"
            )
            rows = []
            for a in att:
                rows.append(
                    f"  ({esc(a.id)},{esc(a.member_id)},{esc(a.gym_id)},"
                    f"{esc(a.check_date)},{esc(a.status)},{esc(a.marked_by)})"
                )
            # Batch in chunks to avoid huge SQL
            chunk = 500
            for i in range(0, len(rows), chunk):
                batch = rows[i:i+chunk]
                lines.append(",\n".join(batch) + "\nON CONFLICT (id) DO NOTHING;\n")
    except Exception as ex:
        lines.append(f"-- Attendance skip: {ex}\n")

    # ── ID SEQUENCES ──────────────────────────────────────────
    lines.append("-- Reset sequences so new inserts don't conflict")
    for tbl in ["gyms","users","members","expenses","attendance"]:
        lines.append(f"SELECT setval('{tbl}_id_seq', (SELECT COALESCE(MAX(id),1) FROM {tbl}));")

sql_text = "\n".join(lines)
out_path  = os.path.join(os.path.dirname(__file__), "gym_export.sql")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(sql_text)

print(f"\n✅ Export complete! File: {out_path}")
print(f"   Gyms: {len(gyms)} | Members: {len(members)}")
print("\n📋 Next step:")
print("   1. gym_export.sql file download karein")
print("   2. Supabase → SQL Editor → yeh file ka content paste karein → Run")
