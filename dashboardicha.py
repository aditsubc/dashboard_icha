import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

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
# ─── Ringkasan Berdasarkan Tanggal ────────────────────────
st.markdown("---")
st.subheader("📅 Ringkasan Harian")
tanggal_filter = st.date_input("Pilih Tanggal", value=datetime.now().date())

# Modal Harian
modal_harian = df_modal[df_modal["tanggal"] == tanggal_filter]
total_modal_harian = modal_harian["total"].sum()

# Penjualan Harian
penjualan_harian = df_penjualan[df_penjualan["tanggal"] == tanggal_filter]
total_penjualan_harian = penjualan_harian["total"].sum()

st.info(f"💸 Total Modal pada {tanggal_filter.strftime('%d/%m/%Y')}: Rp {total_modal_harian:,.0f}")
st.success(f"🛍️ Total Penjualan pada {tanggal_filter.strftime('%d/%m/%Y')}: Rp {total_penjualan_harian:,.0f}")

colM, colP = st.columns(2)
with colM:
    st.info(f"💸 Total Modal pada {tanggal_filter.strftime('%d/%m/%Y')}: Rp {total_modal_harian:,.0f}")
with colP:
    st.success(f"🛍️ Total Penjualan pada {tanggal_filter.strftime('%d/%m/%Y')}: Rp {total_penjualan_harian:,.0f}")

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
    total_penjualan = df_penjualan["total"].sum()
    laba_bersih = total_penjualan - total_modal

    # ─── Ringkasan Total ─────────────────────────────
    st.subheader("💡 Ringkasan Keuangan")
    col1, col2, col3 = st.columns(3)
    col1.metric("🧾 Total Belanja", f"Rp {total_modal:,.0f}")
    col2.metric("🛒 Total Penjualan", f"Rp {total_penjualan:,.0f}")
    col3.metric("📈 Laba Bersih", f"Rp {laba_bersih:,.0f}")

    # ─── Grafik Interaktif ──────────────────────────
    st.subheader("📅 Pilih Interval Grafik")
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

    fig = px.line(df_chart, x="tanggal", y="total", title=f"📊 Grafik Penjualan {mode}", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    # ─── Pie Chart Produk Terjual ─────────────────────
    st.subheader("📊 Distribusi Penjualan per Produk")

    pie_data = df_penjualan.groupby("produk")["total"].sum().reset_index().sort_values("total", ascending=False)
    
    pie_chart = px.pie(
        pie_data,
        names="produk",
        values="total",
        title="Proporsi Penjualan Berdasarkan Produk",
        hole=0.4
    )
    st.plotly_chart(pie_chart, use_container_width=True)

