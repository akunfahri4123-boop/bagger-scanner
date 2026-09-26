# Deandra Bagger Scanner v4.0 — Versi Web App (bisa diakses dari HP)

## Kenapa bukan file .apk beneran?
Scanner ini butuh koneksi live ke Yahoo Finance tiap kali dijalankan lewat Python,
jadi tidak bisa diubah jadi file .apk yang berjalan sendiri offline di HP.
Solusi paling realistis supaya "kerasa kayak app" adalah: hosting permanen (jadi
tidak perlu buka Colab tiap mau pakai) + ikon shortcut di layar utama HP. Ini juga
yang paling umum dipakai untuk tool Streamlit pribadi.

## Yang diperbaiki/ditambahkan di paket ini
- **Bug kecil di rumus scoring dibersihkan** — ada baris sisa kode lama yang tidak
  terpakai; skor akhirnya tidak berubah, cuma kodenya lebih rapi.
- **Tema dark/hijau sekarang benar-benar aktif** — `config.toml` sebelumnya ada di
  lokasi yang tidak dibaca Streamlit (harus di dalam folder `.streamlit/`), sudah
  dipindah ke `.streamlit/config.toml`.
- **Manifest & icon dipindah ke folder `static/`** dan static file serving
  diaktifkan supaya "Add to Home Screen" bisa memakai ikon custom kalian.
- **Injeksi PWA otomatis** di `app.py` — mencoba menambahkan link manifest/icon
  ke halaman saat server nyala. Ini best-effort: kalau karena suatu hal gagal,
  aplikasi tetap jalan normal seperti biasa, cuma tanpa bonus tampilan standalone.

## Cara deploy (gratis, tanpa coding)

### 1. Upload ke GitHub
1. Buat akun di github.com (gratis, kalau belum punya).
2. Klik **New repository** → beri nama (mis. `bagger-scanner`) → **Create repository**.
3. Klik **Add file → Upload files**, seret SEMUA isi folder ini apa adanya
   (termasuk folder `.streamlit` dan `static` — jangan diubah strukturnya).
4. Klik **Commit changes**.

### 2. Deploy di Streamlit Community Cloud
1. Buka **share.streamlit.io**, login pakai akun GitHub yang sama.
2. Klik **New app** → pilih repo `bagger-scanner`, branch `main`, main file `app.py`.
3. Klik **Deploy** dan tunggu beberapa menit. Kalian akan dapat URL tetap, mis.
   `bagger-scanner-xxxx.streamlit.app` — ini tidak berubah-ubah lagi seperti URL Colab.

### 3. Jadikan ikon di HP
**Android (Chrome):**
1. Buka URL tersebut di Chrome.
2. Menu ⋮ → **Add to Home screen** → beri nama → Add.
3. Ikon muncul di home screen, tinggal tap seperti app biasa.

**iPhone (Safari):** tombol Share → **Add to Home Screen**. Ikon custom mungkin
tidak muncul (format SVG-nya tidak didukung Safari), tapi shortcut tetap berfungsi.

## ⚠️ Satu risiko yang perlu diketahui
Yahoo Finance kadang memblokir/rate-limit permintaan data yang datang dari alamat
IP milik Streamlit Community Cloud — ini masalah umum yang dialami banyak pengguna
Streamlit + yfinance, bukan cuma di project ini, dan tidak ada solusi pasti dari
pihak Streamlit maupun yfinance. Kalau setelah deploy scanner tiba-tiba error
"rate limited" terus padahal normal saja saat dicoba dari laptop sendiri, itu
tandanya kena blokir ini.

**Cadangan:** `run_colab.py` tetap disertakan di paket ini. Kalau Streamlit Cloud
kena blokir, scanner masih bisa dijalankan lewat Google Colab seperti sebelumnya.

## Jalankan lokal (opsional)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Catatan data
Versi ini memakai Yahoo Finance untuk data pasar/fundamental yang tersedia. Data
pihak ketiga dapat terlambat, kosong, atau berbeda dari data sekuritas/BEI.
Verifikasi data penting sebelum trading.

## Batasan penting
- Catalyst diberi 0 secara konservatif jika tidak ada event yang diverifikasi.
- "Bandar" tidak dideteksi secara literal; accumulation/order-flow menggunakan
  proxy kuantitatif.
- Score adalah ranking sistem, bukan probabilitas kemenangan.
- Sebelum dipakai dengan uang nyata, lakukan backtest dan paper trading.
