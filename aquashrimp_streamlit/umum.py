"""
AquaShrimp SIA (Streamlit) - Fungsi bantu yang dipakai banyak halaman
Format angka rupiah, format tanggal, dan penampil tabel.
"""

import io

import pandas as pd
import streamlit as st
from openpyxl.styles import Font

import database as db

# Status stok diberi penanda warna supaya langsung terlihat di tabel
IKON_STATUS = {"Aman": "🟢 Aman", "Menipis": "🟡 Menipis", "Habis": "🔴 Habis"}

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
    baris = [[IKON_STATUS.get(sel, sel) if isinstance(sel, str) else sel for sel in b] for b in baris]
    st.dataframe(pd.DataFrame(baris, columns=kolom), hide_index=True, width="stretch")


def tombol_excel(kolom, baris, nama_file, nama_sheet="Data"):
    """
    Tombol Unduh Excel. baris harus berisi ANGKA ASLI (bukan teks berformat '1.234'),
    supaya di Excel nilainya bisa dijumlahkan dan dihitung.
    """
    berkas = io.BytesIO()
    with pd.ExcelWriter(berkas, engine="openpyxl") as penulis:
        pd.DataFrame(baris, columns=kolom).to_excel(penulis, sheet_name=nama_sheet, index=False)
        lembar = penulis.sheets[nama_sheet]
        for sel in lembar[1]:
            sel.font = Font(bold=True)  # judul kolom dicetak tebal
        for nomor, judul in enumerate(kolom):
            lebar = max([len(str(judul))] + [len(str(b[nomor])) for b in baris]) + 2
            lembar.column_dimensions[lembar.cell(row=1, column=nomor + 1).column_letter].width = min(lebar, 50)
        for baris_excel in lembar.iter_rows(min_row=2):
            for sel in baris_excel:
                if isinstance(sel.value, (int, float)):
                    sel.number_format = "#,##0"  # ribuan dipisah koma di Excel
    st.download_button(
        "Unduh Excel", data=berkas.getvalue(), file_name=nama_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def pilih_periode(kunci):
    """Kotak pilihan periode laporan. Mengembalikan '' (semua), '2026', atau '2026-10'."""
    bulan, tahun = db.daftar_periode()
    pilihan = [""] + tahun + bulan
    return st.selectbox("Periode", pilihan, format_func=label_periode, key=kunci)


def kosong(pesan):
    st.info(pesan)
