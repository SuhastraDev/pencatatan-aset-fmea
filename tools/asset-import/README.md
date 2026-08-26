# Tools Import Aset

Script pendukung untuk memeriksa, memetakan, memperbaiki, dan memverifikasi template import aset.

Jalankan dari folder project atau folder mana pun:

```powershell
node tools/asset-import/inspect_asset_workbook.mjs
node tools/asset-import/fix_asset_import_workbook.mjs
node tools/asset-import/verify_asset_import_workbook.mjs
```

File hasil pemeriksaan tersimpan di folder `outputs` dan `workbook_inspection`. Kedua folder tersebut bersifat lokal dan tidak ikut di-commit ke GitHub.
