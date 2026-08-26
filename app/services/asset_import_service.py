"""Import compact asset-registration spreadsheets safely by room."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import tempfile
from uuid import UUID, uuid4

from openpyxl import load_workbook
from werkzeug.datastructures import FileStorage

from app import db
from app.models.asset import Asset
from app.models.asset_category import AssetCategory
from app.models.room import Room
from app.utils.helpers import generate_asset_code


IMPORT_DIR = Path(tempfile.gettempdir()) / 'simaset-asset-imports'
VALID_CONDITIONS = {'baik', 'perlu_perhatian', 'kritis', 'tidak_layak'}

FIELD_ALIASES = {
    'item_code': {'kodebarang', 'kodebarangaset', 'kodeinventaris'},
    'asset_name': {'namaaset', 'namaalat', 'namabarang'},
    'brand_model': {'merkmodel', 'merktype', 'merkatau model', 'merk'},
    'serial_number': {'noseri', 'serialnumber', 'sn'},
    'quantity': {'jumlah', 'jumlahbarang', 'kuantitas'},
    'unit': {'satuan', 'satuanbarang'},
    'specification': {'spesifikasi', 'spesifikasinamabarang'},
    'room_name': {'namaruangan', 'ruangan', 'lokasi'},
    'purchase_date': {'tanggalpembelian', 'tanggalperolehan'},
    'purchase_price': {'hargapembelian', 'hargabeli', 'hargaperolehan'},
    'acquisition_document_number': {'nomordokumenbast', 'dokumenbast', 'nomordokumen'},
    'funding_source': {'sumberdana', 'sumberdanakib'},
    'condition': {'kondisi', 'kondisiaset'},
    'notes': {'catatan', 'keterangan'},
}


@dataclass
class AssetImportRow:
    sheet_name: str
    row_number: int
    item_code: str = ''
    asset_name: str = ''
    brand_model: str = ''
    serial_number: str = ''
    quantity: int | None = None
    unit: str = ''
    specification: str = ''
    room_name: str = ''
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    acquisition_document_number: str = ''
    funding_source: str = ''
    condition: str = ''
    notes: str = ''
    status: str = 'new'
    status_label: str = 'Aset baru'
    match_note: str = ''
    target_room_id: int | None = None


@dataclass
class AssetImportPreview:
    rows: list[AssetImportRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ignored_rows: int = 0

    @property
    def total_rows(self):
        return len(self.rows) + self.ignored_rows

    @property
    def new_count(self):
        return sum(row.status == 'new' for row in self.rows)

    @property
    def duplicate_count(self):
        return sum(row.status == 'duplicate' for row in self.rows)

    @property
    def invalid_count(self):
        return sum(row.status == 'invalid' for row in self.rows)

    @property
    def has_blocking_rows(self):
        return self.invalid_count > 0


@dataclass
class AssetImportResult:
    assets_created: int = 0
    rows_skipped: int = 0
    invalid_rows: int = 0


def store_upload(upload: FileStorage):
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    token = str(uuid4())
    path = IMPORT_DIR / f'{token}.xlsx'
    upload.save(path)
    return token


def pending_upload_path(token):
    if not token:
        return None
    try:
        UUID(token)
    except (ValueError, TypeError, AttributeError):
        return None

    path = (IMPORT_DIR / f'{token}.xlsx').resolve()
    try:
        path.relative_to(IMPORT_DIR.resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def remove_upload(token):
    path = pending_upload_path(token)
    if path:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def build_asset_preview(path, allowed_room_ids=None, default_room_id=None):
    workbook = load_workbook(path, data_only=True, read_only=False)
    allowed_room_ids = None if allowed_room_ids is None else set(allowed_room_ids)
    rooms = _scoped_rooms(allowed_room_ids)
    preview = AssetImportPreview()
    seen_keys = set()

    worksheet = _select_worksheet(workbook)
    header_row, columns = _detect_columns(worksheet)
    is_legacy_kib = not columns
    start_row = header_row + 1 if columns else 7

    for row_number in range(start_row, worksheet.max_row + 1):
        row = (_parse_compact_row(worksheet, worksheet.title, row_number, columns)
               if columns else _parse_legacy_kib_row(worksheet, worksheet.title, row_number))
        if not row:
            preview.ignored_rows += 1
            continue

        _resolve_room(row, rooms, default_room_id)
        if row.status == 'invalid':
            preview.rows.append(row)
            continue

        row_key = (
            row.target_room_id,
            _norm(row.item_code),
            _norm(row.serial_number),
            _norm(row.asset_name),
        )
        if row_key in seen_keys:
            row.status = 'duplicate'
            row.status_label = 'Duplikat file'
            row.match_note = 'Baris aset identik sudah muncul sebelumnya.'
            preview.rows.append(row)
            continue
        seen_keys.add(row_key)

        row.status = 'new'
        row.status_label = 'Aset baru'
        row.match_note = 'Aset akan dibuat dengan kode aset otomatis.'
        preview.rows.append(row)

    if preview.new_count:
        preview.warnings.append(
            f'{preview.new_count} aset baru akan dibuat dan mendapatkan kode aset otomatis.'
        )
    if preview.invalid_count:
        preview.warnings.append(
            f'{preview.invalid_count} baris belum lengkap. Perbaiki kolom wajib sebelum menyimpan.'
        )
    return preview


def commit_asset_import(path, user, allowed_room_ids=None, default_room_id=None):
    preview = build_asset_preview(
        path,
        allowed_room_ids=allowed_room_ids,
        default_room_id=default_room_id,
    )
    if preview.has_blocking_rows:
        raise ValueError('Preview import masih memiliki baris wajib yang kosong atau identitas ganda.')

    result = AssetImportResult(invalid_rows=preview.invalid_count)
    sequence_cache = {}
    category = _default_category()
    for row in preview.rows:
        if row.status in {'duplicate', 'invalid'}:
            result.rows_skipped += 1
            continue

        room = Room.query.get(row.target_room_id)
        if not room or (allowed_room_ids is not None and room.id not in set(allowed_room_ids)):
            result.rows_skipped += 1
            continue

        asset = Asset(
            asset_code=_next_asset_code(room, sequence_cache),
            item_code=row.item_code or None,
            asset_name=row.asset_name,
            specification=row.specification or None,
            category=category,
            room_id=room.id,
            brand=row.brand_model,
            model='',
            serial_number=row.serial_number,
            quantity=row.quantity,
            unit=row.unit or 'unit',
            purchase_date=row.purchase_date,
            purchase_price=row.purchase_price,
            acquisition_document_number=row.acquisition_document_number or None,
            funding_source=row.funding_source or None,
            condition=row.condition,
            status='aktif',
            notes=row.notes or None,
            created_by=user.id,
        )
        db.session.add(asset)
        result.assets_created += 1

    db.session.commit()
    return result


def _scoped_rooms(allowed_room_ids):
    query = Room.query.filter_by(is_active=True)
    if allowed_room_ids is not None:
        if not allowed_room_ids:
            return []
        query = query.filter(Room.id.in_(allowed_room_ids))
    return query.order_by(Room.room_name).all()


def _select_worksheet(workbook):
    # Table 1 berisi baris aset detail pada format KIB klien; Lembar1 biasanya ringkasan.
    for name in ('Table 1', 'Data Aset', 'Lembar1'):
        if name in workbook.sheetnames:
            return workbook[name]
    return workbook[workbook.sheetnames[0]]


def _detect_columns(worksheet):
    best_row = None
    best_columns = {}
    best_score = 0
    for row_number in range(1, min(worksheet.max_row, 10) + 1):
        columns = {}
        for column in range(1, worksheet.max_column + 1):
            label = _norm_header(worksheet.cell(row_number, column).value)
            if not label:
                continue
            for field_name, aliases in FIELD_ALIASES.items():
                if label in {_norm_header(alias) for alias in aliases}:
                    columns.setdefault(field_name, column)
                    break
        score = sum(field in columns for field in ('asset_name', 'brand_model', 'serial_number', 'quantity'))
        if score > best_score:
            best_row, best_columns, best_score = row_number, columns, score
    if best_score < 3 or 'asset_name' not in best_columns:
        return None, {}
    return best_row, best_columns


def _parse_compact_row(worksheet, sheet_name, row_number, columns):
    values = {}
    for field_name, column in columns.items():
        raw_value = worksheet.cell(row_number, column).value
        values[field_name] = raw_value if field_name in {'purchase_date', 'purchase_price'} else _text(raw_value)
    if not any(values.values()):
        return None
    return _make_row(sheet_name, row_number, values, legacy=False)


def _parse_legacy_kib_row(worksheet, sheet_name, row_number):
    asset_name = _text(worksheet.cell(row_number, 10).value)
    if not asset_name or asset_name.lower().startswith('contoh'):
        return None
    values = {
        'item_code': _build_legacy_item_code(worksheet, row_number),
        'asset_name': asset_name,
        'brand_model': _text(worksheet.cell(row_number, 28).value),
        'serial_number': _text(worksheet.cell(row_number, 29).value),
        'quantity': _text(worksheet.cell(row_number, 30).value),
        'unit': _text(worksheet.cell(row_number, 31).value),
        'specification': _text(worksheet.cell(row_number, 21).value),
        'room_name': _text(worksheet.cell(row_number, 17).value),
        'purchase_date': worksheet.cell(row_number, 41).value,
        'purchase_price': worksheet.cell(row_number, 35).value or worksheet.cell(row_number, 33).value,
        'acquisition_document_number': _text(worksheet.cell(row_number, 43).value),
        'funding_source': _text(worksheet.cell(row_number, 44).value),
        'condition': worksheet.cell(row_number, 22).value,
        'notes': _text(worksheet.cell(row_number, 45).value),
    }
    return _make_row(sheet_name, row_number, values, legacy=True)


def _make_row(sheet_name, row_number, values, legacy=False):
    if values.get('asset_name', '').lower().startswith('contoh'):
        return None
    row = AssetImportRow(
        sheet_name=sheet_name,
        row_number=row_number,
        item_code=_text(values.get('item_code')),
        asset_name=_text(values.get('asset_name')),
        brand_model=_text(values.get('brand_model')),
        serial_number=_text(values.get('serial_number')),
        quantity=_to_int(values.get('quantity')),
        unit=_text(values.get('unit')),
        specification=_text(values.get('specification')),
        room_name=_text(values.get('room_name')),
        purchase_date=_to_date(values.get('purchase_date')),
        purchase_price=_to_money(values.get('purchase_price')),
        acquisition_document_number=_text(values.get('acquisition_document_number')),
        funding_source=_text(values.get('funding_source')),
        condition=_normalize_condition(values.get('condition')),
        notes=_text(values.get('notes')),
    )
    errors = []
    if not row.asset_name:
        errors.append('Nama Aset wajib diisi.')
    if not row.brand_model and not legacy:
        errors.append('Merk/Model wajib diisi.')
    if not row.serial_number and not legacy:
        errors.append('No Seri wajib diisi.')
    if not row.quantity or row.quantity < 1:
        if legacy:
            row.quantity = 1
        else:
            errors.append('Jumlah minimal 1.')
    if not row.condition:
        if legacy:
            row.condition = 'baik'
        else:
            errors.append('Kondisi wajib diisi.')
    if errors:
        row.status = 'invalid'
        row.status_label = 'Data belum lengkap'
        row.match_note = ' '.join(errors)
    return row


def _resolve_room(row, rooms, default_room_id):
    if row.status == 'invalid':
        return
    room_by_key = {}
    for room in rooms:
        room_by_key[_norm(room.room_name)] = room
        room_by_key[_norm(room.room_code)] = room

    if default_room_id:
        room = next((item for item in rooms if item.id == default_room_id), None)
        if not room:
            row.status = 'invalid'
            row.status_label = 'Ruangan tidak valid'
            row.match_note = 'Ruangan akun tidak ditemukan.'
            return
        row.target_room_id = room.id
        row.room_name = room.room_name
        return

    room = room_by_key.get(_norm(row.room_name)) if row.room_name else None
    if not room:
        row.status = 'invalid'
        row.status_label = 'Ruangan wajib diperiksa'
        row.match_note = 'Nama Ruangan wajib diisi dengan ruangan yang tersedia.'
        return
    row.target_room_id = room.id
    row.room_name = room.room_name


def _default_category():
    category = AssetCategory.query.filter_by(category_name='Umum').first()
    if category:
        return category
    category = AssetCategory(
        category_name='Umum',
        description='Kategori internal default untuk import data aset.',
    )
    db.session.add(category)
    db.session.flush()
    return category


def _next_asset_code(room, sequence_cache):
    if room.id not in sequence_cache:
        sequence_cache[room.id] = 0
        for asset in Asset.query.filter_by(room_id=room.id).all():
            try:
                sequence_cache[room.id] = max(sequence_cache[room.id], int(asset.asset_code.rsplit('-', 1)[-1]))
            except (AttributeError, ValueError, IndexError):
                continue
    sequence_cache[room.id] += 1
    return generate_asset_code(room.room_code, sequence_cache[room.id])


def _build_legacy_item_code(worksheet, row_number):
    parts = []
    for column in range(1, 9):
        value = worksheet.cell(row_number, column).value
        if value in (None, ''):
            continue
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        parts.append(str(value).strip())
    return '.'.join(parts)


def _norm_header(value):
    return re.sub(r'[^a-z0-9]+', '', _text(value).lower())


def _norm(value):
    return re.sub(r'[^a-z0-9]+', '', _text(value).lower())


def _text(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    if text.lower() in {'-', 'none', 'nan', '—'}:
        return ''
    return re.sub(r'\s+', ' ', text)


def _to_int(value):
    if isinstance(value, int):
        return value
    match = re.search(r'\d+', _text(value))
    return int(match.group(0)) if match else None


def _to_money(value):
    if value in (None, '', '-'):
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    text = _text(value).replace('Rp', '').replace('rp', '').replace('.', '').replace(',', '.')
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _text(value).lower()
    for fmt in (
        '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y',
        '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S',
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_condition(value):
    text = _norm(value)
    if not text:
        return ''
    if text in {'baik', 'b', 'good', 'normal'}:
        return 'baik'
    if text in {'perluperhatian', 'rusakringan', 'ringan', 'perlu'}:
        return 'perlu_perhatian'
    if text in {'kritis', 'rusakberat', 'berat'}:
        return 'kritis'
    if text in {'tidaklayak', 'tidakdapatdigunakan', 'tidakaktif'}:
        return 'tidak_layak'
    return text if text in VALID_CONDITIONS else ''
