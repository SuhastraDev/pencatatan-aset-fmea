from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('super_admin', 'admin_divisi', 'admin_ruangan'), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey('divisions.id'), nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    division = db.relationship('Division', back_populates='users')
    room = db.relationship('Room', back_populates='users')
    fmea_records = db.relationship('FmeaRecord', foreign_keys='FmeaRecord.evaluated_by', backref='evaluator', lazy='dynamic')
    maintenance_logs = db.relationship('MaintenanceLog', foreign_keys='MaintenanceLog.logged_by', backref='logger', lazy='dynamic')
    approval_requests = db.relationship('ApprovalRequest', foreign_keys='ApprovalRequest.requested_by', backref='requester', lazy='dynamic')
    approval_reviews = db.relationship('ApprovalRequest', foreign_keys='ApprovalRequest.reviewed_by', backref='reviewer', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_super_admin(self):
        return self.role == 'super_admin'

    def is_admin_divisi(self):
        return self.role == 'admin_divisi'

    def is_admin_ruangan(self):
        return self.role == 'admin_ruangan'

    def get_division(self):
        """Return Division object yang membawahi user ini."""
        if self.role == 'admin_divisi':
            return self.division
        elif self.role == 'admin_ruangan' and self.room:
            return self.room.division
        return None

    def __repr__(self):
        return f'<User {self.email}>'
