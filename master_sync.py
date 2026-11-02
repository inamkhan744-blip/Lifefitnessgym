import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

# Neon URL
NEON_URL = "postgresql://neondb_owner:npg_uwot6sbWkYV4@ep-gentle-sound-atzaky6g-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

print("🔄 Connections bana rahe hain...")
sqlite_conn = sqlite3.connect('gym_pro_backup_local.db')
neon_engine = create_engine(NEON_URL)

tables_to_sync = ['members', 'fee_records', 'attendance']

for table in tables_to_sync:
    print(f"\n======================================")
    print(f"📦 Syncing Table: {table}")
    
    try:
        # 1. SQLite se data read karein
        df = pd.read_sql(f"SELECT * FROM {table}", sqlite_conn)
        if df.empty:
            print(f"⚠️ {table} mein koi data nahi hai.")
            continue

        # 2. Neon ke existing columns check karein
        with neon_engine.connect() as conn:
            result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
            neon_cols = [row[0] for row in result]

        # 3. Sirf matching columns rakhein
        matching_cols = [c for c in df.columns if c in neon_cols]
        df = df[matching_cols]
        
        # NaN values ko None (NULL) mein convert karein
        df = df.where(pd.notnull(df), None)

        # 4. Primary Key dhoondein
        pk_col = 'id' if 'id' in matching_cols else ('gym_id' if 'gym_id' in matching_cols else None)

        # 5. SQL Query banayein
        cols_str = ", ".join(matching_cols)
        vals_str = ", ".join([f":{c}" for c in matching_cols])
        
        if pk_col:
            query = text(f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str}) ON CONFLICT ({pk_col}) DO NOTHING;")
        else:
            query = text(f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str});")

        # 6. Data insert karein
        success = 0
        with neon_engine.begin() as conn:
            for record in df.to_dict('records'):
                try:
                    conn.execute(query, record)
                    success += 1
                except Exception as row_error:
                    print(f"  ⚠️ Row error in {table}: {row_error}")
                    
        print(f"✅ {table} synced! {success} rows successfully transfer ho gaye.")
        
        # 7. Sequence Reset (Taake naya data sahi ID se aaye)
        if pk_col:
            try:
                conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', '{pk_col}'), coalesce(max({pk_col}), 1)) FROM {table};"))
                print(f"🔄 {table} ki ID sequence reset ho gayi.")
            except Exception as seq_err:
                print(f"⚠️ Sequence reset error: {seq_err}")

    except Exception as e:
        print(f"❌ {table} mein masla aaya: {e}")

sqlite_conn.close()
print("\n🎉 MUBARAK HO! Data transfer ka process mukammal ho gaya.")
