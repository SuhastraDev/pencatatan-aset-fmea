from datetime import datetime
from app import db


class ApprovalRequest(db.Model):
    __tablename__ = 'approval_requests'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    current_status = db.Column(db.String(50), nullable=False)
    requested_status = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    approval_status = db.Column(
        db.Enum('pending', 'approved', 'rejected'),
        default='pending',
        nullable=False
    )
    reviewer_notes = db.Column(db.Text, nullable=True)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # Relasi
    asset = db.relationship('Asset', back_populates='approval_requests')

    def __repr__(self):
        return f'<ApprovalRequest asset_id={self.asset_id} status={self.approval_status}>'
