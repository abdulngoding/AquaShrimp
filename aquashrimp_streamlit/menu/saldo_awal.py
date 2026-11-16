"""
AquaShrimp SIA (Streamlit) - Saldo Awal
Isi saldo awal setiap akun. Tiap akun otomatis masuk ke sisi normalnya (debit atau kredit).
Total debit harus sama dengan total kredit. Disimpan sebagai jurnal ref 'SA'.
"""

import datetime

import pandas as pd
import streamlit as st

import database as db
from umum import rupiah, tampil_tanggal

MODAL_PEMILIK = "Modal Pemilik"


def _data_awal():
    """Tabel awal: semua akun, jumlah diisi dari saldo awal yang sudah tersimpan (kalau ada)."""
    _, tersimpan = db.saldo_awal()
    return pd.DataFrame([
        {"Kode": a["kode"], "Akun": a["nama"], "Sisi normal": a["saldo_normal"],
         "Jumlah (Rp)": tersimpan.get(a["nama"], 0)}
        for a in db.akun_saldo_awal()
    ])


def _total(tabel_isi):
    debit = int(tabel_isi.loc[tabel_isi["Sisi normal"] == "debit", "Jumlah (Rp)"].fillna(0).sum())
    kredit = int(tabel_isi.loc[tabel_isi["Sisi normal"] == "kredit", "Jumlah (Rp)"].fillna(0).sum())
    return debit, kredit


def tampil():
    st.title("Saldo Awal")
    st.caption("Isi saldo awal akun, lalu klik Hitung modal otomatis supaya Modal Pemilik terisi dari selisihnya.")

    if "tabel_sa" not in st.session_state:
        st.session_state["tabel_sa"] = _data_awal()
        st.session_state["versi_sa"] = 0

    tgl_tersimpan, _ = db.saldo_awal()
    if tgl_tersimpan:
        st.info(f"Saldo awal sudah tersimpan (tanggal {tampil_tanggal(tgl_tersimpan)}). Menyimpan lagi akan menggantikannya.")
        tanggal_bawaan = datetime.date.fromisoformat(tgl_tersimpan)
    else:
        tanggal_bawaan = datetime.date.today()
    tanggal = st.date_input("Tanggal saldo awal", value=tanggal_bawaan)

    isi = st.data_editor(
        st.session_state["tabel_sa"], hide_index=True, width="stretch", height=500,
        disabled=["Kode", "Akun", "Sisi normal"], key=f"editor_sa_{st.session_state['versi_sa']}",
        column_config={"Jumlah (Rp)": st.column_config.NumberColumn("Jumlah (Rp)", min_value=0, step=1, format="%d")},
    )

    debit, kredit = _total(isi)
    k1, k2, k3 = st.columns(3)
    k1.metric("Total debit", rupiah(debit))
    k2.metric("Total kredit", rupiah(kredit))
    k3.metric("Selisih", rupiah(abs(debit - kredit)))

    tombol1, tombol2, tombol3 = st.columns(3)
    if tombol1.button("Hitung modal otomatis"):
        lain = isi[isi["Akun"] != MODAL_PEMILIK]
        d, k = _total(lain)
        modal = d - k
        if modal < 0:
            st.error("Kredit selain Modal Pemilik lebih besar dari debit, modal tidak bisa dihitung otomatis.")
        else:
            baru = isi.copy()
            baru.loc[baru["Akun"] == MODAL_PEMILIK, "Jumlah (Rp)"] = modal
            st.session_state["tabel_sa"] = baru
            st.session_state["versi_sa"] += 1  # ganti key supaya tabel dibuat ulang dengan nilai baru
            st.rerun()

    if tombol2.button("Simpan saldo awal", type="primary"):
        nilai = {r["Akun"]: int(r["Jumlah (Rp)"]) for r in isi.to_dict("records") if r["Jumlah (Rp)"]}
        try:
            db.simpan_saldo_awal(tanggal.isoformat(), nilai)
            st.success("Saldo awal tersimpan.")
        except ValueError as galat:
            st.error(str(galat))

    if tombol3.button("Hapus saldo awal"):
        db.hapus_saldo_awal()
        st.session_state.pop("tabel_sa", None)
        st.rerun()
