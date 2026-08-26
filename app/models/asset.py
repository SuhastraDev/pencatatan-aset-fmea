from datetime import datetime
from app import db


class Asset(db.Model):
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    asset_code = db.Column(db.String(50), unique=True, nullable=False)
    item_code = db.Column(db.String(100), nullable=True)
    asset_name = db.Column(db.String(150), nullable=False)
    specification = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('asset_categories.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit = db.Column(db.String(50), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Numeric(15, 2), nullable=True)
    acquisition_document_number = db.Column(db.String(150), nullable=True)
    funding_source = db.Column(db.String(100), nullable=True)
    condition = db.Column(
        db.Enum(
            'baik',
            'perlu_perhatian',
            'kritis',
            'tidak_layak',
            name='asset_condition',
            native_enum=False,
            length=50,
        ),
        default='baik',
        nullable=False
    )
    status = db.Column(
        db.Enum(
            'aktif',
            'dalam_perbaikan',
            'tidak_aktif',
            'menunggu_approval',
            name='asset_status',
            native_enum=False,
            length=50,
        ),
        default='aktif',
        nullable=False
    )
    last_maintenance_date = db.Column(db.Date, nullable=True)
    next_maintenance_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    room = db.relationship('Room', back_populates='assets')
    category = db.relationship('AssetCategory', back_populates='assets')
    creator = db.relationship('User', foreign_keys=[created_by])
    fmea_records = db.relationship('FmeaRecord', back_populates='asset', lazy='dynamic', cascade='all, delete-orphan')
    maintenance_logs = db.relationship('MaintenanceLog', back_populates='asset', lazy='dynamic', cascade='all, delete-orphan')
    preventive_records = db.relationship('PreventiveMaintenance', back_populates='asset', lazy='dynamic', cascade='all, delete-orphan')
    approval_requests = db.relationship('ApprovalRequest', back_populates='asset', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', foreign_keys='Notification.related_asset_id', backref='related_asset', lazy='dynamic')

    def __repr__(self):
        return f'<Asset {self.asset_code} - {self.asset_name}>'

    @property
    def brand_model(self):
        if self.model:
            return f'{self.brand} / {self.model}'
        return self.brand

    @brand_model.setter
    def brand_model(self, value):
        self.brand = (value or '').strip()
        self.model = ''
