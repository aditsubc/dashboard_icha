import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
from datetime import datetime

# ========== Supabase Credentials ==========
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ========== Judul ==========
st.set_page_config(page_title="Dashboard Penjualan & Modal", layout="wide")
st.title("📊 Dashboard Penjualan & Modal Produksi")

# ========== Ambil Data ==========
modal_data = supabase.table("modal_produksi").select("*").execute().data
penjualan_data = supabase.table("data_penjualan").select("*").execute().data

df_modal = pd.DataFrame(modal_data)
df_penjualan = pd.DataFrame(penjualan_data)

if not df_modal.empty:
    df_modal["tanggal"] = pd.to_datetime(df_modal["tanggal"]).dt.date

if not df_penjualan.empty:
    df_penjualan["tanggal"] = pd.to_datetime(df_penjualan["tanggal"]).dt.date

# ========== Ringkasan Keuangan ==========
st.header("📌 Ringkasan Keuangan")

col1, col2 = st.columns(2)
with col1:
    total_modal = df_modal["total"].sum()
    st.metric("💸 Total Belanja (Modal Produksi)", f"Rp {total_modal:,.0f}")

with col2:
    total_penjualan = df_penjualan["total"].sum()
    st.metric("🛍️ Total Penjualan", f"Rp {total_penjualan:,.0f}")

# ========== Filter Tanggal ==========
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

# ========== Grafik Garis ==========
st.subheader("📈 Grafik Garis Penjualan & Modal")
if not df_penjualan.empty and not df_modal.empty:
    df_modal_agg = df_modal.groupby("tanggal")["total"].sum().reset_index(name="Total Modal")
    df_penjualan_agg = df_penjualan.groupby("tanggal")["total"].sum().reset_index(name="Total Penjualan")

    df_combined = pd.merge(df_modal_agg, df_penjualan_agg, on="tanggal", how="outer").fillna(0)

    df_long = pd.melt(df_combined, id_vars="tanggal", var_name="Tipe", value_name="Total")
    fig = px.line(df_long, x="tanggal", y="Total", color="Tipe", markers=True,
                  title="Tren Harian Modal vs Penjualan")
    st.plotly_chart(fig, use_container_width=True)

# ========== Pie Chart ==========
st.subheader("🥧 Komposisi Penjualan Berdasarkan Produk")
if not df_penjualan.empty:
    df_pie = df_penjualan.groupby("produk")["total"].sum().reset_index()
    fig_pie = px.pie(df_pie, names="produk", values="total", title="Persentase Penjualan per Produk")
    st.plotly_chart(fig_pie, use_container_width=True)

# ========== Tabel Opsional ==========
with st.expander("📄 Lihat Data Lengkap"):
    st.write("🧾 Modal Produksi")
    st.dataframe(df_modal)

    st.write("🧾 Data Penjualan")
    st.dataframe(df_penjualan)
