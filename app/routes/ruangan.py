from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, session
from flask_login import login_required, current_user
from app import db
from app.models.asset import Asset
from app.models.asset_category import AssetCategory
from app.models.fmea import FmeaRecord
from app.models.maintenance_log import MaintenanceLog
from app.models.preventive_maintenance import PreventiveMaintenance
from app.models.approval_request import ApprovalRequest
from app.models.user import User
from app.utils.decorators import role_required, check_room_ownership
from app.utils.helpers import generate_asset_code, generate_qr_code
from app.forms.asset_forms import CreateAssetForm, EditAssetForm, RequestChangeForm, RepairLogForm, PreventiveMaintenanceForm
from app.forms.fmea_forms import FmeaEvaluationForm
from app.forms.import_forms import PreventiveImportForm
from app.services.fmea_service import (
    calculate_rpn,
    update_asset_condition,
    sync_asset_condition_from_latest_fmea,
    should_notify,
    generate_recommendation,
)
from app.services.asset_health_service import (
    generate_ai_recommendation,
    infer_condition_from_text,
    recalculate_asset_condition_from_history,
)
from app.services.notif_service import notify_high_rpn, notify_medium_rpn, notify_new_approval_request
from app.services.export_service import generate_excel, generate_pdf, generate_kir_pdf, build_filename
from app.services.preventive_import_service import (
    build_preventive_preview,
    commit_preventive_import,
    pending_upload_path,
    remove_upload,
    store_upload,
)

ruangan_bp = Blueprint('ruangan', __name__, url_prefix='/ruangan')


def _default_asset_category():
    category = AssetCategory.query.filter_by(category_name='Umum').first()
    if category:
        return category

    category = AssetCategory(
        category_name='Umum',
        description='Kategori internal default untuk aset yang tidak diklasifikasikan di form input.',
    )
    db.session.add(category)
    db.session.flush()
    return category


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
    status_filter = request.args.get('status', '')

    query = Asset.query.filter_by(room_id=current_user.room_id)
    if kondisi_filter:
        query = query.filter_by(condition=kondisi_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    assets = query.order_by(Asset.created_at.desc()).paginate(page=page, per_page=10)

    return render_template('ruangan/assets/index.html',
        assets=assets,
        kondisi_filter=kondisi_filter,
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

    if form.validate_on_submit():
        category = _default_asset_category()
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
            item_code=form.item_code.data,
            asset_name=form.asset_name.data,
            specification=form.specification.data,
            category=category,
            room_id=current_user.room_id,
            brand=form.brand_model.data,
            model='',
            serial_number=form.serial_number.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            purchase_date=form.purchase_date.data,
            purchase_price=form.purchase_price.data,
            acquisition_document_number=form.acquisition_document_number.data,
            funding_source=form.funding_source.data,
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
    maintenance_terakhir = (asset.maintenance_logs
        .order_by(MaintenanceLog.action_date.desc(), MaintenanceLog.created_at.desc())
        .first())
    preventive_terbaru = (asset.preventive_records
        .order_by(PreventiveMaintenance.check_date.desc(), PreventiveMaintenance.created_at.desc())
        .limit(5).all())
    preventive_terakhir = preventive_terbaru[0] if preventive_terbaru else None
    ai_rekomendasi = None
    if maintenance_terakhir and maintenance_terakhir.ai_recommendation:
        ai_rekomendasi = maintenance_terakhir.ai_recommendation
    if preventive_terakhir and preventive_terakhir.ai_recommendation:
        ai_rekomendasi = preventive_terakhir.ai_recommendation
    if fmea_terakhir and fmea_terakhir.recommendation and 'AI rekomendasi awal:' in fmea_terakhir.recommendation:
        ai_rekomendasi = fmea_terakhir.recommendation.split('AI rekomendasi awal:', 1)[1].strip()
        ai_rekomendasi = f'AI rekomendasi awal: {ai_rekomendasi}'
    return render_template('ruangan/assets/detail.html',
        asset=asset, fmea_terbaru=fmea_terbaru, fmea_terakhir=fmea_terakhir,
        preventive_terbaru=preventive_terbaru, preventive_terakhir=preventive_terakhir,
        maintenance_terakhir=maintenance_terakhir, ai_rekomendasi=ai_rekomendasi)


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

    if form.validate_on_submit():
        asset.asset_name = form.asset_name.data
        asset.item_code = form.item_code.data
        asset.specification = form.specification.data
        asset.brand_model = form.brand_model.data
        asset.serial_number = form.serial_number.data
        asset.quantity = form.quantity.data
        asset.unit = form.unit.data
        asset.purchase_date = form.purchase_date.data
        asset.purchase_price = form.purchase_price.data
        asset.acquisition_document_number = form.acquisition_document_number.data
        asset.funding_source = form.funding_source.data
        asset.condition = form.condition.data
        asset.notes = form.notes.data

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
        # Deskripsi tetap ringkas untuk daftar, detail lengkap disimpan di kolom terstruktur.
        deskripsi = form.description.data
        detail_parts = []
        if form.complaint.data:
            detail_parts.append(f'Keluhan: {form.complaint.data}')
        if form.result.data:
            detail_parts.append(f'Hasil: {form.result.data}')
        if form.recommendation.data:
            detail_parts.append(f'Saran: {form.recommendation.data}')
        if detail_parts:
            deskripsi += ' — ' + ' | '.join(detail_parts)
        if form.technician_name.data:
            deskripsi += f' (Teknisi: {form.technician_name.data})'
        if form.notes.data:
            deskripsi += f' — Catatan: {form.notes.data}'

        condition_after = form.new_condition.data or infer_condition_from_text(
            form.complaint.data,
            form.result.data,
            form.recommendation.data,
            deskripsi,
        )

        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type=form.action_type.data,
            description=deskripsi,
            reporter_unit=form.reporter_unit.data,
            reporter_name=form.reporter_name.data,
            reporter_position=form.reporter_position.data,
            complaint=form.complaint.data,
            inspection_unit='IPSRS',
            technician_name=form.technician_name.data,
            technician_position=form.technician_position.data,
            result=form.result.data,
            recommendation=form.recommendation.data,
            condition_after=condition_after,
            action_date=form.action_date.data,
        )
        db.session.add(log)

        # Selalu catat tanggal maintenance terakhir saat ada tindakan
        action_types_maintenance = {'perbaikan', 'penggantian', 'pemeriksaan_rutin'}
        if form.action_type.data in action_types_maintenance:
            asset.last_maintenance_date = form.action_date.data

        # Update jadwal maintenance berikutnya jika diisi
        if form.next_maintenance_date.data:
            asset.next_maintenance_date = form.next_maintenance_date.data

        recalculate_asset_condition_from_history(asset)
        log.ai_recommendation = generate_ai_recommendation(asset, maintenance_log=log)
        db.session.commit()
        flash('Catatan perbaikan berhasil disimpan.', 'success')
        return redirect(url_for('ruangan.assets_detail', id=id))

    return render_template('ruangan/assets/repair.html',
        form=form, asset=asset, fmea_terakhir=fmea_terakhir)


@ruangan_bp.route('/assets/<int:id>/preventive', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def assets_preventive(id):
    """Form dan simpan hasil preventive maintenance per aset."""
    asset = Asset.query.get_or_404(id)
    form = PreventiveMaintenanceForm()

    if request.method == 'GET':
        form.check_date.data = date.today()
        form.condition_after.data = ''
        if asset.next_maintenance_date:
            form.next_maintenance_date.data = asset.next_maintenance_date

    if form.validate_on_submit():
        condition_after = form.condition_after.data or infer_condition_from_text(
            form.result.data,
            form.notes.data,
            form.recommendation.data,
        )

        preventive = PreventiveMaintenance(
            asset_id=asset.id,
            checked_by=current_user.id,
            check_date=form.check_date.data,
            room_name_snapshot=asset.room.room_name,
            result=form.result.data,
            notes=form.notes.data,
            recommendation=form.recommendation.data,
            condition_after=condition_after,
        )
        db.session.add(preventive)

        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='preventive_check',
            description=f'Preventive maintenance: {form.result.data}',
            result=form.result.data,
            recommendation=form.recommendation.data,
            condition_after=condition_after,
            action_date=form.check_date.data,
        )
        db.session.add(log)

        asset.last_maintenance_date = form.check_date.data
        if form.next_maintenance_date.data:
            asset.next_maintenance_date = form.next_maintenance_date.data
        recalculate_asset_condition_from_history(asset)
        preventive.ai_recommendation = generate_ai_recommendation(asset, preventive=preventive)
        log.ai_recommendation = preventive.ai_recommendation

        db.session.commit()
        flash('Hasil preventive maintenance berhasil disimpan.', 'success')
        return redirect(url_for('ruangan.assets_detail', id=asset.id))

    return render_template('ruangan/assets/preventive.html', form=form, asset=asset)


@ruangan_bp.route('/preventive')
@login_required
@role_required('admin_ruangan')
def preventive_index():
    asset_ids = [a.id for a in Asset.query.filter_by(room_id=current_user.room_id).all()]
    page = request.args.get('page', 1, type=int)
    if asset_ids:
        records = (PreventiveMaintenance.query
            .filter(PreventiveMaintenance.asset_id.in_(asset_ids))
            .order_by(PreventiveMaintenance.check_date.desc(), PreventiveMaintenance.created_at.desc())
            .paginate(page=page, per_page=15))
    else:
        records = PreventiveMaintenance.query.filter(db.false()).paginate(page=1, per_page=15)
    return render_template(
        'shared/preventive/index.html',
        base_template='layouts/base_ruangan.html',
        records=records,
        scope_label=current_user.room.room_name if current_user.room else 'Ruangan',
        detail_endpoint='ruangan.assets_detail',
        import_endpoint='ruangan.preventive_import',
    )


@ruangan_bp.route('/preventive/import', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
def preventive_import():
    form = PreventiveImportForm()
    room_ids = [current_user.room_id] if current_user.room_id else []
    token = session.get('preventive_import_token')

    if request.method == 'POST' and request.form.get('action') == 'commit':
        if not form.validate_on_submit():
            flash('Permintaan konfirmasi import tidak valid. Silakan ulangi preview.', 'danger')
            return redirect(url_for('ruangan.preventive_import'))
        path = pending_upload_path(token)
        if not path:
            session.pop('preventive_import_token', None)
            flash('Preview import sudah kedaluwarsa. Silakan upload ulang.', 'warning')
            return redirect(url_for('ruangan.preventive_import'))
        try:
            result = commit_preventive_import(path, current_user, allowed_room_ids=room_ids)
            remove_upload(token)
            session.pop('preventive_import_token', None)
            flash(
                f'Import preventive berhasil: {result.preventive_created} pemeriksaan, '
                f'{result.assets_created} aset baru, {result.assets_updated} aset dilengkapi.',
                'success',
            )
            return redirect(url_for('ruangan.preventive_index'))
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect(url_for('ruangan.preventive_import'))

    if form.validate_on_submit():
        if not form.file.data or not form.file.data.filename:
            form.file.errors.append('File Excel wajib dipilih.')
        else:
            if token:
                remove_upload(token)
            token = store_upload(form.file.data)
            session['preventive_import_token'] = token
            preview = build_preventive_preview(
                pending_upload_path(token),
                allowed_room_ids=room_ids,
            )
            return render_template(
                'shared/preventive/import.html',
                base_template='layouts/base_ruangan.html',
                form=form,
                preview=preview,
                import_endpoint='ruangan.preventive_import',
                index_endpoint='ruangan.preventive_index',
            )

    preview = None
    if token and pending_upload_path(token):
        preview = build_preventive_preview(
            pending_upload_path(token),
            allowed_room_ids=room_ids,
        )
    return render_template(
        'shared/preventive/import.html',
        base_template='layouts/base_ruangan.html',
        form=form,
        preview=preview,
        import_endpoint='ruangan.preventive_import',
        index_endpoint='ruangan.preventive_index',
    )


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
        recalculate_asset_condition_from_history(asset)
        record.recommendation = (
            f'{record.recommendation}\n\n'
            f'{generate_ai_recommendation(asset, fmea=record)}'
        )

        # Catat ke maintenance log
        log = MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='evaluasi_fmea',
            description=f'Evaluasi FMEA: RPN={hasil["rpn_score"]} ({hasil["risk_category"].upper()}). Mode: {form.failure_mode.data}',
            ai_recommendation=generate_ai_recommendation(asset, fmea=record),
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

    return render_template('ruangan/fmea/form.html',
        form=form,
        asset=asset,
        form_action=url_for('ruangan.fmea_form', id=asset.id),
        page_title='Evaluasi FMEA',
        submit_label='Simpan Evaluasi',
    )


@ruangan_bp.route('/assets/<int:id>/fmea/<int:fmea_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def fmea_edit(id, fmea_id):
    asset = Asset.query.get_or_404(id)
    record = FmeaRecord.query.filter_by(id=fmea_id, asset_id=asset.id).first_or_404()
    form = FmeaEvaluationForm(obj=record)

    if form.validate_on_submit():
        hasil = calculate_rpn(form.severity.data, form.occurrence.data, form.detection.data)

        record.failure_mode = form.failure_mode.data
        record.failure_effect = form.failure_effect.data
        record.severity = form.severity.data
        record.occurrence = form.occurrence.data
        record.detection = form.detection.data
        record.rpn_score = hasil['rpn_score']
        record.risk_category = hasil['risk_category']
        record.recommendation = generate_recommendation(hasil['rpn_score'])
        record.evaluation_date = form.evaluation_date.data
        record.notes = form.notes.data

        sync_asset_condition_from_latest_fmea(asset)
        record.recommendation = (
            f'{record.recommendation}\n\n'
            f'{generate_ai_recommendation(asset, fmea=record)}'
        )

        db.session.add(MaintenanceLog(
            asset_id=asset.id,
            logged_by=current_user.id,
            action_type='evaluasi_fmea',
            description=f'FMEA diperbarui: RPN={hasil["rpn_score"]} ({hasil["risk_category"].upper()}). Mode: {form.failure_mode.data}',
            action_date=date.today(),
        ))
        db.session.commit()
        flash(f'FMEA berhasil diperbarui. RPN={hasil["rpn_score"]} ({hasil["risk_category"].upper()}).', 'success')
        return redirect(url_for('ruangan.fmea_history', id=asset.id))

    return render_template('ruangan/fmea/form.html',
        form=form,
        asset=asset,
        record=record,
        form_action=url_for('ruangan.fmea_edit', id=asset.id, fmea_id=record.id),
        page_title='Edit Evaluasi FMEA',
        submit_label='Simpan Perubahan',
    )


@ruangan_bp.route('/assets/<int:id>/fmea/<int:fmea_id>/delete', methods=['POST'])
@login_required
@role_required('admin_ruangan')
@check_room_ownership
def fmea_delete(id, fmea_id):
    asset = Asset.query.get_or_404(id)
    record = FmeaRecord.query.filter_by(id=fmea_id, asset_id=asset.id).first_or_404()
    old_rpn = record.rpn_score
    old_mode = record.failure_mode

    db.session.delete(record)
    db.session.flush()
    sync_asset_condition_from_latest_fmea(asset)

    db.session.add(MaintenanceLog(
        asset_id=asset.id,
        logged_by=current_user.id,
        action_type='evaluasi_fmea',
        description=f'FMEA dihapus: RPN={old_rpn}. Mode: {old_mode}',
        action_date=date.today(),
    ))
    db.session.commit()
    flash('Evaluasi FMEA berhasil dihapus dan kondisi aset sudah diperbarui.', 'success')
    return redirect(url_for('ruangan.fmea_history', id=asset.id))


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
