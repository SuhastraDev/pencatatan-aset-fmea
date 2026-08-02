from datetime import date

from app import db
from app.models.division import Division
from app.models.room import Room
from app.models.user import User


DEFAULT_PASSWORD = 'Admin@12345'

DIVISIONS = [
    {
        'name': 'Divisi Rawat Jalan',
        'description': 'Mengelola aset ruangan pelayanan rawat jalan, IGD, dan poli.',
    },
    {
        'name': 'Divisi Operasi & Tindakan',
        'description': 'Mengelola aset ruangan operasi, tindakan, ICU, dan bedah.',
    },
    {
        'name': 'Divisi Penunjang Medis',
        'description': 'Mengelola aset ruangan penunjang medis seperti radiologi.',
    },
]

ROOMS = [
    {
        'code': 'POLI-VIP',
        'name': 'POLI VIP',
        'division': 'Divisi Rawat Jalan',
        'floor': 'Lantai 1',
    },
    {
        'code': 'RAWAT-JALAN',
        'name': 'Rawat Jalan',
        'division': 'Divisi Rawat Jalan',
        'floor': 'Lantai 1',
    },
    {
        'code': 'POLI-UMUM',
        'name': 'Poli Umum',
        'division': 'Divisi Rawat Jalan',
        'floor': 'Lantai 1',
    },
    {
        'code': 'IGD',
        'name': 'IGD',
        'division': 'Divisi Rawat Jalan',
        'floor': 'Lantai 1',
    },
    {
        'code': 'BEDAH',
        'name': 'BEDAH',
        'division': 'Divisi Operasi & Tindakan',
        'floor': 'Lantai 2',
    },
    {
        'code': 'ICU',
        'name': 'ICU',
        'division': 'Divisi Operasi & Tindakan',
        'floor': 'Lantai 2',
    },
    {
        'code': 'RADIOLOGI',
        'name': 'Radiologi',
        'division': 'Divisi Penunjang Medis',
        'floor': 'Lantai 1',
    },
]

DIVISION_ADMINS = [
    {
        'name': 'Admin Divisi Rawat Jalan',
        'email': 'admin.divisi.rawatjalan@rskgm.id',
        'nip': '198501012010011001',
        'jabatan': 'Admin Divisi Rawat Jalan',
        'tanggal_lahir': date(1985, 1, 1),
        'division': 'Divisi Rawat Jalan',
    },
    {
        'name': 'Admin Divisi Operasi dan Tindakan',
        'email': 'admin.divisi.operasi@rskgm.id',
        'nip': '198602022011012001',
        'jabatan': 'Admin Divisi Operasi dan Tindakan',
        'tanggal_lahir': date(1986, 2, 2),
        'division': 'Divisi Operasi & Tindakan',
    },
    {
        'name': 'Admin Divisi Penunjang Medis',
        'email': 'admin.divisi.penunjang@rskgm.id',
        'nip': '198703032012012001',
        'jabatan': 'Admin Divisi Penunjang Medis',
        'tanggal_lahir': date(1987, 3, 3),
        'division': 'Divisi Penunjang Medis',
    },
]

ROOM_ADMINS = [
    {
        'name': 'Admin Ruangan POLI VIP',
        'email': 'admin.ruangan.polivip@rskgm.id',
        'nip': '199001012014032001',
        'jabatan': 'Admin Ruangan POLI VIP',
        'tanggal_lahir': date(1990, 1, 1),
        'room': 'POLI-VIP',
    },
    {
        'name': 'Admin Ruangan Rawat Jalan',
        'email': 'admin.ruangan.rawatjalan@rskgm.id',
        'nip': '199102022015032001',
        'jabatan': 'Admin Ruangan Rawat Jalan',
        'tanggal_lahir': date(1991, 2, 2),
        'room': 'RAWAT-JALAN',
    },
    {
        'name': 'Admin Ruangan Poli Umum',
        'email': 'admin.ruangan.poliumum@rskgm.id',
        'nip': '199203032016032001',
        'jabatan': 'Admin Ruangan Poli Umum',
        'tanggal_lahir': date(1992, 3, 3),
        'room': 'POLI-UMUM',
    },
    {
        'name': 'Admin Ruangan IGD',
        'email': 'admin.ruangan.igd@rskgm.id',
        'nip': '199304042017032001',
        'jabatan': 'Admin Ruangan IGD',
        'tanggal_lahir': date(1993, 4, 4),
        'room': 'IGD',
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
    {
        'name': 'Admin Ruangan Radiologi',
        'email': 'admin.ruangan.radiologi@rskgm.id',
        'nip': '199607072020032001',
        'jabatan': 'Admin Ruangan Radiologi',
        'tanggal_lahir': date(1996, 7, 7),
        'room': 'RADIOLOGI',
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
