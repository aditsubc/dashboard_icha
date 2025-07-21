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
df_modal = pd.DataFrame(supabase.table("modal_produksi").select("*").execute().data)
df_penjualan = pd.DataFrame(supabase.table("data_penjualan").select("*").execute().data)

# ─── Ringkasan & Grafik Interaktif ───────────────────
st.header("📈 Ringkasan Penjualan vs Modal")

if not df_modal.empty and not df_penjualan.empty:
    df_modal["tanggal"] = pd.to_datetime(df_modal["tanggal"])
    df_penjualan["tanggal"] = pd.to_datetime(df_penjualan["tanggal"])

    total_modal = df_modal["total"].sum()
    total_pendapatan = df_penjualan["total"].sum()
    laba_bersih = total_pendapatan - total_modal

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Modal", f"Rp {total_modal:,.0f}")
    col2.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    col3.metric("Laba Bersih", f"Rp {laba_bersih:,.0f}")

    # Dropdown untuk memilih periode
    st.subheader("Grafik Interaktif Pendapatan & Profit")
    pilihan = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"])

    if pilihan == "Harian":
        df = df_penjualan.groupby("tanggal").sum(numeric_only=True).reset_index()
        judul = "Pendapatan Harian"
    elif pilihan == "Mingguan":
        df = df_penjualan.resample("W-Mon", on="tanggal").sum(numeric_only=True).reset_index()
        judul = "Pendapatan Mingguan"
    elif pilihan == "Bulanan":
        df = df_penjualan.resample("M", on="tanggal").sum(numeric_only=True).reset_index()
        judul = "Pendapatan Bulanan"
    elif pilihan == "Tahunan":
        df = df_penjualan.resample("Y", on="tanggal").sum(numeric_only=True).reset_index()
        judul = "Pendapatan Tahunan"

    fig = px.bar(df, x="tanggal", y="total", title=judul, labels={"total": "Total Penjualan"}, hover_data=["total"])
    fig.update_traces(marker_color="royalblue", marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
    fig.update_layout(xaxis_title="Tanggal", yaxis_title="Total Penjualan")
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
        pdf.cell(200, 10, txt=f"{row['tanggal'].date()} | {row['bahan_baku']} | Rp {row['total']:,.0f}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Detail Penjualan:", ln=True)
    for _, row in df_penjualan.iterrows():
        pdf.cell(200, 10, txt=f"{row['tanggal'].date()} | {row['produk']} | Rp {row['total']:,.0f}", ln=True)
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
