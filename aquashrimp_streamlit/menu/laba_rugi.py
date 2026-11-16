"""
AquaShrimp SIA (Streamlit) - Laporan Laba Rugi
  Laba kotor  = Pendapatan - HPP
  Laba bersih = Laba kotor - Beban operasional
Akun dikelompokkan lewat KATEGORI-nya, jadi akun baru otomatis ikut terhitung.
"""

import streamlit as st

import database as db
from umum import angka, kosong, label_periode, pilih_periode, tabel


def _kumpulkan(akun, kategori):
    hasil = []
    for a in akun:
        if a["kategori"] != kategori or not (a["debit"] or a["kredit"]):
            continue
        # Arah ditentukan KATEGORI: pendapatan = kredit - debit, HPP dan beban = debit - kredit.
        nilai = a["kredit"] - a["debit"] if kategori == "Pendapatan" else a["debit"] - a["kredit"]
        hasil.append((a["nama"], nilai))
    return hasil


def tampil():
    st.title("Laporan Laba Rugi")
    periode = pilih_periode("periode_laba_rugi")
    st.caption(f"Periode: {label_periode(periode)}")

    akun = db.total_per_akun(periode or None)
    pendapatan, hpp, beban = _kumpulkan(akun, "Pendapatan"), _kumpulkan(akun, "HPP"), _kumpulkan(akun, "Beban")
    if not (pendapatan or hpp or beban):
        kosong("Belum ada pendapatan, HPP, atau beban pada periode ini.")
        return

    total_pendapatan = sum(n for _, n in pendapatan)
    total_hpp = sum(n for _, n in hpp)
    total_beban = sum(n for _, n in beban)
    laba_kotor = total_pendapatan - total_hpp
    laba_bersih = laba_kotor - total_beban

    def rincian(daftar):
        return [["     " + nama, angka(nilai)] for nama, nilai in daftar]

    baris = [["PENDAPATAN", ""]] + rincian(pendapatan)
    baris.append(["Total pendapatan", angka(total_pendapatan)])
    baris.append(["HARGA POKOK PENJUALAN", ""])
    baris += rincian(hpp)
    baris.append(["Total HPP", angka(total_hpp)])
    baris.append(["LABA KOTOR", angka(laba_kotor)])
    baris.append(["BEBAN OPERASIONAL", ""])
    baris += rincian(beban)
    baris.append(["Total beban", angka(total_beban)])
    baris.append(["LABA BERSIH" if laba_bersih >= 0 else "RUGI BERSIH", angka(abs(laba_bersih))])
    tabel(["Keterangan", "Jumlah (Rp)"], baris)

    st.metric("Laba bersih" if laba_bersih >= 0 else "Rugi bersih", "Rp " + angka(abs(laba_bersih)))
