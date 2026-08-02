from app import db
from app.models.asset import Asset
from app.models.notification import Notification
from app.models.room import Room
from app.models.user import User


DEMO_ASSET_CODES = [
    'AST-RJ-01-2026-0001',
    'AST-RJ-02-2026-0001',
    'AST-OK-01-2026-0001',
]

DEMO_USER_EMAILS = [
    'admin.divisi.rj@rskgm.id',
    'admin.divisi.ok@rskgm.id',
    'admin.ruangan.rj01@rskgm.id',
    'admin.ruangan.rj02@rskgm.id',
    'admin.ruangan.ok01@rskgm.id',
]

DEMO_ROOM_CODES = [
    'RJ-01',
    'RJ-02',
    'OK-01',
]


def clear_demo_data():
    """Hapus data contoh lama tanpa menyentuh akun, ruangan, dan aset real."""
    deleted_assets = 0
    deleted_users = 0
    deleted_rooms = 0
    deleted_notifications = 0

    assets = Asset.query.filter(Asset.asset_code.in_(DEMO_ASSET_CODES)).all()
    asset_ids = [asset.id for asset in assets]
    if asset_ids:
        deleted_notifications = Notification.query.filter(
            Notification.related_asset_id.in_(asset_ids)
        ).delete(synchronize_session=False)

    for asset in assets:
        db.session.delete(asset)
        deleted_assets += 1

    db.session.flush()

    users = User.query.filter(User.email.in_(DEMO_USER_EMAILS)).all()
    user_ids = [user.id for user in users]
    if user_ids:
        deleted_notifications += Notification.query.filter(
            Notification.user_id.in_(user_ids)
        ).delete(synchronize_session=False)

    for user in users:
        db.session.delete(user)
        deleted_users += 1

    db.session.flush()

    rooms = Room.query.filter(Room.room_code.in_(DEMO_ROOM_CODES)).all()
    for room in rooms:
        if room.assets.count() == 0 and room.users.count() == 0:
            db.session.delete(room)
            deleted_rooms += 1

    db.session.commit()

    print('Data demo lama berhasil dibersihkan.')
    print(f'  Aset demo dihapus      : {deleted_assets}')
    print(f'  Notifikasi demo dihapus: {deleted_notifications}')
    print(f'  User demo dihapus      : {deleted_users}')
    print(f'  Ruangan demo dihapus   : {deleted_rooms}')
