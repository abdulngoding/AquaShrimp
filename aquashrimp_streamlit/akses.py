"""
AquaShrimp SIA (Streamlit) - Login
Password disimpan sebagai hash SHA-256 (bukan teks asli).
Salah password 3 kali berturut-turut -> login dikunci 30 detik untuk alamat IP tersebut.
"""

import hashlib
import hmac
import os
import time

import streamlit as st

# Alamat logo dihitung dari lokasi file ini, jadi tetap benar di laptop maupun di hosting.
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "logo.png")
ADA_LOGO = os.path.exists(LOGO)

MAKS_PERCOBAAN = 3
DETIK_KUNCI = 30


def hash_password(password):
    """Ubah password jadi hash SHA-256 supaya tidak disimpan sebagai teks asli."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Akun yang diizinkan (kalau mau tambah user lain, tinggal tambah di sini)
USERS = {
    "AquaShrimp": hash_password("AquaShrimpSIA"),
}

GAGAL = {}  # alamat IP -> (jumlah salah, waktu kunci berakhir)


def alamat_ip():
    """Alamat IP pengunjung (dari header yang ditambahkan proxy hosting)."""
    try:
        diteruskan = st.context.headers.get("X-Forwarded-For", "")
    except Exception:
        diteruskan = ""
    return diteruskan.split(",")[-1].strip() or "lokal"


def sudah_masuk():
    return bool(st.session_state.get("user"))


def _periksa(username, password):
    """True kalau username dan password cocok."""
    hash_benar = USERS.get(username, "")
    # compare_digest: pembandingan waktu-konstan agar password tidak bisa ditebak dari lamanya proses
    return bool(hash_benar) and hmac.compare_digest(hash_benar, hash_password(password))


def tampil_login():
    kolom = st.columns([1, 2, 1])[1]
    with kolom:
        if ADA_LOGO:
            st.image(LOGO, width=120)
        st.title("AquaShrimp SIA")
        st.caption("Sistem Informasi Akuntansi Tambak Udang. Silakan masuk.")

        ip = alamat_ip()
        jumlah, sampai = GAGAL.get(ip, (0, 0))
        sisa = int(sampai - time.time())
        terkunci = sisa > 0

        with st.form("form_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            kirim = st.form_submit_button("Masuk", type="primary", width="stretch")

        if terkunci:
            st.error(f"Terlalu banyak percobaan. Coba lagi dalam {sisa} detik.")
        elif kirim:
            if _periksa(username.strip(), password):
                GAGAL.pop(ip, None)
                st.session_state["user"] = username.strip()
                st.rerun()
            else:
                jumlah += 1
                if jumlah >= MAKS_PERCOBAAN:
                    GAGAL[ip] = (0, time.time() + DETIK_KUNCI)
                    st.error(f"Salah {MAKS_PERCOBAAN} kali. Login dikunci {DETIK_KUNCI} detik.")
                else:
                    GAGAL[ip] = (jumlah, 0)
                    st.error(f"Username atau password salah ({jumlah}/{MAKS_PERCOBAAN}).")


def keluar():
    st.session_state.clear()
    st.rerun()
