from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app import db
from app.models.asset import Asset
from app.models.asset_category import AssetCategory
from app.models.fmea import FmeaRecord
from app.models.maintenance_log import MaintenanceLog
from app.models.approval_request import ApprovalRequest
from app.models.user import User
from app.utils.decorators import role_required, check_room_ownership
from app.utils.helpers import generate_asset_code, generate_qr_code
from app.forms.asset_forms import CreateAssetForm, EditAssetForm, RequestChangeForm, RepairLogForm
from app.forms.fmea_forms import FmeaEvaluationForm
from app.services.fmea_service import calculate_rpn, update_asset_condition, should_notify, generate_recommendation
from app.services.notif_service import notify_high_rpn, notify_medium_rpn, notify_new_approval_request
from app.services.export_service import generate_excel, generate_pdf, generate_kir_pdf, build_filename

ruangan_bp = Blueprint('ruangan', __name__, url_prefix='/ruangan')


def _category_choices():
    cats = AssetCategory.query.order_by(AssetCategory.category_name).all()
    return [(c.id, c.category_name) for c in cats]


# ── Dashboard ──────────────────────────────────────────────────────────────────

@ruangan_bp.route('/dashboard')
@login_required
@role_required('admin_ruangan')
def dashboard():
    room_id = current_user.room_id
    total = Asset.query.filter_by(room_id=room_id).count()
    baik = Asset.query.filter_by(room_id=room_id, condition='baik').count()
    perlu = Asset.query.filter_by(room_id=room_id, condition='perlu_perhatian').count()
    kritis = Asset.query.filter_by(room_id=room_id, condition='kritis').count()
    tidak_layak = Asset.query.filter_by(room_id=room_id, condition='tidak_layak').count()

    asset_ids = [a.id for a in Asset.query.filter_by(room_id=room_id).all()]
    fmea_terbaru = (FmeaRecord.query
        .filter(FmeaRecord.asset_id.in_(asset_ids))
        .order_by(FmeaRecord.created_at.desc())
        .limit(5).all()) if asset_ids else []

    ada_rpn_tinggi = (FmeaRecord.query
        .filter(FmeaRecord.asset_id.in_(asset_ids), FmeaRecord.risk_category == 'tinggi')
        .count() > 0) if asset_ids else False

    return render_template('ruangan/dashboard.html',
        total=total, baik=baik, perlu=perlu, kritis=kritis,
        tidak_layak=tidak_layak, fmea_terbaru=fmea_terbaru,
        ada_rpn_tinggi=ada_rpn_tinggi,
    )


# ── Daftar & CRUD Aset ─────────────────────────────────────────────────────────

@ruangan_bp.route('/assets')
@login_required
@role_required('admin_ruangan')
def assets_index():
    page = request.args.get('page', 1, type=int)
    kondisi_filter = request.args.get('kondisi', '')
    kategori_filter = request.args.get('kategori', 0, type=int)
    status_filter = request.args.get('status', '')

    query = Asset.query.filter_by(room_id=current_user.room_id)
    if kondisi_filter:
        query = query.filter_by(condition=kondisi_filter)
    if kategori_filter:
        query = query.filter_by(category_id=kategori_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    assets = query.order_by(Asset.created_at.desc()).paginate(page=page, per_page=10)
    categories = AssetCategory.query.order_by(AssetCategory.category_name).all()

    return render_template('ruangan/assets/index.html',
        assets=assets, categories=categories,
        kondisi_filter=kondisi_filter,
        kategori_filter=kategori_filter,
        status_filter=status_filter,
    )


@ruangan_bp.route('/assets/create', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
def assets_create():
    # Guard: admin_ruangan harus sudah dikaitkan ke ruangan
    if not current_user.room:
        flash('Akun Anda belum dikaitkan ke ruangan. Hubungi Super Admin.', 'danger')
        return redirect(url_for('ruangan.dashboard'))

    form = CreateAssetForm()
    form.category_id.choices = _category_choices()

    if form.validate_on_submit():
        # Generate kode aset — gunakan MAX sequence agar aman dari race condition
        from sqlalchemy import func
        last_code = (db.session.query(func.max(Asset.asset_code))
                     .filter(Asset.room_id == current_user.room_id)
                     .scalar())
        if last_code:
            try:
                last_seq = int(last_code.rsplit('-', 1)[-1])
            except (ValueError, IndexError):
                last_seq = Asset.query.filter_by(room_id=current_user.room_id).count()
        else:
            last_seq = 0
        kode = generate_asset_code(current_user.room.room_code, last_seq + 1)

        asset = Asset(
            asset_code=kode,
            asset_name=form.asset_name.data,
            category_id=form.category_id.data,
            room_id=current_user.room_id,
            brand=form.brand.data,
            model=form.model.data,
            serial_number=form.serial_number.data,
            purchase_date=form.purchase_date.data,
            purchase_price=form.purchase_price.data,
            condition=form.condition.data,
            status='aktif',
            notes=form.notes.data,
            created_by=current_user.id,
        )
        db.session.add(asset)
        db.session.flush()

        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='pemeriksaan_rutin',
            description='Aset baru ditambahkan ke sistem.',
            action_date=date.today(),
        )
        db.session.add(log)
        db.session.commit()
        flash(f'Aset "{asset.asset_name}" berhasil ditambahkan dengan kode {kode}.', 'success')
        return redirect(url_for('ruangan.assets_index'))

    return render_template('ruangan/assets/create.html', form=form)


@ruangan_bp.route('/assets/<int:id>')
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def assets_detail(id):
    asset = Asset.query.get_or_404(id)
    fmea_terbaru = (asset.fmea_records
        .order_by(FmeaRecord.created_at.desc()).limit(5).all())
    fmea_terakhir = asset.fmea_records.order_by(FmeaRecord.created_at.desc()).first()
    return render_template('ruangan/assets/detail.html',
        asset=asset, fmea_terbaru=fmea_terbaru, fmea_terakhir=fmea_terakhir)


@ruangan_bp.route('/assets/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def assets_edit(id):
    asset = Asset.query.get_or_404(id)

    if asset.status == 'menunggu_approval':
        flash('Aset tidak dapat diedit karena sedang menunggu approval.', 'warning')
        return redirect(url_for('ruangan.assets_detail', id=id))

    form = EditAssetForm(obj=asset)
    form.category_id.choices = _category_choices()

    if form.validate_on_submit():
        form.populate_obj(asset)
        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='pemeriksaan_rutin',
            description='Data aset diperbarui oleh Admin Ruangan.',
            action_date=date.today(),
        )
        db.session.add(log)
        db.session.commit()
        flash(f'Aset "{asset.asset_name}" berhasil diperbarui.', 'success')
        return redirect(url_for('ruangan.assets_detail', id=id))

    return render_template('ruangan/assets/edit.html', form=form, asset=asset)


@ruangan_bp.route('/assets/<int:id>/request-change', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def assets_request_change(id):
    asset = Asset.query.get_or_404(id)
    form = RequestChangeForm()

    # Guard: aset tidak boleh dalam status menunggu_approval
    if asset.status == 'menunggu_approval':
        flash('Sudah ada pengajuan yang sedang menunggu persetujuan untuk aset ini.', 'warning')
        return redirect(url_for('ruangan.assets_detail', id=id))

    # Guard: tidak boleh ada pending request lain untuk aset yang sama
    existing_pending = ApprovalRequest.query.filter_by(
        asset_id=asset.id, approval_status='pending'
    ).first()
    if existing_pending:
        flash('Sudah ada pengajuan pending untuk aset ini. Tunggu hingga diproses.', 'warning')
        return redirect(url_for('ruangan.assets_detail', id=id))

    # Guard: status yang diajukan harus berbeda dari status saat ini
    valid_statuses = {'aktif', 'dalam_perbaikan', 'tidak_aktif'}
    if asset.status not in valid_statuses:
        flash('Status aset saat ini tidak memungkinkan pengajuan perubahan.', 'danger')
        return redirect(url_for('ruangan.assets_detail', id=id))

    if form.validate_on_submit():
        # Snapshot status saat ini (sebelum diubah)
        status_sebelum = asset.status

        req = ApprovalRequest(
            asset_id=asset.id,
            requested_by=current_user.id,
            current_status=status_sebelum,
            requested_status=form.requested_status.data,
            reason=form.reason.data,
            approval_status='pending',
        )
        db.session.add(req)
        asset.status = 'menunggu_approval'

        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='pengajuan_status',
            description=f'Pengajuan perubahan status dari "{status_sebelum}" ke "{form.requested_status.data}". Alasan: {form.reason.data}',
            action_date=date.today(),
        )
        db.session.add(log)
        db.session.commit()

        try:
            notify_new_approval_request(req)
        except Exception:
            pass  # Notifikasi gagal tidak boleh rollback pengajuan yang sudah tersimpan

        flash('Pengajuan perubahan status berhasil dikirim ke Admin Divisi.', 'success')
        return redirect(url_for('ruangan.assets_detail', id=id))

    return render_template('ruangan/assets/request_change.html', form=form, asset=asset)


# ── KIR ───────────────────────────────────────────────────────────────────────

@ruangan_bp.route('/assets/<int:id>/kir')
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def assets_kir(id):
    """Download PDF Kartu KIR aset."""
    asset = Asset.query.get_or_404(id)
    base_url = request.host_url.rstrip('/')

    pdf_bytes = generate_kir_pdf(asset, current_user.name, base_url)

    # Catat ke maintenance_log
    log = MaintenanceLog(
        asset_id=asset.id,
        logged_by=current_user.id,
        action_type='cetak_kir',
        description=f'KIR dicetak oleh {current_user.name}',
        action_date=date.today(),
    )
    db.session.add(log)
    db.session.commit()

    import io
    filename = f"KIR_{asset.asset_code}_{date.today().strftime('%Y%m%d')}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )


# ── QR Code ────────────────────────────────────────────────────────────────────

@ruangan_bp.route('/assets/<int:id>/qr-code')
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def assets_qr_code(id):
    """Download PNG QR Code aset."""
    asset = Asset.query.get_or_404(id)
    base_url = request.host_url.rstrip('/')
    qr_path = generate_qr_code(asset.id, base_url)
    filename = f"QR_{asset.asset_code}.png"
    return send_file(qr_path, mimetype='image/png', as_attachment=True, download_name=filename)


# ── Catat Perbaikan ────────────────────────────────────────────────────────────

@ruangan_bp.route('/assets/<int:id>/repair', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def assets_repair(id):
    """Form dan simpan catatan perbaikan manual aset."""
    asset = Asset.query.get_or_404(id)

    if asset.status == 'menunggu_approval':
        flash('Aset sedang menunggu persetujuan. Tidak dapat mencatat perbaikan saat ini.', 'warning')
        return redirect(url_for('ruangan.assets_detail', id=id))

    fmea_terakhir = asset.fmea_records.order_by(FmeaRecord.created_at.desc()).first()

    form = RepairLogForm()
    if request.method == 'GET':
        form.action_date.data = date.today()
        form.new_condition.data = ''
        if asset.next_maintenance_date:
            form.next_maintenance_date.data = asset.next_maintenance_date

    if form.validate_on_submit():
        # Deskripsi gabungkan teknisi jika ada
        deskripsi = form.description.data
        if form.technician_name.data:
            deskripsi += f' (Teknisi: {form.technician_name.data})'
        if form.notes.data:
            deskripsi += f' — Catatan: {form.notes.data}'

        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type=form.action_type.data,
            description=deskripsi,
            action_date=form.action_date.data,
        )
        db.session.add(log)

        # Update kondisi aset jika diisi
        if form.new_condition.data:
            asset.condition = form.new_condition.data

        # Selalu catat tanggal maintenance terakhir saat ada tindakan
        action_types_maintenance = {'perbaikan', 'penggantian', 'pemeriksaan_rutin'}
        if form.action_type.data in action_types_maintenance:
            asset.last_maintenance_date = form.action_date.data

        # Update jadwal maintenance berikutnya jika diisi
        if form.next_maintenance_date.data:
            asset.next_maintenance_date = form.next_maintenance_date.data

        db.session.commit()
        flash('Catatan perbaikan berhasil disimpan.', 'success')
        return redirect(url_for('ruangan.assets_detail', id=id))

    return render_template('ruangan/assets/repair.html',
        form=form, asset=asset, fmea_terakhir=fmea_terakhir)


# ── FMEA ───────────────────────────────────────────────────────────────────────

@ruangan_bp.route('/assets/<int:id>/fmea', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def fmea_form(id):
    asset = Asset.query.get_or_404(id)
    form = FmeaEvaluationForm()

    if form.validate_on_submit():
        hasil = calculate_rpn(form.severity.data, form.occurrence.data, form.detection.data)
        rekomendasi = generate_recommendation(hasil['rpn_score'])

        record = FmeaRecord(
            asset_id=asset.id,
            evaluated_by=current_user.id,
            failure_mode=form.failure_mode.data,
            failure_effect=form.failure_effect.data,
            severity=form.severity.data,
            occurrence=form.occurrence.data,
            detection=form.detection.data,
            rpn_score=hasil['rpn_score'],
            risk_category=hasil['risk_category'],
            recommendation=rekomendasi,
            evaluation_date=form.evaluation_date.data,
            notes=form.notes.data,
        )
        db.session.add(record)

        # Update kondisi aset
        update_asset_condition(asset, hasil['rpn_score'])

        # Catat ke maintenance log
        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='evaluasi_fmea',
            description=f'Evaluasi FMEA: RPN={hasil["rpn_score"]} ({hasil["risk_category"].upper()}). Mode: {form.failure_mode.data}',
            action_date=date.today(),
        )
        db.session.add(log)
        db.session.commit()

        # Kirim notifikasi (try/except agar kegagalan notif tidak rollback data FMEA)
        try:
            if should_notify(hasil['rpn_score']):
                notify_high_rpn(asset, hasil['rpn_score'])
                flash(f'FMEA disimpan. RPN={hasil["rpn_score"]} (TINGGI) — notifikasi dikirim ke Admin Divisi.', 'danger')
            elif hasil['risk_category'] == 'sedang':
                notify_medium_rpn(asset, hasil['rpn_score'], current_user)
                flash(f'FMEA disimpan. RPN={hasil["rpn_score"]} (SEDANG) — jadwalkan pemeriksaan segera.', 'warning')
            else:
                flash(f'FMEA disimpan. RPN={hasil["rpn_score"]} (RENDAH).', 'success')
        except Exception:
            flash(f'FMEA disimpan. RPN={hasil["rpn_score"]} ({hasil["risk_category"].upper()}). Notifikasi gagal dikirim.', 'warning')

        return redirect(url_for('ruangan.assets_detail', id=id))

    return render_template('ruangan/fmea/form.html', form=form, asset=asset)


@ruangan_bp.route('/assets/<int:id>/fmea/history')
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def fmea_history(id):
    asset = Asset.query.get_or_404(id)
    records = asset.fmea_records.order_by(FmeaRecord.created_at.desc()).all()
    return render_template('ruangan/fmea/history.html', asset=asset, records=records)


# ── Laporan ────────────────────────────────────────────────────────────────────

@ruangan_bp.route('/reports')
@login_required
@role_required('admin_ruangan')
def reports_index():
    kondisi_filter = request.args.get('kondisi', '')
    rpn_filter = request.args.get('rpn', '')

    query = Asset.query.filter_by(room_id=current_user.room_id)
    if kondisi_filter:
        query = query.filter_by(condition=kondisi_filter)

    assets = query.order_by(Asset.asset_name).all()

    # Statistik
    stats = {
        'total': len(assets),
        'baik': sum(1 for a in assets if a.condition == 'baik'),
        'perlu_perhatian': sum(1 for a in assets if a.condition == 'perlu_perhatian'),
        'kritis': sum(1 for a in assets if a.condition == 'kritis'),
        'tidak_layak': sum(1 for a in assets if a.condition == 'tidak_layak'),
    }

    # RPN terakhir per aset
    asset_data = []
    for a in assets:
        last_fmea = a.fmea_records.order_by(FmeaRecord.created_at.desc()).first()
        if rpn_filter and last_fmea:
            if last_fmea.risk_category != rpn_filter:
                continue
        elif rpn_filter and not last_fmea:
            continue
        asset_data.append({'asset': a, 'last_fmea': last_fmea})

    return render_template('ruangan/reports/index.html',
        asset_data=asset_data, stats=stats,
        kondisi_filter=kondisi_filter, rpn_filter=rpn_filter,
    )


@ruangan_bp.route('/reports/export-excel')
@login_required
@role_required('admin_ruangan')
def reports_export_excel():
    # Terapkan filter yang sama dengan reports_index agar ekspor sesuai tampilan
    kondisi_filter = request.args.get('kondisi', '')
    rpn_filter = request.args.get('rpn', '')

    query = Asset.query.filter_by(room_id=current_user.room_id)
    if kondisi_filter:
        query = query.filter_by(condition=kondisi_filter)
    assets = query.order_by(Asset.asset_name).all()

    asset_data = []
    for a in assets:
        last_fmea = a.fmea_records.order_by(FmeaRecord.created_at.desc()).first()
        if rpn_filter and last_fmea:
            if last_fmea.risk_category != rpn_filter:
                continue
        elif rpn_filter and not last_fmea:
            continue
        asset_data.append({'asset': a, 'last_fmea': last_fmea})

    buf = generate_excel(asset_data, current_user.room.room_name, current_user.room.room_code)
    nama_file = build_filename('laporan_aset', current_user.room.room_code, 'xlsx')
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=nama_file)


@ruangan_bp.route('/reports/export-pdf')
@login_required
@role_required('admin_ruangan')
def reports_export_pdf():
    import io
    # Terapkan filter yang sama dengan reports_index agar ekspor sesuai tampilan
    kondisi_filter = request.args.get('kondisi', '')
    rpn_filter = request.args.get('rpn', '')

    query = Asset.query.filter_by(room_id=current_user.room_id)
    if kondisi_filter:
        query = query.filter_by(condition=kondisi_filter)
    assets = query.order_by(Asset.asset_name).all()

    asset_data = []
    for a in assets:
        last_fmea = a.fmea_records.order_by(FmeaRecord.created_at.desc()).first()
        if rpn_filter and last_fmea:
            if last_fmea.risk_category != rpn_filter:
                continue
        elif rpn_filter and not last_fmea:
            continue
        asset_data.append({'asset': a, 'last_fmea': last_fmea})

    html_str = render_template('ruangan/reports/pdf_template.html',
        asset_data=asset_data, room=current_user.room,
        tanggal=datetime.now().strftime('%d %B %Y'),
    )
    pdf = generate_pdf(html_str)
    nama_file = build_filename('laporan_aset', current_user.room.room_code, 'pdf')
    return send_file(io.BytesIO(pdf), mimetype='application/pdf',
                     as_attachment=True, download_name=nama_file)


# ── Riwayat Maintenance ────────────────────────────────────────────────────────

@ruangan_bp.route('/maintenance-logs')
@login_required
@role_required('admin_ruangan')
def maintenance_logs():
    asset_ids = [a.id for a in Asset.query.filter_by(room_id=current_user.room_id).all()]
    page = request.args.get('page', 1, type=int)
    if asset_ids:
        logs = (MaintenanceLog.query
            .filter(MaintenanceLog.asset_id.in_(asset_ids))
            .order_by(MaintenanceLog.created_at.desc())
            .paginate(page=page, per_page=15))
    else:
        # Kembalikan objek paginate kosong agar template tidak crash
        logs = MaintenanceLog.query.filter(db.false()).paginate(page=1, per_page=15)
    return render_template('ruangan/maintenance_logs.html', logs=logs)


