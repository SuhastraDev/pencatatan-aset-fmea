from app import db
from app.models.notification import Notification


def create_notification(user_id, title, message, type, related_asset_id=None):
    """Simpan satu notifikasi ke database."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        related_asset_id=related_asset_id,
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def notify_high_rpn(asset, rpn_score, admin_divisi_users=None):
    """Kirim notifikasi ke Admin Divisi yang membawahi ruangan aset tersebut."""
    from app.models.user import User
    title = f"RPN Tinggi: {asset.asset_name}"
    message = (
        f"Aset {asset.asset_code} — {asset.asset_name} di ruangan {asset.room.room_name} "
        f"memiliki RPN {rpn_score} (Tinggi). Tindakan segera diperlukan."
    )
    division_id = asset.room.division_id if asset.room else None
    if division_id:
        targets = User.query.filter_by(
            role='admin_divisi', division_id=division_id, is_active=True
        ).all()
    else:
        targets = admin_divisi_users or []

    for user in targets:
        db.session.add(Notification(
            user_id=user.id,
            title=title,
            message=message,
            type='rpn_tinggi',
            related_asset_id=asset.id,
        ))
    db.session.commit()


def notify_medium_rpn(asset, rpn_score, requester):
    """Kirim notifikasi ke Admin Ruangan saat RPN sedang (80-199)."""
    title = f"RPN Sedang: {asset.asset_name}"
    message = (
        f"Aset {asset.asset_code} — {asset.asset_name} memiliki RPN {rpn_score} (Sedang). "
        f"Jadwalkan pemeriksaan dalam 7 hari ke depan."
    )
    notif = Notification(
        user_id=requester.id,
        title=title,
        message=message,
        type='rpn_sedang',
        related_asset_id=asset.id,
    )
    db.session.add(notif)
    db.session.commit()


def notify_approval_result(approval_req, is_approved):
    """Kirim notifikasi hasil approval ke Admin Ruangan yang mengajukan."""
    asset = approval_req.asset
    if is_approved:
        title = f"Pengajuan Disetujui: {asset.asset_name}"
        message = (
            f"Pengajuan perubahan status aset {asset.asset_code} — {asset.asset_name} "
            f"dari '{approval_req.current_status}' ke '{approval_req.requested_status}' telah disetujui."
        )
        notif_type = 'approval_disetujui'
    else:
        title = f"Pengajuan Ditolak: {asset.asset_name}"
        message = (
            f"Pengajuan perubahan status aset {asset.asset_code} — {asset.asset_name} "
            f"ditolak. Catatan: {approval_req.reviewer_notes or '-'}"
        )
        notif_type = 'approval_ditolak'

    db.session.add(Notification(
        user_id=approval_req.requested_by,
        title=title,
        message=message,
        type=notif_type,
        related_asset_id=asset.id,
    ))
    db.session.commit()


def notify_new_approval_request(approval_req, admin_divisi_users=None):
    """Kirim notifikasi ke Admin Divisi yang membawahi ruangan aset tersebut."""
    from app.models.user import User
    asset = approval_req.asset
    title = f"Pengajuan Baru: {asset.asset_name}"
    message = (
        f"Pengajuan perubahan status aset {asset.asset_code} — {asset.asset_name} "
        f"dari '{approval_req.current_status}' ke '{approval_req.requested_status}'."
    )
    division_id = asset.room.division_id if asset.room else None
    if division_id:
        targets = User.query.filter_by(
            role='admin_divisi', division_id=division_id, is_active=True
        ).all()
    else:
        targets = admin_divisi_users or []

    for user in targets:
        db.session.add(Notification(
            user_id=user.id,
            title=title,
            message=message,
            type='approval_baru',
            related_asset_id=asset.id,
        ))
    db.session.commit()


def get_unread_count(user_id):
    """Kembalikan jumlah notifikasi belum dibaca milik user."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def check_overdue_maintenance(user):
    """
    Lazy check: cek aset dengan next_maintenance_date yang sudah lewat.
    Dipanggil saat user login — hanya buat notifikasi jika belum ada.
    """
    from datetime import date
    from app.models.asset import Asset
    from app.models.room import Room

    today = date.today()

    if user.role == 'admin_ruangan' and user.room_id:
        overdue = Asset.query.filter(
            Asset.room_id == user.room_id,
            Asset.next_maintenance_date != None,
            Asset.next_maintenance_date < today,
            Asset.status == 'aktif',
        ).all()
        targets = [(a, user.id) for a in overdue]

    elif user.role == 'admin_divisi' and user.division_id:
        rooms = Room.query.filter_by(division_id=user.division_id, is_active=True).all()
        room_ids = [r.id for r in rooms]
        overdue = Asset.query.filter(
            Asset.room_id.in_(room_ids),
            Asset.next_maintenance_date != None,
            Asset.next_maintenance_date < today,
            Asset.status == 'aktif',
        ).all() if room_ids else []
        targets = [(a, user.id) for a in overdue]
    else:
        return

    from datetime import datetime, timedelta
    # Periode de-duplikasi: 1 hari — tidak kirim notif yang sama 2x dalam sehari
    dedup_threshold = datetime.utcnow() - timedelta(hours=24)

    for asset, uid in targets:
        # Jangan duplikat jika sudah ada notifikasi maintenance_terlambat untuk aset ini
        # dalam 24 jam terakhir (terlepas sudah dibaca atau belum)
        exists = Notification.query.filter(
            Notification.user_id == uid,
            Notification.related_asset_id == asset.id,
            Notification.type == 'maintenance_terlambat',
            Notification.created_at >= dedup_threshold,
        ).first()
        if not exists:
            db.session.add(Notification(
                user_id=uid,
                title=f"Maintenance Terlambat: {asset.asset_name}",
                message=(
                    f"Jadwal maintenance aset {asset.asset_code} — {asset.asset_name} "
                    f"di {asset.room.room_name} sudah melewati tanggal "
                    f"{asset.next_maintenance_date.strftime('%d %b %Y')}."
                ),
                type='maintenance_terlambat',
                related_asset_id=asset.id,
            ))
    if targets:
        db.session.commit()
