import sqlite3
from sqlalchemy import create_engine, text

# Neon URL
NEON_URL = "postgresql://neondb_owner:npg_uwot6sbWkYV4@ep-gentle-sound-atzaky6g-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

sqlite_conn = sqlite3.connect('gym_pro_backup_local.db')
sqlite_conn.row_factory = sqlite3.Row
neon_engine = create_engine(NEON_URL)

table = 'members'
print(f"📦 Syncing: {table}...")

try:
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    
    print(f"🔍 SQLite mein total {len(rows)} members mile. Neon par bhej rahe hain...")

    with neon_engine.connect() as conn:
        result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
        neon_cols = [row[0] for row in result]

    sqlite_cols = rows[0].keys()
    common_cols = [c for c in sqlite_cols if c in neon_cols]
    
    placeholders = ", ".join([f":{c}" for c in common_cols])
    col_names = ", ".join(common_cols)
    pk = 'id'

    query = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT ({pk}) DO NOTHING;")

    success = 0
    errors = 0
    with neon_engine.begin() as conn:
        for row in rows:
            data = {c: row[c] for c in common_cols}
            try:
                # Savepoint: Agar error aaya to sirf yeh row rollback hogi
                with conn.begin_nested():
                    conn.execute(query, data)
                success += 1
            except Exception as e:
                if errors < 5: # Pehle 5 errors print karein
                    print(f"⚠️ Error ID {row['id']} par: {e}")
                errors += 1

    print(f"\n✅ Total {success} naye records successfully transfer ho gaye!")
    if errors > 0:
        print(f"❌ {errors} records fail hue (Upar errors dekhein).")

    # ID reset (Alag transaction mein)
    with neon_engine.begin() as conn:
        try:
            conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), coalesce(max({pk}), 1)) FROM {table};"))
            print("🔄 Neon mein ID sequence reset ho gayi.")
        except Exception as seq_err:
            print(f"⚠️ Sequence reset error: {seq_err}")

except Exception as e:
    print(f"❌ Table mein error: {e}")

sqlite_conn.close()
print("\n🎉 Process mukammal!")
