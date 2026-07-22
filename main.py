import cv2
import time
import os
import sqlite3
from datetime import datetime
from ultralytics import YOLO

# ==========================================
# 0. KONFIGURASI DATABASE & SNAPSHOT
# ==========================================
DATABASE_PATH = os.path.join("database", "database.db")
SNAPSHOT_DIR = os.path.join("database", "snapshots")

def init_db():
    """Membuat folder, database, dan tabel secara otomatis jika belum ada."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. Tabel Status Ruangan (Ruang Server)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_occupancy (
            id INTEGER PRIMARY KEY,
            current_occupancy INTEGER,
            total_in_today INTEGER,
            total_out_today INTEGER
        )
    ''')
    
    # Pastikan baris id = 1 sudah ada agar perintah UPDATE di save_event_to_db tidak error
    cursor.execute("SELECT COUNT(*) FROM room_occupancy WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO room_occupancy (id, current_occupancy, total_in_today, total_out_today) VALUES (1, 0, 0, 0)")
        
    # 2. Tabel Catatan Aktivitas (Access Logs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            track_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            direction TEXT NOT NULL,
            snapshot_path TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_event_to_db(frame, track_id, direction_str, in_cnt, out_cnt, person_name="Staff / Guest", is_authorized=True):
    now = datetime.now()
    timestamp_db = now.strftime("%Y-%m-%d %H:%M:%S")
    time_file_str = now.strftime("%Y%m%d_%H%M%S")
    
    snapshot_name = f"{direction_str}_ID{track_id}_{time_file_str}.jpg"
    snapshot_path = os.path.join(SNAPSHOT_DIR, snapshot_name)
    cv2.imwrite(snapshot_path, frame)
    
    status_str = "AUTHORIZED" if is_authorized else "UNAUTHORIZED"
    current_occupancy = max(0, in_cnt - out_cnt)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE room_occupancy 
        SET current_occupancy = ?, total_in_today = ?, total_out_today = ?
        WHERE id = 1
    ''', (current_occupancy, in_cnt, out_cnt))
    
    cursor.execute('''
        INSERT INTO access_logs (timestamp, track_id, name, status, direction, snapshot_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp_db, track_id, person_name, status_str, direction_str, snapshot_path))
    
    conn.commit()
    conn.close()

# Inisialisasi Database sebelum program utama berjalan
init_db()

# ==========================================
# 1. LOAD MODEL & KAMERA
# ==========================================
model = YOLO("yolov8s.pt")
cap = cv2.VideoCapture(0)

# ==========================================
# 2. SETTING GARIS PINTU & THRESHOLD
# ==========================================
LINE_P1 = (81, 289)
LINE_P2 = (177, 270)

tracker_state = {}
in_count = 0
out_count = 0

CROSS_THRESHOLD = 100
CONFIRM_FRAMES = 5
EVENT_COOLDOWN_SEC = 1.5
FLIP_DIRECTION = False

def get_cross_product(P, Q, S):
    cp = (S[0] - P[0]) * (Q[1] - P[1]) - (S[1] - P[1]) * (Q[0] - P[0])
    return -cp if FLIP_DIRECTION else cp

# ==========================================
# 3. LOOPING STREAM VIDEO
# ==========================================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        classes=[0],
        conf=0.35,
        verbose=False
    )

    cv2.line(frame, LINE_P1, LINE_P2, (255, 0, 0), 2)
    mid = ((LINE_P1[0] + LINE_P2[0]) // 2, (LINE_P1[1] + LINE_P2[1]) // 2)
    dx = LINE_P2[0] - LINE_P1[0]
    dy = LINE_P2[1] - LINE_P1[1]
    normal = (-dy, dx) if not FLIP_DIRECTION else (dy, -dx)
    tip = (mid[0] + normal[0] // 3, mid[1] + normal[1] // 3)
    cv2.arrowedLine(frame, mid, tip, (0, 255, 255), 2, tipLength=0.4)
    cv2.putText(frame, "sisi +", (tip[0] + 5, tip[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.int().cpu().numpy()

        for box, track_id in zip(boxes, ids):
            x1, y1, x2, y2 = box
            w, h = x2 - x1, y2 - y1
            if h < 30 or (w * h) < 600:
                continue

            foot_x = int((x1 + x2) / 2)
            foot_y = int(y2)

            cp = get_cross_product(LINE_P1, LINE_P2, (foot_x, foot_y))

            if cp > CROSS_THRESHOLD:
                current_side = 1
            elif cp < -CROSS_THRESHOLD:
                current_side = -1
            else:
                current_side = 0

            now = time.time()

            if track_id not in tracker_state:
                if current_side != 0:
                    tracker_state[track_id] = {
                        "confirmed_side": current_side,
                        "pending_side": None,
                        "pending_count": 0,
                        "last_event_time": 0,
                    }
            else:
                st = tracker_state[track_id]
                confirmed_side = st["confirmed_side"]

                if current_side == 0 or current_side == confirmed_side:
                    st["pending_side"] = None
                    st["pending_count"] = 0
                else:
                    if st["pending_side"] == current_side:
                        st["pending_count"] += 1
                    else:
                        st["pending_side"] = current_side
                        st["pending_count"] = 1

                    if st["pending_count"] >= CONFIRM_FRAMES and (now - st["last_event_time"]) > EVENT_COOLDOWN_SEC:
                        current_staff_name = f"Staff #{track_id}"

                        if confirmed_side == 1 and current_side == -1:
                            in_count += 1
                            print(f"[EVENT] ID {track_id} -> MASUK (IN)")
                            save_event_to_db(frame, track_id, "MASUK", in_count, out_count, current_staff_name, True)

                        elif confirmed_side == -1 and current_side == 1:
                            out_count += 1
                            print(f"[EVENT] ID {track_id} -> KELUAR (OUT)")
                            save_event_to_db(frame, track_id, "KELUAR", in_count, out_count, current_staff_name, True)

                        st["confirmed_side"] = current_side
                        st["pending_side"] = None
                        st["pending_count"] = 0
                        st["last_event_time"] = now

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.circle(frame, (foot_x, foot_y), 4, (0, 0, 255), -1)
            side_label = {1: "Sisi+", -1: "Sisi-", 0: "Netral"}[current_side]
            pend = tracker_state.get(track_id, {}).get("pending_count", 0)
            cv2.putText(frame, f"ID {track_id} {side_label} confirm:{pend}/{CONFIRM_FRAMES}",
                        (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

    cv2.rectangle(frame, (15, 15), (130, 90), (0, 0, 0), -1)
    cv2.putText(frame, f"IN  : {in_count}", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (165, 245, 73), 2)
    cv2.putText(frame, f"OUT : {out_count}", (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    cv2.imshow("Ruang Server - Monitoring", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()