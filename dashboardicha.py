import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import plotly.express as px
from fpdf import FPDF
from io import BytesIO
import base64

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard Modal Produksi", layout="wide")
st.title("📦 Dashboard Modal Produksi")

# Supabase credentials dari secrets.toml
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Form input data
st.subheader("📝 Input Data Modal Produksi")
with st.form("form_modal"):
    tanggal = st.date_input("Tanggal", value=datetime.today())
    bahan = st.text_input("Nama Bahan Baku")
    qty = st.number_input("Jumlah (QTY)", min_value=0, value=0)
    harga_satuan = st.number_input("Harga Satuan", min_value=0.0, value=0.0, step=100.0)
    submitted = st.form_submit_button("Simpan")

    if submitted:
        total_belanja = qty * harga_satuan
        try:
            supabase.table("modal_produksi").insert({
                "tanggal": tanggal.strftime('%Y-%m-%d'),
                "bahan_baku": bahan,
                "qty": qty,
                "harga_satuan": harga_satuan,
                "total": total_belanja
            }).execute()
            st.success("✅ Data berhasil disimpan ke Supabase")
        except Exception as e:
            st.error(f"❌ Gagal menyimpan data: {e}")

# Ambil dan tampilkan data dari Supabase
st.subheader("📊 Data Modal Produksi")
try:
    response = supabase.table("modal_produksi").select("*").order("tanggal", desc=True).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        st.dataframe(df)

        # Grafik total belanja bulanan
        df["bulan"] = df["tanggal"].dt.to_period("M").astype(str)
        monthly = df.groupby("bulan")["total"].sum().reset_index()
        fig = px.bar(monthly, x="bulan", y="total", title="Total Belanja Bulanan", labels={"total": "Total Belanja (Rp)", "bulan": "Bulan"})
        st.plotly_chart(fig, use_container_width=True)

        # Ekspor PDF
        def export_pdf(df):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Laporan Modal Produksi", ln=True, align='C')

            for idx, row in df.iterrows():
                text = f"{row['tanggal'].date()} | {row['bahan_baku']} | Qty: {row['qty']} | Harga: {row['harga_satuan']:.0f} | Total: {row['total']:.0f}"
                pdf.cell(200, 10, txt=text, ln=True)

            buffer = BytesIO()
            pdf.output(buffer)
            return buffer.getvalue()

        if st.button("📄 Export PDF"):
            pdf_data = export_pdf(df)
            b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
            href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="laporan_modal.pdf">📥 Klik untuk mengunduh PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("Belum ada data yang tersimpan.")
except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
