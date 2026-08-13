"""Generate a KIB B template compatible with the asset import parser."""

from datetime import date
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


KIB_HEADERS = [
    'Kode Level 1', 'Kode Level 2', 'Kode Level 3', 'Kode Level 4',
    'Kode Level 5', 'Kode Level 6', 'Kode Level 7', 'Kode Level 8',
    'Uraian/Keterangan', 'Nama Aset', 'Merk', 'Type',
    'Spesifikasi Tambahan', 'Satuan', 'Tahun Perolehan', 'Kode Lokasi',
    'Nama Ruangan', 'Divisi', 'No. Register', 'Kode Inventaris',
    'Spesifikasi', 'Kondisi', 'Status', 'Nomor Dokumen', 'Sumber Dana',
    'Harga Satuan', 'Nilai Perolehan', 'Merk/Type', 'Nomor Seri', 'Jumlah',
    'Satuan', 'Nilai Buku', 'Harga Perolehan', 'Nilai Akumulasi', 'Harga Beli',
    'Tahun', 'Keterangan', 'Kode Barang Tambahan', 'Kode Aset Tambahan',
    'Tanggal Input', 'Tanggal Perolehan', 'Tanggal BAST', 'Dokumen BAST',
    'Sumber Dana KIB', 'Catatan',
]


def generate_asset_template(template_date=None):
    """Return a KIB B workbook whose data starts at row 7."""
    template_date = template_date or date.today()
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Lembar1'

    last_column = _column_name(len(KIB_HEADERS))
    worksheet.merge_cells(f'A1:{last_column}1')
    worksheet['A1'] = 'TEMPLATE IMPORT IDENTITAS ASET KIB B'
    worksheet['A1'].font = Font(bold=True, size=14, color='FFFFFF')
    worksheet['A1'].fill = PatternFill('solid', fgColor='0B7896')
    worksheet['A1'].alignment = Alignment(horizontal='center')

    worksheet.merge_cells(f'A2:{last_column}2')
    worksheet['A2'] = 'Rumah Sakit Khusus Gigi dan Mulut Provinsi Sumatera Selatan'
    worksheet['A2'].font = Font(italic=True, color='666666')
    worksheet['A2'].alignment = Alignment(horizontal='center')

    worksheet.merge_cells(f'A4:{last_column}4')
    worksheet['A4'] = (
        'Isi data mulai baris 7. Hapus baris CONTOH sebelum upload. '
        'Nama aset, spesifikasi, jumlah, dan kode level harus diisi.'
    )
    worksheet['A4'].alignment = Alignment(wrap_text=True)
    worksheet['A4'].font = Font(bold=True, color='404040')

    for column, header in enumerate(KIB_HEADERS, start=1):
        cell = worksheet.cell(row=6, column=column, value=header)
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='1F4E79')
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    sample = [None] * len(KIB_HEADERS)
    sample[0:8] = ['1', '01', '01', '01', '01', '01', '01', '01']
    sample[9] = 'CONTOH - Patient Monitor'
    sample[20] = 'Alat monitor pasien dengan layar digital'
    sample[27] = 'Contoh Merk / Type'
    sample[28] = 'CONTOH-SN-001'
    sample[29] = 1
    sample[30] = 'unit'
    sample[32] = 25000000
    sample[40] = template_date
    sample[41] = template_date
    sample[42] = template_date
    sample[43] = 'CONTOH-BAST-001'
    sample[44] = 'APBD'
    for column, value in enumerate(sample, start=1):
        cell = worksheet.cell(row=7, column=column, value=value)
        cell.fill = PatternFill('solid', fgColor='FFF2CC')
        cell.alignment = Alignment(vertical='top', wrap_text=True)

    thin_gray = Side(style='thin', color='D9E2F3')
    for row in worksheet.iter_rows(min_row=6, max_row=7, min_col=1, max_col=len(KIB_HEADERS)):
        for cell in row:
            cell.border = Border(bottom=thin_gray)

    for column in range(1, len(KIB_HEADERS) + 1):
        worksheet.column_dimensions[_column_name(column)].width = 18
    for column in (9, 10, 21, 27, 28, 37, 43, 44, 45):
        worksheet.column_dimensions[_column_name(column)].width = 28

    worksheet.row_dimensions[6].height = 38
    worksheet.row_dimensions[7].height = 42
    worksheet.freeze_panes = 'A7'
    worksheet.auto_filter.ref = f'A6:{last_column}7'

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def _column_name(number):
    result = ''
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result
