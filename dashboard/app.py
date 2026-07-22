import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import os
import sys

# Menghubungkan ke folder config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DATABASE_PATH

st.set_page_config(page_title="Monitor Ruang Server", layout="wide")

st.title("🛡️ Smart Server Room Access Monitoring")
st.caption("Sistem Monitoring Akses Real-Time Diskominfo")

st.divider()

# --- KARTU INDIKATOR (METRICS) ---
def get_occupancy_data():
    if not os.path.exists(DATABASE_PATH):
        return 0, 0, 0
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT current_occupancy, total_in_today, total_out_today FROM room_occupancy WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row if row else (0, 0, 0)

current, total_in, total_out = get_occupancy_data()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="👥 Orang di Dalam Ruangan", value=f"{current} Orang")
with col2:
    st.metric(label="📥 Total Masuk Hari Ini", value=f"{total_in} Orang")
with col3:
    st.metric(label="📤 Total Keluar Hari Ini", value=f"{total_out} Orang")

st.divider()

# --- TABEL RIWAYAT AKSES ---
st.subheader("📋 Catatan Aktivitas Terakhir")

def get_access_logs():
    if not os.path.exists(DATABASE_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DATABASE_PATH)
    query = """
        SELECT timestamp AS Waktu, track_id AS ID_Track, name AS Nama, 
               status AS Status, direction AS Arah, snapshot_path AS Foto
        FROM access_logs ORDER BY id DESC LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

logs = get_access_logs()

if not logs.empty:
    for _, row in logs.iterrows():
        with st.container():
            c_img, c_info = st.columns([1, 3])
            with c_img:
                if os.path.exists(row['Foto']):
                    st.image(Image.open(row['Foto']), width=140)
                else:
                    st.caption("📷 Foto tidak ada")
            with c_info:
                if row['Status'] == 'AUTHORIZED':
                    st.success(f"**{row['Nama']}** ({row['Arah']})")
                else:
                    st.error(f"🚨 **{row['Nama']} (INTRUDER)** ({row['Arah']})")
                st.write(f"⏰ Waktu: {row['Waktu']} | ID Track: #{row['ID_Track']}")
        st.divider()
else:
    st.info("Belum ada riwayat aktivitas melintas.")