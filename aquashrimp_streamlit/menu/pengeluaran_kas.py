"""AquaShrimp SIA (Streamlit) - Jurnal Pengeluaran Kas: transaksi yang membuat Kas berkurang (Kas di kredit)."""

import streamlit as st

import database as db
from umum import angka, kosong, rupiah, tabel, tampil_tanggal


def tampil():
    st.title("Jurnal Pengeluaran Kas")
    st.caption("Daftar transaksi pengeluaran kas.")

    pengeluaran = [t for t in db.transaksi_kas() if t["kas"] < 0]
    if not pengeluaran:
        kosong("Belum ada pengeluaran kas di jurnal umum.")
        return

    st.write(f"{len(pengeluaran)} pengeluaran. Saldo kas saat ini {rupiah(db.saldo_akun(db.KAS))}")
    baris = [[tampil_tanggal(t["tanggal"]), t["ref"], t["uraian"], ", ".join(t["lawan"]), angka(-t["kas"])]
             for t in pengeluaran]
    baris.append(["", "", "TOTAL PENGELUARAN", "", angka(-sum(t["kas"] for t in pengeluaran))])
    tabel(["Tanggal", "Ref", "Uraian", "Akun debit", "Kas, kredit (Rp)"], baris)
