"""Tes interaksi form lewat AppTest: jurnal umum, saldo awal, stok, reset."""
import os, sys
DB="/tmp/ui.db"
if os.path.exists(DB): os.remove(DB)
os.environ["AQUASHRIMP_DB"]=DB
sys.path.insert(0,".")
import database as db
from streamlit.testing.v1 import AppTest

def buka(nm): return AppTest.from_string(f"import sys; sys.path.insert(0,'.')\nfrom menu import {nm}\n{nm}.tampil()",default_timeout=30).run()

# Jurnal: transaksi benar
at=buka("jurnal_umum")
at.text_input[0].set_value("Beli benur")
at.selectbox[0].set_value("Persediaan Benur"); at.number_input[1].set_value(5000000)
at.selectbox[1].set_value("Kas"); at.number_input[4].set_value(5000000)
at.button[0].click().run()
print("simpan benar:",[s.value for s in at.success],[e.value for e in at.error])
# tidak seimbang
at=buka("jurnal_umum")
at.text_input[0].set_value("Salah")
at.selectbox[0].set_value("Kas"); at.number_input[1].set_value(100)
at.selectbox[1].set_value("Utang Usaha"); at.number_input[4].set_value(90)
at.button[0].click().run()
print("tidak seimbang:",[e.value for e in at.error])
# debit & kredit sekaligus
at=buka("jurnal_umum")
at.text_input[0].set_value("Salah2")
at.selectbox[0].set_value("Kas"); at.number_input[1].set_value(100); at.number_input[2].set_value(100)
at.selectbox[1].set_value("Utang Usaha"); at.number_input[4].set_value(100)
at.button[0].click().run()
print("debit+kredit:",[e.value for e in at.error])
print("jumlah transaksi di db:",db.jumlah_transaksi())


# Stok: catat masuk (butuh stok awal dulu lewat db), lalu keluar berlebih ditolak
db.simpan_stok_awal("2026-10-01",{k:(v[1][0],0,0) for k,v in db.AKUN_PERSEDIAAN.items()})
at=buka("persediaan")
# form catat: number_input urutan -> [0]=jumlah catat
at.number_input[0].set_value(10.5)
at.button[0].click().run()   # masuk Benur 10,5
print("stok masuk:",[s.value for s in at.success],[e.value for e in at.error])
print("sisa benur:",db.format_jumlah(db.ringkasan_stok()[0]["sisa"]))
at=buka("persediaan")
at.radio[0].set_value("keluar"); at.number_input[0].set_value(99)
at.button[0].click().run()
print("keluar berlebih:",[e.value for e in at.error])

# Saldo awal: hitung modal otomatis lalu simpan
db.hapus_saldo_awal()
at=buka("saldo_awal")
print("saldo awal tombol:",[b.label for b in at.button])
# Reset
at=buka("reset_data")
at.text_input[0].set_value("hapus"); at.button[0].click().run()
print("reset salah:",[e.value for e in at.error], db.jumlah_transaksi())
at.text_input[0].set_value("HAPUS"); at.button[0].click().run()
print("reset benar:",[s.value for s in at.success], db.jumlah_transaksi())
