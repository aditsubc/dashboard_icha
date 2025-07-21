import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import plotly.express as px
from fpdf import FPDF
import base64
from io import BytesIO

# ─── SUPABASE CONFIG ─────────────────
SUPABASE_URL = "https://nfopaajzxdiorzsdfkjo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5mb3BhYWp6eGRpb3J6c2Rma2pvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5MDAyODAsImV4cCI6MjA2NjQ3NjI4MH0.Klh9tywG3xA-1cl5jtyFliKwD989Wqb_ZvtyJ8eG2Vc"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── PAGE SETUP ──────────────────────
st.set_page_config("Dashboard Penjualan & Modal", layout="wide")
st.title("📊Penjualan & Perhitungan Modal")

# ─── FORM INPUT MODAL ────────────────
st.subheader("📦 Input Modal Produksi")
with st.form("input_modal"):
    tanggal = st.date_input("Tanggal", datetime.now())
    bahan_baku = st.text_input("Bahan Baku")
    qty = st.number_input("Qty", 0)
    harga = st.number_input("Harga Satuan", 0.0)
    submitted = st.form_submit_button("Simpan Modal")
    if submitted:
        total = qty * harga
        supabase.table("modal_produksi").insert({
            "tanggal": tanggal.isoformat(),
            "bahan_baku": bahan_baku,
            "qty": qty,
            "harga_satuan": harga,
            "total": total
        }).execute()
        st.success("✅ Modal berhasil disimpan!")

# ─── FORM INPUT PENJUALAN ────────────
st.subheader("🛒 Input Data Penjualan")
with st.form("input_penjualan"):
    tgl_jual = st.date_input("Tanggal Penjualan", datetime.now())
    produk = st.text_input("Nama Produk")
    qty_jual = st.number_input("Qty Terjual", 0)
    harga_jual = st.number_input("Harga Jual Satuan", 0.0)
    save_jual = st.form_submit_button("Simpan Penjualan")
    if save_jual:
        total_jual = qty_jual * harga_jual
        supabase.table("data_penjualan").insert({
            "tanggal": tgl_jual.isoformat(),
            "produk": produk,
            "qty": qty_jual,
            "harga_jual": harga_jual,
            "total": total_jual
        }).execute()
        st.success("✅ Penjualan berhasil disimpan!")

# ─── FILTER DATA ─────────────────────
st.subheader("📅 Filter Data Penjualan & Modal")
period = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
today = datetime.today()

if period == "Harian":
    start = today
elif period == "Mingguan":
    start = today - timedelta(days=7)
elif period == "Bulanan":
    start = today.replace(day=1)
elif period == "Tahunan":
    start = today.replace(month=1, day=1)

# ─── AMBIL DATA DARI SUPABASE ────────
modal_data = supabase.table("modal_produksi").select("*").gte("tanggal", start.isoformat()).execute().data
jual_data = supabase.table("data_penjualan").select("*").gte("tanggal", start.isoformat()).execute().data

df_modal = pd.DataFrame(modal_data)
df_jual = pd.DataFrame(jual_data)

# Convert tanggal to datetime for both dataframes
if not df_modal.empty:
    df_modal['tanggal'] = pd.to_datetime(df_modal['tanggal'])
if not df_jual.empty:
    df_jual['tanggal'] = pd.to_datetime(df_jual['tanggal'])

# ─── PERHITUNGAN RINGKASAN ───────────
st.subheader("💰 Ringkasan Keuangan")
total_modal = df_modal["total"].sum() if not df_modal.empty else 0
total_penjualan = df_jual["total"].sum() if not df_jual.empty else 0
laba_bersih = total_penjualan - total_modal

col1, col2, col3 = st.columns(3)
col1.metric("Total Modal", f"Rp {total_modal:,.0f}")
col2.metric("Total Penjualan", f"Rp {total_penjualan:,.0f}")
col3.metric("Laba Bersih", f"Rp {laba_bersih:,.0f}", delta=f"Rp {laba_bersih - total_modal:,.0f}")

# ─── TAMPILKAN DATAFRAME ─────────────
with st.expander("📄 Data Modal"):
    st.dataframe(df_modal)

with st.expander("📄 Data Penjualan"):
    st.dataframe(df_jual)

# ─── VISUALISASI DATA PENJUALAN ──────
st.subheader("📈 Grafik Penjualan")

if not df_jual.empty:
    # Group by date for time series
    df_jual_per_tanggal = df_jual.groupby('tanggal')['total'].sum().reset_index()
    
    # Line chart for sales over time
    fig1 = px.line(df_jual_per_tanggal, 
                  x='tanggal', 
                  y='total',
                  title='Total Penjualan per Hari',
                  labels={'tanggal': 'Tanggal', 'total': 'Total Penjualan (Rp)'})
    st.plotly_chart(fig1, use_container_width=True)
    
    # Bar chart for product sales
    df_produk = df_jual.groupby('produk')['total'].sum().reset_index().sort_values('total', ascending=False)
    fig2 = px.bar(df_produk,
                 x='produk',
                 y='total',
                 title='Total Penjualan per Produk',
                 labels={'produk': 'Nama Produk', 'total': 'Total Penjualan (Rp)'})
    st.plotly_chart(fig2, use_container_width=True)
    
    # Pie chart for product distribution
    fig3 = px.pie(df_produk,
                 names='produk',
                 values='total',
                 title='Persentase Penjualan per Produk')
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Tidak ada data penjualan untuk ditampilkan.")

# ─── VISUALISASI MODAL ──────────────
st.subheader("📉 Grafik Modal Produksi")

if not df_modal.empty:
    # Group by date for time series
    df_modal_per_tanggal = df_modal.groupby('tanggal')['total'].sum().reset_index()
    
    # Line chart for production costs over time
    fig4 = px.line(df_modal_per_tanggal, 
                  x='tanggal', 
                  y='total',
                  title='Total Modal Produksi per Hari',
                  labels={'tanggal': 'Tanggal', 'total': 'Total Modal (Rp)'})
    st.plotly_chart(fig4, use_container_width=True)
    
    # Bar chart for material costs
    df_bahan = df_modal.groupby('bahan_baku')['total'].sum().reset_index().sort_values('total', ascending=False)
    fig5 = px.bar(df_bahan,
                 x='bahan_baku',
                 y='total',
                 title='Total Pengeluaran per Bahan Baku',
                 labels={'bahan_baku': 'Bahan Baku', 'total': 'Total Modal (Rp)'})
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.warning("Tidak ada data modal untuk ditampilkan.")



# ─── PDF DOWNLOAD CARD ──────────────
st.subheader("📥 Download Laporan")

def create_download_card():
    st.markdown("""
    <style>
    .download-card {
        border-radius: 10px;
        padding: 20px;
        background-color: #f8f9fa;
        border-left: 5px solid #4e73df;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .download-header {
        color: #4e73df;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    </style>
    <div class="download-card">
        <div class="download-header">📋 Ekspor Laporan Keuangan</div>
        <p>Hasilkan laporan PDF dari data penjualan dan modal periode ini:</p>
    </div>
    """, unsafe_allow_html=True)

def generate_pdf():
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Laporan Keuangan", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Periode: {period} - {start.date()} hingga {today.date()}", ln=1, align='C')
    pdf.ln(10)
    
    # Ringkasan
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Ringkasan Keuangan", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total Modal: Rp {total_modal:,.0f}", ln=1)
    pdf.cell(200, 10, txt=f"Total Penjualan: Rp {total_penjualan:,.0f}", ln=1)
    pdf.cell(200, 10, txt=f"Laba Bersih: Rp {laba_bersih:,.0f}", ln=1)
    pdf.ln(10)

    # Data Penjualan
    if not df_jual.empty:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Data Penjualan", ln=1)
        pdf.set_font("Arial", size=10)
        col_widths = [40, 60, 30, 30, 40]
        headers = ["Tanggal", "Produk", "Qty", "Harga", "Total"]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        for _, row in df_jual.iterrows():
            pdf.cell(col_widths[0], 10, str(row['tanggal'].date()), 1)
            pdf.cell(col_widths[1], 10, str(row['produk']), 1)
            pdf.cell(col_widths[2], 10, str(row['qty']), 1)
            pdf.cell(col_widths[3], 10, f"Rp {row['harga_jual']:,.0f}", 1)
            pdf.cell(col_widths[4], 10, f"Rp {row['total']:,.0f}", 1)
            pdf.ln()
        pdf.ln(10)

    # Data Modal
    if not df_modal.empty:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Data Modal Produksi", ln=1)
        pdf.set_font("Arial", size=10)
        headers = ["Tanggal", "Bahan Baku", "Qty", "Harga", "Total"]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        for _, row in df_modal.iterrows():
            pdf.cell(col_widths[0], 10, str(row['tanggal'].date()), 1)
            pdf.cell(col_widths[1], 10, str(row['bahan_baku']), 1)
            pdf.cell(col_widths[2], 10, str(row['qty']), 1)
            pdf.cell(col_widths[3], 10, f"Rp {row['harga_satuan']:,.0f}", 1)
            pdf.cell(col_widths[4], 10, f"Rp {row['total']:,.0f}", 1)
            pdf.ln()

    # Save to buffer
    def generate_pdf_bytes(pdf_obj):
        buffer = BytesIO()
        buffer.write(pdf_obj.output(dest='S'))  # tidak perlu .encode()
        return buffer.getvalue()

    return generate_pdf_bytes(pdf)

create_download_card()

if st.button("🖨️ Generate PDF Report", key="generate_pdf"):
    with st.spinner("Membuat laporan PDF..."):
        try:
            # Generate PDF
            pdf_bytes = generate_pdf()
            
            # Create download button
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"laporan_keuangan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/octet-stream"
            )
            st.success("Laporan PDF siap diunduh!")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")
            st.warning("Pastikan package fpdf2 sudah terinstall. Jalankan: pip install fpdf2")