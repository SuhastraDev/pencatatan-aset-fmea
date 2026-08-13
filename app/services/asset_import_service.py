"""Preview and import identity data from the client's KIB B workbook."""

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
from app.services.excel_import_service import _asset_text_matches, _build_item_code, _text


IMPORT_DIR = Path(tempfile.gettempdir()) / 'simaset-asset-imports'


@dataclass
class AssetImportRow:
    sheet_name: str
    row_number: int
    item_code: str
    asset_name: str
    specification: str
    brand_type: str
    quantity: int | None
    unit: str
    purchase_date: date | None
    purchase_price: Decimal | None
    acquisition_document_number: str
    funding_source: str
    status: str
    status_label: str
    match_note: str = ''
    matched_asset: Asset | None = None


@dataclass
class AssetImportPreview:
    rows: list[AssetImportRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ignored_rows: int = 0

    @property
    def total_rows(self):
        return len(self.rows) + self.ignored_rows

    @property
    def matched_count(self):
        return sum(row.status == 'matched' for row in self.rows)

    @property
    def ambiguous_count(self):
        return sum(row.status == 'ambiguous' for row in self.rows)

    @property
    def unmatched_count(self):
        return sum(row.status == 'unmatched' for row in self.rows)

    @property
    def duplicate_count(self):
        return sum(row.status == 'duplicate' for row in self.rows)

    @property
    def invalid_count(self):
        return sum(row.status == 'invalid' for row in self.rows)

    @property
    def has_blocking_rows(self):
        return self.ambiguous_count > 0 or self.invalid_count > 0


@dataclass
class AssetImportResult:
    assets_updated: int = 0
    rows_skipped: int = 0
    ambiguous_rows: int = 0
    unmatched_rows: int = 0


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


def build_asset_preview(path, allowed_room_ids=None):
    workbook = load_workbook(path, data_only=True, read_only=False)
    allowed_room_ids = None if allowed_room_ids is None else set(allowed_room_ids)
    preview = AssetImportPreview()
    seen_keys = set()

    sheet_name = 'Lembar1' if 'Lembar1' in workbook.sheetnames else (
        'Table 1' if 'Table 1' in workbook.sheetnames else None
    )
    if not sheet_name:
        raise ValueError('Sheet Lembar1 atau Table 1 tidak ditemukan pada file KIB B.')

    ws = workbook[sheet_name]
    assets = _scoped_assets(allowed_room_ids)
    for row_number in range(7, ws.max_row + 1):
        row = _parse_row(ws, sheet_name, row_number)
        if not row:
            preview.ignored_rows += 1
            continue

        row_key = (
            _norm(row.item_code),
            _norm(row.asset_name),
            _norm(row.specification),
            row.quantity,
        )
        if row_key in seen_keys:
            row.status = 'duplicate'
            row.status_label = 'Duplikat file'
            row.match_note = 'Baris identik sudah muncul sebelumnya.'
            preview.rows.append(row)
            continue
        seen_keys.add(row_key)

        matches, match_note = _find_matches(row, assets)
        if len(matches) == 1:
            row.status = 'matched'
            row.status_label = 'Aset cocok'
            row.match_note = match_note
            row.matched_asset = matches[0]
        elif len(matches) > 1:
            row.status = 'ambiguous'
            row.status_label = 'Perlu dipilih'
            row.match_note = 'Lebih dari satu aset cocok; tidak diubah otomatis.'
        else:
            row.status = 'unmatched'
            row.status_label = 'Belum cocok'
            row.match_note = 'Tidak ada pasangan aman pada ruangan yang dapat diakses.'
        preview.rows.append(row)

    if preview.unmatched_count:
        preview.warnings.append(
            f'{preview.unmatched_count} baris KIB belum memiliki pasangan aset dan tidak dibuat otomatis agar ruangan tidak keliru.'
        )
    if preview.ambiguous_count:
        preview.warnings.append(
            f'{preview.ambiguous_count} baris memiliki lebih dari satu pasangan; perbaiki identitas aset atau import setelah pemetaan.'
        )
    return preview


def commit_asset_import(path, allowed_room_ids=None):
    preview = build_asset_preview(path, allowed_room_ids=allowed_room_ids)
    if preview.has_blocking_rows:
        raise ValueError('Preview KIB masih memiliki baris ambigu atau tidak valid. Periksa dahulu sebelum menyimpan.')

    result = AssetImportResult(
        ambiguous_rows=preview.ambiguous_count,
        unmatched_rows=preview.unmatched_count,
    )
    updated_ids = set()
    for row in preview.rows:
        if row.status != 'matched' or not row.matched_asset:
            result.rows_skipped += 1
            continue
        if row.matched_asset.id in updated_ids:
            result.rows_skipped += 1
            continue
        updated_ids.add(row.matched_asset.id)
        if _update_asset(row.matched_asset, row):
            result.assets_updated += 1

    db.session.commit()
    return result


def _scoped_assets(allowed_room_ids):
    query = Asset.query
    if allowed_room_ids is not None:
        if not allowed_room_ids:
            return []
        query = query.filter(Asset.room_id.in_(allowed_room_ids))
    return query.order_by(Asset.id).all()


def _parse_row(ws, sheet_name, row_number):
    asset_name = _text(ws.cell(row_number, 10).value)
    specification = _text(ws.cell(row_number, 21).value)
    quantity = _to_int(ws.cell(row_number, 30).value)
    if asset_name.lower().startswith('contoh'):
        return None
    if not asset_name or not specification or not quantity:
        return None

    return AssetImportRow(
        sheet_name=sheet_name,
        row_number=row_number,
        item_code=_build_item_code(ws, row_number),
        asset_name=asset_name,
        specification=specification,
        brand_type=_text(ws.cell(row_number, 28).value),
        quantity=quantity,
        unit=_text(ws.cell(row_number, 31).value),
        purchase_date=_to_date(ws.cell(row_number, 41).value),
        purchase_price=_to_money(ws.cell(row_number, 35).value) or _to_money(ws.cell(row_number, 33).value),
        acquisition_document_number=_text(ws.cell(row_number, 43).value),
        funding_source=_text(ws.cell(row_number, 44).value),
        status='unmatched',
        status_label='Belum cocok',
    )


def _find_matches(row, assets):
    item_code = _norm(row.item_code)
    if item_code:
        matches = [a for a in assets if _norm(a.item_code) == item_code]
        if matches:
            return matches, 'Cocok berdasarkan kode barang.'

    name = _norm(row.asset_name)
    specification = _norm(row.specification)
    brand = _norm(row.brand_type)
    exact = [
        a for a in assets
        if _norm(a.asset_name) == name
        and (not specification or _norm(a.specification) == specification)
    ]
    if len(exact) == 1:
        return exact, 'Cocok berdasarkan nama dan spesifikasi.'
    if len(exact) > 1 and brand:
        branded = [a for a in exact if _norm(a.brand_model) == brand]
        if branded:
            return branded, 'Cocok berdasarkan nama, spesifikasi, dan merek/tipe.'
        return exact, 'Nama dan spesifikasi cocok pada beberapa aset.'

    candidates = [a for a in assets if _asset_text_matches(row.asset_name, a.asset_name)]
    if specification:
        candidates = [
            a for a in candidates
            if not _norm(a.specification) or _asset_text_matches(row.specification, a.specification)
        ]
    if len(candidates) > 1 and brand:
        branded = [a for a in candidates if _asset_text_matches(row.brand_type, a.brand_model)]
        if branded:
            candidates = branded
    if len(candidates) == 1:
        return candidates, 'Cocok berdasarkan kemiripan identitas KIB.'
    return candidates, '' if candidates else 'Tidak ditemukan.'


def _update_asset(asset, row):
    values = {
        'item_code': row.item_code or None,
        'asset_name': row.asset_name,
        'specification': row.specification,
        'brand': row.brand_type or None,
        'quantity': row.quantity,
        'unit': row.unit or None,
        'purchase_date': row.purchase_date,
        'purchase_price': row.purchase_price,
        'acquisition_document_number': row.acquisition_document_number or None,
        'funding_source': row.funding_source or None,
    }
    changed = False
    for key, value in values.items():
        if value in (None, ''):
            continue
        if getattr(asset, key) != value:
            setattr(asset, key, value)
            changed = True
    return changed


def _norm(value):
    return re.sub(r'[^a-z0-9]+', '', _text(value).lower())


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
    text = _text(value)
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None
