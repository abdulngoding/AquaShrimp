"""
AquaShrimp SIA (Streamlit) - Monitoring Persediaan
Memantau JUMLAH barang (ekor, kg, sak, box), terpisah dari nilai rupiah di jurnal.
Empat tab: Ringkasan, Catat Stok, Stok Awal, Riwayat.
Jumlah disimpan sebagai bilangan bulat x100 (SKALA), jadi 12,5 kg disimpan 1250.
"""

import datetime

import pandas as pd
import streamlit as st

import database as db
from umum import angka, kosong, rupiah, tabel, tampil_tanggal


def _ke_bulat(x):
    """Angka desimal dari kotak isian -> bilangan bulat x100."""
    return round(x * db.SKALA)


def _tab_ringkasan():
    if not db.ada_catatan_stok():
        kosong("Belum ada catatan stok. Isi dulu di tab Stok Awal.")
    data = db.ringkasan_stok()

    kolom = st.columns(len(data))
    for k, d in zip(kolom, data):
        k.metric(d["label"], f"{db.format_jumlah(d['sisa'])} {d['satuan']}", d["status"], delta_color="off")

    baris = []
    for d in data:
        baris.append([
            d["label"], d["satuan"], db.format_jumlah(d["awal"]), db.format_jumlah(d["masuk"]),
            db.format_jumlah(d["keluar"]), db.format_jumlah(d["sisa"]), db.format_jumlah(d["minimum"]),
            d["status"], angka(d["nilai"]), angka(d["harga"]) if d["harga"] else "-",
        ])
    tabel(["Barang", "Satuan", "Awal", "Masuk", "Keluar", "Sisa", "Minimum", "Status",
           "Nilai di Buku Besar (Rp)", "Harga rata-rata (Rp/satuan)"], baris)

    for d in data:
        if d["status"] != "Aman":
            st.warning(f"{d['label']}: stok {d['status'].lower()} ({db.format_jumlah(d['sisa'])} {d['satuan']}).")

    st.subheader("Grafik pergerakan stok")
    kode = st.selectbox("Barang", list(db.AKUN_PERSEDIAAN), format_func=lambda k: db.AKUN_PERSEDIAAN[k][0], key="grafik_stok")
    titik = db.tren_stok(kode)
    if len(titik) < 2:
        st.caption("Grafik muncul setelah ada minimal dua catatan pada tanggal berbeda.")
    else:
        st.line_chart(pd.DataFrame({"Sisa stok": [s / db.SKALA for _, s in titik]}, index=[t for t, _ in titik]))


def _tab_catat():
    with st.form("form_gerak", clear_on_submit=True):
        tanggal = st.date_input("Tanggal", value=datetime.date.today())
        kode = st.selectbox("Barang", list(db.AKUN_PERSEDIAAN), format_func=lambda k: db.AKUN_PERSEDIAAN[k][0])
        jenis = st.radio("Jenis", ["masuk", "keluar"], horizontal=True)
        jumlah = st.number_input("Jumlah (sesuai satuan barang)", min_value=0.0, step=0.01, format="%.2f")
        ket = st.text_input("Keterangan (opsional)")
        kirim = st.form_submit_button("Simpan catatan stok", type="primary")
    if kirim:
        try:
            db.simpan_gerak(tanggal.isoformat(), kode, jenis, _ke_bulat(jumlah), ket)
            st.success(f"Tercatat: {jenis} {jumlah:g} {db.satuan_barang(kode)} {db.AKUN_PERSEDIAAN[kode][0]}.")
        except ValueError as galat:
            st.error(str(galat))


def _tab_stok_awal():
    tgl, awal = db.stok_awal_tersimpan()
    tanggal = st.date_input("Tanggal stok awal", value=datetime.date.fromisoformat(tgl) if tgl else datetime.date.today())
    with st.form("form_stok_awal"):
        data = {}
        for kode, (label, satuan_pilihan) in db.AKUN_PERSEDIAAN.items():
            st.markdown(f"**{label}**")
            a, b, c = st.columns(3)
            satuan_sekarang = db.satuan_barang(kode)
            satuan = a.selectbox("Satuan", satuan_pilihan, index=satuan_pilihan.index(satuan_sekarang), key=f"sat_{kode}")
            jumlah = b.number_input("Stok awal", min_value=0.0, step=0.01, format="%.2f",
                                    value=awal.get(kode, 0) / db.SKALA, key=f"awal_{kode}")
            minimum = c.number_input("Batas minimum", min_value=0.0, step=0.01, format="%.2f",
                                     value=db.minimum_barang(kode) / db.SKALA, key=f"min_{kode}")
            data[kode] = (satuan, _ke_bulat(jumlah), _ke_bulat(minimum))
        kirim = st.form_submit_button("Simpan stok awal", type="primary")
    if kirim:
        try:
            db.simpan_stok_awal(tanggal.isoformat(), data)
            st.success("Stok awal tersimpan.")
        except ValueError as galat:
            st.error(str(galat))


def _tab_riwayat():
    riwayat = db.riwayat_stok()
    if not riwayat:
        kosong("Belum ada catatan stok.")
        return
    nama = {k: v[0] for k, v in db.AKUN_PERSEDIAAN.items()}
    tabel(["ID", "Tanggal", "Barang", "Jenis", "Jumlah", "Keterangan"],
          [[r["id"], tampil_tanggal(r["tanggal"]), nama[r["kode"]], r["jenis"],
            f"{db.format_jumlah(r['jumlah'])} {db.satuan_barang(r['kode'])}", r["keterangan"] or ""] for r in riwayat])

    dapat_dihapus = [r for r in riwayat if r["jenis"] != "awal"]
    if dapat_dihapus:
        pilihan = {r["id"]: f"#{r['id']}  {tampil_tanggal(r['tanggal'])}  {nama[r['kode']]}  {r['jenis']}  {db.format_jumlah(r['jumlah'])}"
                   for r in dapat_dihapus}
        id_gerak = st.selectbox("Hapus catatan (stok awal tidak bisa dihapus di sini)", list(pilihan), format_func=lambda i: pilihan[i])
        if st.button("Hapus catatan ini"):
            try:
                db.hapus_gerak(id_gerak)
                st.rerun()
            except ValueError as galat:
                st.error(str(galat))


def tampil():
    st.title("Monitoring Persediaan")
    st.caption("Pantau jumlah benur, pakan, obat, dan udang. Nilai rupiah diambil dari Buku Besar.")
    ringkasan, catat, awal, riwayat = st.tabs(["Ringkasan", "Catat Stok", "Stok Awal", "Riwayat"])
    with ringkasan:
        _tab_ringkasan()
    with catat:
        _tab_catat()
    with awal:
        _tab_stok_awal()
    with riwayat:
        _tab_riwayat()
