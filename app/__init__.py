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
        from app.models import FmeaRecord, MaintenanceLog, PreventiveMaintenance, ApprovalRequest, Notification

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
        """Buat data awal dan akun demo untuk semua role."""
        from app.utils.seeder import seed_demo_accounts_and_assets, seed_super_admin, seed_divisions
        from app.models.asset_category import seed_kategori

        steps = [
            ('Super Admin',      seed_super_admin),
            ('Divisi awal',      seed_divisions),
            ('Kategori aset',    lambda: seed_kategori(db.session)),
            ('Akun dan aset demo', seed_demo_accounts_and_assets),
        ]
        for label, fn in steps:
            try:
                fn()
            except Exception as exc:
                print(f'[ERROR] Seeder "{label}" gagal: {exc}')
                db.session.rollback()

    @app.cli.command('seed-real-accounts')
    def seed_real_accounts_command():
        """Buat/rapikan akun real sesuai mapping data Excel klien."""
        from app.utils.real_accounts import seed_real_accounts

        try:
            seed_real_accounts()
        except Exception as exc:
            print(f'[ERROR] Seeder akun real gagal: {exc}')
            db.session.rollback()
            raise

    @app.cli.command('clear-demo-data')
    def clear_demo_data_command():
        """Hapus data demo lama tanpa menyentuh data real klien."""
        from app.utils.demo_cleanup import clear_demo_data

        try:
            clear_demo_data()
        except Exception as exc:
            print(f'[ERROR] Bersihkan data demo gagal: {exc}')
            db.session.rollback()
            raise

    @app.cli.command('refresh-ai-recommendations')
    def refresh_ai_recommendations_command():
        """Sinkronkan ulang rekomendasi AI dengan kondisi aset terbaru."""
        from app.utils.ai_refresh import refresh_ai_recommendations

        try:
            refresh_ai_recommendations()
        except Exception as exc:
            print(f'[ERROR] Refresh rekomendasi AI gagal: {exc}')
            db.session.rollback()
            raise

    @app.cli.command('import-client-excel')
    @click.option('--history-file', type=click.Path(exists=True), default=None, help='Path Data History Maintenance Aset.xlsx')
    @click.option('--kib-file', type=click.Path(exists=True), default=None, help='Path INTRA EKSTRA KIB B.xlsx')
    @click.option('--preventive-file', type=click.Path(exists=True), default=None, help='Path PREVENTIVE ASET.xlsx')
    @click.option('--default-division', default='Pelayanan Medik dan Keperawatan', show_default=True)
    @click.option('--default-room-code', default=None, help='Opsional: room_code untuk aset KIB yang tidak punya ruangan.')
    @click.option('--dry-run/--commit', default=True, show_default=True, help='Dry-run hanya hitung, commit menyimpan ke database.')
    def import_client_excel(history_file, kib_file, preventive_file, default_division, default_room_code, dry_run):
        """Import file Excel klien dengan pencocokan data aset yang sudah ada."""
        from app.services.excel_import_service import ClientExcelImporter

        if not any([history_file, kib_file, preventive_file]):
            raise click.UsageError('Isi minimal salah satu: --history-file, --kib-file, atau --preventive-file.')

        importer = ClientExcelImporter(
            dry_run=dry_run,
            default_division_name=default_division,
            default_room_code=default_room_code,
        )
        stats = importer.run(
            history_file=history_file,
            kib_file=kib_file,
            preventive_file=preventive_file,
        )
        click.echo('Import mode: DRY-RUN' if dry_run else 'Import mode: COMMIT')
        for line in stats.lines():
            click.echo(line)
        for warning in stats.warnings[:20]:
            click.echo(f'warning: {warning}')

    return app
