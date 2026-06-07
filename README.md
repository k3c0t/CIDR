
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-GUI-green?logo=qt)
![License](https://img.shields.io/badge/License-MIT-orange)

**NetScan Pro** adalah aplikasi pemindai port dan jaringan (*network scanner*) asinkron berkecepatan tinggi yang dibangun menggunakan ekosistem Python. 

Dirancang dengan antarmuka grafis (GUI) modern berbasis PySide6 dan mesin pemindai tangguh berbasis `asyncio`, aplikasi ini mampu memindai ribuan alamat IP dalam hitungan detik. Arsitektur internalnya telah diaudit secara ketat untuk memastikan stabilitas tingkat tinggi pada sistem operasi.

---

## ✨ Fitur Utama

* ⚡ **Pemindaian Asinkron Super Cepat:** Memanfaatkan `asyncio` dan `qasync` untuk menjalankan ratusan koneksi secara simultan (bersamaan) dalam satu *event loop* tanpa memblokir antarmuka pengguna (UI anti-*freeze*).
* 🔒 **Deteksi Protokol Cerdas (HTTP/HTTPS):** Dilengkapi dengan mekanisme *SSL Handshake* otomatis. Jika sebuah port terbuka (misalnya port 80 atau 443), sistem akan mencoba menginjeksi konteks SSL. Jika berhasil, hasil akan dilabeli sebagai `https://`, dan jika tidak, akan otomatis diturunkan menjadi `http://`.
* 💾 **Penyimpanan Real-Time (I/O Aman):** Menerapkan teknik *flushing buffer* (penulisan I/O langsung ke media penyimpanan). Hasil *scan* diamankan baris per baris secara *real-time*. Jika terjadi pemadaman listrik atau aplikasi tertutup, data yang sudah dipindai tidak akan hilang.
* ⚙️ **Optimalisasi Suhu & Perangkat Keras:** Mesin pemindai ini dirancang khusus dengan prioritas pada efisiensi perangkat keras keras. Pembungkusan *resource* jaringan secara ketat memastikan tidak ada *socket* yang bocor, mencegah pemakaian RAM berlebih, dan menjaga suhu prosesor tetap stabil meskipun sedang memproses ribuan IP.
* 🖥️ **Modern Dark-Theme UI:** Antarmuka visual yang elegan dan rapi, lengkap dengan *progress bar* interaktif, pemilihan *subnet* (CIDR) otomatis, dan tabel hasil responsif.

---

## 🛠️ Arsitektur Anti-Crash (Pembaruan Terbaru)

Versi stabil ini telah melewati audit menyeluruh dan menyertakan perlindungan lapis ganda terhadap masalah *Force Close*:
1. **Pencegahan File Descriptor Leak:** Setiap koneksi TCP dan SSL dibungkus dengan blok `try-finally` terisolasi (`_do_check()`). Sistem dijamin selalu menutup `writer.close()` apapun hasil dari respon server target (sukses, *timeout*, atau RTO).
2. **Graceful Shutdown (Pembersihan Zombie Task):** Saat pengguna menekan tombol "Batalkan", sistem tidak hanya berhenti, tetapi memburu dan membatalkan (`task.cancel()`) semua antrean *thread* yang menggantung di *background*, memastikan memori langsung dikosongkan.
3. **UI Rendering Batching:** Memperbarui tabel hasil *scan* secara *batch* (kelompok) alih-alih merender ulang antarmuka per IP, menghilangkan kemacetan (*bottleneck*) pada CPU.

---



