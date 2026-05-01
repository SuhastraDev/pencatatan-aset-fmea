# SIMASET — Sistem Informasi Manajemen Aset RSKGM Palembang

Aplikasi web berbasis Flask untuk pencatatan dan pemantauan aset rumah sakit. Dilengkapi evaluasi risiko FMEA, alur approval perubahan status aset, ekspor laporan (Excel & PDF), dan notifikasi real-time antar peran.

---

## Tech Stack

| Layer | Teknologi |
|---|---|
| Backend | Python 3.11, Flask 3.0.3 |
| ORM | Flask-SQLAlchemy 3.1.1 + SQLAlchemy 2.0 |
| Database | MySQL (driver: PyMySQL 1.1.1) |
| Auth | Flask-Login 0.6.3 + Flask-Bcrypt 1.0.1 |
| Form & CSRF | Flask-WTF 1.2.1 + WTForms 3.1.2 |
| Migrasi DB | Flask-Migrate 4.0.7 (Alembic) |
| Export PDF | WeasyPrint 62.3 |
| Export Excel | OpenPyXL 3.1.2 |
| QR Code | qrcode[pil] 7.4.2 + Pillow 10.3.0 |
| Template | Jinja2 (bawaan Flask) |
| Frontend | Bootstrap 5.3.3 + Bootstrap Icons 1.11.3 + Inter Font |
| Production | Gunicorn 22.0.0 |

---

## Struktur Proyek

```
simaset/
├── run.py                    # Entry point aplikasi
├── config.py                 # Konfigurasi (env vars, thresholds)
├── requirements.txt
├── .env.example
├── exports/                  # File ekspor yang digenerate (runtime)
├── migrations/               # Alembic migrations
└── app/
    ├── __init__.py           # Application factory (create_app)
    ├── models/               # SQLAlchemy models
    │   ├── user.py
    │   ├── division.py
    │   ├── room.py
    │   ├── asset.py
    │   ├── asset_category.py
    │   ├── fmea.py
    │   ├── maintenance_log.py
    │   ├── approval_request.py
    │   └── notification.py
    ├── routes/               # Blueprints
    │   ├── auth.py
    │   ├── super_admin.py
    │   ├── divisi.py
    │   └── ruangan.py
    ├── forms/                # WTForms form classes
    ├── services/             # Business logic
    │   ├── fmea_service.py
    │   ├── notif_service.py
    │   └── export_service.py
    ├── utils/
    │   ├── decorators.py     # @role_required, @check_room_ownership
    │   ├── helpers.py        # generate_asset_code, time_ago, QR code
    │   └── seeder.py         # flask seed command
    ├── static/
    │   └── qrcodes/          # QR code PNG yang digenerate
    └── templates/
        ├── layouts/          # base.html, base_super_admin.html, dll
        ├── auth/
        ├── super_admin/
        ├── divisi/
        ├── ruangan/
        ├── shared/
        ├── exports/          # Template KIR PDF
        └── errors/           # 403, 404, 500
```

---

## Instalasi & Setup

### 1. Clone & Virtual Environment

```bash
git clone https://github.com/SuhastraDev/pencatatan-aset-fmea.git
cd pencatatan-aset-fmea
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment

Salin `.env.example` menjadi `.env` lalu sesuaikan:

```bash
cp .env.example .env
```

Isi file `.env`:

```env
SECRET_KEY=ganti-dengan-secret-key-yang-kuat
DATABASE_URL=mysql+pymysql://root:password@localhost/simaset_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=email@gmail.com
MAIL_PASSWORD=app-password-gmail
```

### 4. Buat Database

```sql
CREATE DATABASE simaset_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Jalankan Migrasi

```bash
flask db upgrade
```

### 6. Seed Data Awal

```bash
flask seed
```

Perintah ini akan membuat:
- **1 akun Super Admin** (lihat seksi [User Seeder](#user-seeder) di bawah)
- **2 divisi** awal: `Divisi Rawat Jalan` dan `Divisi Operasi & Tindakan`
- **5 kategori aset**: Alat Diagnostik, Alat Terapi, Alat Sterilisasi, Alat Penunjang, Alat Darurat

### 7. Jalankan Aplikasi

**Development:**
```bash
flask run
```
atau:
```bash
python run.py
```

**Production:**
```bash
gunicorn run:app --bind 0.0.0.0:8000 --workers 4
```

Akses di: `http://localhost:5000`

---

## User Seeder

Seeder dijalankan dengan `flask seed`. Membuat akun awal jika belum ada.

### Akun Super Admin

| Field | Value |
|---|---|
| **Email** | `superadmin@rskgm.id` |
| **Password** | `password` |
| **Role** | `super_admin` |
| **Status** | Aktif |

> **Penting:** Segera ganti password setelah login pertama melalui menu **Profil Saya**.

### Alur Pembuatan Akun Lain

Semua akun (Admin Divisi & Admin Ruangan) **hanya dapat dibuat oleh Super Admin** melalui menu **Tambah User** di panel admin. Tidak ada halaman registrasi publik.

---

## Peran & Hak Akses

Sistem memiliki **tiga peran** dengan hierarki bertingkat:

### Super Admin
Mengelola seluruh struktur organisasi sistem:
- CRUD divisi dan ruangan
- Membuat & mengelola akun Admin Divisi dan Admin Ruangan
- Mengaktifkan/menonaktifkan akun pengguna
- Melihat dashboard ringkasan keseluruhan

### Admin Divisi
Memantau dan menyetujui perubahan di tingkat divisi:
- Melihat daftar aset seluruh ruangan dalam divisinya
- Memproses approval request perubahan status aset
- Melihat laporan & riwayat maintenance per ruangan
- Ekspor laporan ke Excel dan PDF
- Menerima notifikasi RPN tinggi (≥ 200)

### Admin Ruangan
Pengelola aset harian di tingkat ruangan:
- CRUD aset dalam ruangannya
- Melakukan evaluasi FMEA (Severity × Occurrence × Detection = RPN)
- Mengajukan permintaan perubahan status aset
- Mencatat riwayat perbaikan/maintenance
- Mengunduh KIR (Kartu Identitas Registrasi) dan QR code aset
- Ekspor laporan ruangan ke Excel dan PDF

---

## Fitur Utama

### Manajemen Aset
- Kode aset otomatis: format `AST-{KODERUANGAN}-{TAHUN}-{URUTAN}`
- Kondisi aset: `baik`, `perlu_perhatian`, `kritis`, `tidak_layak`
- Status aset: `aktif`, `dalam_perbaikan`, `tidak_aktif`, `menunggu_approval`
- QR code otomatis per aset (disimpan di `app/static/qrcodes/`)

### Evaluasi FMEA
- Input: Severity (1–10), Occurrence (1–10), Detection (1–10)
- **RPN = S × O × D**
- Kategori risiko otomatis:
  - RPN ≥ 200 → **Tinggi** → kondisi aset: `kritis` → notifikasi ke Admin Divisi
  - RPN 80–199 → **Sedang** → kondisi aset: `perlu_perhatian` → notifikasi ke Admin Ruangan
  - RPN < 80 → **Rendah** → kondisi aset: `baik`
- Rekomendasi tindakan digenerate otomatis berdasarkan kategori risiko

### Alur Approval
1. Admin Ruangan mengajukan permintaan perubahan status aset
2. Aset masuk status `menunggu_approval` (terkunci, tidak bisa diedit)
3. Admin Divisi menerima notifikasi dan memproses di **Approval Center**
4. Jika disetujui → status aset diperbarui + log tercatat + notifikasi ke Admin Ruangan
5. Jika ditolak → status aset dikembalikan + alasan penolakan dikirim

### Laporan & Ekspor
- Ekspor Excel (Admin Ruangan: 1 sheet; Admin Divisi: 2 sheet — data aset + statistik per ruangan)
- Ekspor PDF via WeasyPrint
- KIR (Kartu Identitas Registrasi) aset dalam format PDF, lengkap QR code

### Notifikasi
| Tipe | Trigger | Penerima |
|---|---|---|
| `rpn_tinggi` | RPN ≥ 200 | Semua Admin Divisi di divisi tersebut |
| `rpn_sedang` | RPN 80–199 | Admin Ruangan yang submit |
| `approval_baru` | Request change diajukan | Semua Admin Divisi di divisi tersebut |
| `approval_disetujui` | Approval disetujui | Admin Ruangan pemohon |
| `approval_ditolak` | Approval ditolak | Admin Ruangan pemohon |
| `maintenance_terlambat` | Login (lazy check) | Pengguna yang login (jika ada aset overdue) |

---

## Endpoint URL Ringkasan

### Auth (`/`)
| Method | URL | Keterangan |
|---|---|---|
| GET/POST | `/login` | Halaman login |
| GET | `/logout` | Logout |
| GET/POST | `/profile` | Edit profil & ganti password |
| GET | `/notifications` | Daftar notifikasi |

### Super Admin (`/super-admin/`)
| URL | Keterangan |
|---|---|
| `/super-admin/dashboard` | Dashboard ringkasan |
| `/super-admin/divisions` | Manajemen divisi |
| `/super-admin/rooms` | Manajemen ruangan |
| `/super-admin/users/admin-divisi` | Daftar Admin Divisi |
| `/super-admin/users/admin-ruangan` | Daftar Admin Ruangan |
| `/super-admin/users/create` | Tambah user baru |

### Admin Divisi (`/divisi/`)
| URL | Keterangan |
|---|---|
| `/divisi/dashboard` | Dashboard divisi + grafik RPN |
| `/divisi/assets` | Daftar aset seluruh ruangan |
| `/divisi/approvals` | Approval Center |
| `/divisi/reports` | Laporan & ekspor divisi |
| `/divisi/members` | Daftar ruangan & adminnya |
| `/divisi/maintenance-logs` | Riwayat maintenance divisi |

### Admin Ruangan (`/ruangan/`)
| URL | Keterangan |
|---|---|
| `/ruangan/dashboard` | Dashboard ruangan |
| `/ruangan/assets` | Daftar aset ruangan |
| `/ruangan/assets/create` | Tambah aset baru |
| `/ruangan/assets/<id>/fmea` | Form evaluasi FMEA |
| `/ruangan/assets/<id>/request-change` | Ajukan perubahan status |
| `/ruangan/assets/<id>/kir` | Download KIR PDF |
| `/ruangan/reports` | Laporan & ekspor ruangan |
| `/ruangan/maintenance-logs` | Riwayat maintenance ruangan |

---

## Konfigurasi Penting

| Variabel | Default | Keterangan |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key` | **Wajib diganti** di production |
| `DATABASE_URL` | `mysql+pymysql://root:@localhost/simaset_db` | URI koneksi database |
| `RPN_HIGH_THRESHOLD` | `200` | Batas RPN kategori tinggi |
| `RPN_MEDIUM_THRESHOLD` | `80` | Batas RPN kategori sedang |
| `PERMANENT_SESSION_LIFETIME` | 8 jam | Durasi sesi login |
| `EXPORTS_FOLDER` | `<root>/exports` | Folder output file ekspor |

---

## Database Migrations

```bash
# Terapkan semua migrasi
flask db upgrade

# Buat migrasi baru setelah mengubah model
flask db migrate -m "deskripsi perubahan"
flask db upgrade

# Rollback satu versi
flask db downgrade
```

---

## Catatan Deployment Production

1. Set `FLASK_ENV=production` dan `FLASK_DEBUG=0`
2. Ganti `SECRET_KEY` dengan nilai acak yang kuat (min 32 karakter)
3. Pastikan folder `exports/` dan `app/static/qrcodes/` dapat ditulis oleh proses web server
4. Konfigurasi reverse proxy (Nginx/Apache) di depan Gunicorn
5. Gunakan HTTPS — WeasyPrint & QR code menggunakan path file absolut yang sensitif terhadap base URL

---

## Lisensi

Dibuat untuk keperluan internal **RS Khusus Gigi dan Mulut (RSKGM) Palembang**.
