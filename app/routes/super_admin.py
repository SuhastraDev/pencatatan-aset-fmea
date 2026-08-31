from datetime import date
import json

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.division import Division
from app.models.user import User
from app.models.room import Room
from app.models.asset import Asset
from app.models.fmea import FmeaRecord
from app.models.maintenance_log import MaintenanceLog
from app.models.preventive_maintenance import PreventiveMaintenance
from app.utils.decorators import role_required
from app.forms.division_forms import CreateDivisionForm, EditDivisionForm
from app.forms.user_forms import CreateUserForm, EditUserForm
from app.forms.room_forms import CreateRoomForm, EditRoomForm

super_admin_bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')


def _division_choices():
    divs = Division.query.filter_by(is_active=True).order_by(Division.division_name).all()
    return [(0, '— Pilih Divisi —')] + [(d.id, d.division_name) for d in divs]


def _room_choices():
    rooms = Room.query.filter_by(is_active=True).order_by(Room.room_name).all()
    return [(0, '— Pilih Ruangan —')] + [(r.id, f"{r.room_code} — {r.room_name}") for r in rooms]


# ── Dashboard ─────────────────────────────────────────────────────────────────

@super_admin_bp.route('/dashboard')
@login_required
@role_required('super_admin')
def dashboard():
    total_divisi = Division.query.filter_by(is_active=True).count()
    total_ruangan_aktif = Room.query.filter_by(is_active=True).count()
    total_assets = Asset.query.count()
    total_admin_divisi = User.query.filter_by(role='admin_divisi', is_active=True).count()
    total_admin_ruangan = User.query.filter_by(role='admin_ruangan', is_active=True).count()
    total_user_nonaktif = User.query.filter_by(is_active=False).count()
    ruangan_tanpa_divisi = Room.query.filter(Room.division_id == None).count()
    admin_divisi_tanpa_divisi = User.query.filter(
        User.role == 'admin_divisi', User.is_active == True, User.division_id == None
    ).count()
    admin_ruangan_tanpa_ruangan = User.query.filter(
        User.role == 'admin_ruangan', User.is_active == True, User.room_id == None
    ).count()
    user_terbaru = User.query.filter(
        User.role.in_(('admin_divisi', 'admin_ruangan'))
    ).order_by(User.created_at.desc()).limit(5).all()

    divisi_summary = []
    for d in Division.query.filter_by(is_active=True).order_by(Division.division_name).all():
        admin = User.query.filter_by(division_id=d.id, role='admin_divisi', is_active=True).first()
        ruangan_count = Room.query.filter_by(division_id=d.id, is_active=True).count()
        asset_count = Asset.query.join(Room).filter(Room.division_id == d.id).count()
        divisi_summary.append({
            'divisi': d,
            'admin': admin,
            'ruangan_count': ruangan_count,
            'asset_count': asset_count,
        })

    return render_template('super_admin/dashboard.html',
        total_divisi=total_divisi,
        total_ruangan_aktif=total_ruangan_aktif,
        total_assets=total_assets,
        total_admin_divisi=total_admin_divisi,
        total_admin_ruangan=total_admin_ruangan,
        total_user_nonaktif=total_user_nonaktif,
        ruangan_tanpa_divisi=ruangan_tanpa_divisi,
        admin_divisi_tanpa_divisi=admin_divisi_tanpa_divisi,
        admin_ruangan_tanpa_ruangan=admin_ruangan_tanpa_ruangan,
        user_terbaru=user_terbaru,
        divisi_summary=divisi_summary,
    )


# ── Manajemen Divisi ───────────────────────────────────────────────────────────

@super_admin_bp.route('/assets')
@login_required
@role_required('super_admin')
def assets_index():
    page = request.args.get('page', 1, type=int)
    division_filter = request.args.get('division', 0, type=int)
    room_filter = request.args.get('room', 0, type=int)
    kondisi_filter = request.args.get('kondisi', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('q', '').strip()

    query = Asset.query.join(Room).outerjoin(Division)
    if division_filter:
        query = query.filter(Room.division_id == division_filter)
    if room_filter:
        query = query.filter(Asset.room_id == room_filter)
    if kondisi_filter:
        query = query.filter(Asset.condition == kondisi_filter)
    if status_filter:
        query = query.filter(Asset.status == status_filter)
    if search:
        like = f'%{search}%'
        query = query.filter(db.or_(
            Asset.asset_code.ilike(like),
            Asset.item_code.ilike(like),
            Asset.asset_name.ilike(like),
            Asset.serial_number.ilike(like),
            Room.room_name.ilike(like),
            Division.division_name.ilike(like),
        ))

    assets = query.order_by(
        Division.division_name.asc(),
        Room.room_name.asc(),
        Asset.asset_name.asc(),
    ).paginate(page=page, per_page=20)

    asset_ids_page = [asset.id for asset in assets.items]
    latest_rows = []
    if asset_ids_page:
        latest_dates = (
            db.session.query(
                FmeaRecord.asset_id,
                func.max(FmeaRecord.evaluation_date).label('max_date'),
            )
            .filter(FmeaRecord.asset_id.in_(asset_ids_page))
            .group_by(FmeaRecord.asset_id)
            .subquery()
        )
        latest_rows = (
            FmeaRecord.query
            .join(
                latest_dates,
                db.and_(
                    FmeaRecord.asset_id == latest_dates.c.asset_id,
                    FmeaRecord.evaluation_date == latest_dates.c.max_date,
                )
            )
            .order_by(FmeaRecord.created_at.desc())
            .all()
        )

    fmea_map = {}
    for row in latest_rows:
        fmea_map.setdefault(row.asset_id, row)

    divisions = Division.query.order_by(Division.division_name).all()
    rooms = Room.query.order_by(Room.room_name).all()
    return render_template(
        'super_admin/assets/index.html',
        assets=assets,
        divisions=divisions,
        rooms=rooms,
        fmea_map=fmea_map,
        division_filter=division_filter,
        room_filter=room_filter,
        kondisi_filter=kondisi_filter,
        status_filter=status_filter,
        search=search,
    )


@super_admin_bp.route('/assets/<int:id>')
@login_required
@role_required('super_admin')
def assets_detail(id):
    asset = Asset.query.get_or_404(id)
    fmea_records = asset.fmea_records.order_by(FmeaRecord.rpn_score.desc(), FmeaRecord.evaluation_date.desc(), FmeaRecord.created_at.desc()).all()
    logs = asset.maintenance_logs.order_by(MaintenanceLog.created_at.desc()).all()
    maintenance_terakhir = logs[0] if logs else None
    preventive_records = (
        asset.preventive_records
        .order_by(PreventiveMaintenance.check_date.desc(), PreventiveMaintenance.created_at.desc())
        .all()
    )
    preventive_terakhir = preventive_records[0] if preventive_records else None
    ai_rekomendasi = None
    if maintenance_terakhir and maintenance_terakhir.ai_recommendation:
        ai_rekomendasi = maintenance_terakhir.ai_recommendation
    if preventive_terakhir and preventive_terakhir.ai_recommendation:
        ai_rekomendasi = preventive_terakhir.ai_recommendation
    if fmea_records and fmea_records[0].recommendation and 'AI rekomendasi awal:' in fmea_records[0].recommendation:
        ai_rekomendasi = fmea_records[0].recommendation.split('AI rekomendasi awal:', 1)[1].strip()
        ai_rekomendasi = f'AI rekomendasi awal: {ai_rekomendasi}'

    log_user_ids = {log.logged_by for log in logs}
    users_map = {u.id: u for u in User.query.filter(User.id.in_(log_user_ids)).all()} if log_user_ids else {}
    chart_dates = json.dumps([str(f.evaluation_date) for f in reversed(fmea_records)])
    chart_rpn = json.dumps([f.rpn_score for f in reversed(fmea_records)])

    return render_template(
        'super_admin/assets/detail.html',
        asset=asset,
        fmea_records=fmea_records,
        fmea_terakhir=fmea_records[0] if fmea_records else None,
        preventive_records=preventive_records,
        preventive_terakhir=preventive_terakhir,
        maintenance_terakhir=maintenance_terakhir,
        ai_rekomendasi=ai_rekomendasi,
        logs=logs,
        users_map=users_map,
        chart_dates=chart_dates,
        chart_rpn=chart_rpn,
        today=date.today(),
    )


@super_admin_bp.route('/divisions')
@login_required
@role_required('super_admin')
def divisions_index():
    divisions = Division.query.order_by(Division.division_name).all()
    return render_template('super_admin/divisions/index.html', divisions=divisions)


@super_admin_bp.route('/divisions/create', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def divisions_create():
    form = CreateDivisionForm()
    if form.validate_on_submit():
        div = Division(
            division_name=form.division_name.data,
            description=form.description.data,
            is_active=True,
        )
        db.session.add(div)
        db.session.commit()
        flash(f'Divisi "{div.division_name}" berhasil ditambahkan.', 'success')
        return redirect(url_for('super_admin.divisions_index'))
    return render_template('super_admin/divisions/create.html', form=form)


@super_admin_bp.route('/divisions/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def divisions_edit(id):
    division = Division.query.get_or_404(id)
    form = EditDivisionForm(division_id=division.id, obj=division)
    if form.validate_on_submit():
        division.division_name = form.division_name.data
        division.description = form.description.data
        db.session.commit()
        flash(f'Divisi "{division.division_name}" berhasil diperbarui.', 'success')
        return redirect(url_for('super_admin.divisions_index'))
    return render_template('super_admin/divisions/edit.html', form=form, division=division)


@super_admin_bp.route('/divisions/<int:id>/toggle', methods=['POST'])
@login_required
@role_required('super_admin')
def divisions_toggle(id):
    division = Division.query.get_or_404(id)

    if division.is_active:
        ruangan_aktif = Room.query.filter_by(division_id=division.id, is_active=True).count()
        if ruangan_aktif > 0:
            flash(
                f'Divisi "{division.division_name}" tidak dapat dinonaktifkan karena '
                f'masih memiliki {ruangan_aktif} ruangan aktif.',
                'danger'
            )
            return redirect(url_for('super_admin.divisions_index'))

    division.is_active = not division.is_active
    db.session.commit()
    status = 'diaktifkan' if division.is_active else 'dinonaktifkan'
    flash(f'Divisi "{division.division_name}" berhasil {status}.', 'success')
    return redirect(url_for('super_admin.divisions_index'))


# ── Manajemen User ─────────────────────────────────────────────────────────────

@super_admin_bp.route('/users/admin-divisi')
@login_required
@role_required('super_admin')
def users_admin_divisi():
    search = request.args.get('q', '').strip()
    status = request.args.get('status', '')

    query = User.query.filter_by(role='admin_divisi')
    if status == 'aktif':
        query = query.filter_by(is_active=True)
    elif status == 'nonaktif':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.nip.ilike(f'%{search}%'),
                User.jabatan.ilike(f'%{search}%'),
            )
        )
    users = query.order_by(User.name).all()
    return render_template('super_admin/users/admin_divisi.html',
        users=users, search=search, status=status)


@super_admin_bp.route('/users/admin-ruangan')
@login_required
@role_required('super_admin')
def users_admin_ruangan():
    search = request.args.get('q', '').strip()
    status = request.args.get('status', '')

    query = User.query.filter_by(role='admin_ruangan')
    if status == 'aktif':
        query = query.filter_by(is_active=True)
    elif status == 'nonaktif':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.nip.ilike(f'%{search}%'),
                User.jabatan.ilike(f'%{search}%'),
            )
        )
    users = query.order_by(User.name).all()
    return render_template('super_admin/users/admin_ruangan.html',
        users=users, search=search, status=status)


@super_admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def users_create():
    form = CreateUserForm()
    form.division_id.choices = _division_choices()
    form.room_id.choices = _room_choices()

    if form.validate_on_submit():
        role = form.role.data
        division_id = form.division_id.data if role == 'admin_divisi' and form.division_id.data != 0 else None
        room_id = form.room_id.data if role == 'admin_ruangan' and form.room_id.data != 0 else None

        # Validasi: 1 divisi hanya boleh punya 1 Admin Divisi aktif
        if role == 'admin_divisi' and division_id:
            existing = User.query.filter_by(
                division_id=division_id, role='admin_divisi', is_active=True
            ).first()
            if existing:
                flash(
                    f'Divisi ini sudah memiliki Admin Divisi aktif ({existing.name}). '
                    'Nonaktifkan terlebih dahulu sebelum menambah yang baru.',
                    'danger'
                )
                return render_template('super_admin/users/create.html', form=form)

        # Validasi: 1 ruangan hanya boleh punya 1 Admin Ruangan aktif
        if role == 'admin_ruangan' and room_id:
            existing = User.query.filter_by(
                room_id=room_id, role='admin_ruangan', is_active=True
            ).first()
            if existing:
                flash(
                    f'Ruangan ini sudah memiliki Admin Ruangan aktif ({existing.name}). '
                    'Nonaktifkan terlebih dahulu sebelum menambah yang baru.',
                    'danger'
                )
                return render_template('super_admin/users/create.html', form=form)

        user = User(
            name=form.name.data,
            nip=form.nip.data or None,
            jabatan=form.jabatan.data or None,
            tanggal_lahir=form.tanggal_lahir.data,
            email=form.email.data.lower(),
            role=role,
            division_id=division_id,
            room_id=room_id,
            is_active=True,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Akun "{user.name}" berhasil dibuat.', 'success')
        if role == 'admin_divisi':
            return redirect(url_for('super_admin.users_admin_divisi'))
        return redirect(url_for('super_admin.users_admin_ruangan'))

    occupied_room_ids = {
        u.room_id for u in User.query.filter(
            User.role == 'admin_ruangan', User.is_active == True, User.room_id != None
        ).all()
    }
    occupied_division_ids = {
        u.division_id for u in User.query.filter(
            User.role == 'admin_divisi', User.is_active == True, User.division_id != None
        ).all()
    }
    return render_template('super_admin/users/create.html', form=form,
        occupied_room_ids=occupied_room_ids, occupied_division_ids=occupied_division_ids)


@super_admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def users_edit(id):
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('Anda tidak dapat mengedit akun Anda sendiri dari sini.', 'warning')
        return redirect(url_for('super_admin.users_admin_divisi'))

    form = EditUserForm(user_id=user.id, obj=user)
    form.division_id.choices = _division_choices()
    form.room_id.choices = _room_choices()

    if form.validate_on_submit():
        role = form.role.data
        division_id = form.division_id.data if role == 'admin_divisi' and form.division_id.data != 0 else None
        room_id = form.room_id.data if role == 'admin_ruangan' and form.room_id.data != 0 else None

        if role == 'admin_divisi' and division_id:
            existing = User.query.filter_by(
                division_id=division_id, role='admin_divisi', is_active=True
            ).filter(User.id != user.id).first()
            if existing:
                flash(
                    f'Divisi ini sudah memiliki Admin Divisi aktif ({existing.name}).',
                    'danger'
                )
                return render_template('super_admin/users/edit.html', form=form, user=user)

        if role == 'admin_ruangan' and room_id:
            existing = User.query.filter_by(
                room_id=room_id, role='admin_ruangan', is_active=True
            ).filter(User.id != user.id).first()
            if existing:
                flash(
                    f'Ruangan ini sudah memiliki Admin Ruangan aktif ({existing.name}).',
                    'danger'
                )
                return render_template('super_admin/users/edit.html', form=form, user=user)

        user.name = form.name.data
        user.nip = form.nip.data or None
        user.jabatan = form.jabatan.data or None
        user.tanggal_lahir = form.tanggal_lahir.data
        user.email = form.email.data.lower()
        user.role = role
        user.division_id = division_id
        user.room_id = room_id

        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash(f'Data akun "{user.name}" berhasil diperbarui.', 'success')
        if role == 'admin_divisi':
            return redirect(url_for('super_admin.users_admin_divisi'))
        return redirect(url_for('super_admin.users_admin_ruangan'))

    if request.method == 'GET':
        form.division_id.data = user.division_id or 0
        form.room_id.data = user.room_id or 0

    occupied_room_ids = {
        u.room_id for u in User.query.filter(
            User.role == 'admin_ruangan', User.is_active == True,
            User.room_id != None, User.id != user.id
        ).all()
    }
    occupied_division_ids = {
        u.division_id for u in User.query.filter(
            User.role == 'admin_divisi', User.is_active == True,
            User.division_id != None, User.id != user.id
        ).all()
    }
    return render_template('super_admin/users/edit.html', form=form, user=user,
        occupied_room_ids=occupied_room_ids, occupied_division_ids=occupied_division_ids)


@super_admin_bp.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
@role_required('super_admin')
def users_toggle(id):
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('Anda tidak dapat menonaktifkan akun Anda sendiri.', 'danger')
        return redirect(url_for('super_admin.users_admin_divisi'))

    # Saat mengaktifkan kembali, pastikan tidak melanggar aturan 1-admin-per-divisi/ruangan
    if not user.is_active:
        if user.role == 'admin_divisi' and user.division_id:
            conflict = User.query.filter(
                User.role == 'admin_divisi',
                User.is_active == True,
                User.division_id == user.division_id,
                User.id != user.id,
            ).first()
            if conflict:
                flash(
                    f'Tidak dapat mengaktifkan "{user.name}": divisi ini sudah memiliki Admin Divisi aktif ({conflict.name}).',
                    'danger',
                )
                return redirect(url_for('super_admin.users_admin_divisi'))

        elif user.role == 'admin_ruangan' and user.room_id:
            conflict = User.query.filter(
                User.role == 'admin_ruangan',
                User.is_active == True,
                User.room_id == user.room_id,
                User.id != user.id,
            ).first()
            if conflict:
                flash(
                    f'Tidak dapat mengaktifkan "{user.name}": ruangan ini sudah memiliki Admin Ruangan aktif ({conflict.name}).',
                    'danger',
                )
                return redirect(url_for('super_admin.users_admin_ruangan'))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
    flash(f'Akun "{user.name}" berhasil {status}.', 'success')
    if user.role == 'admin_divisi':
        return redirect(url_for('super_admin.users_admin_divisi'))
    return redirect(url_for('super_admin.users_admin_ruangan'))


# ── Manajemen Ruangan ──────────────────────────────────────────────────────────

@super_admin_bp.route('/rooms')
@login_required
@role_required('super_admin')
def rooms_index():
    page = request.args.get('page', 1, type=int)
    division_filter = request.args.get('division', 0, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('q', '').strip()

    query = Room.query
    if division_filter:
        query = query.filter_by(division_id=division_filter)
    if status_filter == 'aktif':
        query = query.filter_by(is_active=True)
    elif status_filter == 'nonaktif':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(
            db.or_(Room.room_name.ilike(f'%{search}%'), Room.room_code.ilike(f'%{search}%'))
        )

    rooms = query.order_by(Room.division_id, Room.room_name).paginate(page=page, per_page=15)
    divisions = Division.query.order_by(Division.division_name).all()
    return render_template('super_admin/rooms/index.html',
        rooms=rooms, divisions=divisions,
        division_filter=division_filter, status_filter=status_filter, search=search,
    )


@super_admin_bp.route('/rooms/create', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def rooms_create():
    form = CreateRoomForm()
    form.division_id.choices = _division_choices()

    if form.validate_on_submit():
        room = Room(
            division_id=form.division_id.data,
            room_code=form.room_code.data.upper(),
            room_name=form.room_name.data,
            floor=form.floor.data,
            description=form.description.data,
            is_active=True,
        )
        db.session.add(room)
        db.session.commit()
        flash(f'Ruangan "{room.room_name}" berhasil ditambahkan.', 'success')
        return redirect(url_for('super_admin.rooms_index'))

    return render_template('super_admin/rooms/create.html', form=form)


@super_admin_bp.route('/rooms/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def rooms_edit(id):
    room = Room.query.get_or_404(id)
    form = EditRoomForm(room_id=room.id, obj=room)
    form.division_id.choices = _division_choices()

    if form.validate_on_submit():
        # Cek apakah divisi diubah sementara ada aset aktif
        if room.division_id != form.division_id.data:
            aset_aktif = Asset.query.filter_by(room_id=room.id).count()
            if aset_aktif > 0:
                flash(
                    f'Ruangan tidak dapat dipindah divisi karena masih memiliki {aset_aktif} aset terdaftar.',
                    'danger'
                )
                return render_template('super_admin/rooms/edit.html', form=form, room=room)

        room.division_id = form.division_id.data
        room.room_code = form.room_code.data.upper()
        room.room_name = form.room_name.data
        room.floor = form.floor.data
        room.description = form.description.data
        db.session.commit()
        flash(f'Ruangan "{room.room_name}" berhasil diperbarui.', 'success')
        return redirect(url_for('super_admin.rooms_index'))

    if request.method == 'GET':
        form.division_id.data = room.division_id or 0

    return render_template('super_admin/rooms/edit.html', form=form, room=room)


@super_admin_bp.route('/rooms/<int:id>/delete', methods=['POST'])
@login_required
@role_required('super_admin')
def rooms_delete(id):
    room = Room.query.get_or_404(id)

    if Asset.query.filter_by(room_id=room.id).count() > 0:
        flash(f'Ruangan "{room.room_name}" tidak dapat dihapus karena masih memiliki aset terdaftar.', 'danger')
        return redirect(url_for('super_admin.rooms_index'))

    db.session.delete(room)
    db.session.commit()
    flash(f'Ruangan "{room.room_name}" berhasil dihapus.', 'success')
    return redirect(url_for('super_admin.rooms_index'))
