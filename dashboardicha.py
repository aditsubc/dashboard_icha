import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime
import io

# Konfigurasi
st.set_page_config(page_title="Dashboard Penjualan & Modal", layout="wide")

# --- Supabase ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Ambil Data ---
modal_data = supabase.table("modal_produksi").select("*").execute().data
penjualan_data = supabase.table("data_penjualan").select("*").execute().data

# Konversi ke DataFrame
df_modal = pd.DataFrame(modal_data)
df_penjualan = pd.DataFrame(penjualan_data)

# --- Tampilkan Ringkasan ---
st.title("📊 Dashboard Penjualan dan Modal Produksi")

col1, col2 = st.columns(2)

with col1:
    total_belanja = df_modal['total'].sum() if not df_modal.empty else 0
    st.metric("💰 Total Belanja (Modal)", f"Rp {total_belanja:,.0f}")

with col2:
    total_penjualan = df_penjualan['total'].sum() if not df_penjualan.empty else 0
    st.metric("🛒 Total Penjualan", f"Rp {total_penjualan:,.0f}")

# --- Ringkasan Harian Berdasarkan Tanggal ---
st.markdown("---")
st.header("📅 Ringkasan Harian Berdasarkan Tanggal")

if not df_modal.empty and not df_penjualan.empty:
    semua_tanggal = sorted(
        set(df_modal['tanggal'].unique()).union(set(df_penjualan['tanggal'].unique())),
        reverse=True
    )
    tanggal_pilihan = st.selectbox("Pilih Tanggal", semua_tanggal)

    modal_harian = df_modal[df_modal['tanggal'] == tanggal_pilihan]
    penjualan_harian = df_penjualan[df_penjualan['tanggal'] == tanggal_pilihan]

    total_modal = modal_harian['total'].sum()
    total_penjualan = penjualan_harian['total'].sum()
    laba = total_penjualan - total_modal

    col3, col4, col5 = st.columns(3)
    col3.metric("💸 Modal Harian", f"Rp {total_modal:,.0f}")
    col4.metric("🛒 Penjualan Harian", f"Rp {total_penjualan:,.0f}")
    col5.metric("📈 Laba", f"Rp {laba:,.0f}", delta=f"{(laba / total_modal * 100):.2f}%" if total_modal else "N/A")
else:
    st.info("Belum ada data untuk ditampilkan.")

# --- Pie Chart Produk ---
st.markdown("---")
st.subheader("📊 Distribusi Penjualan per Produk")
if not df_penjualan.empty:
    pie_data = df_penjualan.groupby("produk")["total"].sum().reset_index()
    fig_pie = px.pie(pie_data, names="produk", values="total", title="Persentase Penjualan")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.warning("Data penjualan kosong.")

# --- Grafik Garis Tren Penjualan ---
st.markdown("---")
st.subheader("📈 Tren Penjualan Harian")
if not df_penjualan.empty:
    df_penjualan["tanggal"] = pd.to_datetime(df_penjualan["tanggal"])
    tren_penjualan = df_penjualan.groupby("tanggal")["total"].sum().reset_index()
    fig_line = px.line(tren_penjualan, x="tanggal", y="total", title="Total Penjualan per Hari")
    st.plotly_chart(fig_line, use_container_width=True)

# --- PDF Export ---
st.markdown("---")
st.subheader("📥 Unduh Laporan PDF")
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 14)
        self.cell(200, 10, "Laporan Keuangan", ln=True, align='C')

    def laporan_ringkasan(self):
        self.set_font("Arial", '', 12)
        self.cell(100, 10, f"Total Modal: Rp {total_belanja:,.0f}", ln=True)
        self.cell(100, 10, f"Total Penjualan: Rp {total_penjualan:,.0f}", ln=True)
        self.cell(100, 10, f"Laba Bersih: Rp {total_penjualan - total_belanja:,.0f}", ln=True)
