"""
AquaShrimp SIA (Streamlit) - File utama
Jalankan dengan:  streamlit run AquaShrimp.py
100% Python: tampilan dibuat dengan komponen Streamlit, tanpa HTML, CSS, atau JavaScript.

Alur: login -> menu di sidebar -> setiap menu adalah satu fungsi tampil() di folder menu/.
"""

import streamlit as st

import akses
from menu import (buku_besar, dashboard, jurnal_umum, laba_rugi, neraca_saldo,
                  penerimaan_kas, pengeluaran_kas, persediaan, reset_data, saldo_awal)

st.set_page_config(page_title="AquaShrimp SIA", page_icon=akses.LOGO if akses.ADA_LOGO else None, layout="wide")

if not akses.sudah_masuk():
    akses.tampil_login()
    st.stop()

HALAMAN = [
    st.Page(dashboard.tampil, title="Dashboard", icon=":material/dashboard:", url_path="dashboard", default=True),
    st.Page(saldo_awal.tampil, title="Saldo Awal", icon=":material/account_balance:", url_path="saldo-awal"),
    st.Page(jurnal_umum.tampil, title="Jurnal Umum", icon=":material/edit_note:", url_path="jurnal-umum"),
    st.Page(buku_besar.tampil, title="Buku Besar", icon=":material/menu_book:", url_path="buku-besar"),
    st.Page(neraca_saldo.tampil, title="Neraca Saldo", icon=":material/balance:", url_path="neraca-saldo"),
    st.Page(penerimaan_kas.tampil, title="Jurnal Penerimaan Kas", icon=":material/call_received:", url_path="penerimaan-kas"),
    st.Page(pengeluaran_kas.tampil, title="Jurnal Pengeluaran Kas", icon=":material/call_made:", url_path="pengeluaran-kas"),
    st.Page(laba_rugi.tampil, title="Laporan Laba Rugi", icon=":material/trending_up:", url_path="laba-rugi"),
    st.Page(persediaan.tampil, title="Monitoring Persediaan", icon=":material/inventory_2:", url_path="persediaan"),
    st.Page(reset_data.tampil, title="Reset Data", icon=":material/delete_forever:", url_path="reset"),
]

halaman = st.navigation(HALAMAN)

with st.sidebar:
    if akses.ADA_LOGO:
        st.image(akses.LOGO, width=90)
    st.caption(f"Masuk sebagai **{st.session_state['user']}**")
    if st.button("Keluar", width="stretch"):
        akses.keluar()

# Isi menu dibungkus kotak berbingkai supaya tampilan lebih rapi
with st.container(border=True):
    halaman.run()
