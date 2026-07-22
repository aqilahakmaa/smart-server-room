import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DATABASE_PATH

def initialize_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Tabel Log Akses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            direction TEXT NOT NULL,
            snapshot_path TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabel Jumlah Orang (Occupancy)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_occupancy (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_occupancy INTEGER NOT NULL DEFAULT 0,
            total_in_today INTEGER NOT NULL DEFAULT 0,
            total_out_today INTEGER NOT NULL DEFAULT 0
        )
    ''')

    cursor.execute('''
        INSERT OR IGNORE INTO room_occupancy (id, current_occupancy, total_in_today, total_out_today)
        VALUES (1, 0, 0, 0)
    ''')

    conn.commit()
    conn.close()
    print("✅ Database SQLite Berhasil Dibuat!")

if __name__ == "__main__":
    initialize_database()