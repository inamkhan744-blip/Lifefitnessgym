import database as db

STAFF_MAPPING = {
    "LKS": "shehzad",
    "LFS": "zakir",
    "KSL": "arifa",
    "STL": "jiya",
}

session = db.get_db()
members = session.query(db.Member).filter(db.Member.created_by_staff.is_(None)).all()

print(f"📌 Total members without staff: {len(members)}")

updated = 0
skipped = 0

for member in members:
    serial = member.serial_number or ""
    if "-" in serial:
        prefix = serial.split("-")[0]
    else:
        prefix = serial[:3] if len(serial) >= 3 else serial
    
    staff = STAFF_MAPPING.get(prefix)
    
    if staff:
        member.created_by_staff = staff
        updated += 1
        print(f"✅ {member.full_name} ({serial}) → {staff}")
    else:
        skipped += 1
        print(f"⚠️ {member.full_name} ({serial}) → No staff for prefix: {prefix}")

session.commit()
session.close()

print(f"✅ Updated: {updated} members")
print(f"⚠️ Skipped: {skipped} members")