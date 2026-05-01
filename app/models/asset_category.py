from datetime import datetime
from app import db


class AssetCategory(db.Model):
    __tablename__ = 'asset_categories'

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    assets = db.relationship('Asset', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<AssetCategory {self.category_name}>'


# Data seeder 5 kategori awal
KATEGORI_AWAL = [
    {'category_name': 'Alat Diagnostik', 'description': 'Peralatan untuk pemeriksaan dan diagnosis'},
    {'category_name': 'Alat Terapi', 'description': 'Peralatan untuk tindakan dan perawatan'},
    {'category_name': 'Alat Sterilisasi', 'description': 'Peralatan untuk sterilisasi instrumen'},
    {'category_name': 'Alat Penunjang', 'description': 'Peralatan penunjang operasional ruangan'},
    {'category_name': 'Alat Darurat', 'description': 'Peralatan untuk kondisi darurat dan emergensi'},
]


def seed_kategori(db_session):
    """Isi tabel asset_categories dengan data awal jika masih kosong."""
    if AssetCategory.query.count() == 0:
        for data in KATEGORI_AWAL:
            kategori = AssetCategory(**data)
            db_session.add(kategori)
        db_session.commit()
