# PANDUAN PENGGUNA SIMASET RSKGM

**Sistem Informasi Manajemen Aset — RS Khusus Gigi dan Mulut Palembang**
Versi 1.0 | 2026

---

## DAFTAR ISI

- [BAB 1 — Pendahuluan](#bab-1--pendahuluan)
- [BAB 2 — Login & Profil](#bab-2--login--profil)
- [BAB 3 — Panduan Super Admin](#bab-3--panduan-super-admin)
- [BAB 4 — Panduan Admin Divisi](#bab-4--panduan-admin-divisi)
- [BAB 5 — Panduan Admin Ruangan](#bab-5--panduan-admin-ruangan)
- [BAB 6 — Alur Kerja Step-by-Step](#bab-6--alur-kerja-step-by-step)
- [BAB 7 — Kode Warna & Badge](#bab-7--kode-warna--badge)
- [BAB 8 — Pertanyaan Umum (FAQ)](#bab-8--pertanyaan-umum-faq)

---

# BAB 1 — PENDAHULUAN

## 1.1 Tentang SIMASET

SIMASET (Sistem Informasi Manajemen Aset) adalah sistem berbasis web yang digunakan oleh RSKGM Palembang untuk mencatat, memantau, dan mengevaluasi kondisi aset medis secara terstruktur.

Fitur utama:
- Pencatatan aset terpusat per ruangan
- Evaluasi risiko dengan metode FMEA (RPN = S × O × D)
- Sistem approval untuk perubahan status aset
- Notifikasi otomatis berbasis prioritas risiko
- Cetak KIR (Kartu Identifikasi & Riwayat) dan QR Code per aset
- Ekspor laporan ke Excel dan PDF

## 1.2 Cara Akses

1. Buka browser (disarankan **Google Chrome** atau **Mozilla Firefox**)
2. Masuk ke alamat sistem yang telah diberikan oleh administrator
3. Login menggunakan email dan password yang telah diberikan

## 1.3 Tiga Peran Pengguna

| Peran | Tanggung Jawab | Akses |
|-------|----------------|-------|
| **Super Admin** | Mengelola seluruh struktur sistem: divisi, ruangan, dan akun pengguna | Semua halaman |
| **Admin Divisi** | Memantau aset seluruh ruangan dalam divisi, mereview pengajuan perubahan status aset | Dashboard, Aset Divisi, Approval Center, Laporan Divisi, Anggota, Notifikasi |
| **Admin Ruangan** | Mengelola aset di ruangannya sendiri, melakukan evaluasi FMEA, mencatat perbaikan | Dashboard, Daftar Aset, Laporan, Riwayat Maintenance, Notifikasi |

**Hierarki**:
```
Super Admin
    └── Admin Divisi (1 admin per divisi)
            └── Admin Ruangan (1 admin per ruangan)
```

---

# BAB 2 — LOGIN & PROFIL

## 2.1 Halaman Login

Tampilan login terdiri dari dua panel:
- **Panel kiri**: Branding SIMASET RSKGM (hanya tampil di layar lebar/desktop, otomatis tersembunyi di layar mobile)
- **Panel kanan**: Form login

### Langkah Login

1. Masukkan **Alamat Email** pada kolom "Alamat Email"
2. Masukkan **Password** pada kolom "Password"
   - Klik ikon mata 👁 di sisi kanan kolom untuk menampilkan/menyembunyikan password
3. Klik tombol **"Masuk"** (gradien biru)
4. Jika berhasil → diarahkan ke Dashboard sesuai peran
5. Jika gagal → pesan error muncul di atas form

> **Catatan**: Akun hanya dapat dibuat oleh Super Admin. Pengguna tidak dapat mendaftar sendiri.

## 2.2 Edit Profil

**Akses**: Menu sidebar → **Profil**, atau klik nama pengguna di topbar

Field yang dapat diedit:
- **Nama Lengkap**
- **Password Baru** (wajib mengisi password saat ini terlebih dahulu)
- **Konfirmasi Password Baru**

Tombol:
- **"Simpan Perubahan"** → menyimpan perubahan profil
- **"Batal"** → kembali tanpa menyimpan

## 2.3 Notifikasi

**Akses**: Ikon lonceng 🔔 di topbar atau menu **Notifikasi** di sidebar

Halaman Notifikasi menampilkan:
- Daftar seluruh notifikasi (terbaru di atas)
- Status: ✅ sudah dibaca atau 🔵 belum dibaca
- **Pagination** jika notifikasi banyak

Tombol di setiap notifikasi:
- **"Tandai Dibaca"** → mengubah status notifikasi menjadi sudah dibaca
- **"Tandai Semua Dibaca"** (di header) → menandai semua notifikasi sebagai sudah dibaca

### Jenis Notifikasi yang Diterima

**Admin Ruangan**:
- ⚠️ Peringatan RPN Sedang dari hasil evaluasi FMEA sendiri
- 🔔 Peringatan maintenance terlambat (jadwal perawatan lewat)
- ✅ Hasil approval (disetujui/ditolak) dari Admin Divisi

**Admin Divisi**:
- 🚨 Peringatan RPN Tinggi dari aset di ruangan bawahannya
- 📋 Pengajuan approval baru dari Admin Ruangan

---

# BAB 3 — PANDUAN SUPER ADMIN

Super Admin memiliki akses penuh ke seluruh sistem.

**Menu di sidebar**: Dashboard | Manajemen Divisi | Manajemen Ruangan | Admin Divisi | Admin Ruangan | Profil | Notifikasi

## 3.1 Dashboard Super Admin

Halaman pertama setelah login.

### Header
- **"Tambah User"** (tombol biru kanan atas) → langsung ke form tambah pengguna baru

### Kartu Statistik (4 kartu)

| Kartu | Penjelasan |
|-------|-----------|
| 🏢 **Divisi Aktif** | Jumlah total divisi yang aktif |
| 🚪 **Ruangan Aktif** | Jumlah total ruangan aktif |
| 👤 **Admin Divisi** | Jumlah akun Admin Divisi terdaftar |
| 👥 **Admin Ruangan** | Jumlah akun Admin Ruangan terdaftar |

### Tabel Ringkasan Divisi

Kolom: **Divisi** | **Admin** | **Ruangan** | **Status**

Tombol: **"Kelola"** → menuju Manajemen Divisi

### Tabel User Terbaru

Kolom: **Pengguna** (nama + email + avatar inisial) | **Role** | **Status** | **Tanggal Dibuat**

Tombol: **"Lihat Semua"** → menuju Admin Divisi

## 3.2 Manajemen Divisi

**Akses**: Sidebar → **Manajemen Divisi**

### Tombol Header
- **"Tambah Divisi"** (biru) → form tambah divisi baru

### Tabel Daftar Divisi

| Kolom | Isi |
|-------|-----|
| **#** | Nomor urut |
| **Nama Divisi** | Nama divisi |
| **Deskripsi** | Keterangan singkat |
| **Admin Divisi** | Nama dan email admin (jika ada) atau "Belum ada admin" |
| **Ruangan** | Daftar kode + nama ruangan dalam divisi |
| **Total Aset** | Jumlah aset di seluruh ruangan divisi |
| **Status** | Aktif (hijau) / Nonaktif (abu) |
| **Aksi** | Tombol Edit dan Toggle |

### Tombol Aksi per Baris

- ✏️ **Ikon Pensil** → buka form edit divisi
- 🔘 **Ikon Toggle** (Aktifkan/Nonaktifkan) → muncul dialog konfirmasi: *"Apakah Anda yakin ingin [aktifkan/nonaktifkan] divisi [nama]?"*

### Form Tambah Divisi

Field:
- **Nama Divisi** (wajib, maks. 100 karakter, ada penghitung otomatis)
- **Deskripsi** (opsional, maks. 300 karakter, ada penghitung otomatis)

Tombol:
- **"Tambah Divisi"** (biru) → simpan
- **"Batal"** → kembali ke daftar

## 3.3 Manajemen Ruangan

**Akses**: Sidebar → **Manajemen Ruangan**

### Filter Pencarian

- 🔍 **Kolom Cari**: kode atau nama ruangan
- 📁 **Dropdown Divisi**: filter per divisi
- 🔘 **Dropdown Status**: Semua / Aktif / Nonaktif
- **"Terapkan"** dan **"Reset"**

### Tabel Daftar Ruangan

Kolom: **#** | **Ruangan** (nama + kode) | **Divisi** | **Lantai** | **Admin Ruangan** | **Jumlah Aset** | **Status** | **Aksi**

Pagination tersedia di bawah tabel jika data banyak.

### Tombol Aksi per Baris

- ✏️ **Ikon Pensil** → form edit ruangan
- 🗑️ **Ikon Tempat Sampah (Hapus)**:
  - **Aktif** jika ruangan kosong (tidak ada aset)
  - **Disabled (abu-abu)** jika masih ada aset, dengan tooltip: *"Tidak dapat dihapus karena masih memiliki aset"*
  - Saat klik aktif → muncul konfirmasi: *"Apakah Anda yakin ingin menghapus ruangan [nama]? Tindakan ini tidak dapat dibatalkan."*

### Form Tambah/Edit Ruangan

Field:
- **Nama Ruangan** (wajib)
- **Kode Ruangan** (wajib, harus unik)
- **Lantai** (wajib)
- **Divisi** (wajib, dropdown)

Tombol: **"Simpan"** | **"Batal"**

## 3.4 Manajemen Pengguna — Admin Divisi

**Akses**: Sidebar → **Admin Divisi**

### Filter Pencarian

- 🔍 **Cari**: nama atau email
- 🔘 **Status**: Semua / Aktif / Nonaktif
- **"Terapkan"** dan **"Reset"**

### Tabel Daftar Admin Divisi

Kolom: **#** | **Pengguna** (avatar + nama + email) | **Divisi** | **Ruangan** (jumlah) | **Total Aset** | **Login Terakhir** | **Status** | **Aksi**

### Tombol Aksi per Baris

- ✏️ **Ikon Pensil** → form edit user
- 👤➖ **Ikon Person-Dash** (jika aktif) → tombol nonaktifkan
- 👤➕ **Ikon Person-Check** (jika nonaktif) → tombol aktifkan

> **Penting**: Sistem mencegah aktivasi jika divisi sudah memiliki Admin Divisi aktif lain. Pesan error akan muncul.

## 3.5 Manajemen Pengguna — Admin Ruangan

**Akses**: Sidebar → **Admin Ruangan**

Tampilan dan tombol sama dengan Admin Divisi, hanya kolom diganti dengan **Ruangan** (nama ruangan yang dikelola).

> **Penting**: Sama seperti Admin Divisi, sistem mencegah aktivasi jika ruangan sudah memiliki Admin Ruangan aktif lain.

## 3.6 Form Tambah User Baru

**Akses**: Tombol **"Tambah User"** dari mana saja

### Bagian 1 — Informasi Dasar

- **Nama Lengkap** (wajib, maks. 100 karakter, ada penghitung)
- **Email** (wajib, harus format email valid, harus unik)

### Bagian 2 — Keamanan

- **Password** (wajib, minimal 8 karakter)
  - Tombol mata 👁 untuk tampilkan/sembunyikan password
  - **Indikator kekuatan password** otomatis: Lemah / Cukup / Baik / Kuat (dengan warna)

### Bagian 3 — Peran & Akses

- **Role** (wajib, dropdown):
  - Admin Divisi
  - Admin Ruangan

**Behavior dinamis**:
- Pilih **Admin Divisi** → muncul dropdown **Divisi**
  - Divisi yang sudah memiliki admin aktif: ditandai *"(sudah ada admin aktif)"* dan **dinonaktifkan**
- Pilih **Admin Ruangan** → muncul dropdown **Ruangan**
  - Ruangan yang sudah memiliki admin aktif: ditandai dan **dinonaktifkan**

Tombol:
- **"Buat Akun"** (biru) → simpan dan kembali ke daftar
- **"Batal"** → kembali tanpa menyimpan

## 3.7 Form Edit User

Sama dengan form tambah user, dengan field sudah terisi data lama.

> Field **Password** dapat dikosongkan jika tidak ingin mengganti password.

Tombol: **"Simpan Perubahan"** | **"Batal"**

---

# BAB 4 — PANDUAN ADMIN DIVISI

Admin Divisi mengelola satu divisi dan memantau seluruh ruangan di bawahnya.

**Menu di sidebar**: Dashboard | Daftar Aset | Approval Center | Laporan | Anggota | Riwayat Maintenance | Notifikasi | Profil

## 4.1 Dashboard Admin Divisi

### Banner "Divisi Saya" (atas)

Menampilkan:
- Nama divisi
- Deskripsi divisi (jika ada)
- **Jumlah Ruangan Aktif** (angka)
- **Total Aset** (angka)

Tombol: **"Lihat Detail Anggota"** → halaman Anggota

### Alert Approval Pending

Muncul **hanya jika** ada pengajuan yang belum direview.
> ⚠️ *"Ada [X] pengajuan approval yang belum direview. [Tinjau sekarang →]"*

Klik link → langsung ke Approval Center filter Pending.

### Kartu Statistik (4 kartu)

| Kartu | Penjelasan |
|-------|-----------|
| 📦 **Total Aset** | Jumlah aset di seluruh ruangan divisi |
| ⚠️ **Aset Kritis/Tidak Layak** | Angka **merah** jika lebih dari 0 |
| 📋 **Approval Pending** | Angka **kuning** jika lebih dari 0 |
| 🔔 **Notifikasi Belum Dibaca** | Jumlah notifikasi yang belum dibaca |

### Grafik

- 🍩 **Donut Chart**: "Distribusi Kondisi Aset" — proporsi Baik / Perlu Perhatian / Kritis / Tidak Layak
- 📊 **Bar Chart**: "Distribusi RPN per Ruangan" — stacked bar dengan warna:
  - 🔴 Merah: RPN Tinggi
  - 🟡 Kuning: RPN Sedang
  - 🟢 Hijau: RPN Rendah

### Tabel Ringkasan per Ruangan

Kolom: **Ruangan** (nama + kode + lantai) | **Total** | **Baik** | **Perlu Perhatian** | **Kritis** | **Tidak Layak** | **RPN Tertinggi**

Klik nama ruangan → lihat aset di ruangan tersebut.

## 4.2 Daftar Aset Divisi

**Akses**: Menu **Daftar Aset**

Menampilkan **semua aset** dari seluruh ruangan dalam divisi.

### Filter

- 🚪 **Dropdown Ruangan**: filter per ruangan
- 🏷️ **Dropdown Kondisi**: Semua / Baik / Perlu Perhatian / Kritis / Tidak Layak
- Tombol **"Filter"** dan **"Reset"**

### Tabel Aset

Kolom: **Kode Aset** | **Nama Aset** | **Ruangan** | **Kategori** | **Kondisi** | **Status** | **RPN Terakhir** | **Aksi**

### Tombol Aksi per Baris

- 👁 **Ikon Mata** → halaman Detail Aset (read-only — Admin Divisi tidak bisa edit)

## 4.3 Detail Aset (Admin Divisi)

Halaman **read-only**. Menampilkan:

### Kartu Informasi Dasar
Kode, kategori, merek, model, nomor seri, tanggal pembelian, harga, catatan

### Kartu Kondisi & Status
Kondisi terkini (badge), status (badge), tanggal maintenance terakhir & berikutnya

### Kartu Evaluasi FMEA Terakhir
RPN score (angka besar berwarna), kategori risiko, tanggal evaluasi

### Tabel Riwayat FMEA
5 evaluasi terbaru: **Tanggal** | **Mode Kegagalan** | **S** | **O** | **D** | **RPN** | **Kategori**

## 4.4 Approval Center

**Akses**: Menu **Approval Center**

Halaman untuk **mereview pengajuan perubahan status aset** dari Admin Ruangan.

### Filter

- 🔘 **Status Approval**: Semua / Pending / Disetujui / Ditolak
- 🚪 **Ruangan**: filter per ruangan
- Tombol **"Filter"** dan **"Reset"**

### Tabel Pengajuan

Kolom: **Aset** (nama + kode) | **Ruangan** | **Status Lama** | **Status Baru** | **Diajukan Oleh** | **Tgl Pengajuan** | **Status Approval** | **Aksi**

> Baris dengan status **Pending** ditandai background **kuning** untuk menarik perhatian.

### Tombol Aksi

- 🟡 **"Review"** → halaman detail pengajuan (untuk yang masih Pending)
- ⚫ **"Detail"** → halaman detail pengajuan (untuk yang sudah diproses)

### Halaman Detail Pengajuan

Tampilan dua kolom:

#### Kolom Kiri

**Kartu "Detail Pengajuan"**:
- Nama aset & kode
- Ruangan
- Status Lama (badge abu)
- Status Diminta (badge biru)
- Alasan pengajuan
- Diajukan oleh (nama Admin Ruangan)
- Tanggal pengajuan

Jika sudah diproses, tambahan:
- Direview oleh
- Tanggal review
- Catatan reviewer

**Kartu "Evaluasi FMEA Terbaru"** (sebagai bahan pertimbangan):
Tabel kolom: **Tgl Evaluasi** | **Mode Kegagalan** | **RPN** | **Kategori**

#### Kolom Kanan (hanya jika status Pending)

**Kartu Hijau — "Setujui Pengajuan"**:
- Field **Catatan Reviewer** (opsional, textarea)
- Tombol ✅ **"Setujui Pengajuan"** (hijau)
- Saat klik → konfirmasi *"Yakin ingin menyetujui pengajuan ini?"*

**Kartu Merah — "Tolak Pengajuan"**:
- Field **Alasan Penolakan** (**WAJIB**, minimal 10 karakter)
- Tombol ❌ **"Tolak Pengajuan"** (merah)
- Saat klik → konfirmasi *"Yakin ingin menolak pengajuan ini?"*

#### Jika Sudah Diproses

Tampil kartu **"Hasil Keputusan"** dengan:
- Ikon ✅ centang hijau (Disetujui) atau ❌ silang merah (Ditolak)
- Nama reviewer dan tanggal
- Catatan reviewer (jika ada)

### Dampak Setelah Approval

**Jika Disetujui**:
- Status aset berubah ke status yang diminta
- Admin Ruangan mendapat notifikasi
- Aset terbuka kembali (tidak lagi "Menunggu Approval")

**Jika Ditolak**:
- Status aset kembali ke status sebelum pengajuan
- Admin Ruangan mendapat notifikasi dengan alasan penolakan
- Aset terbuka kembali

## 4.5 Laporan Divisi

**Akses**: Menu **Laporan**

Menampilkan rekap seluruh aset di divisi dengan statistik kondisi per ruangan.

Tombol ekspor:
- 🟢 **"Ekspor Excel"** → unduh file `.xlsx`
- 🔴 **"Ekspor PDF"** → unduh file `.pdf`

## 4.6 Anggota Divisi

**Akses**: Menu **Anggota** atau tombol **"Lihat Detail Anggota"** di Dashboard

Menampilkan daftar Admin Ruangan di bawah divisi beserta ruangan yang dikelola.

## 4.7 Riwayat Maintenance Divisi

**Akses**: Menu **Riwayat Maintenance**

Menampilkan seluruh catatan maintenance dari semua ruangan dalam divisi. Dapat difilter per ruangan.

Kolom: **Tanggal** | **Aset** | **Ruangan** | **Jenis Tindakan** | **Deskripsi** | **Dicatat Oleh**

---

# BAB 5 — PANDUAN ADMIN RUANGAN

Admin Ruangan mengelola **satu ruangan** dan asetnya.

**Menu di sidebar**: Dashboard | Daftar Aset | Laporan | Riwayat Maintenance | Notifikasi | Profil

## 5.1 Dashboard Admin Ruangan

### Header

Menampilkan nama ruangan dan kode ruangan.

Tombol: **"Tambah Aset"** (biru) → form tambah aset baru

### Alert RPN Tinggi

Muncul **hanya jika** ada aset dengan RPN ≥ 200.
> 🚨 *"Perhatian! Terdapat aset dengan RPN Tinggi (≥200) di ruangan ini. Segera lakukan tindakan perbaikan. [Lihat Aset Kritis →]"*

### Kartu Statistik (4 kartu)

| Kartu | Penjelasan |
|-------|-----------|
| 📦 **Total Aset** | Jumlah aset di ruangan |
| ✅ **Kondisi Baik** | Aset kondisi baik |
| ⚠️ **Perlu Perhatian** | Aset perlu perhatian |
| ❌ **Kritis** | Aset kondisi kritis |

### Grafik

- 🍩 **Donut Chart**: "Distribusi Kondisi Aset"
  - 🟢 Baik
  - 🟡 Perlu Perhatian
  - 🟠 Kritis
  - 🔴 Tidak Layak

### Tabel Evaluasi FMEA Terbaru

Kolom: **Aset** (link) | **Mode Kegagalan** | **RPN** | **Kategori** | **Tanggal**

Tombol: **"Lihat Aset"** → Daftar Aset

## 5.2 Daftar Aset

**Akses**: Menu **Daftar Aset**

### Filter

- 🏷️ **Kondisi**: Semua / Baik / Perlu Perhatian / Kritis / Tidak Layak
- 📁 **Kategori**: pilih dari daftar kategori
- 🔘 **Status**: Semua / Aktif / Dalam Perbaikan / Tidak Aktif / Menunggu Approval
- Tombol **"Filter"** dan **"Reset"**

### Tabel Aset

Kolom: **Kode** | **Nama Aset** | **Kategori** | **Kondisi** | **Status** | **RPN** (warna) | **Tgl Evaluasi** | **Aksi**

Pagination tersedia di bawah.

### Tombol Aksi per Baris

| Ikon | Fungsi |
|------|--------|
| 👁 **Mata** | Buka halaman Detail Aset |
| ✏️ **Pensil** | Buka form Edit Aset |
| 📋 **Clipboard-Check** | Buka form Evaluasi FMEA |

## 5.3 Tambah Aset Baru

**Akses**: Tombol **"Tambah Aset"** dari Dashboard atau Daftar Aset

### Field Form

| Field | Wajib | Keterangan |
|-------|-------|-----------|
| **Nama Aset** | ✅ | Nama lengkap aset |
| **Kategori** | ✅ | Pilih dari dropdown |
| **Merek** | ✅ | Contoh: Carestream |
| **Model** | ✅ | Contoh: CS 8200 3D |
| **Nomor Seri** | ❌ | Opsional |
| **Tanggal Pembelian** | ❌ | Opsional |
| **Harga Pembelian** | ❌ | Dalam Rupiah, **tidak boleh negatif** |
| **Kondisi Awal** | ✅ | Baik / Perlu Perhatian / Kritis / Tidak Layak |
| **Catatan** | ❌ | Opsional |

> **Kode Aset dibuat otomatis** oleh sistem (format: kode-ruangan + nomor urut)

Tombol: **"Simpan"** (biru) | **"Batal"**

## 5.4 Edit Aset

**Akses**: Ikon ✏️ pensil dari Daftar Aset, atau tombol **"Edit"** di halaman Detail Aset

> ⚠️ **Tombol Edit TIDAK MUNCUL** jika aset sedang dalam status **"Menunggu Approval"**.

Form sama seperti Tambah Aset, field sudah terisi data lama.

Tombol: **"Simpan Perubahan"** | **"Batal"**

## 5.5 Detail Aset

**Akses**: Ikon 👁 mata dari Daftar Aset, atau klik nama aset

### Tombol-Tombol di Header (atas kanan)

| Tombol | Warna | Fungsi |
|--------|-------|--------|
| 📋 **Evaluasi FMEA** | Biru | Buka form evaluasi FMEA |
| 🖨️ **Cetak KIR** | Hitam | Download PDF Kartu Identifikasi & Riwayat aset |
| 🔲 **QR Code** | Abu-abu | Download QR Code PNG aset |
| 🔧 **Catat Perbaikan** | Hijau | Buka form catatan perbaikan/maintenance |
| ✏️ **Edit** | Biru outline | Form edit aset *(hilang jika Menunggu Approval)* |
| 📤 **Ajukan Perubahan Status** | Kuning | Form pengajuan ke Admin Divisi *(hilang jika Menunggu Approval)* |
| 🔒 **Menunggu Approval** | Abu disabled | Pengganti tombol Edit & Ajukan saat sedang dalam proses approval |

### Kartu Informasi Dasar

Menampilkan: Kode Aset, Kategori, Merek, Model, Nomor Seri, Tanggal Pembelian, Harga, Catatan

### Kartu Kondisi & Status

Menampilkan:
- **Kondisi** (badge berwarna)
- **Status** (badge berwarna)
- **Maintenance Terakhir** (tanggal)
- **Maintenance Berikutnya** (tanggal)
- **Tanggal Ditambahkan**

Jika ada FMEA: tampilan **RPN Score** dalam angka besar berwarna sesuai kategori, beserta tanggal evaluasi.

### Kartu QR Code Aset

- Gambar QR Code aset
- Tombol **"Download QR Code"** → unduh file PNG

> QR Code dapat ditempel di fisik aset. Saat discan, langsung menuju halaman detail aset ini.

### Tabel 5 Evaluasi FMEA Terbaru

Kolom: **Tanggal** | **Mode Kegagalan** | **S** | **O** | **D** | **RPN** | **Kategori**

Tombol: **"Lihat Semua"** → halaman riwayat FMEA lengkap

## 5.6 Evaluasi FMEA

**Akses**: Tombol **"Evaluasi FMEA"** di Detail Aset, atau ikon 📋 di Daftar Aset

> **FMEA** (Failure Mode and Effects Analysis) adalah metode evaluasi risiko aset.

### Form Evaluasi (kolom kiri)

| Field | Wajib | Keterangan |
|-------|-------|-----------|
| **Mode Kegagalan** | ✅ | Deskripsi kerusakan/masalah. Contoh: "Motor tidak berputar" |
| **Efek Kegagalan** | ✅ | Dampak dari kerusakan. Contoh: "Alat tidak dapat digunakan untuk diagnosis" |
| **Severity (S)** | ✅ | 1–10 (slider atau ketik) — Tingkat keparahan |
| **Occurrence (O)** | ✅ | 1–10 (slider atau ketik) — Frekuensi kejadian |
| **Detection (D)** | ✅ | 1–10 (slider atau ketik) — Kemampuan deteksi |
| **Tanggal Evaluasi** | ✅ | Default: hari ini |
| **Catatan** | ❌ | Opsional |

### Preview RPN (real-time)

Kotak preview menampilkan **RPN = S × O × D** secara langsung saat slider digeser, dengan warna dan rekomendasi:

| RPN | Warna | Status | Rekomendasi |
|-----|-------|--------|-------------|
| ≥ 200 | 🔴 Merah | **TINGGI** | Hentikan penggunaan jika berisiko. Perbaikan dalam 1×24 jam |
| 80–199 | 🟡 Kuning | **SEDANG** | Pantau dan jadwalkan perawatan dalam 7 hari |
| < 80 | 🟢 Hijau | **RENDAH** | Lanjutkan pemeliharaan rutin, dokumentasikan untuk audit |

Tombol: **"Simpan Evaluasi"** (biru info)

### Panduan Nilai (kolom kanan)

#### Severity (S) — Tingkat Keparahan
| Nilai | Deskripsi |
|-------|-----------|
| 1 | Tidak ada efek |
| 2–3 | Efek sangat ringan, tidak mengganggu fungsi |
| 4–6 | Efek sedang, penurunan performa |
| 7–8 | Efek berat, alat tidak berfungsi optimal |
| 9–10 | Efek sangat berat, membahayakan keselamatan |

#### Occurrence (O) — Frekuensi Kejadian
| Nilai | Deskripsi |
|-------|-----------|
| 1 | Hampir tidak pernah terjadi |
| 2–3 | Sangat jarang (1×/tahun) |
| 4–6 | Kadang-kadang (1×/bulan) |
| 7–8 | Sering (1×/minggu) |
| 9–10 | Hampir selalu terjadi |

#### Detection (D) — Kemampuan Deteksi
| Nilai | Deskripsi |
|-------|-----------|
| 1 | Hampir pasti terdeteksi |
| 2–3 | Kemungkinan besar terdeteksi |
| 4–6 | Kemungkinan sedang terdeteksi |
| 7–8 | Kemungkinan kecil terdeteksi |
| 9–10 | Hampir tidak mungkin terdeteksi |

### Dampak Otomatis Setelah Simpan FMEA

Sistem otomatis melakukan:

1. **Hitung RPN** = S × O × D
2. **Tentukan Kategori Risiko** (Tinggi / Sedang / Rendah)
3. **Update Kondisi Aset** (hanya bisa MEMPERBURUK, tidak otomatis membaik):
   - RPN Tinggi → kondisi menjadi **Kritis** (jika sebelumnya bukan Tidak Layak)
   - RPN Sedang → kondisi menjadi **Perlu Perhatian** (jika sebelumnya Baik)
   - RPN Rendah → kondisi tetap (TIDAK otomatis kembali ke Baik)
4. **Kirim Notifikasi**:
   - RPN Tinggi → ke Admin Divisi
   - RPN Sedang → ke Admin Ruangan sendiri
5. **Catat ke Riwayat Maintenance** dengan jenis tindakan "Evaluasi FMEA"

> ⚠️ **Penting**: Kondisi **"Tidak Layak"** HANYA bisa diubah secara manual melalui form **Catat Perbaikan**, bukan oleh evaluasi FMEA.

## 5.7 Riwayat FMEA

**Akses**: Tombol **"Lihat Semua"** di kartu riwayat FMEA pada halaman Detail Aset

Menampilkan seluruh riwayat evaluasi FMEA aset.

Kolom: **Tanggal** | **Mode Kegagalan** | **Efek** | **S** | **O** | **D** | **RPN** | **Kategori** | **Catatan**

## 5.8 Catat Perbaikan / Maintenance

**Akses**: Tombol 🔧 **"Catat Perbaikan"** (hijau) di Detail Aset

> Digunakan untuk mencatat tindakan perawatan/perbaikan. **Tidak memerlukan approval**.

### Kolom Kiri — Ringkasan Aset
Menampilkan: nama, merek/model, kondisi saat ini, status, RPN terakhir (sebagai referensi).

### Kolom Kanan — Form Catatan

| Field | Wajib | Keterangan |
|-------|-------|-----------|
| **Jenis Tindakan** | ✅ | Pilih: Perbaikan / Penggantian Komponen / Pemeriksaan Rutin |
| **Tanggal Tindakan** | ✅ | Default: hari ini |
| **Deskripsi Tindakan** | ✅ | **Min. 20 karakter**, jelaskan secara rinci |
| **Nama Teknisi** | ❌ | Nama teknisi/petugas yang mengerjakan |
| **Kondisi Setelah Perbaikan** | ❌ | Update kondisi: Baik / Perlu Perhatian / Kritis / Tidak Layak |
| **Jadwal Maintenance Berikutnya** | ❌ | **Tidak boleh di masa lalu** |
| **Catatan Tambahan** | ❌ | Opsional |

> 💡 **Field "Kondisi Setelah Perbaikan"** adalah **satu-satunya cara** untuk:
> - Mengembalikan kondisi aset ke **Baik** secara manual
> - Menandai aset sebagai **Tidak Layak** (untuk pensiunkan dari operasional)

Tombol: **"Simpan Catatan"** (hijau) | **"Batal"**

## 5.9 Ajukan Perubahan Status

**Akses**: Tombol 📤 **"Ajukan Perubahan Status"** (kuning) di Detail Aset

> Tombol **TIDAK TERSEDIA** jika aset sudah dalam status "Menunggu Approval".

### Status yang Bisa Diajukan

| Status | Penjelasan |
|--------|-----------|
| **Aktif** | Aset siap digunakan |
| **Dalam Perbaikan** | Aset sedang dalam proses perbaikan |
| **Tidak Aktif** | Aset tidak digunakan sementara |

### Form Pengajuan

| Field | Wajib | Keterangan |
|-------|-------|-----------|
| **Status yang Diajukan** | ✅ | Dropdown |
| **Alasan Pengajuan** | ✅ | **Min. 20 karakter**, jelaskan alasan perubahan |

Tombol: **"Kirim Pengajuan"** (kuning) | **"Batal"**

### Setelah Pengajuan Terkirim

1. ✅ Status aset langsung berubah menjadi **"Menunggu Approval"**
2. 🔒 Aset **tidak dapat diedit** dan **tidak dapat diajukan perubahan baru** sampai diproses
3. 🔔 Admin Divisi otomatis menerima notifikasi
4. ⏳ Setelah Admin Divisi menyetujui/menolak, Anda menerima notifikasi hasilnya

## 5.10 Cetak KIR (Kartu Identifikasi dan Riwayat)

**Akses**: Tombol 🖨️ **"Cetak KIR"** (hitam) di Detail Aset

Mengunduh **file PDF** berisi:
- 📌 Identitas aset lengkap (kode, nama, kategori, merek, model, nomor seri)
- 📊 Kondisi dan status terkini
- 📝 Riwayat evaluasi FMEA
- 🔧 Riwayat maintenance

Berguna untuk:
- Audit aset
- Inspeksi rumah sakit
- Dokumentasi fisik aset

> Sistem juga mencatat aksi cetak KIR ke riwayat maintenance (action type: `cetak_kir`).

## 5.11 Download QR Code

**Akses**:
- Tombol **"QR Code"** di header Detail Aset
- Tombol **"Download QR Code"** di kartu QR Code

Mengunduh **file PNG** QR Code unik untuk aset ini.

Cara menggunakan:
1. Cetak QR Code yang telah diunduh
2. Tempel di fisik aset
3. Scan dengan kamera HP atau aplikasi QR scanner
4. Otomatis terbuka halaman detail aset di browser

## 5.12 Rekap Laporan

**Akses**: Menu **Laporan**

### Filter

- 🏷️ **Kondisi**: Semua / Baik / Perlu Perhatian / Kritis / Tidak Layak
- 📊 **Kategori RPN**: Semua / Tinggi (≥200) / Sedang (80–199) / Rendah (<80)
- Tombol **"Filter"** dan **"Reset"**

### Kartu Statistik (4 kartu)

| Kartu | Isi |
|-------|-----|
| **Total Aset** | Sesuai filter |
| **Kondisi Baik** | Sesuai filter |
| **Perlu Perhatian** | Sesuai filter |
| **Kritis** | Sesuai filter |

### Tabel Laporan

Kolom: **Kode** | **Nama Aset** | **Kategori** | **Kondisi** | **RPN** | **Kategori RPN** | **Tgl Evaluasi**

### Tombol Ekspor (kanan atas)

- 🟢 **"Ekspor Excel"** → unduh `.xlsx` (sesuai filter aktif)
- 🔴 **"Ekspor PDF"** → unduh `.pdf` (sesuai filter aktif)

> ⚠️ **Penting**: Ekspor mengikuti **filter yang sedang aktif**. Pastikan filter sudah benar sebelum klik ekspor!

## 5.13 Riwayat Maintenance

**Akses**: Menu **Riwayat Maintenance**

Menampilkan seluruh catatan maintenance semua aset di ruangan.

Kolom: **Tanggal** | **Aset** | **Jenis Tindakan** | **Deskripsi** | **Dicatat Oleh**

Jenis tindakan yang ditampilkan:
- Evaluasi FMEA
- Perbaikan
- Penggantian Komponen
- Pemeriksaan Rutin
- Approval Disetujui / Ditolak
- Pengajuan Status
- Cetak KIR

---

# BAB 6 — ALUR KERJA STEP-BY-STEP

## 6.1 Alur Tambah Aset Baru

```
[Admin Ruangan] Login
    ↓
Klik "Tambah Aset" (Dashboard atau Daftar Aset)
    ↓
Isi field wajib: Nama, Kategori, Merek, Model, Kondisi Awal
Isi field opsional: Nomor Seri, Tanggal Pembelian, Harga, Catatan
    ↓
Klik "Simpan"
    ↓
✅ Aset muncul di Daftar Aset dengan kode otomatis
```

## 6.2 Alur Evaluasi FMEA

```
[Admin Ruangan] Buka Detail Aset
    ↓
Klik "Evaluasi FMEA" (biru)
    ↓
Isi Mode Kegagalan & Efek Kegagalan
    ↓
Atur slider Severity (1-10)
Atur slider Occurrence (1-10)
Atur slider Detection (1-10)
    ↓
Lihat Preview RPN (warna berubah otomatis)
    ↓
Isi Tanggal Evaluasi
    ↓
Klik "Simpan Evaluasi"
    ↓
Sistem otomatis:
✅ Hitung RPN = S × O × D
✅ Tentukan kategori risiko
✅ Update kondisi aset (jika perlu memburuk)
✅ Kirim notifikasi (jika RPN Tinggi → Admin Divisi)
✅ Catat ke riwayat maintenance
```

## 6.3 Alur Perubahan Status Aset (dengan Approval)

```
[Admin Ruangan] Buka Detail Aset
    ↓
Klik "Ajukan Perubahan Status" (kuning)
    ↓
Pilih Status Baru (Aktif/Dalam Perbaikan/Tidak Aktif)
Isi Alasan Pengajuan (min. 20 karakter)
    ↓
Klik "Kirim Pengajuan"
    ↓
🔒 Status aset → "Menunggu Approval"
🔔 Admin Divisi mendapat notifikasi
    ↓
============== [Admin Divisi] ==============
    ↓
Buka "Approval Center"
    ↓
Klik "Review" pada pengajuan Pending
    ↓
Baca detail pengajuan & riwayat FMEA
    ↓
┌─ Setuju? ────────────────┐    ┌─ Tolak? ──────────────────┐
│ Isi catatan (opsional)   │    │ Isi alasan (WAJIB ≥10ch)  │
│ Klik "Setujui Pengajuan" │    │ Klik "Tolak Pengajuan"    │
│ Konfirmasi               │    │ Konfirmasi                │
└──────────────────────────┘    └───────────────────────────┘
    ↓
============================================
    ↓
[Admin Ruangan]
🔔 Menerima notifikasi hasil
✅ Disetujui → status aset = status baru
❌ Ditolak → status aset kembali ke status lama
```

## 6.4 Alur Catat Perbaikan

```
[Admin Ruangan] Aset selesai diperbaiki
    ↓
Buka Detail Aset → klik "Catat Perbaikan" (hijau)
    ↓
Pilih Jenis Tindakan: Perbaikan/Penggantian/Pemeriksaan Rutin
Isi Tanggal Tindakan
Isi Deskripsi (min. 20 karakter)
Isi Nama Teknisi (opsional)
    ↓
Aset sekarang dalam kondisi apa? (opsional tapi disarankan)
→ Pilih "Kondisi Setelah Perbaikan" (Baik/Perlu Perhatian/Kritis/Tidak Layak)
    ↓
Atur Jadwal Maintenance Berikutnya (opsional, tidak boleh di masa lalu)
    ↓
Klik "Simpan Catatan"
    ↓
✅ Tersimpan langsung ke riwayat maintenance (TANPA approval)
✅ Kondisi aset terupdate jika diisi
✅ last_maintenance_date terupdate
```

## 6.5 Alur Cetak KIR & QR Code

```
[Admin Ruangan] Buka Detail Aset
    ↓
┌─ Cetak KIR ──────────────────┐
│ Klik tombol "Cetak KIR"      │
│ → File PDF terunduh otomatis │
│ → Sistem catat ke maintenance│
└──────────────────────────────┘
    ↓
┌─ QR Code ────────────────────┐
│ Klik tombol "QR Code" atau   │
│ "Download QR Code" di kartu  │
│ → File PNG terunduh otomatis │
│ → Cetak & tempel di aset     │
└──────────────────────────────┘
```

---

# BAB 7 — KODE WARNA & BADGE

## 7.1 Kondisi Aset

| Kondisi | Warna Badge | Maksud |
|---------|-------------|--------|
| **Baik** | 🟢 Hijau | Aset normal, siap digunakan |
| **Perlu Perhatian** | 🟡 Kuning | Mulai ada gejala, butuh pemantauan |
| **Kritis** | 🟠 Oranye | Risiko tinggi, perlu tindakan segera |
| **Tidak Layak** | 🔴 Merah | Tidak boleh digunakan, harus diganti/dipensiunkan |

## 7.2 Status Operasional Aset

| Status | Warna Badge | Maksud |
|--------|-------------|--------|
| **Aktif** | 🟢 Hijau | Aset sedang digunakan operasional |
| **Dalam Perbaikan** | 🟡 Kuning | Sedang diperbaiki, sementara tidak operasional |
| **Tidak Aktif** | ⚫ Abu-abu | Tidak digunakan, tidak rusak |
| **Menunggu Approval** | 🔵 Biru | Sedang menunggu keputusan Admin Divisi |

## 7.3 Kategori RPN

| Kategori | Rentang | Warna | Aksi yang Disarankan |
|----------|---------|-------|---------------------|
| **Rendah** | < 80 | 🟢 Hijau | Pemeliharaan rutin sesuai jadwal |
| **Sedang** | 80 – 199 | 🟡 Kuning | Pemeriksaan dalam maks. 7 hari |
| **Tinggi** | ≥ 200 | 🔴 Merah | Tindakan segera dalam 1×24 jam |

## 7.4 Status Approval

| Status | Warna Badge |
|--------|-------------|
| **Pending** | 🟡 Kuning |
| **Disetujui** | 🟢 Hijau |
| **Ditolak** | 🔴 Merah |

## 7.5 Status Akun Pengguna

| Status | Warna Badge |
|--------|-------------|
| **Aktif** | 🟢 Hijau |
| **Nonaktif** | 🔴 Merah |

---

# BAB 8 — PERTANYAAN UMUM (FAQ)

### ❓ Kenapa tombol "Edit" dan "Ajukan Perubahan Status" tidak muncul di Detail Aset?

> Aset sedang dalam status **"Menunggu Approval"**. Tunggu hingga Admin Divisi memproses pengajuan sebelumnya. Setelah disetujui/ditolak, tombol akan muncul kembali.

### ❓ Kenapa kondisi aset berubah sendiri setelah evaluasi FMEA?

> Sistem secara otomatis **memperburuk kondisi aset** berdasarkan hasil RPN:
> - RPN Tinggi → kondisi menjadi Kritis
> - RPN Sedang → kondisi menjadi Perlu Perhatian
>
> Kondisi **hanya bisa membaik secara manual** melalui form **Catat Perbaikan** dengan field "Kondisi Setelah Perbaikan".

### ❓ Kenapa file ekspor Excel/PDF berbeda dari yang tampil di layar?

> Pastikan **filter di halaman Laporan sudah di-set** sesuai keinginan **sebelum** klik ekspor. Sistem mengekspor data sesuai filter yang aktif, bukan semua aset.

### ❓ Bagaimana cara memulihkan aset dari kondisi "Tidak Layak"?

> 1. Buka halaman **Detail Aset**
> 2. Klik **"Catat Perbaikan"** (hijau)
> 3. Isi form perbaikan
> 4. Pada field **"Kondisi Setelah Perbaikan"** → pilih kondisi baru (misal "Baik")
> 5. Klik **"Simpan Catatan"**

### ❓ Saya tidak bisa membuat akun. Apa yang harus dilakukan?

> Akun **hanya dapat dibuat oleh Super Admin**. Hubungi Super Admin sistem untuk meminta akun baru, dengan menyebutkan: nama lengkap, email, role yang diminta (Admin Divisi/Ruangan), dan divisi/ruangan yang akan dikelola.

### ❓ Kenapa tidak bisa menghapus ruangan?

> Ruangan **hanya bisa dihapus jika sudah tidak memiliki aset sama sekali**. Pindahkan atau hapus semua aset terlebih dahulu, baru ruangan bisa dihapus.

### ❓ Apa itu KIR?

> **KIR** = Kartu Identifikasi dan Riwayat — dokumen PDF berisi identitas lengkap dan riwayat perawatan aset. Berguna untuk:
> - Keperluan audit
> - Inspeksi rumah sakit
> - Dokumentasi fisik aset

### ❓ Kenapa pengajuan perubahan status saya ditolak?

> Cek halaman **Notifikasi** atau **Approval Center** → klik detail pengajuan tersebut. Akan tertulis **alasan penolakan** dari Admin Divisi pada bagian "Hasil Keputusan". Anda dapat mengajukan ulang setelah memperbaiki sesuai catatan reviewer.

### ❓ Kenapa saya tidak bisa mengaktifkan kembali akun yang nonaktif?

> Sistem mencegah aktivasi akun jika **divisi/ruangan terkait sudah memiliki admin aktif lain**. Solusi: nonaktifkan dulu admin yang sedang aktif di divisi/ruangan tersebut, baru aktifkan akun yang ingin dikembalikan.

### ❓ QR Code aset untuk apa?

> QR Code berisi link langsung ke halaman detail aset. Cetak dan tempel di fisik aset, lalu scan dengan HP untuk akses cepat ke informasi aset (kondisi, riwayat, dll) tanpa perlu mencari di sistem.

### ❓ Apa beda "Catat Perbaikan" dan "Ajukan Perubahan Status"?

> | **Catat Perbaikan** | **Ajukan Perubahan Status** |
> |--------------------|----------------------------|
> | Tidak butuh approval | Butuh approval Admin Divisi |
> | Mencatat tindakan teknis | Mengubah status operasional |
> | Bisa update kondisi (Baik/Kritis/dll) | Mengubah status (Aktif/Dalam Perbaikan/Tidak Aktif) |
> | Untuk: laporan teknisi/perawatan | Untuk: keputusan operasional |

### ❓ Kenapa saya tidak menerima notifikasi RPN Tinggi?

> Notifikasi RPN Tinggi (≥200) **dikirim ke Admin Divisi**, bukan ke Admin Ruangan yang membuat evaluasi. Admin Ruangan hanya menerima notifikasi RPN **Sedang**. Cek juga: pastikan email dan akun Anda aktif.

---

## INFORMASI KONTAK

Untuk pertanyaan teknis, hubungi **Super Admin sistem** atau tim IT RSKGM Palembang.

---

**Dokumen ini dibuat untuk keperluan internal RSKGM Palembang.**
*Versi 1.0 — 2026*
