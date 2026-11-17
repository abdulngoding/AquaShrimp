"""AquaShrimp SIA (Streamlit) - Jurnal Penerimaan Kas: transaksi yang membuat Kas bertambah (Kas di debit)."""

import streamlit as st

import database as db
from umum import angka, kosong, rupiah, tabel, tampil_tanggal, tombol_excel


def tampil():
    st.title("Jurnal Penerimaan Kas")
    st.caption("Daftar transaksi penerimaan kas.")

    penerimaan = [t for t in db.transaksi_kas() if t["kas"] > 0]
    if not penerimaan:
        kosong("Belum ada penerimaan kas di jurnal umum.")
        return

    st.write(f"{len(penerimaan)} penerimaan. Saldo kas saat ini {rupiah(db.saldo_akun(db.KAS))}")
    baris = [[tampil_tanggal(t["tanggal"]), t["ref"], t["uraian"], ", ".join(t["lawan"]), angka(t["kas"])]
             for t in penerimaan]
    baris.append(["", "", "TOTAL PENERIMAAN", "", angka(sum(t["kas"] for t in penerimaan))])
    tabel(["Tanggal", "Ref", "Uraian", "Akun kredit", "Kas, debit (Rp)"], baris)

    # Versi Excel memakai angka asli (bukan teks berformat) supaya bisa dijumlah di Excel
    baris_excel = [[tampil_tanggal(t["tanggal"]), t["ref"], t["uraian"], ", ".join(t["lawan"]), t["kas"]]
                   for t in penerimaan]
    baris_excel.append(["", "", "TOTAL PENERIMAAN", "", sum(b[4] for b in baris_excel)])
    tombol_excel(["Tanggal", "Ref", "Uraian", "Akun kredit", "Kas, debit (Rp)"], baris_excel, "jurnal_penerimaan_kas.xlsx", "Penerimaan Kas")
