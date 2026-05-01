from datetime import datetime
from app import db


class FmeaRecord(db.Model):
    __tablename__ = 'fmea_records'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    evaluated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    failure_mode = db.Column(db.String(255), nullable=False)
    failure_effect = db.Column(db.Text, nullable=False)
    severity = db.Column(db.Integer, nullable=False)       # 1-10
    occurrence = db.Column(db.Integer, nullable=False)     # 1-10
    detection = db.Column(db.Integer, nullable=False)      # 1-10
    rpn_score = db.Column(db.Integer, nullable=False)      # otomatis = S × O × D
    risk_category = db.Column(db.Enum('rendah', 'sedang', 'tinggi'), nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    evaluation_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    asset = db.relationship('Asset', back_populates='fmea_records')

    def __repr__(self):
        return f'<FmeaRecord asset_id={self.asset_id} rpn={self.rpn_score}>'
