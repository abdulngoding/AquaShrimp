"""
AquaShrimp SIA (Streamlit) - Neraca Saldo
Saldo bersisi debit ditaruh di kolom Debit, saldo bersisi kredit di kolom Kredit.
Total kedua kolom harus sama.
"""

import streamlit as st

import database as db
from umum import angka, angka_kosong, kosong, rupiah, tabel


def tampil():
    st.title("Neraca Saldo")
    st.caption("Daftar saldo akhir seluruh akun.")

    baris = []
    total_debit = total_kredit = 0
    for a in db.total_per_akun():
        if not (a["debit"] or a["kredit"]):
            continue  # akun yang belum pernah dipakai tidak ditampilkan
        bersih = a["debit"] - a["kredit"]
        debit, kredit = (bersih, 0) if bersih > 0 else (0, -bersih)
        total_debit += debit
        total_kredit += kredit
        baris.append([a["kode"], a["nama"], a["kategori"], angka_kosong(debit), angka_kosong(kredit)])

    if not baris:
        kosong("Belum ada transaksi di jurnal umum.")
        return

    baris.append(["", "TOTAL", "", angka(total_debit), angka(total_kredit)])
    tabel(["Kode", "Nama akun", "Kategori", "Debit (Rp)", "Kredit (Rp)"], baris)

    if total_debit == total_kredit:
        st.success("Seimbang: total debit sama dengan total kredit.")
    else:
        st.error(f"Tidak seimbang, selisih {rupiah(abs(total_debit - total_kredit))}")
