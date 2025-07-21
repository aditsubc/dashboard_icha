import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px
from fpdf import FPDF
from io import BytesIO
import base64

# ─── Konfigurasi Supabase ────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Konfigurasi Streamlit ───────────────────────────
st.set_page_config(page_title="Dashboard Penjualan", layout="wide")
st.title("📊 Dashboard Penjualan & Perhitungan Modal")

# ─── Input Modal Produksi ────────────────────────────
st.header("Input Modal Produksi")
with st.form("form_modal"):
    tanggal = st.date_input("Tanggal", datetime.today())
    bahan_baku = st.text_input("Nama Bahan Baku")
    qty = st.number_input("Qty", min_value=0, step=1)
    harga_satuan = st.number_input("Harga Satuan", min_value=0)
    total = qty * harga_satuan
    submitted = st.form_submit_button("Simpan")
    if submitted:
        supabase.table("modal_produksi").insert({
            "tanggal": str(tanggal),
            "bahan_baku": bahan_baku,
            "qty": qty,
            "harga_satuan": harga_satuan,
            "total": total
        }).execute()
        st.success("✅ Data modal berhasil disimpan!")

# ─── Input Penjualan ─────────────────────────────────
st.header("Input Penjualan")
with st.form("form_penjualan"):
    tanggal_pj = st.date_input("Tanggal Penjualan", datetime.today(), key="pj")
    produk = st.text_input("Nama Produk")
    qty_pj = st.number_input("Jumlah Terjual", min_value=0, step=1)
    harga_jual = st.number_input("Harga Jual per Item", min_value=0)
    total_pj = qty_pj * harga_jual
    submitted2 = st.form_submit_button("Simpan Penjualan")
    if submitted2:
        supabase.table("data_penjualan").insert({
            "tanggal": str(tanggal_pj),
            "produk": produk,
            "qty": qty_pj,
            "harga_jual": harga_jual,
            "total": total_pj
        }).execute()
        st.success("✅ Data penjualan berhasil disimpan!")

# ─── Ambil Data dari Supabase ────────────────────────
df_modal = pd.DataFrame(supabase.table("modal_produksi").select("tanggal,bahan_baku,qty,harga_satuan,total").execute().data)
df_penjualan = pd.DataFrame(supabase.table("data_penjualan").select("tanggal, produk,qty,harga_jual,total").execute().data)

# ─── Dropdown Ringkasan Modal & Penjualan ────────────
st.header("📦 Ringkasan Data")

colA, colB = st.columns(2)
with colA:
    show_modal = st.checkbox("📌 Tampilkan Ringkasan Modal")
    if show_modal and not df_modal.empty:
        st.dataframe(df_modal.sort_values("tanggal", ascending=False), use_container_width=True)

with colB:
    show_penjualan = st.checkbox("🛒 Tampilkan Ringkasan Penjualan")
    if show_penjualan and not df_penjualan.empty:
        st.dataframe(df_penjualan.sort_values("tanggal", ascending=False), use_container_width=True)

# ─── Ringkasan & Grafik Interaktif ───────────────────
st.header("📈 Grafik & Ringkasan Profit")

if not df_modal.empty and not df_penjualan.empty:
    df_penjualan["tanggal"] = pd.to_datetime(df_penjualan["tanggal"])
    df_modal["tanggal"] = pd.to_datetime(df_modal["tanggal"])

    total_modal = df_modal["total"].sum()
    total_pendapatan = df_penjualan["total"].sum()
    laba_bersih = total_pendapatan - total_modal

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Modal", f"Rp {total_modal:,.0f}")
    col2.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    col3.metric("Laba Bersih", f"Rp {laba_bersih:,.0f}")

    st.subheader("Pilih Interval Grafik")
    mode = st.selectbox("Tampilkan Grafik Berdasarkan:", ["Harian", "Mingguan", "Bulanan", "Tahunan"])

    if mode == "Harian":
        df_chart = df_penjualan.groupby('tanggal').sum(numeric_only=True).reset_index()
    elif mode == "Mingguan":
        df_chart = df_penjualan.copy()
        df_chart["minggu"] = df_chart["tanggal"].dt.to_period("W").apply(lambda r: r.start_time)
        df_chart = df_chart.groupby("minggu").sum(numeric_only=True).reset_index().rename(columns={"minggu": "tanggal"})
    elif mode == "Bulanan":
        df_chart = df_penjualan.copy()
        df_chart["bulan"] = df_chart["tanggal"].dt.to_period("M").dt.to_timestamp()
        df_chart = df_chart.groupby("bulan").sum(numeric_only=True).reset_index().rename(columns={"bulan": "tanggal"})
    else:  # Tahunan
        df_chart = df_penjualan.copy()
        df_chart["tahun"] = df_chart["tanggal"].dt.year
        df_chart = df_chart.groupby("tahun").sum(numeric_only=True).reset_index().rename(columns={"tahun": "tanggal"})

    fig = px.bar(df_chart, x="tanggal", y="total", title=f"Pendapatan {mode}")
    st.plotly_chart(fig, use_container_width=True)

# ─── Fungsi Export PDF ───────────────────────────────
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Laporan Penjualan dan Modal", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Modal: Rp {total_modal:,.0f}", ln=True)
    pdf.cell(200, 10, txt=f"Total Pendapatan: Rp {total_pendapatan:,.0f}", ln=True)
    pdf.cell(200, 10, txt=f"Laba Bersih: Rp {laba_bersih:,.0f}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Detail Modal:", ln=True)
    for _, row in df_modal.iterrows():
        pdf.cell(200, 10, txt=f"{row['tanggal']} | {row['bahan_baku']} | Rp {row['total']:,.0f}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Detail Penjualan:", ln=True)
    for _, row in df_penjualan.iterrows():
        pdf.cell(200, 10, txt=f"{row['tanggal']} | {row['produk']} | Rp {row['total']:,.0f}", ln=True)
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# ─── Tombol Unduh PDF ────────────────────────────────
if not df_modal.empty and not df_penjualan.empty:
    if st.button("📄 Download Laporan PDF"):
        pdf_bytes = export_pdf()
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="laporan_penjualan.pdf">📥 Klik untuk download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
