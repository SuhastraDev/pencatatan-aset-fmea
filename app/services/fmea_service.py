from flask import current_app


def calculate_rpn(severity, occurrence, detection):
    """Hitung RPN dan kategori risiko dari nilai S, O, D."""
    rpn_score = severity * occurrence * detection
    risk_category = get_risk_category(rpn_score)

    warna = {
        'rendah': '#28a745',
        'sedang': '#ffc107',
        'tinggi': '#dc3545',
    }
    label = {
        'rendah': 'Rendah',
        'sedang': 'Sedang',
        'tinggi': 'Tinggi',
    }

    return {
        'rpn_score': rpn_score,
        'risk_category': risk_category,
        'color_code': warna[risk_category],
        'label': label[risk_category],
    }


def get_risk_category(rpn_score):
    """Tentukan kategori risiko berdasarkan nilai RPN."""
    threshold_tinggi = 200
    threshold_sedang = 80

    try:
        threshold_tinggi = current_app.config.get('RPN_HIGH_THRESHOLD', 200)
        threshold_sedang = current_app.config.get('RPN_MEDIUM_THRESHOLD', 80)
    except RuntimeError:
        pass

    if rpn_score >= threshold_tinggi:
        return 'tinggi'
    elif rpn_score >= threshold_sedang:
        return 'sedang'
    else:
        return 'rendah'


def generate_recommendation(rpn_score):
    """Generate rekomendasi tindakan berdasarkan nilai RPN."""
    kategori = get_risk_category(rpn_score)

    if kategori == 'tinggi':
        return (
            'Tindakan segera diperlukan. Hentikan penggunaan alat jika berisiko '
            'terhadap keselamatan pasien. Lakukan perbaikan atau penggantian dalam '
            '1×24 jam dan catat laporan insiden.'
        )
    elif kategori == 'sedang':
        return (
            'Jadwalkan pemeriksaan dan perawatan dalam waktu dekat (maksimal 7 hari). '
            'Pantau kondisi alat secara berkala dan laporkan ke Admin Divisi.'
        )
    else:
        return (
            'Lanjutkan pemeliharaan rutin sesuai jadwal. '
            'Dokumentasikan hasil evaluasi untuk keperluan audit.'
        )


def should_notify(rpn_score):
    """Kembalikan True jika RPN ≥ threshold tinggi (default 200)."""
    threshold = 200
    try:
        threshold = current_app.config.get('RPN_HIGH_THRESHOLD', 200)
    except RuntimeError:
        pass
    return rpn_score >= threshold


def update_asset_condition(asset, rpn_score):
    """
    Perbarui kondisi aset berdasarkan nilai RPN terbaru.
    Kondisi 'tidak_layak' tidak pernah di-downgrade otomatis oleh FMEA —
    hanya bisa diubah secara manual oleh admin melalui form repair.
    """
    # Kondisi yang hanya bisa diubah secara manual (via repair log), bukan oleh FMEA
    if asset.condition in ('tidak_layak',):
        return asset

    kategori = get_risk_category(rpn_score)

    # Urutan keparahan: tidak_layak > kritis > perlu_perhatian > baik
    # FMEA hanya boleh MEMPERBURUK kondisi, tidak boleh otomatis memperbaikinya
    severity_rank = {'baik': 0, 'perlu_perhatian': 1, 'kritis': 2, 'tidak_layak': 3}
    kondisi_baru_map = {'tinggi': 'kritis', 'sedang': 'perlu_perhatian', 'rendah': 'baik'}
    kondisi_baru = kondisi_baru_map[kategori]

    # Hanya update jika kondisi baru LEBIH PARAH dari kondisi saat ini
    if severity_rank.get(kondisi_baru, 0) > severity_rank.get(asset.condition, 0):
        asset.condition = kondisi_baru

    return asset
