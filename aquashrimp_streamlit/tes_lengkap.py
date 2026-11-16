import os, sys
DB="/tmp/tes_lengkap.db"
if os.path.exists(DB): os.remove(DB)
os.environ["AQUASHRIMP_DB"]=DB
sys.path.insert(0,".")
import database as db
from streamlit.testing.v1 import AppTest

# --- data uji ---
db.simpan_saldo_awal("2026-10-01",{"Kas":50_000_000,"Peralatan Tambak":20_000_000,"Modal Pemilik":70_000_000})
T=[("2026-10-02","Beli benur tunai",[("Persediaan Benur",5_000_000,0),("Kas",0,5_000_000)]),
   ("2026-10-05","Beli pakan kredit",[("Persediaan Pakan",8_000_000,0),("Utang Usaha",0,8_000_000)]),
   ("2026-10-20","Jual udang tunai",[("Kas",30_000_000,0),("Penjualan Udang",0,30_000_000)]),
   ("2026-10-20","HPP udang",[("HPP Udang",12_000_000,0),("Persediaan Benur",0,5_000_000),("Persediaan Pakan",0,7_000_000)]),
   ("2026-10-25","Bayar listrik",[("Beban Listrik Tambak",1_500_000,0),("Kas",0,1_500_000)]),
   ("2026-11-02","Retur penjualan",[("Retur Penjualan",2_000_000,0),("Kas",0,2_000_000)]),
   ("2026-11-03","Bayar utang",[("Utang Usaha",3_000_000,0),("Kas",0,3_000_000)])]
for t in T: db.simpan_transaksi(*t)
# salah: tidak seimbang harus ditolak
try: db.simpan_transaksi("2026-11-04","x",[("Kas",100,0),("Utang Usaha",0,90)]); print("GAGAL: tidak ditolak")
except ValueError: print("ok tolak tidak seimbang")

# --- angka yang dihitung tangan ---
kas=50_000_000-5_000_000+30_000_000-1_500_000-2_000_000-3_000_000
assert db.saldo_akun("Kas")==kas, db.saldo_akun("Kas")
aku=db.total_per_akun()
pend=sum(a["kredit"]-a["debit"] for a in aku if a["kategori"]=="Pendapatan")
assert pend==28_000_000
D=sum(a["debit"] for a in aku); K=sum(a["kredit"] for a in aku); assert D==K
print("kas",kas,"pendapatan",pend,"D=K",D)
db.simpan_stok_awal("2026-10-01",{"1103":("ekor",100000*100,5000*100),"1104":("kg",2000*100,300*100),"1105":("kg",0,0),"1106":("kg",0,0),"1107":("kg",0,0)})
db.simpan_gerak("2026-10-20","1104","keluar",500*100,"pakai")
try: db.simpan_gerak("2026-10-21","1104","keluar",9999*100,"x"); print("GAGAL stok minus")
except ValueError: print("ok tolak stok minus")

# --- render semua halaman ---
import importlib
for nm in ["dashboard","saldo_awal","jurnal_umum","buku_besar","neraca_saldo","penerimaan_kas","pengeluaran_kas","laba_rugi","persediaan","reset_data"]:
    kode=f"import sys; sys.path.insert(0,'.')\nfrom menu import {nm}\n{nm}.tampil()"
    at=AppTest.from_string(kode,default_timeout=30).run()
    print(f"{nm:16s}", "ERROR "+str(at.exception[0].value) if at.exception else "ok", "| tabel:",len(at.dataframe),"metric:",len(at.metric))

# neraca seimbang?
at=AppTest.from_string("import sys; sys.path.insert(0,'.')\nfrom menu import neraca_saldo\nneraca_saldo.tampil()").run()
print([s.value for s in at.success])
at=AppTest.from_string("import sys; sys.path.insert(0,'.')\nfrom menu import laba_rugi\nlaba_rugi.tampil()").run()
print([ (m.label,m.value) for m in at.metric])
