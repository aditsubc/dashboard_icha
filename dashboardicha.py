import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from supabase import create_client, Client
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Dashboard Penjualan", layout="wide")
st.title("📊 Dashboard Penjualan & Modal Produksi")

# --- SUPABASE SETUP ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- DATA FETCHING ---
@st.cache_data
def fetch_data():
    data_modal = supabase.table("modal_produksi").select("*").execute().data
    data_penjualan = supabase.table("data_penjualan").select("*").execute().data
    return pd.DataFrame(data_modal), pd.DataFrame(data_penjualan)

df_modal, df_penjualan = fetch_data()

# --- RINGKASAN KEUANGAN ---
st.subheader("💰 Ringkasan Keuangan")
total_belanja = df_modal["total"].sum() if not df_modal.empty else 0
total_penjualan = df_penjualan["total"].sum() if not df_penjualan.empty else 0
laba = total_penjualan - total_belanja

col1, col2, col3 = st.columns(3)
col1.metric("Total Belanja (Modal)", f"Rp {total_belanja:,.0f}")
col2.metric("Total Penjualan", f"Rp {total_penjualan:,.0f}")
col3.metric("Laba Kotor", f"Rp {laba:,.0f}")

# --- GRAFIK GARIS PERTUMBUHAN PENJUALAN ---
st.markdown("---")
st.subheader("📈 Grafik Garis Pertumbuhan Penjualan")

if not df_penjualan.empty:
    df_penjualan["tanggal"] = pd.to_datetime(df_penjualan["tanggal"])
    df_penjualan_sorted = df_penjualan.sort_values("tanggal")
    garis = df_penjualan_sorted.groupby("tanggal")["total"].sum().reset_index()
    fig_line = px.line(garis, x="tanggal", y="total", markers=True, title="Tren Penjualan Harian")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Belum ada data penjualan.")

# --- PIE CHART PRODUK TERJUAL ---
st.subheader("🥧 Pie Chart Penjualan per Produk")
if not df_penjualan.empty:
    pie_data = df_penjualan.groupby("produk")["total"].sum().reset_index()
    fig_pie = px.pie(pie_data, names="produk", values="total", title="Distribusi Penjualan Produk")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("Belum ada data penjualan.")

# --- RINGKASAN BERDASARKAN TANGGAL ---
st.markdown("---")
st.subheader("📆 Ringkasan Harian")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📦 Modal Produksi Harian")
    if not df_modal.empty:
        df_modal["tanggal"] = pd.to_datetime(df_modal["tanggal"])
        ringkasan_modal = df_modal.groupby(df_modal["tanggal"].dt.date)["total"].sum().reset_index()
        ringkasan_modal.columns = ["Tanggal", "Total Modal"]
        st.dataframe(ringkasan_modal, use_container_width=True)
    else:
        st.info("Belum ada data modal.")

with col2:
    st.markdown("### 🛒 Penjualan Harian")
    if not df_penjualan.empty:
        df_penjualan["tanggal"] = pd.to_datetime(df_penjualan["tanggal"])
        ringkasan_penjualan = df_penjualan.groupby(df_penjualan["tanggal"].dt.date)["total"].sum().reset_index()
        ringkasan_penjualan.columns = ["Tanggal", "Total Penjualan"]
        st.dataframe(ringkasan_penjualan, use_container_width=True)
    else:
        st.info("Belum ada data penjualan.")

# --- EXPORT PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(200, 10, "Laporan Penjualan & Modal", ln=True, align="C")
        self.ln(10)

def export_to_pdf():
    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Total Modal: Rp {total_belanja:,.0f}", ln=True)
    pdf.cell(200, 10, f"Total Penjualan: Rp {total_penjualan:,.0f}", ln=True)
    pdf.cell(200, 10, f"Laba Kotor: Rp {laba:,.0f}", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, "Ringkasan Modal Harian:", ln=True)
    for idx, row in ringkasan_modal.iterrows():
        pdf.cell(200, 8, f"{row['Tanggal']}: Rp {row['Total Modal']:,.0f}", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, "Ringkasan Penjualan Harian:", ln=True)
    for idx, row in ringkasan_penjualan.iterrows():
        pdf.cell(200, 8, f"{row['Tanggal']}: Rp {row['Total Penjualan']:,.0f}", ln=True)

    filename = f"laporan_penjualan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

if st.button("📄 Download Laporan PDF"):
    file_path = export_to_pdf()
    with open(file_path, "rb") as f:
        st.download_button(label="Download PDF", data=f, file_name=file_path, mime="application/pdf")
