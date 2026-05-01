from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
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

    if form.validate_on_submit():
        current_user.name = form.name.data

        if form.new_password.data:
            if not form.current_password.data:
                flash('Masukkan password saat ini untuk mengganti password.', 'warning')
                return render_template('auth/profile.html', form=form)

            if not current_user.check_password(form.current_password.data):
                flash('Password saat ini tidak sesuai.', 'danger')
                return render_template('auth/profile.html', form=form)

            current_user.set_password(form.new_password.data)
            flash('Password berhasil diperbarui.', 'success')

        db.session.commit()
        flash('Profil berhasil disimpan.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)


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
