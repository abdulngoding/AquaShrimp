"""AquaShrimp SIA (Streamlit) - Reset Data: hapus transaksi, saldo awal, dan catatan stok. Daftar akun tetap ada."""

import streamlit as st

import database as db


def tampil():
    st.title("Reset Data")
    st.caption("Penghapusan seluruh data transaksi.")

    st.warning(
        f"Menghapus seluruh isi jurnal umum ({db.jumlah_transaksi()} transaksi saat ini). "
        "Saldo awal dan catatan stok persediaan ikut terhapus. Daftar akun tetap ada. "
        "Tindakan ini tidak dapat dibatalkan."
    )
    with st.form("form_reset"):
        konfirmasi = st.text_input("Ketik HAPUS untuk melanjutkan")
        kirim = st.form_submit_button("Hapus semua transaksi", type="primary")
    if kirim:
        if konfirmasi.strip() != "HAPUS":
            st.error("Konfirmasi salah. Ketik HAPUS (huruf besar) untuk melanjutkan.")
        else:
            db.hapus_semua_transaksi()
            st.success("Semua transaksi sudah dihapus.")
