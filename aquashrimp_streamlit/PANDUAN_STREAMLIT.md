# Panduan AquaShrimp SIA (Streamlit, 100% Python)

Login: username AquaShrimp, password AquaShrimpSIA

## A. Jalankan di laptop
1. Install Python 3.10 atau lebih baru.
2. Buka terminal di folder ini, lalu: pip install -r requirements.txt
3. Jalankan: streamlit run AquaShrimp.py
4. Browser terbuka otomatis. Berhenti dengan Ctrl+C.
Data tersimpan di file aquashrimp.db (dibuat otomatis di folder ini).

## B. Online lewat Streamlit Community Cloud
1. Buat akun GitHub, buat repository baru (public), upload SEMUA isi folder ini
   (AquaShrimp.py, database.py, akses.py, umum.py, requirements.txt, folder menu, static, .streamlit).
   Jangan upload aquashrimp.db.
2. Buka share.streamlit.io, login dengan GitHub, klik Create app.
3. Pilih repository tadi, Main file path: AquaShrimp.py, lalu Deploy.
4. Tunggu beberapa menit sampai muncul alamat https://namaapp.streamlit.app

## C. PENTING: data di Streamlit Cloud bisa hilang
Database SQLite tersimpan di server sementara. Kalau aplikasi restart, tidur lama, atau
di-deploy ulang, data kembali kosong. Untuk presentasi/demo ini aman, asalkan:
- isi data (saldo awal dan transaksi) tepat sebelum demo, dan
- jangan mengandalkan data tahan berhari-hari.
Kalau butuh data permanen, perlu database luar (misalnya Supabase atau Neon).

## D. Struktur file
AquaShrimp.py   file utama: login, menu sidebar
akses.py        login, hash password, kunci 3x salah
database.py     semua akses database SQLite
umum.py         format angka/tanggal dan tampilan tabel
menu/           satu file per menu (dashboard, saldo_awal, jurnal_umum, buku_besar,
                neraca_saldo, penerimaan_kas, pengeluaran_kas, laba_rugi, persediaan, reset_data)
tes_lengkap.py, tes_form.py   tes otomatis (python tes_lengkap.py)
