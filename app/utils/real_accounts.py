from datetime import date

from app import db
from app.models.division import Division
from app.models.room import Room
from app.models.user import User


DEFAULT_PASSWORD = 'Admin@12345'

DIVISIONS = [
    {
        'name': 'Tata Usaha',
        'description': 'Master divisi tata usaha untuk pengembangan berikutnya.',
    },
    {
        'name': 'Pelayanan Medik dan Keperawatan',
        'description': 'Mengelola seluruh aset dan ruangan pelayanan medik dan keperawatan.',
    },
    {
        'name': 'Penunjang Medik',
        'description': 'Master divisi penunjang medik untuk pengembangan berikutnya.',
    },
]

ROOMS = [
    {
        'code': 'VIP',
        'name': 'VIP',
        'division': 'Pelayanan Medik dan Keperawatan',
        'floor': 'Lantai 1',
    },
    {
        'code': 'BEDAH',
        'name': 'BEDAH',
        'division': 'Pelayanan Medik dan Keperawatan',
        'floor': 'Lantai 2',
    },
    {
        'code': 'ICU',
        'name': 'ICU',
        'division': 'Pelayanan Medik dan Keperawatan',
        'floor': 'Lantai 2',
    },
]

DIVISION_ADMINS = [
    {
        'name': 'Admin Divisi Pelayanan Medik dan Keperawatan',
        'email': 'admin.divisi.rawatjalan@rskgm.id',
        'nip': '198501012010011001',
        'jabatan': 'Admin Divisi Pelayanan Medik dan Keperawatan',
        'tanggal_lahir': date(1985, 1, 1),
        'division': 'Pelayanan Medik dan Keperawatan',
    },
    {
        'name': 'Admin Divisi Tata Usaha',
        'email': 'admin.divisi.operasi@rskgm.id',
        'nip': '198602022011012001',
        'jabatan': 'Admin Divisi Tata Usaha',
        'tanggal_lahir': date(1986, 2, 2),
        'division': 'Tata Usaha',
    },
    {
        'name': 'Admin Divisi Penunjang Medik',
        'email': 'admin.divisi.penunjang@rskgm.id',
        'nip': '198703032012012001',
        'jabatan': 'Admin Divisi Penunjang Medik',
        'tanggal_lahir': date(1987, 3, 3),
        'division': 'Penunjang Medik',
    },
]

ROOM_ADMINS = [
    {
        'name': 'Admin Ruangan VIP',
        'email': 'admin.ruangan.polivip@rskgm.id',
        'nip': '199001012014032001',
        'jabatan': 'Admin Ruangan VIP',
        'tanggal_lahir': date(1990, 1, 1),
        'room': 'VIP',
    },
    {
        'name': 'Admin Ruangan BEDAH',
        'email': 'admin.ruangan.bedah@rskgm.id',
        'nip': '199405052018032001',
        'jabatan': 'Admin Ruangan BEDAH',
        'tanggal_lahir': date(1994, 5, 5),
        'room': 'BEDAH',
    },
    {
        'name': 'Admin Ruangan ICU',
        'email': 'admin.ruangan.icu@rskgm.id',
        'nip': '199506062019032001',
        'jabatan': 'Admin Ruangan ICU',
        'tanggal_lahir': date(1995, 6, 6),
        'room': 'ICU',
    },
]


def seed_real_accounts():
    """Pastikan akun dan master ruangan real dari file Excel tersedia."""
    division_map = {}
    created_divisions = 0
    created_rooms = 0
    created_users = 0
    updated_users = 0

    for item in DIVISIONS:
        division = Division.query.filter_by(division_name=item['name']).first()
        if not division:
            division = Division(
                division_name=item['name'],
                description=item['description'],
                is_active=True,
            )
            db.session.add(division)
            created_divisions += 1
        else:
            division.description = division.description or item['description']
            division.is_active = True
        division_map[item['name']] = division

    db.session.flush()

    room_map = {}
    for item in ROOMS:
        room = Room.query.filter_by(room_code=item['code']).first()
        if not room:
            room = Room(
                room_code=item['code'],
                room_name=item['name'],
                floor=item['floor'],
                description=f"Ruangan dari mapping data Excel klien: {item['name']}.",
                is_active=True,
            )
            db.session.add(room)
            created_rooms += 1
        room.room_name = item['name']
        room.floor = item['floor']
        room.division = division_map[item['division']]
        room.is_active = True
        room_map[item['code']] = room

    db.session.flush()

    for item in DIVISION_ADMINS:
        result = _upsert_user(
            name=item['name'],
            email=item['email'],
            role='admin_divisi',
            nip=item['nip'],
            jabatan=item['jabatan'],
            tanggal_lahir=item['tanggal_lahir'],
            division=division_map[item['division']],
            room=None,
        )
        created_users += result == 'created'
        updated_users += result == 'updated'

    for item in ROOM_ADMINS:
        room = room_map[item['room']]
        result = _upsert_user(
            name=item['name'],
            email=item['email'],
            role='admin_ruangan',
            nip=item['nip'],
            jabatan=item['jabatan'],
            tanggal_lahir=item['tanggal_lahir'],
            division=room.division,
            room=room,
        )
        created_users += result == 'created'
        updated_users += result == 'updated'

    db.session.commit()

    print('Akun real berhasil dipastikan.')
    print(f'  Divisi dibuat : {created_divisions}')
    print(f'  Ruangan dibuat: {created_rooms}')
    print(f'  User dibuat   : {created_users}')
    print(f'  User diperbarui: {updated_users}')
    print(f'  Password awal : {DEFAULT_PASSWORD}')


def _upsert_user(name, email, role, nip, jabatan, tanggal_lahir, division, room):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        user.set_password(DEFAULT_PASSWORD)
        db.session.add(user)
        status = 'created'
    else:
        status = 'updated'

    user.name = name
    user.role = role
    user.nip = nip
    user.jabatan = jabatan
    user.tanggal_lahir = tanggal_lahir
    user.division = division
    user.room = room
    user.is_active = True
    return status
