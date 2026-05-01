from datetime import datetime
from app import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(
        db.Enum(
            'rpn_tinggi',
            'rpn_sedang',
            'approval_baru',
            'approval_disetujui',
            'approval_ditolak',
            'maintenance_terlambat'
        ),
        nullable=False
    )
    is_read = db.Column(db.Boolean, default=False)
    related_asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification user_id={self.user_id} type={self.type}>'
