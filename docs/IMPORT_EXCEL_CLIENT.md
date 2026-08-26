# Panduan Import Excel Klien

Importer ini dipakai untuk memasukkan data dari file Excel klien ke SIMASET tanpa menggandakan data yang sudah ada.

## File yang Didukung

- `INTRA EKSTRA KIB B.xlsx` untuk master aset/KIB.
- `Data History Maintenance Aset.xlsx` untuk riwayat kerusakan dan perbaikan.
- `PREVENTIVE ASET.xlsx` untuk checklist preventive maintenance.

## Cara Kerja Sinkronisasi

Importer mencocokkan aset dengan urutan berikut:

1. `No Seri`
2. `Kode Barang`
3. `Nama Aset + Ruangan`

Jika cocok, data aset yang masih kosong akan dilengkapi. Jika tidak cocok, aset baru dibuat sesuai ruangan dari file history/preventive.

## Dry Run

Jalankan ini dulu untuk melihat perkiraan perubahan tanpa menyimpan ke database:

```bash
flask import-client-excel \
  --kib-file "/var/www/simaset/imports/INTRA EKSTRA KIB B.xlsx" \
  --history-file "/var/www/simaset/imports/Data History Maintenance Aset.xlsx" \
  --preventive-file "/var/www/simaset/imports/PREVENTIVE ASET.xlsx" \
  --dry-run
```

## Commit Import

Jika hasil dry-run sudah aman, jalankan:

```bash
flask import-client-excel \
  --kib-file "/var/www/simaset/imports/INTRA EKSTRA KIB B.xlsx" \
  --history-file "/var/www/simaset/imports/Data History Maintenance Aset.xlsx" \
  --preventive-file "/var/www/simaset/imports/PREVENTIVE ASET.xlsx" \
  --commit
```

## Catatan

- KIB tidak selalu punya nama ruangan, jadi KIB dipakai terutama untuk melengkapi data aset.
- History dan preventive lebih kuat untuk menentukan ruangan aset.
- Jika ada data ruangan yang belum ada, importer membuat ruangan baru dengan kode `IMP-*`.
- Setelah import, cek menu Admin Ruangan dan Admin Divisi untuk memastikan data tersinkron.
