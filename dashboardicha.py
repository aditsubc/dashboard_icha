import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date
from fpdf import FPDF
import tempfile
import os

# ─────────────────────────────────────────────────────────────
# Konfigurasi Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Dashboard Icha", layout="wide")
st.title("📊 Dashboard Modal & Penjualan")

# ────────────────────────────────
# Tab Input Modal & Penjualan
tab1, tab2 = st.tabs(["🧾 Input Modal Produksi", "🛒 Input Penjualan"])

with tab1:
    st.subheader("Input Modal Produksi")
    with st.form("form_modal"):
        tanggal = st.date_input("Tanggal", value=date.today(), key="modal_tgl")
        bahan_baku = st.text_input("Bahan Baku", key="bahan_baku")
        qty = st.number_input("Jumlah (Qty)", min_value=1, key="qty_modal")
        harga_satuan = st.number_input("Harga Satuan", min_value=0.0, format="%.2f", key="harga_modal")
        total = qty * harga_satuan
        st.markdown(f"**Total: Rp {total:,.0f}**")
        submitted = st.form_submit_button("Simpan")
        if submitted:
            try:
                supabase.table("modal_produksi").insert({
                    "tanggal": str(tanggal),
                    "bahan_baku": bahan_baku,
                    "qty": qty,
                    "harga_satuan": harga_satuan,
                    "total": total
                }).execute()
                st.success("✅ Data modal berhasil disimpan!")
            except Exception as e:
                st.error(f"❌ Gagal menyimpan data modal: {e}")

with tab2:
    st.subheader("Input Penjualan")
    with st.form("form_penjualan"):
        tanggal = st.date_input("Tanggal", value=date.today(), key="penjualan_tgl")
        produk = st.text_input("Nama Produk", key="produk")
        qty = st.number_input("Jumlah Terjual", min_value=1, key="qty_jual")
        harga_jual = st.number_input("Harga Jual", min_value=0.0, format="%.2f", key="harga_jual")
        total = qty * harga_jual
        st.markdown(f"**Total: Rp {total:,.0f}**")
        submitted2 = st.form_submit_button("Simpan")
        if submitted2:
            try:
                supabase.table("data_penjualan").insert({
                    "tanggal": str(tanggal),
                    "produk": produk,
                    "qty": qty,
                    "harga_jual": harga_jual,
                    "total": total
                }).execute()
                st.success("✅ Data penjualan berhasil disimpan!")
            except Exception as e:
                st.error(f"❌ Gagal menyimpan data penjualan: {e}")

# ───────────────────────────────────────────
# Ringkasan Data + Subtotal + Download PDF
st.markdown("---")
st.header("📌 Ringkasan Data")

col1, col2 = st.columns(2)

with col1:
    show_modal = st.checkbox("📦 Tampilkan Ringkasan Modal")
    if show_modal:
        try:
            data_modal = supabase.table("modal_produksi").select("*").order("tanggal", desc=True).execute().data
            df_modal = pd.DataFrame(data_modal)
            if not df_modal.empty:
                st.dataframe(df_modal)
                subtotal = df_modal["total"].sum()
                st.markdown(f"### 💰 Subtotal Modal: Rp {subtotal:,.0f}")

                if st.button("⬇️ Download PDF Ringkasan Modal"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 14)
                    pdf.cell(200, 10, "Ringkasan Modal Produksi", ln=True, align="C")
                    pdf.ln(10)
                    pdf.set_font("Arial", "", 12)
                    for i, row in df_modal.iterrows():
                        pdf.cell(200, 10, f"{row['tanggal']} - {row['bahan_baku']} x{row['qty']} @Rp{row['harga_satuan']} = Rp{row['total']}", ln=True)
                    pdf.ln(5)
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(200, 10, f"Subtotal: Rp {subtotal:,.0f}", ln=True)

                    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    pdf.output(tmp_path.name)
                    with open(tmp_path.name, "rb") as f:
                        st.download_button("📄 Download PDF", f, file_name="ringkasan_modal.pdf")
                    os.unlink(tmp_path.name)
            else:
                st.info("Belum ada data modal.")
        except Exception as e:
            st.error(f"❌ Gagal mengambil data modal: {e}")

with col2:
    show_penjualan = st.checkbox("🛒 Tampilkan Ringkasan Penjualan")
    if show_penjualan:
        try:
            data_penjualan = supabase.table("data_penjualan").select("*").order("tanggal", desc=True).execute().data
            df_penjualan = pd.DataFrame(data_penjualan)
            if not df_penjualan.empty:
                st.dataframe(df_penjualan)
                subtotal = df_penjualan["total"].sum()
                st.markdown(f"### 🧾 Subtotal Penjualan: Rp {subtotal:,.0f}")

                if st.button("⬇️ Download PDF Ringkasan Penjualan"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 14)
                    pdf.cell(200, 10, "Ringkasan Penjualan", ln=True, align="C")
                    pdf.ln(10)
                    pdf.set_font("Arial", "", 12)
                    for i, row in df_penjualan.iterrows():
                        pdf.cell(200, 10, f"{row['tanggal']} - {row['produk']} x{row['qty']} @Rp{row['harga_jual']} = Rp{row['total']}", ln=True)
                    pdf.ln(5)
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(200, 10, f"Subtotal: Rp {subtotal:,.0f}", ln=True)

                    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    pdf.output(tmp_path.name)
                    with open(tmp_path.name, "rb") as f:
                        st.download_button("📄 Download PDF", f, file_name="ringkasan_penjualan.pdf")
                    os.unlink(tmp_path.name)
            else:
                st.info("Belum ada data penjualan.")
        except Exception as e:
            st.error(f"❌ Gagal mengambil data penjualan: {e}")
