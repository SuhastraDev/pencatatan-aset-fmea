from datetime import date, timedelta

from app.models.fmea import FmeaRecord
from app.models.maintenance_log import MaintenanceLog
from app.models.preventive_maintenance import PreventiveMaintenance


SEVERITY_RANK = {
    'baik': 0,
    'perlu_perhatian': 1,
    'kritis': 2,
    'tidak_layak': 3,
}

# Aset yang baru diimpor belum tentu sudah memiliki evaluasi FMEA.
# Nilai ini hanya fallback untuk rekap laporan; tidak membuat FmeaRecord palsu.
DEFAULT_REPORT_RISK_CATEGORY = 'rendah'
VALID_RISK_CATEGORIES = {'rendah', 'sedang', 'tinggi'}


def _is_valid_report_fmea(fmea):
    """Check whether an FMEA record is safe to show as a report result."""
    rpn_score = getattr(fmea, 'rpn_score', None)
    risk_category = getattr(fmea, 'risk_category', None)
    return bool(
        fmea
        and str(rpn_score).strip()
        and risk_category in VALID_RISK_CATEGORIES
    )


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


def latest_asset_records(asset):
    """Return the latest records used by the report and maintenance schedule."""
    return {
        'last_fmea': asset.fmea_records.order_by(
            FmeaRecord.evaluation_date.desc(), FmeaRecord.created_at.desc()
        ).first(),
        'last_maintenance': asset.maintenance_logs.filter(
            MaintenanceLog.action_type.in_([
                'perbaikan', 'penggantian', 'pemeriksaan_rutin', 'preventive_check'
            ])
        ).order_by(
            MaintenanceLog.action_date.desc(), MaintenanceLog.created_at.desc()
        ).first(),
        'last_preventive': asset.preventive_records.order_by(
            PreventiveMaintenance.check_date.desc(), PreventiveMaintenance.created_at.desc()
        ).first(),
    }


def build_asset_report_context(asset):
    """Build the values shown in Rekap Laporan for one asset."""
    records = latest_asset_records(asset)
    maintenance = records['last_maintenance']
    preventive = records['last_preventive']
    fmea = records['last_fmea']
    report_fmea = fmea if _is_valid_report_fmea(fmea) else None

    action_parts = []
    if maintenance:
        action_parts.extend([maintenance.result, maintenance.recommendation, maintenance.description])
    elif preventive:
        action_parts.extend([preventive.result, preventive.notes, preventive.recommendation])
    action_note = ' | '.join(dict.fromkeys(str(part).strip() for part in action_parts if part))

    ai_recommendation = None
    for record in (maintenance, preventive):
        if record and record.ai_recommendation:
            ai_recommendation = record.ai_recommendation
            break
    if not ai_recommendation and report_fmea and report_fmea.recommendation:
        ai_recommendation = report_fmea.recommendation

    return {
        **records,
        # Report views/exports use this value so missing RPN is handled
        # consistently without creating a fake FmeaRecord.
        'report_fmea': report_fmea,
        'action_note': action_note,
        'ai_recommendation': ai_recommendation,
        # Dipakai oleh rekap/filter/export. Jika FMEA asli tersedia, selalu gunakan nilai asli.
        'report_risk_category': report_fmea.risk_category if report_fmea else DEFAULT_REPORT_RISK_CATEGORY,
        'report_rpn_score': report_fmea.rpn_score if report_fmea else None,
        'report_evaluation_date': report_fmea.evaluation_date if report_fmea else None,
        'report_risk_is_default': report_fmea is None,
    }


def calculate_next_maintenance_date(asset, reference_date=None):
    """Calculate the next schedule from RPN and the latest asset history."""
    records = latest_asset_records(asset)
    fmea = records['last_fmea']
    maintenance = records['last_maintenance']
    preventive = records['last_preventive']

    interval_days = {
        'tinggi': 7,
        'sedang': 14,
        'rendah': 30,
    }.get(fmea.risk_category if fmea else None, 30)

    history_condition = None
    if maintenance:
        history_condition = maintenance.condition_after or infer_condition_from_text(
            maintenance.complaint,
            maintenance.result,
            maintenance.recommendation,
            maintenance.description,
        )
    if not history_condition and preventive:
        history_condition = preventive.condition_after or infer_condition_from_text(
            preventive.result,
            preventive.notes,
            preventive.recommendation,
        )

    if history_condition in ('kritis', 'tidak_layak'):
        interval_days = min(interval_days, 7)
    elif history_condition == 'perlu_perhatian':
        interval_days = min(interval_days, 14)
    elif asset.condition in ('kritis', 'tidak_layak'):
        interval_days = min(interval_days, 7)
    elif asset.condition == 'perlu_perhatian':
        interval_days = min(interval_days, 14)

    latest_dates = [date.today()]
    if reference_date:
        latest_dates.append(reference_date)
    for record, field in (
        (fmea, 'evaluation_date'),
        (maintenance, 'action_date'),
        (preventive, 'check_date'),
    ):
        value = getattr(record, field, None) if record else None
        if value:
            latest_dates.append(value)
    base_date = max(latest_dates) if latest_dates else date.today()
    return base_date + timedelta(days=interval_days)
