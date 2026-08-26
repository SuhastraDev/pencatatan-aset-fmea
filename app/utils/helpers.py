from datetime import datetime, date
import os


def generate_asset_code(room_code, sequence):
    """Generate kode aset format AST-[ROOMCODE]-[YEAR]-[SEQUENCE]."""
    year = datetime.now().year
    seq = str(sequence).zfill(4)
    return f"AST-{room_code.upper()}-{year}-{seq}"


def format_date(d):
    """Format tanggal ke string Indonesia (contoh: 28 April 2026)."""
    if d is None:
        return '-'
    BULAN = [
        '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    if isinstance(d, (datetime, date)):
        return f"{d.day} {BULAN[d.month]} {d.year}"
    return str(d)


def time_ago(dt):
    """Konversi datetime ke format relatif Indonesia (contoh: 2 jam lalu)."""
    if dt is None:
        return '-'
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return 'Baru saja'
    elif seconds < 3600:
        menit = seconds // 60
        return f"{menit} menit lalu"
    elif seconds < 86400:
        jam = seconds // 3600
        return f"{jam} jam lalu"
    elif seconds < 2592000:
        hari = seconds // 86400
        return f"{hari} hari lalu"
    elif seconds < 31536000:
        bulan = seconds // 2592000
        return f"{bulan} bulan lalu"
    else:
        tahun = seconds // 31536000
        return f"{tahun} tahun lalu"


def generate_qr_code(asset_id, base_url):
    """Generate QR code PNG untuk aset. Hanya dibuat sekali, jika sudah ada pakai yang lama.

    Returns:
        str: Absolute path ke file PNG.
    """
    import qrcode

    # Resolve folder static/qrcodes relatif ke direktori app/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qr_dir = os.path.join(base_dir, 'static', 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    filename = f"qr_asset_{asset_id}.png"
    filepath = os.path.join(qr_dir, filename)

    # Idempotent — jangan generate ulang jika sudah ada
    if os.path.exists(filepath):
        return filepath

    url = f"{base_url.rstrip('/')}/ruangan/assets/{asset_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img.save(filepath)
    return filepath
