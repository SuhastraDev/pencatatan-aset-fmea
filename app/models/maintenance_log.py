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
            'preventive_check',
            name='maintenance_action_type',
            native_enum=False,
            length=50,
        ),
        nullable=False
    )
    description = db.Column(db.Text, nullable=False)
    reporter_unit = db.Column(db.String(100), nullable=True)
    reporter_name = db.Column(db.String(100), nullable=True)
    reporter_position = db.Column(db.String(100), nullable=True)
    complaint = db.Column(db.Text, nullable=True)
    inspection_unit = db.Column(db.String(100), nullable=True)
    technician_name = db.Column(db.String(100), nullable=True)
    technician_position = db.Column(db.String(100), nullable=True)
    result = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    condition_after = db.Column(db.String(50), nullable=True)
    ai_recommendation = db.Column(db.Text, nullable=True)
    action_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    asset = db.relationship('Asset', back_populates='maintenance_logs')

    def __repr__(self):
        return f'<MaintenanceLog asset_id={self.asset_id} type={self.action_type}>'
