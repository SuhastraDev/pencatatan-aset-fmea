from datetime import datetime
from app import db


class Division(db.Model):
    __tablename__ = 'divisions'

    id = db.Column(db.Integer, primary_key=True)
    division_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    rooms = db.relationship('Room', back_populates='division', lazy='dynamic')
    users = db.relationship('User', back_populates='division', lazy='dynamic')

    def __repr__(self):
        return f'<Division {self.division_name}>'
