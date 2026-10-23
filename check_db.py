import sqlite3

conn = sqlite3.connect('gym_pro_backup_local.db')
cursor = conn.cursor()

# Saare tables ke naam dhoondein
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("📋 Aapki SQLite file mein ye tables hain:")
for t in tables:
    table_name = t[0]
    print(f"\n👉 Table: {table_name}")
    
    # Har table ke columns check karein
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print("   Columns:", [col[1] for col in columns])
    
conn.close()
