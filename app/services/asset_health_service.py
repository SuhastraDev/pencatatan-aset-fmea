from app.models.fmea import FmeaRecord
from app.models.maintenance_log import MaintenanceLog
from app.models.preventive_maintenance import PreventiveMaintenance


SEVERITY_RANK = {
    'baik': 0,
    'perlu_perhatian': 1,
    'kritis': 2,
    'tidak_layak': 3,
}


def infer_condition_from_text(*parts):
    text = ' '.join(str(p or '').lower() for p in parts)
    if not text.strip():
        return None

    tidak_layak_terms = [
        'tidak boleh digunakan',
        'tidak dapat digunakan',
        'tidak dianjurkan',
        'tidak di sarankan',
        'tidak disarankan',
        'mati total',
        'tidak layak',
    ]
    kritis_terms = [
        'trouble',
        'troble',
        'bermasalah',
        'bocor',
        'rusak',
        'tidak menyala',
        'tidak berfungsi',
    ]
    perlu_terms = [
        'lemah',
        'perlu',
        'catatan',
        'evaluasi berkala',
        'sementara',
        'saran',
    ]
    baik_terms = [
        'baik',
        'sudah dapat digunakan',
        'dapat digunakan',
        'normal',
    ]

    if any(term in text for term in tidak_layak_terms):
        return 'tidak_layak'
    if any(term in text for term in kritis_terms):
        return 'kritis'
    if any(term in text for term in perlu_terms):
        return 'perlu_perhatian'
    if any(term in text for term in baik_terms):
        return 'baik'
    return None


def _worse_condition(a, b):
    if not a:
        return b
    if not b:
        return a
    return a if SEVERITY_RANK.get(a, 0) >= SEVERITY_RANK.get(b, 0) else b


def recalculate_asset_condition_from_history(asset):
    conditions = []

    latest_fmea = (
        FmeaRecord.query
        .filter_by(asset_id=asset.id)
        .order_by(FmeaRecord.evaluation_date.desc(), FmeaRecord.created_at.desc())
        .first()
    )
    if latest_fmea:
        conditions.append({
            'tinggi': 'kritis',
            'sedang': 'perlu_perhatian',
            'rendah': 'baik',
        }.get(latest_fmea.risk_category, 'baik'))

    latest_maintenance = (
        MaintenanceLog.query
        .filter_by(asset_id=asset.id)
        .order_by(MaintenanceLog.action_date.desc(), MaintenanceLog.created_at.desc())
        .first()
    )
    if latest_maintenance:
        conditions.append(latest_maintenance.condition_after)
        conditions.append(infer_condition_from_text(
            latest_maintenance.complaint,
            latest_maintenance.result,
            latest_maintenance.recommendation,
            latest_maintenance.description,
        ))

    latest_preventive = (
        PreventiveMaintenance.query
        .filter_by(asset_id=asset.id)
        .order_by(PreventiveMaintenance.check_date.desc(), PreventiveMaintenance.created_at.desc())
        .first()
    )
    if latest_preventive:
        conditions.append(latest_preventive.condition_after)
        conditions.append(infer_condition_from_text(
            latest_preventive.result,
            latest_preventive.notes,
            latest_preventive.recommendation,
        ))

    final_condition = 'baik'
    for condition in conditions:
        final_condition = _worse_condition(final_condition, condition)

    asset.condition = final_condition
    return asset


def generate_ai_recommendation(asset, fmea=None, maintenance_log=None, preventive=None):
    condition = asset.condition.replace('_', ' ').title()
    context = []
    if fmea:
        context.append(f'RPN terakhir {fmea.rpn_score} ({fmea.risk_category})')
    if maintenance_log and maintenance_log.complaint:
        context.append(f'keluhan: {maintenance_log.complaint[:120]}')
    if preventive:
        context.append(f'preventive: {preventive.result[:120]}')

    if asset.condition in ('tidak_layak', 'kritis'):
        action = 'prioritaskan pemeriksaan teknis, batasi penggunaan alat, dan buat tindak lanjut perbaikan/penggantian.'
    elif asset.condition == 'perlu_perhatian':
        action = 'jadwalkan monitoring ulang dan preventive lebih dekat dari jadwal rutin.'
    else:
        action = 'lanjutkan preventive sesuai jadwal dan dokumentasikan hasil pemeriksaan.'

    detail = '; '.join(context) if context else 'belum ada riwayat risiko khusus.'
    return f'AI rekomendasi awal: kondisi {condition}; {detail}; {action}'
