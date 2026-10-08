import sqlite3
import os

db_path = 'backend/bharatagri.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"Total tables: {len(tables)}")
    for t in tables:
        count = c.execute(f"SELECT count(*) FROM `{t}`").fetchone()[0]
        cols = [col[1] for col in c.execute(f"PRAGMA table_info(`{t}`)").fetchall()]
        print(f"{t} ({count} rows): {cols}")
    conn.close()
else:
    print(f"File {db_path} does not exist.")
