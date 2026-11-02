import sqlite3
from sqlalchemy import create_engine, text

# Neon URL (Aapka)
NEON_URL = "postgresql://neondb_owner:npg_uwot6sbWkYV4@ep-gentle-sound-atzaky6g-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

sqlite_conn = sqlite3.connect('gym_pro_backup_local.db')
sqlite_conn.row_factory = sqlite3.Row
neon_engine = create_engine(NEON_URL)

tables = ['members', 'fee_records', 'attendance']

for table in tables:
    print(f"📦 Syncing: {table}...")
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        if not rows:
            print(f"⚠️ {table} khali hai.")
            continue

        with neon_engine.connect() as conn:
            result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
            neon_cols = [row[0] for row in result]

        # Sirf matching columns
        sqlite_cols = rows[0].keys()
        common_cols = [c for c in sqlite_cols if c in neon_cols]
        if not common_cols:
            print(f"❌ {table} ke liye koi column match nahi hua.")
            continue

        placeholders = ", ".join([f":{c}" for c in common_cols])
        col_names = ", ".join(common_cols)
        pk = 'id' if 'id' in common_cols else ('gym_id' if 'gym_id' in common_cols else None)

        if pk:
            query = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT ({pk}) DO NOTHING;")
        else:
            query = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders});")

        success = 0
        with neon_engine.begin() as conn:
            for row in rows:
                data = {c: row[c] for c in common_cols}
                try:
                    conn.execute(query, data)
                    success += 1
                except Exception as e:
                    # Duplicate ya type errors ko skip karein
                    pass

        print(f"✅ {table}: {success} naye records transfer ho gaye.")

        # ID reset
        if pk:
            try:
                conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), coalesce(max({pk}), 1)) FROM {table};"))
            except:
                pass
    except Exception as e:
        print(f"❌ {table} mein error: {e}")

sqlite_conn.close()
print("\n🎉 Data transfer mukammal!")
