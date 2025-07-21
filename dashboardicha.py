
import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px
from fpdf import FPDF
from io import BytesIO
import base64

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Dashboard Penjualan", layout="wide")
st.title("📊 Dashboard Penjualan & Perhitungan Modal")

st.header("Input Modal Produksi")
with st.form("form_modal"):
    tanggal = st.date_input("Tanggal", datetime.today())
    bahan = st.text_input("Nama Bahan Baku")
    qty = st.number_input("Qty", min_value=0, step=1)
    harga_satuan = st.number_input("Harga Satuan", min_value=0)
    total_belanja = qty * harga_satuan
    submitted = st.form_submit_button("Simpan")
    if submitted:
        supabase.table("modal_produksi").insert({
            "tanggal": str(tanggal),
            "bahan": bahan,
            "qty": qty,
            "harga_satuan": harga_satuan,
            "total_belanja": total_belanja
        }).execute()
        st.success("✅ Data modal berhasil disimpan!")

st.header("Input Penjualan")
with st.form("form_penjualan"):
    tanggal_pj = st.date_input("Tanggal Penjualan", datetime.today(), key="pj")
    produk = st.text_input("Nama Produk")
    jumlah = st.number_input("Jumlah Terjual", min_value=0, step=1)
    harga_jual = st.number_input("Harga Jual per Item", min_value=0)
    pendapatan = jumlah * harga_jual
    submitted2 = st.form_submit_button("Simpan Penjualan")
    if submitted2:
        supabase.table("data_penjualan").insert({
            "tanggal": str(tanggal_pj),
            "produk": produk,
            "jumlah": jumlah,
            "harga_jual": harga_jual,
            "pendapatan": pendapatan
        }).execute()
        st.success("✅ Data penjualan berhasil disimpan!")

df_modal = pd.DataFrame(supabase.table("modal_produksi").select("*").execute().data)
df_penjualan = pd.DataFrame(supabase.table("data_penjualan").select("*").execute().data)

st.header("📈 Ringkasan Penjualan vs Modal")
if not df_modal.empty and not df_penjualan.empty:
    total_modal = df_modal["total_belanja"].sum()
    total_pendapatan = df_penjualan["pendapatan"].sum()
    laba_bersih = total_pendapatan - total_modal

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Modal", f"Rp {total_modal:,.0f}")
    col2.metric("Total Pendapatan", f"Rp {total_pendapatan:,.0f}")
    col3.metric("Laba Bersih", f"Rp {laba_bersih:,.0f}")

    st.subheader("Grafik Penjualan Harian")
    df_penjualan['tanggal'] = pd.to_datetime(df_penjualan['tanggal'])
    daily = df_penjualan.groupby('tanggal').sum(numeric_only=True).reset_index()
    st.plotly_chart(px.bar(daily, x="tanggal", y="pendapatan", title="Pendapatan Harian"))

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
        pdf.cell(200, 10, txt=f"{row['tanggal']} | {row['bahan']} | Rp {row['total_belanja']}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Detail Penjualan:", ln=True)
    for _, row in df_penjualan.iterrows():
        pdf.cell(200, 10, txt=f"{row['tanggal']} | {row['produk']} | Rp {row['pendapatan']}", ln=True)
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

if st.button("📄 Download Laporan PDF"):
    pdf_bytes = export_pdf()
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="laporan_penjualan.pdf">📥 Klik untuk download PDF</a>'
    st.markdown(href, unsafe_allow_html=True)
