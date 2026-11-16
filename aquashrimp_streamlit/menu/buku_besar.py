"""
AquaShrimp SIA (Streamlit) - Buku Besar
Rincian mutasi per akun dengan saldo berjalan.
  saldo normal DEBIT  : saldo = debit - kredit  (aset, HPP, beban, prive)
  saldo normal KREDIT : saldo = kredit - debit  (utang, modal, pendapatan)
"""

import streamlit as st

import database as db
from umum import angka, angka_kosong, kosong, tabel, tampil_tanggal


def _tabel_akun(akun, semua_baris):
    saldo = total_d = total_k = 0
    baris = []
    for b in semua_baris:
        if b["keterangan"] != akun["nama"]:
            continue
        saldo += (b["debit"] - b["kredit"]) if akun["saldo_normal"] == "debit" else (b["kredit"] - b["debit"])
        total_d += b["debit"]
        total_k += b["kredit"]
        baris.append([tampil_tanggal(b["tanggal"]), b["uraian"], b["ref"],
                      angka_kosong(b["debit"]), angka_kosong(b["kredit"]), angka(saldo)])
    baris.append(["", "SALDO AKHIR", "", angka(total_d), angka(total_k), angka(saldo)])
    st.subheader(f"{akun['kode']}  {akun['nama']}")
    st.caption(f"{akun['kategori']}, saldo normal {akun['saldo_normal']}")
    tabel(["Tanggal", "Uraian", "Ref", "Debit (Rp)", "Kredit (Rp)", "Saldo (Rp)"], baris)


def tampil():
    st.title("Buku Besar")
    st.caption("Rincian mutasi dan saldo setiap akun.")

    aktif = [a for a in db.total_per_akun() if a["debit"] or a["kredit"]]
    if not aktif:
        kosong("Belum ada transaksi di jurnal umum.")
        return

    pilihan = ["semua"] + [a["kode"] for a in aktif]
    nama = {a["kode"]: f"{a['kode']}  {a['nama']}" for a in aktif}
    nama["semua"] = "Semua akun"
    kode = st.selectbox("Akun", pilihan, format_func=lambda k: nama[k])

    semua_baris = db.semua_baris()
    for a in aktif:
        if kode == "semua" or a["kode"] == kode:
            _tabel_akun(a, semua_baris)
