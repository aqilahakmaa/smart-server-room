import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from PIL import Image
import os
import sys

# --- OTOMATIS ME-REFRESH HALAMAN TIAP 2 DETIK (REAL-TIME) ---
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="data_autorefresh")
except ImportError:
    pass  # Jika library belum terinstall, sistem tetap berjalan manual

# --- MENGHUBUNGKAN KE CONFIG DATABASE ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config.settings import DATABASE_PATH
except ImportError:
    # Path cadangan jika config/settings.py gagal dimuat
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "database.db")

# --- CONFIG HALAMAN ---
st.set_page_config(
    page_title="Smart Server Room — Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS UI ENHANCEMENT (PALETTE PASTEL) ---
st.markdown("""
    <style>
        /* Modern Soft Card Style */
        .metric-card {
            background: #FFFFFF;
            border: 2px solid #BAD6DA;
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
            transition: all 0.2s ease-in-out;
        }
        .metric-card:hover {
            border-color: #F791A9;
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #5A737B;
            margin-bottom: 6px;
        }
        .metric-val {
            font-size: 2.4rem;
            font-weight: 800;
            color: #2D3748;
            margin: 0;
            line-height: 1.1;
        }
        .metric-sub {
            font-size: 0.85rem;
            color: #4A5568;
            font-weight: 600;
            margin-top: 6px;
        }

        /* Banner Status Custom */
        .banner-safe {
            background-color: #DDDD7B;
            color: #2D3748;
            border-radius: 12px;
            padding: 14px 20px;
            font-weight: 700;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }
        .banner-alert {
            background-color: #F791A9;
            color: #FFFFFF;
            border-radius: 12px;
            padding: 14px 20px;
            font-weight: 700;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        /* Styling Judul & Sidebar Teks */
        h1, h2, h3, h4 {
            color: #2D3748 !important;
        }
        
        /* Tab Navigation Pastel Header */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 8px 16px;
            background-color: #FFFFFF;
            border: 1px solid #BAD6DA;
            color: #2D3748;
        }
        .stTabs [aria-selected="true"] {
            background-color: #F791A9 !important;
            color: #FFFFFF !important;
            border-color: #F791A9 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSIONALITAS DATABASE ---
def get_occupancy_data():
    if not os.path.exists(DATABASE_PATH):
        return 0, 0, 0
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT current_occupancy, total_in_today, total_out_today FROM room_occupancy WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return row if row else (0, 0, 0)
    except Exception:
        return 0, 0, 0

def get_access_logs():
    if not os.path.exists(DATABASE_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        query = """
            SELECT id AS ID, timestamp AS Waktu, track_id AS Track_ID, name AS Nama, 
                   status AS Status, direction AS Arah, snapshot_path AS Foto
            FROM access_logs ORDER BY id DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# --- SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/100/data-protection.png", width=65)
    st.title("Command Center")
    st.caption("v1.0.0 — Diskominfotik")
    st.divider()
    
    st.subheader("🔍 Filter Data")
    status_filter = st.multiselect(
        "Status Akses:",
        options=["AUTHORIZED", "UNAUTHORIZED"],
        default=["AUTHORIZED", "UNAUTHORIZED"]
    )
    
    st.divider()
    st.subheader("⚙️ System Status")
    st.success("🟢 YOLOv8 Engine: Active")
    st.success("🟢 DB Stream: Connected")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
        st.rerun()

# --- LOAD DATA ---
current_occ, total_in, total_out = get_occupancy_data()
df_logs = get_access_logs()

if not df_logs.empty and status_filter:
    filtered_df = df_logs[df_logs['Status'].isin(status_filter)]
else:
    filtered_df = df_logs

# --- HEADER TITLE ---
st.title("🛡️ Smart Server Room Access Monitoring")
st.caption("Sistem Keamanan Real-Time Berbasis AI & Computer Vision")
st.markdown("<br>", unsafe_allow_html=True)

# --- BANNER KEAMANAN ---
has_intruder = not df_logs.empty and (df_logs['Status'] == 'UNAUTHORIZED').any()

if has_intruder:
    st.markdown("""
        <div class="banner-alert">
            🚨 <b>SECURITY ALERT:</b> Terdeteksi aktivitas tidak dikenal (UNAUTHORIZED) di dalam Ruang Server!
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="banner-safe">
            ✅ <b>SYSTEM SECURE:</b> Area Server Room dalam keadaan aman dan terpantau normal.
        </div>
    """, unsafe_allow_html=True)

# --- METRIC CARDS ---
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current Occupancy</div>
            <div class="metric-val">{current_occ} <span style="font-size: 1.2rem; font-weight:500;">Orang</span></div>
            <div class="metric-sub">👥 Di dalam ruangan</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Entrance Today</div>
            <div class="metric-val">{total_in} <span style="font-size: 1.2rem; font-weight:500;">Event</span></div>
            <div class="metric-sub">📥 Total Masuk</div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Exit Today</div>
            <div class="metric-val">{total_out} <span style="font-size: 1.2rem; font-weight:500;">Event</span></div>
            <div class="metric-sub">📤 Total Keluar</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# --- TAB NAVIGASI UTAMA ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📸 Live Activity Feed", 
    "📊 Analytics & Trends", 
    "📋 Detailed Audit Log", 
    "📥 Export Report"
])

# ================= TAB 1: LIVE ACTIVITY FEED =================
with tab1:
    st.subheader("📸 Aktivitas Melintas Terbaru")
    
    if not filtered_df.empty:
        recent_logs = filtered_df.head(6)
        for idx in range(0, len(recent_logs), 2):
            cols = st.columns(2)
            for i, col in enumerate(cols):
                if idx + i < len(recent_logs):
                    row = recent_logs.iloc[idx + i]
                    with col:
                        with st.container():
                            i_col, t_col = st.columns([1, 2])
                            with i_col:
                                if os.path.exists(row['Foto']):
                                    st.image(Image.open(row['Foto']), use_column_width=True)
                                else:
                                    st.caption("📷 Foto Tidak Tersedia")
                            with t_col:
                                if row['Status'] == 'AUTHORIZED':
                                    st.success(f"🟢 **{row['Nama']}**")
                                else:
                                    st.error(f"🚨 **{row['Nama']} (UNAUTHORIZED)**")
                                
                                st.markdown(f"**Arah:** `{row['Arah']}`")
                                st.markdown(f"**Waktu:** {row['Waktu']}")
                                st.caption(f"Track ID: #{row['Track_ID']}")
                        st.markdown("---")
    else:
        st.info("Belum ada aktivitas melintas.")

# ================= TAB 2: ANALYTICS & CHARTS =================
with tab2:
    st.subheader("📊 Analytics Dashboard")
    if not df_logs.empty:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("##### 📈 Perbandingan Traffic (Masuk vs Keluar)")
            fig_bar = px.histogram(
                df_logs, x="Arah", color="Arah",
                color_discrete_map={"MASUK": "#DDDD7B", "KELUAR": "#F791A9"},
                text_auto=True, template="plotly_white"
            )
            fig_bar.update_layout(showlegend=False, height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.markdown("##### 🛡️ Rasio Keamanan Akses")
            status_counts = df_logs['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Jumlah']
            fig_pie = px.pie(
                status_counts, names='Status', values='Jumlah', color='Status',
                color_discrete_map={"AUTHORIZED": "#BAD6DA", "UNAUTHORIZED": "#F791A9"},
                hole=0.45, template="plotly_white"
            )
            fig_pie.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Data belum cukup untuk analisis.")

# ================= TAB 3: DETAILED AUDIT LOG =================
with tab3:
    st.subheader("📋 Audit Log Lengkap")
    if not filtered_df.empty:
        st.dataframe(
            filtered_df[['ID', 'Waktu', 'Track_ID', 'Nama', 'Status', 'Arah', 'Foto']],
            use_container_width=True,
            height=400
        )
    else:
        st.info("Tidak ada data log.")

# ================= TAB 4: EXPORT REPORT =================
with tab4:
    st.subheader("📥 Export Laporan Audit")
    if not df_logs.empty:
        csv_file = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Audit Log (.CSV)",
            data=csv_file,
            file_name="Laporan_Akses_Server_Room.csv",
            mime="text/csv",
            type="primary"
        )