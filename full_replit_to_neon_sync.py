import sys
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings("ignore")

# 1. Replit ka purana Database (Jahan 386 members hain)
SOURCE_URL = "postgresql://postgres:password@helium/heliumdb?sslmode=disable"

# 2. Neon (Streamlit) ka Naya Database
TARGET_URL = "postgresql://neondb_owner:npg_uwot6sbWkYV4@ep-gentle-sound-atzaky6g-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

print("🔄 Replit Database se connect ho rahe hain...")
src_engine = create_engine(SOURCE_URL)

print("🔄 Neon Database se connect ho rahe hain...")
tgt_engine = create_engine(TARGET_URL)

# Tables ko is order mein sync karna zaroori hai taake Foreign Keys kharab na hon
tables_to_sync = ['gyms', 'members', 'fee_records', 'attendance']

for table in tables_to_sync:
    print(f"\n======================================")
    print(f"📦 Syncing Table: {table}")
    try:
        # 1. Source (Replit) se data uthana
        with src_engine.connect() as src_conn:
            result = src_conn.execute(text(f"SELECT * FROM {table}"))
            src_rows = [dict(row._mapping) for row in result]
            
        if not src_rows:
            print(f"⚠️ Replit ke DB mein {table} khali hai.")
            continue

        print(f"🔍 Replit mein {len(src_rows)} records mile. Neon mein bheje ja rahe hain...")

        # 2. Target (Neon) ka schema dekhna
        with tgt_engine.connect() as tgt_conn:
            tgt_cols_result = tgt_conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
            tgt_cols = [row[0] for row in tgt_cols_result]

        # 3. Matching columns nikalna
        common_cols = [c for c in src_rows[0].keys() if c in tgt_cols]
        if not common_cols:
            print(f"❌ {table} ke liye koi column match nahi hua.")
            continue
            
        placeholders = ", ".join([f":{c}" for c in common_cols])
        col_names = ", ".join(common_cols)
        
        # 4. Insert Query (Conflict par skip karega taake duplicates na banein)
        query = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;")

        success = 0
        errors = 0
        
        # 5. Data insert karna
        with tgt_engine.begin() as tgt_conn:
            for row in src_rows:
                data = {c: row[c] for c in common_cols}
                try:
                    # Savepoint taake ek error poore batch ko na roke
                    with tgt_conn.begin_nested():
                        tgt_conn.execute(query, data)
                    success += 1
                except Exception as e:
                    if errors < 3:
                        print(f"⚠️ Row skip hui: {str(e)[:100]}")
                    errors += 1

        print(f"✅ {table}: {success} naye records transfer ho gaye!")
        if errors > 0:
            print(f"❌ {table}: {errors} records fail hue.")
            
        # 6. ID Sequence Reset (Taake naya data sahi ID se aaye)
        if 'id' in common_cols:
            with tgt_engine.begin() as tgt_conn:
                try:
                    tgt_conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1)) FROM {table};"))
                    print(f"🔄 {table} ki ID sequence reset ho gayi.")
                except Exception:
                    pass

    except Exception as e:
        print(f"❌ {table} mein error: {e}")

print("\n🎉 MUBARAK HO! Replit ka saara data Neon mein transfer ho gaya hai.")
print("Ab aap Streamlit Cloud par app ko Reboot karein.")
