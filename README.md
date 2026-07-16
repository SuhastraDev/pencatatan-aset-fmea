# SIMASET RSKGM Palembang

SIMASET adalah Sistem Informasi Manajemen Aset untuk RS Khusus Gigi dan
Mulut (RSKGM) Palembang. Aplikasi ini membantu pencatatan aset, pemantauan
kondisi aset, evaluasi risiko FMEA, approval perubahan status, riwayat
maintenance, notifikasi internal, serta ekspor laporan.

Dokumen ini menjelaskan kondisi repository saat ini, cara menjalankan sistem,
komponen utama aplikasi, dan catatan production yang perlu diperhatikan saat
sistem diserahterimakan ke klien.

## Status Repository

| Area | Status saat ini |
| --- | --- |
| Tipe aplikasi | Flask monolith: backend, frontend template, dan server-side rendering dalam satu aplikasi |
| Frontend | Jinja2 template + Bootstrap |
| Backend | Flask routes, services, forms, dan SQLAlchemy models |
| Database default kode | PostgreSQL melalui `psycopg2-binary` |
| Migration | Flask-Migrate / Alembic |
| Production server | Gunicorn |
| Deployment config yang tersedia | Dockerfile, Procfile, Railway config |
| CI | GitHub Actions untuk syntax check dan import check |

> Catatan penting: repository sudah diarahkan ke PostgreSQL. Untuk Supabase,
> gunakan `DATABASE_URL` PostgreSQL dengan `sslmode=require`, lalu jalankan
> migration dan seeder pada database production.

## Fitur Utama

- Manajemen divisi dan ruangan.
- Manajemen user dengan role bertingkat.
- Manajemen aset berdasarkan ruangan.
- Kode aset otomatis.
- Evaluasi FMEA dengan perhitungan RPN.
- Kategori risiko otomatis berdasarkan RPN.
- Approval perubahan status aset.
- Riwayat maintenance aset.
- Notifikasi internal untuk risiko, approval, dan maintenance.
- Ekspor laporan Excel.
- Ekspor laporan PDF menggunakan `xhtml2pdf`.
- Generate KIR dan QR code aset.

## Role dan Hak Akses

### Super Admin

Super Admin mengelola struktur utama sistem:

- Mengelola divisi.
- Mengelola ruangan.
- Membuat dan mengelola akun Admin Divisi dan Admin Ruangan.
- Mengaktifkan atau menonaktifkan akun.
- Melihat dashboard ringkasan seluruh sistem.

### Admin Divisi

Admin Divisi memantau aset pada divisinya:

- Melihat aset seluruh ruangan dalam divisi.
- Memproses approval perubahan status aset.
- Melihat laporan dan riwayat maintenance per ruangan.
- Mengekspor laporan divisi.
- Menerima notifikasi risiko tinggi.

### Admin Ruangan

Admin Ruangan mengelola aset harian dalam ruangan:

- Menambah, mengubah, dan melihat aset ruangan.
- Melakukan evaluasi FMEA.
- Mengajukan perubahan status aset.
- Mencatat riwayat maintenance.
- Mengunduh KIR dan QR code aset.
- Mengekspor laporan ruangan.

## Alur Utama Sistem

### Manajemen Aset

Kode aset dibuat otomatis dengan pola:

```text
AST-{KODERUANGAN}-{TAHUN}-{URUTAN}
```

Status aset yang digunakan:

- `aktif`
- `dalam_perbaikan`
- `tidak_aktif`
- `menunggu_approval`

Kondisi aset yang digunakan:

- `baik`
- `perlu_perhatian`
- `kritis`
- `tidak_layak`

### Evaluasi FMEA

Admin Ruangan mengisi nilai:

- Severity: 1-10
- Occurrence: 1-10
- Detection: 1-10

RPN dihitung dengan rumus:

```text
RPN = Severity x Occurrence x Detection
```

Kategori risiko:

| Nilai RPN | Kategori | Dampak sistem |
| --- | --- | --- |
| `< 80` | Rendah | Kondisi aset menjadi `baik` |
| `80 - 199` | Sedang | Kondisi aset menjadi `perlu_perhatian` |
| `>= 200` | Tinggi | Kondisi aset menjadi `kritis` dan notifikasi dikirim ke Admin Divisi |

### Approval Perubahan Status

1. Admin Ruangan mengajukan perubahan status aset.
2. Aset masuk status `menunggu_approval`.
3. Admin Divisi menerima notifikasi.
4. Admin Divisi menyetujui atau menolak request.
5. Sistem memperbarui status aset, mencatat log, dan mengirim notifikasi hasil.

## Stack Teknologi

| Layer | Teknologi |
| --- | --- |
| Bahasa | Python 3.11 |
| Framework | Flask 3.0.3 |
| ORM | Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.30 |
| Database default kode | PostgreSQL dengan psycopg2-binary 2.9.9 |
| Database target production final | Supabase PostgreSQL |
| Auth | Flask-Login, Flask-Bcrypt |
| Form dan CSRF | Flask-WTF, WTForms |
| Migration | Flask-Migrate / Alembic |
| PDF | xhtml2pdf |
| Excel | OpenPyXL |
| QR Code | qrcode[pil], Pillow |
| Template | Jinja2 |
| UI | Bootstrap 5, Bootstrap Icons, Inter Font |
| App server | Gunicorn |

## Struktur Project

```text
simaset/
|-- run.py
|-- config.py
|-- requirements.txt
|-- .env.example
|-- Dockerfile
|-- Procfile
|-- railway.json
|-- nixpacks.toml
|-- exports/
|-- migrations/
|-- tests/
`-- app/
    |-- __init__.py
    |-- models/
    |   |-- user.py
    |   |-- division.py
    |   |-- room.py
    |   |-- asset.py
    |   |-- asset_category.py
    |   |-- fmea.py
    |   |-- maintenance_log.py
    |   |-- approval_request.py
    |   `-- notification.py
    |-- routes/
    |   |-- auth.py
    |   |-- super_admin.py
    |   |-- divisi.py
    |   `-- ruangan.py
    |-- forms/
    |-- services/
    |   |-- fmea_service.py
    |   |-- notif_service.py
    |   `-- export_service.py
    |-- utils/
    |-- static/
    `-- templates/
```

## Environment Variable

| Variable | Fungsi | Catatan |
| --- | --- | --- |
| `SECRET_KEY` | Kunci session dan security Flask | Wajib diganti di production |
| `DATABASE_URL` | Connection string database | Gunakan PostgreSQL URL |
| `MAIL_SERVER` | SMTP server | Default `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | Default `587` |
| `MAIL_USERNAME` | Akun email pengirim | Opsional sesuai fitur email |
| `MAIL_PASSWORD` | App password email | Jangan commit ke Git |

Contoh `.env` untuk PostgreSQL lokal:

```env
SECRET_KEY=ganti-dengan-string-random-panjang
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/simaset_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=email@gmail.com
MAIL_PASSWORD=app-password-gmail
```

Contoh format production jika memakai Supabase PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres?sslmode=require
```

Format Supabase di atas tetap perlu dites dengan `flask db upgrade` dari
environment production.

## Setup Lokal

### 1. Clone repository

```bash
git clone https://github.com/SuhastraDev/pencatatan-aset-fmea.git
cd pencatatan-aset-fmea
```

Jika project berada di subfolder `simaset`, masuk ke folder tersebut sebelum
menjalankan command berikutnya.

### 2. Buat virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install dependency

```bash
pip install -r requirements.txt
```

### 4. Buat file environment

```bash
cp .env.example .env
```

Sesuaikan `SECRET_KEY`, `DATABASE_URL`, dan konfigurasi email.

### 5. Siapkan database

Untuk PostgreSQL lokal:

```sql
CREATE DATABASE simaset_db;
```

### 6. Jalankan migration

```bash
flask db upgrade
```

### 7. Jalankan seeder awal

```bash
flask seed
```

Seeder membuat data awal:

- 1 akun Super Admin.
- Divisi awal.
- Kategori aset awal.

### 8. Jalankan aplikasi

```bash
flask run
```

atau:

```bash
python run.py
```

Default lokal dapat diakses melalui:

```text
http://localhost:5000
```

## Akun Awal Seeder

| Field | Value |
| --- | --- |
| Email | `superadmin@rskgm.id` |
| Password | `password` |
| Role | `super_admin` |
| Status | Aktif |

Segera ganti password setelah login pertama melalui menu profil.

## Endpoint Ringkas

### Auth

| Method | URL | Fungsi |
| --- | --- | --- |
| GET/POST | `/login` | Login |
| GET | `/logout` | Logout |
| GET/POST | `/profile` | Edit profil dan password |
| GET | `/notifications` | Daftar notifikasi |

### Super Admin

| URL | Fungsi |
| --- | --- |
| `/super-admin/dashboard` | Dashboard Super Admin |
| `/super-admin/divisions` | Manajemen divisi |
| `/super-admin/rooms` | Manajemen ruangan |
| `/super-admin/users/admin-divisi` | Daftar Admin Divisi |
| `/super-admin/users/admin-ruangan` | Daftar Admin Ruangan |
| `/super-admin/users/create` | Tambah user |

### Admin Divisi

| URL | Fungsi |
| --- | --- |
| `/divisi/dashboard` | Dashboard divisi |
| `/divisi/assets` | Daftar aset divisi |
| `/divisi/approvals` | Approval Center |
| `/divisi/reports` | Laporan divisi |
| `/divisi/members` | Daftar ruangan dan admin |
| `/divisi/maintenance-logs` | Riwayat maintenance divisi |

### Admin Ruangan

| URL | Fungsi |
| --- | --- |
| `/ruangan/dashboard` | Dashboard ruangan |
| `/ruangan/assets` | Daftar aset ruangan |
| `/ruangan/assets/create` | Tambah aset |
| `/ruangan/assets/<id>/fmea` | Evaluasi FMEA |
| `/ruangan/assets/<id>/request-change` | Ajukan perubahan status |
| `/ruangan/assets/<id>/kir` | Download KIR |
| `/ruangan/reports` | Laporan ruangan |
| `/ruangan/maintenance-logs` | Riwayat maintenance ruangan |

## Production dan Hosting

Repository saat ini memiliki beberapa file pendukung deployment:

- `Dockerfile`
- `Procfile`
- `railway.json`
- `nixpacks.toml`
- `.github/workflows/deploy.yml`
- `deployment/`

Workflow GitHub saat ini melakukan:

- install dependency,
- compile semua file Python,
- import `create_app()`,
- deploy ke VPS via SSH saat ada push ke branch `main`.

Secrets untuk deploy disimpan di GitHub repository klien, bukan di kode.
Lihat `deployment/README.md` untuk daftar secrets dan template file production.
Workflow juga melakukan health check ke
`https://simaset-rskgm.duckdns.org/login` setelah restart service.

## Target Production VPS + Supabase

Rencana production yang disarankan:

```text
GitHub client
  -> VPS Ubuntu
  -> Gunicorn + Nginx
  -> Flask SIMASET
  -> Supabase PostgreSQL
```

Checklist teknis sebelum memakai Supabase:

- Set `DATABASE_URL` PostgreSQL di `.env` VPS.
- Jalankan `flask db upgrade` ke database Supabase.
- Jalankan `flask seed` jika database masih kosong.
- Tes login Super Admin.
- Tes export Excel.
- Tes export PDF.
- Tes pembuatan QR code.

## File Runtime yang Perlu Dijaga

| Path | Fungsi | Catatan |
| --- | --- | --- |
| `exports/` | Output file export | Pastikan writable di production |
| `app/static/qrcodes/` | QR code aset | Pastikan writable dan dibackup bila perlu |
| `.env` | Konfigurasi production | Jangan commit ke Git |

## Migration Database

Command umum:

```bash
flask db upgrade
```

Membuat migration baru setelah model berubah:

```bash
flask db migrate -m "deskripsi perubahan"
flask db upgrade
```

Rollback satu versi:

```bash
flask db downgrade
```

## Keamanan Production

- Jangan gunakan `SECRET_KEY` default.
- Jangan commit `.env`, private key SSH, password database, atau app password email.
- Ganti password akun Super Admin setelah login pertama.
- Gunakan HTTPS untuk production.
- Pastikan folder runtime hanya writable sesuai kebutuhan aplikasi.
- Simpan credential final di password manager atau akun resmi klien, bukan di README.

## Catatan Serah Terima

Untuk serah-terima ke klien, dokumentasikan minimal:

- URL website production.
- Domain dan DNS.
- IP VPS.
- Provider VPS.
- User SSH dan lokasi penyimpanan private key.
- Repository GitHub dan branch production.
- Provider database.
- Nama project database.
- Lokasi file `.env` di VPS.
- Nama service systemd.
- Cara backup database dan file runtime.

## Lisensi / Kepemilikan

Dibuat untuk kebutuhan internal RS Khusus Gigi dan Mulut (RSKGM) Palembang.
