"""
AquaShrimp SIA (Streamlit) - Jurnal Umum
Tiga tab: daftar transaksi, catat transaksi baru, dan hapus transaksi / tambah akun baru.
Setiap transaksi wajib seimbang (total debit = total kredit), dicek lagi di database.py.
"""

import datetime

import streamlit as st

import database as db
from umum import angka, angka_kosong, kosong, tabel, tampil_tanggal


def _tab_daftar():
    kelompok = db.kelompok_transaksi()
    if not kelompok:
        kosong("Belum ada transaksi. Catat transaksi pertama di tab Catat Transaksi.")
        return
    baris = []
    for ref, grup in kelompok.items():
        for i, b in enumerate(grup):
            # tanggal, ref, dan uraian hanya ditulis di baris pertama tiap transaksi
            baris.append([
                tampil_tanggal(b["tanggal"]) if i == 0 else "",
                ref if i == 0 else "",
                b["uraian"] if i == 0 else "",
                ("     " if b["kredit"] else "") + b["keterangan"],
                angka_kosong(b["debit"]), angka_kosong(b["kredit"]),
            ])
    tabel(["Tanggal", "Ref", "Uraian", "Akun", "Debit (Rp)", "Kredit (Rp)"], baris)


def _tab_catat():
    nama_akun = [a["nama"] for a in db.daftar_akun()]
    st.caption(f"Nomor bukti berikutnya: {db.ref_berikutnya()}")
    jumlah_baris = st.number_input("Jumlah baris jurnal", min_value=2, max_value=12, value=2, step=1)
    st.write("Pada setiap baris, isi salah satu saja: Debit atau Kredit.")

    with st.form("form_transaksi"):
        tanggal = st.date_input("Tanggal", value=datetime.date.today())
        uraian = st.text_input("Uraian transaksi")
        isian = []
        for i in range(int(jumlah_baris)):
            a, b, c = st.columns([3, 1, 1])
            akun = a.selectbox(f"Akun baris {i + 1}", [""] + nama_akun, key=f"akun_{i}")
            debit = b.number_input("Debit (Rp)", min_value=0, step=1, key=f"debit_{i}")
            kredit = c.number_input("Kredit (Rp)", min_value=0, step=1, key=f"kredit_{i}")
            isian.append((akun, debit, kredit))
        simpan = st.form_submit_button("Simpan transaksi", type="primary")

    if not simpan:
        return
    if not uraian.strip():
        st.error("Uraian transaksi wajib diisi.")
        return

    isi = []
    for no, (akun, debit, kredit) in enumerate(isian, start=1):
        if not akun and not debit and not kredit:
            continue  # baris kosong dilewati
        if not akun or not db.cari_akun(akun):
            st.error(f"Baris {no}: akun belum dipilih.")
            return
        if debit and kredit:
            st.error(f"Baris {no}: isi salah satu saja, Debit atau Kredit.")
            return
        if not debit and not kredit:
            st.error(f"Baris {no}: nominal tidak boleh 0.")
            return
        isi.append((akun, int(debit), int(kredit)))

    try:
        ref = db.simpan_transaksi(tanggal.isoformat(), uraian.strip(), isi)
    except ValueError as galat:
        st.error(str(galat))
        return
    st.success(f"Transaksi {ref} tersimpan. Lihat di tab Daftar Transaksi.")


def _tab_kelola():
    st.subheader("Hapus transaksi")
    daftar = db.daftar_transaksi()
    if not daftar:
        kosong("Belum ada transaksi yang bisa dihapus.")
    else:
        pilihan = {t["ref"]: f"{t['ref']}  {tampil_tanggal(t['tanggal'])}  {t['uraian']}  (Rp {angka(t['total'])})"
                   for t in daftar}
        ref = st.selectbox("Pilih transaksi", list(pilihan), format_func=lambda r: pilihan[r])
        if st.button("Hapus transaksi ini"):
            db.hapus_transaksi(ref)
            st.success(f"Transaksi {ref} dihapus.")
            st.rerun()

    st.subheader("Tambah akun baru")
    with st.form("form_akun_baru", clear_on_submit=True):
        nama = st.text_input("Nama akun")
        kategori = st.selectbox("Kategori", db.KATEGORI)
        kirim = st.form_submit_button("Tambah akun")
    if kirim:
        try:
            kode = db.tambah_akun(nama, kategori)
            st.success(f"Akun '{nama.strip()}' ditambahkan dengan kode {kode}.")
        except ValueError as galat:
            st.error(str(galat))


def tampil():
    st.title("Jurnal Umum")
    st.caption("Catatan seluruh transaksi keuangan.")
    daftar, catat, kelola = st.tabs(["Daftar Transaksi", "Catat Transaksi", "Hapus / Akun Baru"])
    with daftar:
        _tab_daftar()
    with catat:
        _tab_catat()
    with kelola:
        _tab_kelola()
