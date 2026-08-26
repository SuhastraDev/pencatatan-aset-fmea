from datetime import datetime
from app import db


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    division_id = db.Column(db.Integer, db.ForeignKey('divisions.id'), nullable=True)
    room_code = db.Column(db.String(20), unique=True, nullable=False)
    room_name = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    division = db.relationship('Division', back_populates='rooms')
    users = db.relationship('User', back_populates='room', lazy='dynamic')
    assets = db.relationship('Asset', back_populates='room', lazy='dynamic')

    def __repr__(self):
        return f'<Room {self.room_code} - {self.room_name}>'
