"""
AquaShrimp SIA (Streamlit) - Fungsi bantu yang dipakai banyak halaman
Format angka rupiah, format tanggal, dan penampil tabel.
"""

import pandas as pd
import streamlit as st

import database as db

NAMA_BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def angka(n):
    """1234567 -> '1.234.567' (pemisah ribuan titik). Nilai negatif diberi tanda minus."""
    teks = f"{abs(int(n)):,}".replace(",", ".")
    return "-" + teks if n < 0 else teks


def angka_kosong(n):
    """Seperti angka(), tetapi nilai 0 ditampilkan sebagai tanda strip."""
    return angka(n) if n else "-"


def rupiah(n):
    return "Rp " + angka(n)


def tampil_tanggal(iso):
    """'2026-10-05' -> '05/10/2026'."""
    t, b, h = iso.split("-")
    return f"{h}/{b}/{t}"


def label_periode(periode):
    if not periode:
        return "Semua periode"
    if len(periode) == 4:
        return f"Tahun {periode}"
    return f"{NAMA_BULAN[int(periode[5:7]) - 1]} {periode[:4]}"


def tabel(kolom, baris):
    """Menampilkan tabel. kolom = daftar judul, baris = daftar baris (daftar nilai)."""
    st.dataframe(pd.DataFrame(baris, columns=kolom), hide_index=True, width="stretch")


def pilih_periode(kunci):
    """Kotak pilihan periode laporan. Mengembalikan '' (semua), '2026', atau '2026-10'."""
    bulan, tahun = db.daftar_periode()
    pilihan = [""] + tahun + bulan
    return st.selectbox("Periode", pilihan, format_func=label_periode, key=kunci)


def kosong(pesan):
    st.info(pesan)
