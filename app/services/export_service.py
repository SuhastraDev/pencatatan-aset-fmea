"""
Export service — generate PDF dan Excel laporan aset.
Digunakan oleh Admin Ruangan dan Admin Divisi.
"""
import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


def generate_excel(asset_data, room_name, room_code):
    """
    Generate file Excel laporan aset.
    asset_data: list of dict {'asset': Asset, 'last_fmea': FmeaRecord|None}
    Return: BytesIO buffer siap di-send_file
    """
    wb = Workbook()
    ws = wb.active
    ws.title = 'Laporan Aset'

    # Header
    headers = [
        'No', 'Kode Aset', 'Nama Aset', 'Kategori', 'Merek', 'Model',
        'Kondisi', 'Status', 'RPN Terakhir', 'Kategori RPN', 'Tanggal Evaluasi'
    ]
    ws.append(headers)
    header_fill = PatternFill('solid', fgColor='1F4E79')
    header_font = Font(bold=True, color='FFFFFF')
    center = Alignment(horizontal='center')
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center

    for i, item in enumerate(asset_data, start=1):
        a = item['asset']
        f = item['last_fmea']
        ws.append([
            i,
            a.asset_code,
            a.asset_name,
            a.category.category_name,
            a.brand,
            a.model,
            a.condition.replace('_', ' ').title(),
            a.status.replace('_', ' ').title(),
            f.rpn_score if f else '-',
            f.risk_category.title() if f else '-',
            str(f.evaluation_date) if f else '-',
        ])

    # Auto column width
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def generate_excel_divisi(asset_data, room_stats):
    """
    Generate Excel 2-sheet laporan lintas ruangan.
    asset_data: list of dict {'asset': Asset, 'last_fmea': FmeaRecord|None}
    room_stats: list of dict dengan key room_name, total, baik, perlu, kritis, tidak_layak,
                rpn_rendah, rpn_sedang, rpn_tinggi
    Return: BytesIO buffer
    """
    wb = Workbook()

    # ── Sheet 1: Data Aset ──────────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = 'Data Aset'

    headers = ['No', 'Kode Aset', 'Nama Aset', 'Ruangan', 'Kategori', 'Merek', 'Model',
               'Kondisi', 'Status', 'RPN Terakhir', 'Kategori RPN', 'Tgl Evaluasi']
    ws1.append(headers)
    hdr_fill = PatternFill('solid', fgColor='1F4E79')
    hdr_font = Font(bold=True, color='FFFFFF')
    center = Alignment(horizontal='center')
    for cell in ws1[1]:
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = center

    fill_map = {
        'baik': PatternFill('solid', fgColor='D9EAD3'),
        'perlu_perhatian': PatternFill('solid', fgColor='FFF2CC'),
        'kritis': PatternFill('solid', fgColor='FCE5CD'),
        'tidak_layak': PatternFill('solid', fgColor='F4CCCC'),
    }

    for i, item in enumerate(asset_data, start=1):
        a = item['asset']
        f = item['last_fmea']
        ws1.append([
            i, a.asset_code, a.asset_name,
            a.room.room_name, a.category.category_name,
            a.brand, a.model,
            a.condition.replace('_', ' ').title(),
            a.status.replace('_', ' ').title(),
            f.rpn_score if f else '-',
            f.risk_category.title() if f else '-',
            str(f.evaluation_date) if f else '-',
        ])
        row_fill = fill_map.get(a.condition)
        if row_fill:
            for cell in ws1[i + 1]:
                cell.fill = row_fill

    for col in ws1.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws1.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    # ── Sheet 2: Statistik per Ruangan ──────────────────────────────────────
    ws2 = wb.create_sheet('Statistik per Ruangan')
    headers2 = ['Ruangan', 'Total Aset', 'Baik', 'Perlu Perhatian', 'Kritis',
                'Tidak Layak', 'RPN Rendah', 'RPN Sedang', 'RPN Tinggi']
    ws2.append(headers2)
    for cell in ws2[1]:
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = center

    for rs in room_stats:
        ws2.append([
            rs['room_name'], rs['total'],
            rs['baik'], rs['perlu'], rs['kritis'], rs['tidak_layak'],
            rs.get('rpn_rendah', 0), rs.get('rpn_sedang', 0), rs.get('rpn_tinggi', 0),
        ])

    for col in ws2.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws2.column_dimensions[col[0].column_letter].width = min(max_len + 4, 30)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def generate_pdf(template_string):
    """
    Generate PDF dari HTML string menggunakan xhtml2pdf.
    template_string: hasil render_template HTML
    Return: bytes PDF
    """
    from xhtml2pdf import pisa
    buf = io.BytesIO()
    pisa.CreatePDF(template_string, dest=buf, encoding='utf-8')
    buf.seek(0)
    return buf.read()


def build_filename(prefix, room_code, ext):
    """Helper untuk nama file ekspor."""
    tanggal = datetime.now().strftime('%Y%m%d')
    return f"{prefix}_{room_code}_{tanggal}.{ext}"


def generate_kir_pdf(asset, printed_by, base_url):
    """
    Generate PDF Kartu KIR untuk satu aset menggunakan xhtml2pdf.

    Args:
        asset:       instance model Asset
        printed_by:  string nama user yang mencetak
        base_url:    base URL aplikasi (tidak digunakan, QR embed sebagai base64)

    Returns:
        bytes: isi file PDF
    """
    import base64
    from datetime import date
    from flask import render_template
    from xhtml2pdf import pisa
    from app.utils.helpers import generate_qr_code, format_date

    # Generate (atau reuse) QR code
    qr_path = generate_qr_code(asset.id, base_url)

    # xhtml2pdf mendukung data URI base64 — tidak butuh file:// atau server running
    qr_uri = None
    if qr_path:
        try:
            with open(qr_path, 'rb') as f:
                qr_b64 = base64.b64encode(f.read()).decode('utf-8')
            qr_uri = f"data:image/png;base64,{qr_b64}"
        except Exception:
            qr_uri = None

    from app.models.fmea import FmeaRecord
    fmea_terakhir = (FmeaRecord.query
                     .filter_by(asset_id=asset.id)
                     .order_by(FmeaRecord.created_at.desc())
                     .first())

    html_string = render_template(
        'exports/kir_template.html',
        asset=asset,
        fmea_terakhir=fmea_terakhir,
        qr_path=qr_uri,
        printed_by=printed_by,
        printed_at=datetime.now(),
        today_date=date.today(),
        format_date=format_date,
    )

    buf = io.BytesIO()
    pisa.CreatePDF(html_string, dest=buf, encoding='utf-8')
    buf.seek(0)
    return buf.read()
