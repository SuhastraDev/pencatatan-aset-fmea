from app import db, bcrypt
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
    """Buat 2 divisi awal jika belum ada."""
    if Division.query.count() > 0:
        print('Data divisi sudah ada, seeder dilewati.')
        return

    divisions = [
        Division(
            division_name='Divisi Rawat Jalan',
            description='Divisi yang mengelola ruangan-ruangan pelayanan rawat jalan pasien.',
            is_active=True,
        ),
        Division(
            division_name='Divisi Operasi & Tindakan',
            description='Divisi yang mengelola ruangan operasi dan tindakan medis.',
            is_active=True,
        ),
    ]
    db.session.add_all(divisions)
    db.session.commit()
    print('2 divisi awal berhasil dibuat:')
    for d in divisions:
        print(f'  - {d.division_name}')
