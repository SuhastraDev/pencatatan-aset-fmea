from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user
from sqlalchemy import and_, func
import io, json

from app import db
from app.models.asset import Asset
from app.models.asset_category import AssetCategory
from app.models.fmea import FmeaRecord
from app.models.maintenance_log import MaintenanceLog
from app.models.approval_request import ApprovalRequest
from app.models.room import Room
from app.models.user import User
from app.utils.decorators import role_required
from app.utils.helpers import generate_qr_code
from app.forms.approval_forms import ApproveForm, RejectForm
from app.services.notif_service import notify_approval_result
from app.services.export_service import generate_excel_divisi, generate_pdf, generate_kir_pdf, build_filename

divisi_bp = Blueprint('divisi', __name__, url_prefix='/divisi')


def get_division_rooms(admin_divisi_user):
    """Return list Room yang berada di divisi user ini."""
    return Room.query.filter_by(
        division_id=admin_divisi_user.division_id,
        is_active=True
    ).all()


def get_division_room_ids(admin_divisi_user):
    """Return list room_id yang berada di divisi user ini."""
    return [r.id for r in get_division_rooms(admin_divisi_user)]


# ── Dashboard ─────────────────────────────────────────────────────────────────

@divisi_bp.route('/dashboard')
@login_required
@role_required('admin_divisi')
def dashboard():
    room_ids = get_division_room_ids(current_user)
    rooms = get_division_rooms(current_user)

    total_assets = Asset.query.filter(Asset.room_id.in_(room_ids)).count() if room_ids else 0
    kritis_count = Asset.query.filter(
        Asset.room_id.in_(room_ids),
        Asset.condition.in_(['kritis', 'tidak_layak'])
    ).count() if room_ids else 0
    pending_count = (
        ApprovalRequest.query
        .join(Asset, ApprovalRequest.asset_id == Asset.id)
        .filter(Asset.room_id.in_(room_ids), ApprovalRequest.approval_status == 'pending')
        .count()
    ) if room_ids else 0

    cond_baik = Asset.query.filter(Asset.room_id.in_(room_ids), Asset.condition == 'baik').count() if room_ids else 0
    cond_perlu = Asset.query.filter(Asset.room_id.in_(room_ids), Asset.condition == 'perlu_perhatian').count() if room_ids else 0
    cond_kritis = Asset.query.filter(Asset.room_id.in_(room_ids), Asset.condition == 'kritis').count() if room_ids else 0
    cond_tidak = Asset.query.filter(Asset.room_id.in_(room_ids), Asset.condition == 'tidak_layak').count() if room_ids else 0

    room_stats = []
    chart_labels = []
    chart_rpn_tinggi = []
    chart_rpn_sedang = []
    chart_rpn_rendah = []

    for r in rooms:
        assets = r.assets.all()

        a_baik = sum(1 for a in assets if a.condition == 'baik')
        a_perlu = sum(1 for a in assets if a.condition == 'perlu_perhatian')
        a_kritis = sum(1 for a in assets if a.condition == 'kritis')
        a_tidak = sum(1 for a in assets if a.condition == 'tidak_layak')

        highest_rpn = None
        rt = rs_c = rr = 0
        for a in assets:
            last_f = a.fmea_records.order_by(FmeaRecord.created_at.desc()).first()
            if last_f:
                if highest_rpn is None or last_f.rpn_score > highest_rpn:
                    highest_rpn = last_f.rpn_score
                if last_f.risk_category == 'tinggi':
                    rt += 1
                elif last_f.risk_category == 'sedang':
                    rs_c += 1
                else:
                    rr += 1

        room_stats.append({
            'room': r, 'total': len(assets),
            'baik': a_baik, 'perlu': a_perlu,
            'kritis': a_kritis, 'tidak_layak': a_tidak,
            'highest_rpn': highest_rpn,
        })
        chart_labels.append(r.room_name)
        chart_rpn_tinggi.append(rt)
        chart_rpn_sedang.append(rs_c)
        chart_rpn_rendah.append(rr)

    return render_template('divisi/dashboard.html',
        total_assets=total_assets, kritis_count=kritis_count, pending_count=pending_count,
        cond_baik=cond_baik, cond_perlu=cond_perlu,
        cond_kritis=cond_kritis, cond_tidak=cond_tidak,
        room_stats=room_stats,
        chart_labels=json.dumps(chart_labels),
        chart_rpn_tinggi=json.dumps(chart_rpn_tinggi),
        chart_rpn_sedang=json.dumps(chart_rpn_sedang),
        chart_rpn_rendah=json.dumps(chart_rpn_rendah),
    )


# ── Aset ──────────────────────────────────────────────────────────────────────

@divisi_bp.route('/assets')
@login_required
@role_required('admin_divisi')
def assets_index():
    room_ids = get_division_room_ids(current_user)
    page = request.args.get('page', 1, type=int)
    room_filter = request.args.get('room', 0, type=int)
    kondisi_filter = request.args.get('kondisi', '')
    status_filter = request.args.get('status', '')
    rpn_filter = request.args.get('rpn', '')

    query = Asset.query.filter(Asset.room_id.in_(room_ids)) if room_ids else Asset.query.filter_by(id=None)

    if room_filter:
        if room_filter not in room_ids:
            abort(403)
        query = query.filter_by(room_id=room_filter)
    if kondisi_filter:
        query = query.filter_by(condition=kondisi_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    if rpn_filter and room_ids:
        latest_sq = (db.session.query(
            FmeaRecord.asset_id,
            func.max(FmeaRecord.id).label('max_id')
        ).group_by(FmeaRecord.asset_id).subquery())

        matching = (db.session.query(FmeaRecord.asset_id)
            .join(latest_sq, and_(
                FmeaRecord.asset_id == latest_sq.c.asset_id,
                FmeaRecord.id == latest_sq.c.max_id
            ))
            .filter(FmeaRecord.risk_category == rpn_filter)
            .all())
        query = query.filter(Asset.id.in_([r[0] for r in matching]))

    assets = query.order_by(Asset.room_id, Asset.asset_name).paginate(page=page, per_page=15)
    rooms = get_division_rooms(current_user)

    # Bangun fmea_map {asset_id: FmeaRecord_terakhir} — satu query, hindari N+1 di template
    asset_ids_page = [a.id for a in assets.items]
    fmea_map = {}
    if asset_ids_page:
        latest_sq = (db.session.query(
            FmeaRecord.asset_id,
            func.max(FmeaRecord.id).label('max_id')
        ).filter(FmeaRecord.asset_id.in_(asset_ids_page))
         .group_by(FmeaRecord.asset_id).subquery())

        latest_records = (db.session.query(FmeaRecord)
            .join(latest_sq, and_(
                FmeaRecord.asset_id == latest_sq.c.asset_id,
                FmeaRecord.id == latest_sq.c.max_id
            )).all())
        fmea_map = {f.asset_id: f for f in latest_records}

    return render_template('divisi/assets/index.html',
        assets=assets, rooms=rooms, fmea_map=fmea_map,
        room_filter=room_filter, kondisi_filter=kondisi_filter,
        status_filter=status_filter, rpn_filter=rpn_filter,
    )


@divisi_bp.route('/assets/<int:id>')
@login_required
@role_required('admin_divisi')
def assets_detail(id):
    asset = Asset.query.get_or_404(id)

    # Pastikan aset ini berada di divisi yang sama
    if asset.room.division_id != current_user.division_id:
        abort(403)

    fmea_records = asset.fmea_records.order_by(FmeaRecord.created_at.desc()).all()
    logs = asset.maintenance_logs.order_by(MaintenanceLog.created_at.desc()).all()

    log_user_ids = {l.logged_by for l in logs}
    users_map = {u.id: u for u in User.query.filter(User.id.in_(log_user_ids)).all()} if log_user_ids else {}

    chart_dates = json.dumps([str(f.evaluation_date) for f in reversed(fmea_records)])
    chart_rpn = json.dumps([f.rpn_score for f in reversed(fmea_records)])

    return render_template('divisi/assets/detail.html',
        asset=asset,
        fmea_records=fmea_records,
        fmea_terakhir=fmea_records[0] if fmea_records else None,
        logs=logs, users_map=users_map,
        chart_dates=chart_dates, chart_rpn=chart_rpn,
        today=date.today(),
    )


# ── KIR (Admin Divisi — read only) ────────────────────────────────────────────

@divisi_bp.route('/assets/<int:id>/kir')
@login_required
@role_required('admin_divisi')
def assets_kir(id):
    """Download PDF Kartu KIR aset (Admin Divisi — read only, tanpa mencatat log)."""
    asset = Asset.query.get_or_404(id)
    if asset.room.division_id != current_user.division_id:
        abort(403)

    base_url = request.host_url.rstrip('/')
    pdf_bytes = generate_kir_pdf(asset, current_user.name, base_url)

    filename = f"KIR_{asset.asset_code}_{date.today().strftime('%Y%m%d')}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )


@divisi_bp.route('/assets/<int:id>/qr-code')
@login_required
@role_required('admin_divisi')
def assets_qr_code(id):
    """Download PNG QR Code aset (Admin Divisi — read only)."""
    asset = Asset.query.get_or_404(id)
    if asset.room.division_id != current_user.division_id:
        abort(403)

    base_url = request.host_url.rstrip('/')
    qr_path = generate_qr_code(asset.id, base_url)
    filename = f"QR_{asset.asset_code}.png"
    return send_file(qr_path, mimetype='image/png', as_attachment=True, download_name=filename)


# ── Approval ──────────────────────────────────────────────────────────────────

@divisi_bp.route('/approvals')
@login_required
@role_required('admin_divisi')
def approvals_index():
    room_ids = get_division_room_ids(current_user)
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    room_filter = request.args.get('room', 0, type=int)

    query = (
        ApprovalRequest.query
        .join(Asset, ApprovalRequest.asset_id == Asset.id)
        .filter(Asset.room_id.in_(room_ids))
    ) if room_ids else ApprovalRequest.query.filter_by(id=None)

    if status_filter:
        query = query.filter(ApprovalRequest.approval_status == status_filter)
    if room_filter:
        if room_filter not in room_ids:
            abort(403)
        query = query.filter(Asset.room_id == room_filter)

    approvals = query.order_by(ApprovalRequest.requested_at.desc()).paginate(page=page, per_page=15)
    pending_count = (
        ApprovalRequest.query
        .join(Asset, ApprovalRequest.asset_id == Asset.id)
        .filter(Asset.room_id.in_(room_ids), ApprovalRequest.approval_status == 'pending')
        .count()
    ) if room_ids else 0
    rooms = get_division_rooms(current_user)

    user_ids = set()
    for a in approvals.items:
        user_ids.add(a.requested_by)
        if a.reviewed_by:
            user_ids.add(a.reviewed_by)
    users_map = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return render_template('divisi/approvals/index.html',
        approvals=approvals, rooms=rooms,
        status_filter=status_filter, room_filter=room_filter,
        pending_count=pending_count, users_map=users_map,
    )


@divisi_bp.route('/approvals/<int:id>')
@login_required
@role_required('admin_divisi')
def approvals_detail(id):
    approval = ApprovalRequest.query.get_or_404(id)

    # Pastikan approval ini berasal dari divisi yang sama
    if approval.asset.room.division_id != current_user.division_id:
        abort(403)

    asset = approval.asset
    fmea_recent = asset.fmea_records.order_by(FmeaRecord.created_at.desc()).limit(3).all()
    requester = User.query.get(approval.requested_by)
    reviewer = User.query.get(approval.reviewed_by) if approval.reviewed_by else None

    approve_form = ApproveForm(prefix='approve')
    reject_form = RejectForm(prefix='reject')

    return render_template('divisi/approvals/detail.html',
        approval=approval, asset=asset,
        fmea_recent=fmea_recent,
        requester=requester, reviewer=reviewer,
        approve_form=approve_form, reject_form=reject_form,
    )


@divisi_bp.route('/approvals/<int:id>/approve', methods=['POST'])
@login_required
@role_required('admin_divisi')
def approvals_approve(id):
    approval = ApprovalRequest.query.get_or_404(id)

    if approval.asset.room.division_id != current_user.division_id:
        abort(403)

    if approval.approval_status != 'pending':
        flash('Pengajuan ini sudah diproses sebelumnya.', 'warning')
        return redirect(url_for('divisi.approvals_detail', id=id))

    form = ApproveForm(prefix='approve')
    if form.validate_on_submit():
        approval.approval_status = 'approved'
        approval.reviewed_by = current_user.id
        approval.reviewed_at = datetime.utcnow()
        approval.reviewer_notes = form.reviewer_notes.data or None

        asset = approval.asset

        # Validasi enum status sebelum assign ke aset
        valid_statuses = {'aktif', 'dalam_perbaikan', 'tidak_aktif'}
        if approval.requested_status not in valid_statuses:
            flash('Status yang diajukan tidak valid. Pengajuan tidak dapat diproses.', 'danger')
            return redirect(url_for('divisi.approvals_detail', id=id))

        asset.status = approval.requested_status

        db.session.add(MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='approval_disetujui',
            description=f'Perubahan status ke "{approval.requested_status}" disetujui oleh {current_user.name}.',
            action_date=date.today(),
        ))
        db.session.commit()
        try:
            notify_approval_result(approval, is_approved=True)
        except Exception:
            pass  # Notifikasi gagal tidak boleh rollback data approval yang sudah tersimpan
        flash(f'Pengajuan untuk aset "{asset.asset_name}" telah disetujui.', 'success')
    else:
        flash('Form tidak valid.', 'danger')
        return redirect(url_for('divisi.approvals_detail', id=id))

    return redirect(url_for('divisi.approvals_index'))


@divisi_bp.route('/approvals/<int:id>/reject', methods=['POST'])
@login_required
@role_required('admin_divisi')
def approvals_reject(id):
    approval = ApprovalRequest.query.get_or_404(id)

    if approval.asset.room.division_id != current_user.division_id:
        abort(403)

    if approval.approval_status != 'pending':
        flash('Pengajuan ini sudah diproses sebelumnya.', 'warning')
        return redirect(url_for('divisi.approvals_detail', id=id))

    form = RejectForm(prefix='reject')
    if form.validate_on_submit():
        approval.approval_status = 'rejected'
        approval.reviewed_by = current_user.id
        approval.reviewed_at = datetime.utcnow()
        approval.reviewer_notes = form.reviewer_notes.data

        asset = approval.asset
        asset.status = approval.current_status

        db.session.add(MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='approval_ditolak',
            description=f'Perubahan status ke "{approval.requested_status}" ditolak. Alasan: {form.reviewer_notes.data}',
            action_date=date.today(),
        ))
        db.session.commit()
        try:
            notify_approval_result(approval, is_approved=False)
        except Exception:
            pass  # Notifikasi gagal tidak boleh rollback data penolakan yang sudah tersimpan
        flash(f'Pengajuan untuk aset "{asset.asset_name}" telah ditolak.', 'warning')
    else:
        flash('Alasan penolakan wajib diisi (minimal 10 karakter).', 'danger')
        return redirect(url_for('divisi.approvals_detail', id=id))

    return redirect(url_for('divisi.approvals_index'))


# ── Laporan ────────────────────────────────────────────────────────────────────

def _build_report_data(room_ids, room_filter, kondisi_filter, rpn_filter):
    if not room_ids:
        return [], {
            'total': 0, 'baik': 0, 'perlu_perhatian': 0,
            'kritis': 0, 'tidak_layak': 0,
            'rpn_rendah': 0, 'rpn_sedang': 0, 'rpn_tinggi': 0,
        }

    query = Asset.query.filter(Asset.room_id.in_(room_ids))
    if room_filter:
        query = query.filter_by(room_id=room_filter)
    if kondisi_filter:
        query = query.filter_by(condition=kondisi_filter)

    assets = query.order_by(Asset.room_id, Asset.asset_name).all()
    asset_data = []
    for a in assets:
        last_f = a.fmea_records.order_by(FmeaRecord.created_at.desc()).first()
        if rpn_filter and (not last_f or last_f.risk_category != rpn_filter):
            continue
        asset_data.append({'asset': a, 'last_fmea': last_f})

    stats = {
        'total': len(asset_data),
        'baik': sum(1 for d in asset_data if d['asset'].condition == 'baik'),
        'perlu_perhatian': sum(1 for d in asset_data if d['asset'].condition == 'perlu_perhatian'),
        'kritis': sum(1 for d in asset_data if d['asset'].condition == 'kritis'),
        'tidak_layak': sum(1 for d in asset_data if d['asset'].condition == 'tidak_layak'),
        'rpn_rendah': sum(1 for d in asset_data if d['last_fmea'] and d['last_fmea'].risk_category == 'rendah'),
        'rpn_sedang': sum(1 for d in asset_data if d['last_fmea'] and d['last_fmea'].risk_category == 'sedang'),
        'rpn_tinggi': sum(1 for d in asset_data if d['last_fmea'] and d['last_fmea'].risk_category == 'tinggi'),
    }
    return asset_data, stats


@divisi_bp.route('/reports')
@login_required
@role_required('admin_divisi')
def reports_index():
    room_ids = get_division_room_ids(current_user)
    room_filter = request.args.get('room', 0, type=int)
    kondisi_filter = request.args.get('kondisi', '')
    rpn_filter = request.args.get('rpn', '')

    if room_filter and room_filter not in room_ids:
        abort(403)

    asset_data, stats = _build_report_data(room_ids, room_filter, kondisi_filter, rpn_filter)
    rooms = get_division_rooms(current_user)

    room_summary = []
    for r in rooms:
        r_d = [d for d in asset_data if d['asset'].room_id == r.id]
        if not r_d:
            continue
        room_summary.append({
            'room': r,
            'total': len(r_d),
            'kritis': sum(1 for d in r_d if d['asset'].condition in ['kritis', 'tidak_layak']),
            'rpn_tinggi': sum(1 for d in r_d if d['last_fmea'] and d['last_fmea'].risk_category == 'tinggi'),
        })

    return render_template('divisi/reports/index.html',
        asset_data=asset_data, stats=stats, rooms=rooms,
        room_summary=room_summary,
        room_filter=room_filter, kondisi_filter=kondisi_filter, rpn_filter=rpn_filter,
    )


@divisi_bp.route('/reports/export-excel')
@login_required
@role_required('admin_divisi')
def reports_export_excel():
    room_ids = get_division_room_ids(current_user)
    room_filter = request.args.get('room', 0, type=int)
    kondisi_filter = request.args.get('kondisi', '')
    rpn_filter = request.args.get('rpn', '')

    if room_filter and room_filter not in room_ids:
        abort(403)

    asset_data, _ = _build_report_data(room_ids, room_filter, kondisi_filter, rpn_filter)
    rooms = get_division_rooms(current_user)

    room_stats_sheet = []
    for r in rooms:
        r_d = [d for d in asset_data if d['asset'].room_id == r.id]
        if not r_d:
            continue
        room_stats_sheet.append({
            'room_name': r.room_name,
            'total': len(r_d),
            'baik': sum(1 for d in r_d if d['asset'].condition == 'baik'),
            'perlu': sum(1 for d in r_d if d['asset'].condition == 'perlu_perhatian'),
            'kritis': sum(1 for d in r_d if d['asset'].condition == 'kritis'),
            'tidak_layak': sum(1 for d in r_d if d['asset'].condition == 'tidak_layak'),
            'rpn_rendah': sum(1 for d in r_d if d['last_fmea'] and d['last_fmea'].risk_category == 'rendah'),
            'rpn_sedang': sum(1 for d in r_d if d['last_fmea'] and d['last_fmea'].risk_category == 'sedang'),
            'rpn_tinggi': sum(1 for d in r_d if d['last_fmea'] and d['last_fmea'].risk_category == 'tinggi'),
        })

    buf = generate_excel_divisi(asset_data, room_stats_sheet)
    nama_file = build_filename('laporan_divisi', 'all', 'xlsx')
    return send_file(buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, download_name=nama_file)


@divisi_bp.route('/reports/export-pdf')
@login_required
@role_required('admin_divisi')
def reports_export_pdf():
    room_ids = get_division_room_ids(current_user)
    room_filter = request.args.get('room', 0, type=int)
    kondisi_filter = request.args.get('kondisi', '')
    rpn_filter = request.args.get('rpn', '')

    if room_filter and room_filter not in room_ids:
        abort(403)

    asset_data, stats = _build_report_data(room_ids, room_filter, kondisi_filter, rpn_filter)
    room_name = ''
    if room_filter:
        r = Room.query.get(room_filter)
        room_name = r.room_name if r else ''

    html_str = render_template('divisi/reports/pdf_template.html',
        asset_data=asset_data, stats=stats,
        room_name=room_name, kondisi_filter=kondisi_filter, rpn_filter=rpn_filter,
        tanggal=datetime.now().strftime('%d %B %Y'),
    )
    pdf = generate_pdf(html_str)
    nama_file = build_filename('laporan_divisi', 'all', 'pdf')
    return send_file(io.BytesIO(pdf), mimetype='application/pdf',
        as_attachment=True, download_name=nama_file)


# ── Riwayat Maintenance ────────────────────────────────────────────────────────

@divisi_bp.route('/maintenance-logs')
@login_required
@role_required('admin_divisi')
def maintenance_logs():
    room_ids = get_division_room_ids(current_user)
    page = request.args.get('page', 1, type=int)
    room_filter = request.args.get('room', 0, type=int)
    action_filter = request.args.get('action', '')

    if room_filter and room_filter not in room_ids:
        abort(403)

    query = (
        MaintenanceLog.query
        .join(Asset, MaintenanceLog.asset_id == Asset.id)
        .filter(Asset.room_id.in_(room_ids))
    ) if room_ids else MaintenanceLog.query.filter_by(id=None)

    if room_filter:
        query = query.filter(Asset.room_id == room_filter)
    if action_filter:
        query = query.filter(MaintenanceLog.action_type == action_filter)

    logs = query.order_by(MaintenanceLog.created_at.desc()).paginate(page=page, per_page=20)
    rooms = get_division_rooms(current_user)

    user_ids = {l.logged_by for l in logs.items}
    users_map = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return render_template('divisi/maintenance_logs/index.html',
        logs=logs, rooms=rooms, users_map=users_map,
        room_filter=room_filter, action_filter=action_filter,
    )


# ── Anggota Divisi ─────────────────────────────────────────────────────────────

@divisi_bp.route('/members')
@login_required
@role_required('admin_divisi')
def members():
    rooms = get_division_rooms(current_user)
    division = current_user.division

    member_data = []
    total_assets_all = 0
    total_admin_ruangan = 0

    for room in rooms:
        assets = room.assets.all()
        total = len(assets)
        total_assets_all += total

        kritis = sum(1 for a in assets if a.condition in ['kritis', 'tidak_layak'])

        # RPN tertinggi di ruangan ini
        highest_rpn = None
        highest_rpn_cat = None
        for a in assets:
            last_f = a.fmea_records.order_by(FmeaRecord.created_at.desc()).first()
            if last_f and (highest_rpn is None or last_f.rpn_score > highest_rpn):
                highest_rpn = last_f.rpn_score
                highest_rpn_cat = last_f.risk_category

        # Admin Ruangan untuk ruangan ini
        admins = User.query.filter_by(
            room_id=room.id,
            role='admin_ruangan',
            is_active=True,
        ).all()
        total_admin_ruangan += len(admins)

        member_data.append({
            'room': room,
            'admins': admins,
            'total_assets': total,
            'kritis': kritis,
            'highest_rpn': highest_rpn,
            'highest_rpn_cat': highest_rpn_cat,
        })

    return render_template('divisi/members/index.html',
        division=division,
        member_data=member_data,
        total_rooms=len(rooms),
        total_admin_ruangan=total_admin_ruangan,
        total_assets_all=total_assets_all,
    )
