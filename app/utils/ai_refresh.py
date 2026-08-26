from app import db
from app.models.asset import Asset
from app.models.maintenance_log import MaintenanceLog
from app.models.preventive_maintenance import PreventiveMaintenance
from app.services.asset_health_service import (
    generate_ai_recommendation,
    recalculate_asset_condition_from_history,
)


def refresh_ai_recommendations():
    """Hitung ulang kondisi aset lalu sinkronkan rekomendasi yang tersimpan."""
    assets_updated = 0
    maintenance_updated = 0
    preventive_updated = 0

    assets = Asset.query.order_by(Asset.id).all()
    for asset in assets:
        previous_condition = asset.condition
        recalculate_asset_condition_from_history(asset)
        if asset.condition != previous_condition:
            assets_updated += 1

        maintenance_logs = (
            MaintenanceLog.query
            .filter_by(asset_id=asset.id)
            .order_by(MaintenanceLog.action_date.asc(), MaintenanceLog.created_at.asc())
            .all()
        )
        for log in maintenance_logs:
            if log.action_type == 'preventive_check':
                continue
            log.ai_recommendation = generate_ai_recommendation(asset, maintenance_log=log)
            maintenance_updated += 1

        preventive_records = (
            PreventiveMaintenance.query
            .filter_by(asset_id=asset.id)
            .order_by(PreventiveMaintenance.check_date.asc(), PreventiveMaintenance.created_at.asc())
            .all()
        )
        for preventive in preventive_records:
            preventive.ai_recommendation = generate_ai_recommendation(asset, preventive=preventive)
            preventive_updated += 1
            for log in maintenance_logs:
                if (
                    log.action_type == 'preventive_check'
                    and log.action_date == preventive.check_date
                    and log.result == preventive.result
                ):
                    log.ai_recommendation = preventive.ai_recommendation
                    break

    db.session.commit()
    print('Rekomendasi berhasil disinkronkan.')
    print(f'  Kondisi aset berubah       : {assets_updated}')
    print(f'  Maintenance AI diperbarui : {maintenance_updated}')
    print(f'  Preventive AI diperbarui  : {preventive_updated}')
