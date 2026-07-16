# Deployment VPS SIMASET

Folder ini berisi template persiapan deployment production untuk VPS Ubuntu.
File di sini tidak menyimpan secret asli.

## File

| File | Fungsi |
| --- | --- |
| `env.production.example` | Contoh isi `.env` production di VPS |
| `simaset.service` | Template systemd service untuk Gunicorn |
| `nginx-simaset.conf` | Template Nginx reverse proxy |
| `deploy.sh` | Script update aplikasi di VPS |

## GitHub Secrets

Tambahkan secrets berikut di repository GitHub klien:

| Secret | Isi |
| --- | --- |
| `VPS_HOST` | IP/domain VPS, contoh `52.65.94.214` |
| `VPS_USER` | User SSH, contoh `ubuntu` |
| `VPS_SSH_KEY` | Isi private key SSH untuk deploy |
| `VPS_APP_DIR` | Path project di VPS, contoh `/var/www/simaset` |

## Catatan

- File `.env` production dibuat langsung di VPS, tidak di-commit.
- `DATABASE_URL` production menggunakan connection string Supabase PostgreSQL.
- Jalankan `flask db upgrade` dari VPS setelah environment production benar.
- Pastikan folder `exports/` dan `app/static/qrcodes/` writable oleh user service.
