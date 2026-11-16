"""
AquaShrimp SIA (versi web) - Database (SQLite).
sqlite3 sudah bawaan Python, jadi tetap pure Python (tanpa install apa pun).

Dua tabel:
  akun         : daftar akun (kode, nama, kategori, saldo normal)
  jurnal_umum  : semua baris jurnal (satu transaksi = beberapa baris dengan ref sama)

Semua rupiah disimpan sebagai bilangan bulat (INTEGER) supaya tidak ada selisih
pembulatan seperti pada angka desimal.
"""

import os
import sqlite3
import threading

KAS = "Kas"  # nama akun yang dipakai Jurnal Penerimaan/Pengeluaran Kas
REF_SALDO_AWAL = "SA"  # nomor bukti khusus untuk saldo awal (transaksi biasa memakai J001, J002, ...)
URAIAN_SALDO_AWAL = "Saldo awal"
NAMA_BEBAN_PENYUSUTAN = "Beban Penyusutan"

# Persediaan yang dipantau jumlahnya: kode akun -> (nama pendek, satuan yang boleh dipilih).
# Satuan pertama adalah bawaan. Setiap akun memakai SATU satuan supaya angkanya konsisten.
AKUN_PERSEDIAAN = {
    "1103": ("Benur", ["ekor", "box"]),
    "1104": ("Pakan", ["kg", "sak"]),
    "1105": ("Obat & Probiotik", ["kg", "box"]),
    "1106": ("Udang Pemeliharaan", ["kg", "ekor"]),
    "1107": ("Udang Siap Jual", ["kg", "ekor"]),
}
SKALA = 100  # jumlah disimpan sebagai bilangan bulat x100 (dua angka di belakang koma)

LOKASI_DB = os.environ.get("AQUASHRIMP_DB") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "aquashrimp.db"
)

KATEGORI = ["Aset", "Utang", "Modal", "Pendapatan", "HPP", "Beban"]
PREFIKS_KODE = {"Aset": "1", "Utang": "2", "Modal": "3", "Pendapatan": "4", "HPP": "5", "Beban": "5"}
SALDO_NORMAL = {
    "Aset": "debit",
    "Utang": "kredit",
    "Modal": "kredit",
    "Pendapatan": "kredit",
    "HPP": "debit",
    "Beban": "debit",
}

# Akun bawaan untuk usaha tambak udang: (kode, nama, kategori, saldo normal)
AKUN_AWAL = [
    # Aset lancar
    ("1101", "Kas", "Aset", "debit"),
    ("1102", "Piutang Usaha", "Aset", "debit"),
    ("1103", "Persediaan Benur", "Aset", "debit"),
    ("1104", "Persediaan Pakan", "Aset", "debit"),
    ("1105", "Persediaan Obat, Probiotik & Vitamin", "Aset", "debit"),
    ("1106", "Persediaan Udang dalam Pemeliharaan", "Aset", "debit"),
    ("1107", "Persediaan Udang Siap Jual", "Aset", "debit"),
    ("1108", "Perlengkapan", "Aset", "debit"),
    ("1109", "Uang Muka Pembelian", "Aset", "debit"),
    # Aset tetap
    ("1201", "Tanah", "Aset", "debit"),
    ("1202", "Kolam & Bangunan Tambak", "Aset", "debit"),
    ("1203", "Mesin", "Aset", "debit"),
    ("1204", "Peralatan Tambak", "Aset", "debit"),  # kincir, pompa, genset
    ("1205", "Kendaraan", "Aset", "debit"),
    # Akumulasi penyusutan: tergolong aset, tapi saldo normalnya KREDIT (pengurang aset)
    ("1212", "Akum. Penyusutan Kolam & Bangunan", "Aset", "kredit"),
    ("1213", "Akum. Penyusutan Mesin", "Aset", "kredit"),
    ("1214", "Akum. Penyusutan Peralatan Tambak", "Aset", "kredit"),
    ("1215", "Akum. Penyusutan Kendaraan", "Aset", "kredit"),
    # Utang
    ("2101", "Utang Usaha", "Utang", "kredit"),
    ("2102", "Utang Gaji", "Utang", "kredit"),
    ("2103", "Utang Bunga", "Utang", "kredit"),
    ("2201", "Utang Bank / Pinjaman Jangka Panjang", "Utang", "kredit"),
    # Modal
    ("3101", "Modal Pemilik", "Modal", "kredit"),
    ("3102", "Prive", "Modal", "debit"),
    ("3103", "Ikhtisar Laba Rugi", "Modal", "kredit"),
    # Pendapatan (retur dan potongan penjualan bersaldo normal DEBIT, mengurangi penjualan)
    ("4101", "Penjualan Udang", "Pendapatan", "kredit"),
    ("4102", "Retur Penjualan", "Pendapatan", "debit"),
    ("4103", "Potongan Penjualan", "Pendapatan", "debit"),
    ("4201", "Pendapatan Lain-lain", "Pendapatan", "kredit"),
    # HPP
    ("5101", "HPP Udang", "HPP", "debit"),
    # Beban produksi
    ("5201", "Beban Listrik Tambak", "Beban", "debit"),
    ("5202", "Beban Solar & BBM", "Beban", "debit"),
    ("5203", "Beban Gaji Pegawai Tambak", "Beban", "debit"),
    ("5204", "Biaya Perawatan Tambak", "Beban", "debit"),
    ("5205", "Beban Angkut/Pengiriman", "Beban", "debit"),
    ("5206", "Beban Peralatan", "Beban", "debit"),
    ("5207", "Beban Kerugian Udang", "Beban", "debit"),
    ("5208", "Beban Pemeliharaan Tambak", "Beban", "debit"),
    ("5209", "Beban Lain-lain", "Beban", "debit"),
    ("5210", NAMA_BEBAN_PENYUSUTAN, "Beban", "debit"),
]

def kelompok_akun(kode, kategori):
    """Judul kelompok akun di daftar pilihan (dropdown)."""
    if kategori == "Aset":
        return "Aset lancar" if kode.startswith("11") else "Aset tetap"
    if kategori == "Beban":
        return "Beban produksi"
    return kategori


_lokal = threading.local()   # satu koneksi untuk setiap thread (Streamlit memakai banyak thread)


def koneksi():
    """Membuka database untuk thread ini (sekali saja), sekaligus membuat tabel kalau belum ada."""
    db = getattr(_lokal, "db", None)
    if db is None:
        db = sqlite3.connect(LOKASI_DB, timeout=30)
        db.row_factory = sqlite3.Row
        _siapkan(db)
        _lokal.db = db
    return db


def _siapkan(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS akun (
            kode         TEXT PRIMARY KEY,
            nama         TEXT NOT NULL UNIQUE,
            kategori     TEXT NOT NULL,
            saldo_normal TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS jurnal_umum (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal    TEXT NOT NULL,
            uraian     TEXT NOT NULL,
            keterangan TEXT NOT NULL,
            ref        TEXT NOT NULL,
            debit      INTEGER NOT NULL DEFAULT 0,
            kredit     INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS stok_barang (
            kode    TEXT PRIMARY KEY,
            satuan  TEXT NOT NULL,
            minimum INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS stok_gerak (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal    TEXT NOT NULL,
            kode       TEXT NOT NULL,
            jenis      TEXT NOT NULL,
            jumlah     INTEGER NOT NULL,
            keterangan TEXT NOT NULL DEFAULT ''
        )
        """
    )
    for kode, (_, satuan) in AKUN_PERSEDIAAN.items():
        db.execute("INSERT OR IGNORE INTO stok_barang (kode, satuan, minimum) VALUES (?, ?, 0)", (kode, satuan[0]))
    kode_ada = {r[0] for r in db.execute("SELECT kode FROM akun")}
    jurnal_kosong = db.execute("SELECT COUNT(*) FROM jurnal_umum").fetchone()[0] == 0
    kode_awal = {a[0] for a in AKUN_AWAL}
    # Daftar akun diisi saat pertama kali jalan. Kalau yang tersimpan masih daftar versi lama
    # dan belum ada transaksi, daftar akun diganti dengan yang baru (aman, tidak ada data terhapus).
    if not kode_ada or (jurnal_kosong and not kode_awal <= kode_ada):
        db.execute("DELETE FROM akun")
        db.executemany("INSERT INTO akun VALUES (?, ?, ?, ?)", AKUN_AWAL)
    # Akun yang ditambahkan di versi baru (Beban Penyusutan) dimasukkan ke database lama tanpa
    # mengubah data apa pun. Kalau kodenya sudah dipakai akun lain, dipakai kode kosong berikutnya.
    if not db.execute("SELECT 1 FROM akun WHERE lower(nama) = lower(?)", (NAMA_BEBAN_PENYUSUTAN,)).fetchone():
        kode = "5210"
        while db.execute("SELECT 1 FROM akun WHERE kode = ?", (kode,)).fetchone():
            kode = str(int(kode) + 1)
        db.execute("INSERT INTO akun VALUES (?, ?, 'Beban', 'debit')", (kode, NAMA_BEBAN_PENYUSUTAN))
    db.commit()


# ------------------------------------
#   AKUN
# ------------------------------------
def daftar_akun():
    return koneksi().execute("SELECT kode, nama, kategori, saldo_normal FROM akun ORDER BY kode").fetchall()


def cari_akun(kunci):
    """Cari akun lewat kode atau nama (huruf besar/kecil tidak berpengaruh)."""
    return koneksi().execute(
        "SELECT kode, nama, kategori, saldo_normal FROM akun WHERE kode = ? OR lower(nama) = lower(?)",
        (kunci.strip(), kunci.strip()),
    ).fetchone()


def tambah_akun(nama, kategori):
    """Menambah akun baru, mengembalikan kode akun. Gagal -> ValueError."""
    nama = " ".join(nama.split())
    if not nama:
        raise ValueError("Nama akun tidak boleh kosong.")
    if kategori not in KATEGORI:
        raise ValueError("Kategori tidak valid.")
    if cari_akun(nama):
        raise ValueError(f"Akun '{nama}' sudah ada.")

    db = koneksi()
    prefiks = PREFIKS_KODE[kategori]
    terbesar = db.execute(
        "SELECT MAX(CAST(kode AS INTEGER)) FROM akun WHERE kode LIKE ?", (prefiks + "%",)
    ).fetchone()[0]
    kode = str(terbesar + 1) if terbesar else prefiks + "101"
    with db:
        db.execute("INSERT INTO akun VALUES (?, ?, ?, ?)", (kode, nama, kategori, SALDO_NORMAL[kategori]))
    return kode


# ------------------------------------
#   TRANSAKSI
# ------------------------------------
def ref_berikutnya():
    """Nomor bukti transaksi berikutnya: J001, J002, ..."""
    semua = koneksi().execute("SELECT ref FROM jurnal_umum").fetchall()
    angka = [int(r["ref"][1:]) for r in semua if r["ref"][1:].isdigit()]
    return f"J{(max(angka) if angka else 0) + 1:03d}"


def simpan_transaksi(tanggal, uraian, baris):
    """
    Menyimpan satu transaksi. baris = [(nama_akun, debit, kredit), ...]
    Syarat: minimal 2 baris dan total debit = total kredit. Gagal -> ValueError.
    """
    total_debit = sum(b[1] for b in baris)
    total_kredit = sum(b[2] for b in baris)
    if len(baris) < 2 or total_debit == 0 or total_debit != total_kredit:
        raise ValueError("Transaksi harus punya minimal 2 baris dengan total debit = total kredit.")

    ref = ref_berikutnya()
    db = koneksi()
    with db:  # semua baris tersimpan sekaligus, atau batal semua kalau ada error
        db.executemany(
            "INSERT INTO jurnal_umum (tanggal, uraian, keterangan, ref, debit, kredit) VALUES (?, ?, ?, ?, ?, ?)",
            [(tanggal, uraian, akun, ref, d, k) for akun, d, k in baris],
        )
    return ref


def hapus_transaksi(ref):
    db = koneksi()
    with db:
        db.execute("DELETE FROM jurnal_umum WHERE ref = ?", (ref,))


def hapus_semua_transaksi():
    db = koneksi()
    with db:
        db.execute("DELETE FROM jurnal_umum")
        db.execute("DELETE FROM sqlite_sequence WHERE name = 'jurnal_umum'")
        db.execute("DELETE FROM stok_gerak")  # catatan stok ikut dikosongkan (satuan dan batas minimum tetap)


def jumlah_transaksi():
    """Jumlah transaksi biasa (saldo awal tidak dihitung sebagai transaksi)."""
    return koneksi().execute(
        "SELECT COUNT(DISTINCT ref) FROM jurnal_umum WHERE ref != ?", (REF_SALDO_AWAL,)
    ).fetchone()[0]


def daftar_transaksi():
    """Satu baris per transaksi (buat daftar pilihan hapus)."""
    return koneksi().execute(
        """
        SELECT ref, MIN(tanggal) AS tanggal, MIN(uraian) AS uraian, SUM(debit) AS total
        FROM jurnal_umum WHERE ref != ? GROUP BY ref ORDER BY MIN(tanggal), MIN(id)
        """,
        (REF_SALDO_AWAL,),
    ).fetchall()


# ------------------------------------
#   SALDO AWAL
#   Disimpan sebagai satu jurnal biasa dengan ref 'SA', jadi Buku Besar dan Neraca Saldo
#   otomatis ikut menghitungnya tanpa perubahan.
# ------------------------------------
def akun_saldo_awal():
    """Semua akun boleh punya saldo awal, urut kode."""
    return list(daftar_akun())


def ada_saldo_awal():
    return koneksi().execute(
        "SELECT 1 FROM jurnal_umum WHERE ref = ? LIMIT 1", (REF_SALDO_AWAL,)
    ).fetchone() is not None


def saldo_awal():
    """(tanggal, {nama akun: nilai}) saldo awal yang tersimpan; (None, {}) kalau belum ada."""
    baris = koneksi().execute(
        "SELECT tanggal, keterangan, debit, kredit FROM jurnal_umum WHERE ref = ? ORDER BY id",
        (REF_SALDO_AWAL,),
    ).fetchall()
    if not baris:
        return None, {}
    normal = {a["nama"]: a["saldo_normal"] for a in daftar_akun()}
    nilai = {}
    for b in baris:
        # nilai dalam sisi normal akun (debit untuk aset dan beban, kredit untuk utang, modal, dan pendapatan)
        n = b["debit"] - b["kredit"] if normal.get(b["keterangan"]) == "debit" else b["kredit"] - b["debit"]
        nilai[b["keterangan"]] = nilai.get(b["keterangan"], 0) + n
    return baris[0]["tanggal"], nilai


def simpan_saldo_awal(tanggal, nilai):
    """
    nilai = {nama akun: jumlah}. Tiap akun otomatis masuk sisi normalnya (debit/kredit).
    Menggantikan saldo awal sebelumnya. Total debit harus sama dengan total kredit.
    """
    boleh = {a["nama"]: a["saldo_normal"] for a in akun_saldo_awal()}
    baris = []
    for nama, jumlah in nilai.items():
        if not jumlah:
            continue
        if nama not in boleh or jumlah < 0:
            raise ValueError(f"Akun '{nama}' tidak valid untuk saldo awal.")
        baris.append((tanggal, URAIAN_SALDO_AWAL, nama, jumlah if boleh[nama] == "debit" else 0,
                      jumlah if boleh[nama] == "kredit" else 0))
    total_debit = sum(b[3] for b in baris)
    total_kredit = sum(b[4] for b in baris)
    if not baris:
        raise ValueError("Isi minimal satu saldo.")
    if total_debit != total_kredit:
        raise ValueError(
            f"Total debit {total_debit:,} dan total kredit {total_kredit:,} belum sama.".replace(",", ".")
        )
    db = koneksi()
    with db:  # hapus yang lama dan simpan yang baru dalam satu langkah
        db.execute("DELETE FROM jurnal_umum WHERE ref = ?", (REF_SALDO_AWAL,))
        db.executemany(
            "INSERT INTO jurnal_umum (tanggal, uraian, keterangan, ref, debit, kredit) "
            "VALUES (?, ?, ?, '" + REF_SALDO_AWAL + "', ?, ?)",
            [(t, u, k, d, c) for t, u, k, d, c in baris],
        )


def hapus_saldo_awal():
    db = koneksi()
    with db:
        db.execute("DELETE FROM jurnal_umum WHERE ref = ?", (REF_SALDO_AWAL,))


# ------------------------------------
#   DATA UNTUK LAPORAN
# ------------------------------------
def semua_baris(periode=None):
    """
    Semua baris jurnal beserta data akunnya, urut tanggal lalu id.
    periode: None = semua, atau awalan tanggal seperti '2026-10' atau '2026'.
    """
    sql = """
        SELECT j.id, j.tanggal, j.uraian, j.keterangan, j.ref, j.debit, j.kredit,
               a.kode, a.kategori, a.saldo_normal
        FROM jurnal_umum j JOIN akun a ON a.nama = j.keterangan
    """
    parameter = ()
    if periode:
        sql += " WHERE j.tanggal LIKE ?"
        parameter = (periode + "%",)
    sql += " ORDER BY j.tanggal, j.id"
    return koneksi().execute(sql, parameter).fetchall()


def kelompok_transaksi(periode=None):
    """Baris jurnal dikelompokkan per transaksi: {ref: [baris, baris, ...]} (urut tanggal)."""
    hasil = {}
    for baris in semua_baris(periode):
        hasil.setdefault(baris["ref"], []).append(baris)
    return hasil


def total_per_akun(periode=None):
    """Total debit dan kredit untuk SETIAP akun (yang belum dipakai bernilai 0)."""
    sql = """
        SELECT a.kode, a.nama, a.kategori, a.saldo_normal,
               COALESCE(SUM(j.debit), 0) AS debit, COALESCE(SUM(j.kredit), 0) AS kredit
        FROM akun a LEFT JOIN jurnal_umum j ON j.keterangan = a.nama
    """
    parameter = ()
    if periode:
        sql += " AND j.tanggal LIKE ?"
        parameter = (periode + "%",)
    sql += " GROUP BY a.kode ORDER BY a.kode"
    return koneksi().execute(sql, parameter).fetchall()


def daftar_periode():
    """Bulan ('2026-10') dan tahun ('2026') yang punya transaksi, buat pilihan filter laporan."""
    bulan = [r[0] for r in koneksi().execute(
        "SELECT DISTINCT substr(tanggal, 1, 7) FROM jurnal_umum ORDER BY 1 DESC")]
    tahun = sorted({b[:4] for b in bulan}, reverse=True)
    return bulan, tahun


def saldo_akun(nama):
    """Saldo akhir akun, dihitung sesuai saldo normalnya (debit atau kredit)."""
    for r in total_per_akun():
        if r["nama"] == nama:
            return r["debit"] - r["kredit"] if r["saldo_normal"] == "debit" else r["kredit"] - r["debit"]
    return 0


def transaksi_kas():
    """
    Transaksi yang melibatkan akun Kas. 'kas' = perubahan bersih kas pada transaksi itu:
    positif = penerimaan kas, negatif = pengeluaran kas.
    """
    hasil = []
    for ref, grup in kelompok_transaksi().items():
        if ref == REF_SALDO_AWAL:
            continue  # saldo awal kas bukan penerimaan kas
        kas = sum(b["debit"] - b["kredit"] for b in grup if b["keterangan"] == KAS)
        if kas == 0:
            continue
        hasil.append(
            {
                "ref": ref,
                "tanggal": grup[0]["tanggal"],
                "uraian": grup[0]["uraian"],
                "kas": kas,
                "lawan": [b["keterangan"] for b in grup if b["keterangan"] != KAS],
            }
        )
    return hasil


# ------------------------------------
#   STOK PERSEDIAAN (jumlah, bukan rupiah)
#   Dipisah dari jurnal: jurnal mencatat NILAI (Rp), tabel ini mencatat JUMLAH
#   (ekor, kg, sak, box). Nilai Rp di halaman monitoring diambil dari saldo akun.
# ------------------------------------
def format_jumlah(n):
    """150000 (=1.500,00) -> '1.500'; 1250 -> '12,5'. Pemisah ribuan titik, desimal koma."""
    negatif = n < 0
    bulat, sisa = divmod(abs(int(n)), SKALA)
    teks = f"{bulat:,}".replace(",", ".")
    if sisa:
        teks += "," + f"{sisa:02d}".rstrip("0")
    return "-" + teks if negatif else teks


def satuan_barang(kode):
    r = koneksi().execute("SELECT satuan FROM stok_barang WHERE kode = ?", (kode,)).fetchone()
    return r["satuan"] if r else AKUN_PERSEDIAAN[kode][1][0]


def minimum_barang(kode):
    r = koneksi().execute("SELECT minimum FROM stok_barang WHERE kode = ?", (kode,)).fetchone()
    return r["minimum"] if r else 0


def atur_minimum(kode, minimum):
    with koneksi() as db:
        db.execute("UPDATE stok_barang SET minimum = ? WHERE kode = ?", (minimum, kode))


def ada_catatan_stok():
    return koneksi().execute("SELECT 1 FROM stok_gerak LIMIT 1").fetchone() is not None


def riwayat_stok(kode=None):
    """Catatan stok urut waktu (stok awal dulu, lalu masuk, lalu keluar pada tanggal yang sama)."""
    sql = """SELECT id, tanggal, kode, jenis, jumlah, keterangan FROM stok_gerak
             {where} ORDER BY tanggal, CASE jenis WHEN 'awal' THEN 0 WHEN 'masuk' THEN 1 ELSE 2 END, id"""
    if kode:
        return koneksi().execute(sql.format(where="WHERE kode = ?"), (kode,)).fetchall()
    return koneksi().execute(sql.format(where=""), ()).fetchall()


def _arah(jenis):
    return -1 if jenis == "keluar" else 1


def _pastikan_tidak_minus(kode):
    """Stok tidak boleh minus di titik waktu mana pun. Dipanggil di dalam transaksi database."""
    saldo = 0
    for r in riwayat_stok(kode):
        saldo += _arah(r["jenis"]) * r["jumlah"]
        if saldo < 0:
            raise ValueError(
                f"Stok {AKUN_PERSEDIAAN[kode][0]} jadi minus ({format_jumlah(saldo)} {satuan_barang(kode)}) "
                f"pada {r['tanggal']}. Periksa kembali jumlahnya atau catat stok masuk terlebih dahulu."
            )


def simpan_gerak(tanggal, kode, jenis, jumlah, keterangan=""):
    if kode not in AKUN_PERSEDIAAN:
        raise ValueError("Barang tidak valid.")
    if jenis not in ("masuk", "keluar"):
        raise ValueError("Jenis harus masuk atau keluar.")
    if jumlah <= 0:
        raise ValueError("Jumlah harus lebih dari 0.")
    db = koneksi()
    with db:  # kalau stok jadi minus, semuanya dibatalkan
        db.execute(
            "INSERT INTO stok_gerak (tanggal, kode, jenis, jumlah, keterangan) VALUES (?, ?, ?, ?, ?)",
            (tanggal, kode, jenis, jumlah, keterangan[:120]),
        )
        _pastikan_tidak_minus(kode)


def hapus_gerak(id_gerak):
    db = koneksi()
    r = db.execute("SELECT kode, jenis FROM stok_gerak WHERE id = ?", (id_gerak,)).fetchone()
    if r is None or r["jenis"] == "awal":
        raise ValueError("Catatan tidak ditemukan.")
    with db:
        db.execute("DELETE FROM stok_gerak WHERE id = ?", (id_gerak,))
        _pastikan_tidak_minus(r["kode"])


def simpan_stok_awal(tanggal, data):
    """
    data = {kode: (satuan, stok awal, batas minimum)}, jumlah dalam bilangan bulat x100.
    Menggantikan stok awal sebelumnya. Satuan hanya bisa diganti kalau akun itu belum punya
    catatan masuk/keluar (supaya angka lama tidak berubah arti).
    """
    db = koneksi()
    with db:
        for kode, (satuan, awal, minimum) in data.items():
            label, pilihan = AKUN_PERSEDIAAN[kode]
            if satuan not in pilihan:
                raise ValueError(f"Satuan {label} tidak valid.")
            if satuan != satuan_barang(kode):
                dipakai = db.execute(
                    "SELECT 1 FROM stok_gerak WHERE kode = ? AND jenis != 'awal' LIMIT 1", (kode,)
                ).fetchone()
                if dipakai:
                    raise ValueError(
                        f"Satuan {label} tidak bisa diganti karena sudah ada catatan masuk/keluar. "
                        "Hapus catatan tersebut terlebih dahulu jika satuan perlu diganti."
                    )
            db.execute("UPDATE stok_barang SET satuan = ?, minimum = ? WHERE kode = ?", (satuan, minimum, kode))
            db.execute("DELETE FROM stok_gerak WHERE kode = ? AND jenis = 'awal'", (kode,))
            if awal > 0:
                db.execute(
                    "INSERT INTO stok_gerak (tanggal, kode, jenis, jumlah, keterangan) VALUES (?, ?, 'awal', ?, 'Stok awal')",
                    (tanggal, kode, awal),
                )
            _pastikan_tidak_minus(kode)


def stok_awal_tersimpan():
    """(tanggal, {kode: jumlah}) stok awal yang tersimpan."""
    baris = koneksi().execute(
        "SELECT tanggal, kode, jumlah FROM stok_gerak WHERE jenis = 'awal' ORDER BY id"
    ).fetchall()
    return (baris[0]["tanggal"] if baris else None), {r["kode"]: r["jumlah"] for r in baris}


def status_stok(sisa, minimum):
    if sisa <= 0:
        return "Habis"
    if minimum and sisa <= minimum:
        return "Menipis"
    return "Aman"


def ringkasan_stok():
    """Satu dict per barang: satuan, awal, masuk, keluar, sisa, status, nilai Rp, harga rata-rata."""
    db = koneksi()
    nama = {r["kode"]: r["nama"] for r in daftar_akun()}
    nilai_akun = {r["kode"]: r["debit"] - r["kredit"] for r in total_per_akun()}
    hasil = []
    for kode, (label, _) in AKUN_PERSEDIAAN.items():
        jumlah = {"awal": 0, "masuk": 0, "keluar": 0}
        for r in db.execute("SELECT jenis, SUM(jumlah) AS total FROM stok_gerak WHERE kode = ? GROUP BY jenis", (kode,)):
            jumlah[r["jenis"]] = r["total"]
        sisa = jumlah["awal"] + jumlah["masuk"] - jumlah["keluar"]
        tersedia = jumlah["awal"] + jumlah["masuk"]
        minimum = minimum_barang(kode)
        nilai = nilai_akun.get(kode, 0)
        hasil.append(
            {
                "kode": kode, "label": label, "nama": nama.get(kode, label), "satuan": satuan_barang(kode),
                "awal": jumlah["awal"], "masuk": jumlah["masuk"], "keluar": jumlah["keluar"],
                "sisa": sisa, "tersedia": tersedia, "minimum": minimum,
                "status": status_stok(sisa, minimum), "nilai": nilai,
                # harga rata-rata per satuan = nilai di buku besar / jumlah sisa
                "harga": round(nilai * SKALA / sisa) if sisa > 0 and nilai > 0 else None,
            }
        )
    return hasil


def tren_stok(kode):
    """[(tanggal, sisa setelah semua catatan di tanggal itu)] untuk grafik."""
    saldo, titik = 0, []
    for r in riwayat_stok(kode):
        saldo += _arah(r["jenis"]) * r["jumlah"]
        if titik and titik[-1][0] == r["tanggal"]:
            titik[-1] = (r["tanggal"], saldo)
        else:
            titik.append((r["tanggal"], saldo))
    return titik
