from datetime import datetime
from app import db


class PreventiveMaintenance(db.Model):
    __tablename__ = 'preventive_maintenance'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    checked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_date = db.Column(db.Date, nullable=False)
    room_name_snapshot = db.Column(db.String(100), nullable=True)
    result = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    condition_after = db.Column(db.String(50), nullable=True)
    ai_recommendation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    asset = db.relationship('Asset', back_populates='preventive_records')
    checker = db.relationship('User', foreign_keys=[checked_by], backref='preventive_checks')

    def __repr__(self):
        return f'<PreventiveMaintenance asset_id={self.asset_id} date={self.check_date}>'
