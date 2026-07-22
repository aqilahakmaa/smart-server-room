import os

# Alamat Stream Kamera (0 = Webcam Laptop, atau isi URL iVCam)
RTSP_URL = 0 

# Lokasi Path Folder Proyek
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')
SNAPSHOT_DIR = os.path.join(BASE_DIR, 'captured_events')

# Config Model AI
YOLO_MODEL_PATH = 'yolov8n.pt'
CONFIDENCE_THRESHOLD = 0.5