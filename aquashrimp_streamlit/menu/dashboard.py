"""AquaShrimp SIA (Streamlit) - Dashboard: ringkasan kas, pendapatan, laba, dan transaksi terbaru."""

import pandas as pd
import streamlit as st

import database as db
from umum import angka, kosong, rupiah, tabel, tampil_tanggal


def total_kategori(akun, kategori):
    total = 0
    for a in akun:
        if a["kategori"] == kategori:
            # pendapatan = kredit - debit; HPP dan beban = debit - kredit (retur/potongan mengurangi pendapatan)
            total += a["kredit"] - a["debit"] if kategori == "Pendapatan" else a["debit"] - a["kredit"]
    return total


def tampil():
    st.title("Dashboard")
    st.caption("Ringkasan posisi keuangan AquaShrimp.")

    akun = db.total_per_akun()
    pendapatan = total_kategori(akun, "Pendapatan")
    hpp = total_kategori(akun, "HPP")
    beban = total_kategori(akun, "Beban")
    laba = pendapatan - hpp - beban

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Saldo kas", rupiah(db.saldo_akun(db.KAS)))
    k2.metric("Pendapatan", rupiah(pendapatan))
    k3.metric("Laba bersih" if laba >= 0 else "Rugi bersih", rupiah(abs(laba)))
    k4.metric("Transaksi tercatat", db.jumlah_transaksi())

    if pendapatan or hpp or beban:
        st.subheader("Pendapatan, HPP, dan beban")
        data = pd.DataFrame({"Rupiah": [pendapatan, hpp, beban]}, index=["Pendapatan", "HPP", "Beban"])
        st.bar_chart(data)

    st.subheader("Transaksi terbaru")
    terbaru = db.daftar_transaksi()[-5:]
    if not terbaru:
        kosong("Belum ada transaksi. Isi menu Saldo Awal atau catat transaksi di menu Jurnal Umum.")
    else:
        tabel(["Tanggal", "Ref", "Uraian", "Nilai (Rp)"],
              [[tampil_tanggal(t["tanggal"]), t["ref"], t["uraian"], angka(t["total"])] for t in reversed(terbaru)])
