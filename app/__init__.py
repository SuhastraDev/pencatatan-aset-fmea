import click
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import generate_csrf
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login terlebih dahulu.'
    login_manager.login_message_category = 'warning'

    # Import model agar Flask-Migrate mendeteksi semua tabel
    with app.app_context():
        from app.models import Division, User, Room, AssetCategory, Asset
        from app.models import FmeaRecord, MaintenanceLog, ApprovalRequest, Notification

    # Daftarkan csrf_token dan time_ago sebagai fungsi global di semua template
    app.jinja_env.globals['csrf_token'] = generate_csrf
    from app.utils.helpers import time_ago
    app.jinja_env.globals['time_ago'] = time_ago

    # Context processor: inject recent_notifications ke semua template
    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            from app.models.notification import Notification
            recent = (Notification.query
                .filter_by(user_id=current_user.id)
                .order_by(Notification.created_at.desc())
                .limit(5).all())
            return {'recent_notifications': recent}
        return {'recent_notifications': []}

    # Daftarkan blueprint
    from app.routes.auth import auth_bp
    from app.routes.super_admin import super_admin_bp
    from app.routes.divisi import divisi_bp
    from app.routes.ruangan import ruangan_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(divisi_bp)
    app.register_blueprint(ruangan_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # CLI command: flask seed
    @app.cli.command('seed')
    def seed():
        """Buat data awal: Super Admin, divisi, dan kategori aset."""
        from app.utils.seeder import seed_super_admin, seed_divisions
        from app.models.asset_category import seed_kategori

        steps = [
            ('Super Admin',      seed_super_admin),
            ('Divisi awal',      seed_divisions),
            ('Kategori aset',    lambda: seed_kategori(db.session)),
        ]
        for label, fn in steps:
            try:
                fn()
            except Exception as exc:
                print(f'[ERROR] Seeder "{label}" gagal: {exc}')
                db.session.rollback()

    return app
