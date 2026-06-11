import sqlite3
import os
from backend.config import DB_DIR

db_path = os.path.join(DB_DIR, "database.db")
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM kb_entries LIMIT 10")
    for row in cursor.fetchall():
        print(row[0][:100])
