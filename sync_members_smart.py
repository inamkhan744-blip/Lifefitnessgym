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
        # 1. Neon ke saare columns aur unki details nikalein
        result = conn.execute(text(f"""
            SELECT column_name, is_nullable, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
        """))
        neon_schema = {row[0]: {'is_nullable': row[1], 'type': row[2]} for row in result}
        neon_cols = list(neon_schema.keys())
        
        # 2. 🚨 FIX: Neon ke 'gyms' table se asli valid gym_id nikalein
        gym_res = conn.execute(text("SELECT id FROM gyms LIMIT 1;"))
        valid_gym_id = gym_res.fetchone()[0]
        print(f"🏢 Neon se valid gym_id mil gaya: {valid_gym_id}")

    placeholders = ", ".join([f":{c}" for c in neon_cols])
    col_names = ", ".join(neon_cols)
    query = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING;")

    success = 0
    errors = 0
    with neon_engine.begin() as conn:
        for row in rows:
            row_dict = dict(row)
            data = {}

            # Har column ke liye data tayar karein
            for col in neon_cols:
                if col in row_dict:
                    data[col] = row_dict[col]
                elif col == 'gym_id':
                    # Ab hum gym_id ko member ki id nahi, balke asli Gym ID denge
                    data['gym_id'] = valid_gym_id 
                else:
                    # Agar naya column Neon mein hai lekin purani file mein nahi
                    if neon_schema[col]['is_nullable'] == 'NO':
                        if 'bool' in neon_schema[col]['type'] or 'whatsapp' in col:
                            data[col] = False 
                        elif 'int' in neon_schema[col]['type'] or 'numeric' in neon_schema[col]['type']:
                            data[col] = 0     
                        else:
                            data[col] = ''    
                    else:
                        data[col] = None      

            try:
                with conn.begin_nested():
                    conn.execute(query, data)
                success += 1
            except Exception as e:
                if errors < 3: 
                    print(f"⚠️ Error ID {row['id']} par: {e}")
                errors += 1

    print(f"\n✅ Total {success} naye records successfully transfer ho gaye!")
    if errors > 0:
        print(f"❌ {errors} records fail hue.")

    # ID Reset
    with neon_engine.begin() as conn:
        try:
            conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1)) FROM {table};"))
            print("🔄 Neon mein ID sequence reset ho gayi.")
        except Exception as seq_err:
            pass

except Exception as e:
    print(f"❌ Table mein error: {e}")

sqlite_conn.close()
print("\n🎉 Data Transfer Mukammal! Ab Streamlit Cloud par app reboot karein.")
