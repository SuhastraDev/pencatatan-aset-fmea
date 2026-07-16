from datetime import date, timedelta
from app import db
from app.models.asset import Asset
from app.models.asset_category import AssetCategory
from app.models.fmea import FmeaRecord
from app.models.room import Room
from app.models.user import User
from app.models.division import Division


def seed_super_admin():
    """Buat akun Super Admin awal jika belum ada."""
    if User.query.filter_by(email='superadmin@rskgm.id').first():
        print('Super Admin sudah ada, seeder dilewati.')
        return

    admin = User(
        name='Super Administrator',
        email='superadmin@rskgm.id',
        role='super_admin',
        is_active=True,
    )
    admin.set_password('Admin@12345')
    db.session.add(admin)
    db.session.commit()
    print('Super Admin berhasil dibuat.')
    print('  Email   : superadmin@rskgm.id')
    print('  Password: Admin@12345')


def seed_divisions():
    """Pastikan divisi awal tersedia."""
    divisions = {
        'Divisi Rawat Jalan': 'Divisi yang mengelola ruangan-ruangan pelayanan rawat jalan pasien.',
        'Divisi Operasi & Tindakan': 'Divisi yang mengelola ruangan operasi dan tindakan medis.',
    }

    created = []
    for name, description in divisions.items():
        division = Division.query.filter_by(division_name=name).first()
        if division:
            continue
        division = Division(
            division_name=name,
            description=description,
            is_active=True,
        )
        db.session.add(division)
        created.append(name)

    db.session.commit()
    if created:
        print('Divisi awal berhasil dibuat:')
        for name in created:
            print(f'  - {name}')
    else:
        print('Data divisi awal sudah lengkap.')


def seed_demo_accounts_and_assets():
    """Lengkapi data demo agar semua role punya akun dan data awal."""
    rawat_jalan = _get_division('Divisi Rawat Jalan')
    operasi = _get_division('Divisi Operasi & Tindakan')

    rooms = {
        'RJ-01': {
            'room_name': 'Poli Gigi Umum',
            'floor': 'Lantai 1',
            'division': rawat_jalan,
            'description': 'Ruangan pelayanan pemeriksaan gigi umum.',
        },
        'RJ-02': {
            'room_name': 'Poli Ortodonti',
            'floor': 'Lantai 1',
            'division': rawat_jalan,
            'description': 'Ruangan pelayanan ortodonti.',
        },
        'OK-01': {
            'room_name': 'Ruang Operasi Gigi',
            'floor': 'Lantai 2',
            'division': operasi,
            'description': 'Ruangan tindakan operasi gigi dan mulut.',
        },
    }

    room_map = {}
    for code, data in rooms.items():
        room_map[code] = _get_or_create_room(code, **data)

    accounts = [
        {
            'name': 'Admin Divisi Rawat Jalan',
            'email': 'admin.divisi.rj@rskgm.id',
            'role': 'admin_divisi',
            'division': rawat_jalan,
            'room': None,
        },
        {
            'name': 'Admin Divisi Operasi',
            'email': 'admin.divisi.ok@rskgm.id',
            'role': 'admin_divisi',
            'division': operasi,
            'room': None,
        },
        {
            'name': 'Admin Ruangan Poli Gigi Umum',
            'email': 'admin.ruangan.rj01@rskgm.id',
            'role': 'admin_ruangan',
            'division': rawat_jalan,
            'room': room_map['RJ-01'],
        },
        {
            'name': 'Admin Ruangan Poli Ortodonti',
            'email': 'admin.ruangan.rj02@rskgm.id',
            'role': 'admin_ruangan',
            'division': rawat_jalan,
            'room': room_map['RJ-02'],
        },
        {
            'name': 'Admin Ruangan Operasi Gigi',
            'email': 'admin.ruangan.ok01@rskgm.id',
            'role': 'admin_ruangan',
            'division': operasi,
            'room': room_map['OK-01'],
        },
    ]

    user_map = {}
    for account in accounts:
        user_map[account['email']] = _get_or_create_user(**account)

    categories = {category.category_name: category for category in AssetCategory.query.all()}
    super_admin = User.query.filter_by(email='superadmin@rskgm.id').first()
    fallback_creator = user_map['admin.ruangan.rj01@rskgm.id']

    asset_specs = [
        {
            'asset_code': 'AST-RJ-01-2026-0001',
            'asset_name': 'Dental Unit Demo RJ-01',
            'category': 'Alat Terapi',
            'room': room_map['RJ-01'],
            'brand': 'DemoDent',
            'model': 'DU-100',
            'serial_number': 'DEMO-RJ01-001',
            'purchase_price': 85000000,
            'condition': 'baik',
            'status': 'aktif',
            'created_by': user_map['admin.ruangan.rj01@rskgm.id'],
            'rpn': (3, 2, 4, 'rendah'),
        },
        {
            'asset_code': 'AST-RJ-02-2026-0001',
            'asset_name': 'Autoclave Demo RJ-02',
            'category': 'Alat Sterilisasi',
            'room': room_map['RJ-02'],
            'brand': 'SterilPro',
            'model': 'AC-24',
            'serial_number': 'DEMO-RJ02-001',
            'purchase_price': 42000000,
            'condition': 'perlu_perhatian',
            'status': 'aktif',
            'created_by': user_map['admin.ruangan.rj02@rskgm.id'],
            'rpn': (6, 4, 5, 'sedang'),
        },
        {
            'asset_code': 'AST-OK-01-2026-0001',
            'asset_name': 'Monitor Pasien Demo OK-01',
            'category': 'Alat Darurat',
            'room': room_map['OK-01'],
            'brand': 'MediView',
            'model': 'PM-900',
            'serial_number': 'DEMO-OK01-001',
            'purchase_price': 65000000,
            'condition': 'kritis',
            'status': 'aktif',
            'created_by': user_map['admin.ruangan.ok01@rskgm.id'],
            'rpn': (8, 6, 5, 'tinggi'),
        },
    ]

    for spec in asset_specs:
        category = categories.get(spec['category']) or next(iter(categories.values()), None)
        if not category:
            continue
        asset = _get_or_create_asset(spec, category, super_admin or fallback_creator)
        _get_or_create_fmea(asset, spec['created_by'], spec['rpn'])

    db.session.commit()
    print('Data demo akun dan aset berhasil dipastikan.')
    print('Password semua akun demo: Admin@12345')
    print('Akun demo:')
    print('  admin.divisi.rj@rskgm.id')
    print('  admin.divisi.ok@rskgm.id')
    print('  admin.ruangan.rj01@rskgm.id')
    print('  admin.ruangan.rj02@rskgm.id')
    print('  admin.ruangan.ok01@rskgm.id')


def _get_division(name):
    return Division.query.filter_by(division_name=name).first()


def _get_or_create_room(room_code, room_name, floor, division, description):
    room = Room.query.filter_by(room_code=room_code).first()
    if room:
        room.division = division
        room.room_name = room_name
        room.floor = floor
        room.description = description
        room.is_active = True
        return room

    room = Room(
        room_code=room_code,
        room_name=room_name,
        floor=floor,
        division=division,
        description=description,
        is_active=True,
    )
    db.session.add(room)
    return room


def _get_or_create_user(name, email, role, division, room):
    user = User.query.filter_by(email=email).first()
    if user:
        user.name = name
        user.role = role
        user.division = division
        user.room = room
        user.is_active = True
        return user

    user = User(
        name=name,
        email=email,
        role=role,
        division=division,
        room=room,
        is_active=True,
    )
    user.set_password('Admin@12345')
    db.session.add(user)
    return user


def _get_or_create_asset(spec, category, fallback_creator):
    asset = Asset.query.filter_by(asset_code=spec['asset_code']).first()
    if asset:
        asset.asset_name = spec['asset_name']
        asset.category = category
        asset.room = spec['room']
        asset.brand = spec['brand']
        asset.model = spec['model']
        asset.serial_number = spec['serial_number']
        asset.purchase_price = spec['purchase_price']
        asset.condition = spec['condition']
        asset.status = spec['status']
        return asset

    asset = Asset(
        asset_code=spec['asset_code'],
        asset_name=spec['asset_name'],
        category=category,
        room=spec['room'],
        brand=spec['brand'],
        model=spec['model'],
        serial_number=spec['serial_number'],
        purchase_date=date.today() - timedelta(days=180),
        purchase_price=spec['purchase_price'],
        condition=spec['condition'],
        status=spec['status'],
        next_maintenance_date=date.today() + timedelta(days=60),
        notes='Data demo untuk validasi tampilan awal sistem.',
        creator=spec.get('created_by') or fallback_creator,
    )
    db.session.add(asset)
    return asset


def _get_or_create_fmea(asset, evaluator, rpn_tuple):
    existing = FmeaRecord.query.filter_by(asset=asset, failure_mode='Evaluasi demo awal').first()
    severity, occurrence, detection, risk_category = rpn_tuple
    rpn_score = severity * occurrence * detection

    if existing:
        existing.evaluator = evaluator
        existing.severity = severity
        existing.occurrence = occurrence
        existing.detection = detection
        existing.rpn_score = rpn_score
        existing.risk_category = risk_category
        return existing

    fmea = FmeaRecord(
        asset=asset,
        evaluator=evaluator,
        failure_mode='Evaluasi demo awal',
        failure_effect='Data contoh untuk melihat hasil perhitungan risiko pada dashboard.',
        severity=severity,
        occurrence=occurrence,
        detection=detection,
        rpn_score=rpn_score,
        risk_category=risk_category,
        recommendation='Gunakan data ini hanya sebagai contoh, lalu ganti dengan evaluasi aktual.',
        evaluation_date=date.today(),
        notes='Seeder demo.',
    )
    db.session.add(fmea)
    return fmea
