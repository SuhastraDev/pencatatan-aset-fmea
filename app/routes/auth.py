from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.notification import Notification
from app.forms.auth_forms import LoginForm, ProfileForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(_dashboard_url(current_user.role))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_url(current_user.role))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if not user or not user.check_password(form.password.data):
            flash('Email atau password salah.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.is_active:
            flash('Akun Anda telah dinonaktifkan. Hubungi Super Admin.', 'danger')
            return render_template('auth/login.html', form=form)

        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Lazy check: buat notifikasi maintenance terlambat jika ada
        try:
            from app.services.notif_service import check_overdue_maintenance
            check_overdue_maintenance(user)
        except Exception:
            pass  # Jangan biarkan check ini gagalkan login

        # Arahkan ke next URL jika ada dan aman (bukan redirect eksternal)
        from urllib.parse import urlparse
        next_url = request.args.get('next', '')
        if next_url and urlparse(next_url).netloc == '' and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(_dashboard_url(user.role))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    edit_mode = request.args.get('edit') == '1'

    if form.validate_on_submit():
        password_to_update = form.new_password.data or None
        if password_to_update:
            if not form.current_password.data:
                flash('Masukkan password saat ini untuk mengganti password.', 'warning')
                return render_template('auth/profile.html', form=form, edit_mode=True)

            if not current_user.check_password(form.current_password.data):
                flash('Password saat ini tidak sesuai.', 'danger')
                return render_template('auth/profile.html', form=form, edit_mode=True)

        new_email = None
        if current_user.is_super_admin():
            new_email = form.email.data.strip().lower()
            email_owner = User.query.filter(
                User.email == new_email,
                User.id != current_user.id,
            ).first()
            if email_owner:
                form.email.errors.append('Email tersebut sudah digunakan akun lain.')
                return render_template('auth/profile.html', form=form, edit_mode=True)

        previous_photo = current_user.profile_photo
        try:
            new_photo = _save_profile_photo(form.photo.data, current_user.id)
        except ValueError as exc:
            form.photo.errors.append(str(exc))
            return render_template('auth/profile.html', form=form, edit_mode=True)

        current_user.name = form.name.data
        current_user.nip = form.nip.data or None
        current_user.jabatan = form.jabatan.data or None
        current_user.tanggal_lahir = form.tanggal_lahir.data
        if new_email is not None:
            current_user.email = new_email
        if new_photo:
            current_user.profile_photo = new_photo
        if password_to_update:
            current_user.set_password(password_to_update)

        db.session.commit()
        if new_photo and previous_photo:
            _delete_profile_photo(previous_photo)
        if password_to_update:
            flash('Password berhasil diperbarui.', 'success')
        flash('Profil berhasil disimpan.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form, edit_mode=edit_mode or bool(form.errors))


def _save_profile_photo(upload, user_id):
    """Validasi dan simpan foto profil, lalu kembalikan nama file aman."""
    if not upload or not upload.filename:
        return None

    try:
        image = Image.open(upload.stream)
        image.verify()
        upload.stream.seek(0)
        image_format = (image.format or '').upper()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValueError('File yang dipilih bukan gambar yang valid.')

    extension_by_format = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}
    extension = extension_by_format.get(image_format)
    if not extension:
        raise ValueError('Foto harus berformat JPG, PNG, atau WEBP.')

    if not secure_filename(upload.filename):
        raise ValueError('Nama file foto tidak valid.')

    upload_dir = Path(current_app.static_folder) / 'uploads' / 'profile'
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f'user_{user_id}_{uuid4().hex}.{extension}'
    upload.save(upload_dir / filename)
    return filename


def _delete_profile_photo(filename):
    """Hapus foto lama hanya dari folder upload profil."""
    photo_path = Path(current_app.static_folder) / 'uploads' / 'profile' / Path(filename).name
    try:
        photo_path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning('Foto profil lama tidak dapat dihapus: %s', photo_path)


# ── Notifikasi (shared semua role) ────────────────────────────────────────────

@auth_bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifs = (Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .paginate(page=page, per_page=15))
    return render_template('shared/notifications.html', notifs=notifs)


@auth_bp.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def notifications_read(id):
    notif = Notification.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(url_for('auth.notifications'))


@auth_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def notifications_read_all():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('Semua notifikasi telah ditandai sudah dibaca.', 'success')
    return redirect(url_for('auth.notifications'))


def _dashboard_url(role):
    """Kembalikan URL dashboard berdasarkan role."""
    mapping = {
        'super_admin': 'super_admin.dashboard',
        'admin_divisi': 'divisi.dashboard',
        'admin_ruangan': 'ruangan.dashboard',
    }
    return url_for(mapping.get(role, 'auth.login'))
