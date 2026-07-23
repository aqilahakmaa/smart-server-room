# Isi di dalam config/settings.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "database.db")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "database", "snapshots")

# --- KONFIGURASI NOTIFIKASI WHATSAPP (FONNTE) ---
FONNTE_TOKEN = "BtS3yg2Hm4qVY79uZiDy"
ADMIN_WA_NUMBER = "081378946896"  
