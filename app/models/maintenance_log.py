from datetime import datetime
from app import db


class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    logged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(
        db.Enum(
            'evaluasi_fmea',
            'perbaikan',
            'penggantian',
            'pemeriksaan_rutin',
            'approval_disetujui',
            'approval_ditolak',
            'pengajuan_status',   # admin_ruangan ajukan perubahan status
            'cetak_kir',          # log cetak KIR — tidak mengubah kondisi aset
        ),
        nullable=False
    )
    description = db.Column(db.Text, nullable=False)
    action_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    asset = db.relationship('Asset', back_populates='maintenance_logs')

    def __repr__(self):
        return f'<MaintenanceLog asset_id={self.asset_id} type={self.action_type}>'
