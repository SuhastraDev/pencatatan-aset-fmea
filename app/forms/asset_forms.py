from datetime import date
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SelectField, TextAreaField, DateField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError


class CreateAssetForm(FlaskForm):
    asset_name = StringField('Nama Aset', validators=[DataRequired(), Length(max=150)])
    item_code = StringField('Kode Barang', validators=[Optional(), Length(max=100)])
    specification = TextAreaField('Spesifikasi Nama Barang', validators=[Optional()])
    brand_model = StringField('Merk / Model', validators=[DataRequired(), Length(max=100)])
    serial_number = StringField('No Seri', validators=[DataRequired(), Length(max=100)])
    quantity = IntegerField('Jumlah Barang', validators=[DataRequired(), NumberRange(min=1, message='Jumlah minimal 1.')], default=1)
    unit = StringField('Satuan Barang', validators=[Optional(), Length(max=50)])
    purchase_date = DateField('Tanggal Pembelian', validators=[Optional()])
    purchase_price = DecimalField('Harga Pembelian (Rp)', validators=[Optional(), NumberRange(min=0, message='Harga tidak boleh negatif.')], places=2)
    acquisition_document_number = StringField('Nomor Dokumen/BAST', validators=[Optional(), Length(max=150)])
    funding_source = StringField('Sumber Dana', validators=[Optional(), Length(max=100)])
    condition = SelectField('Kondisi', choices=[
        ('baik', 'Baik'),
        ('perlu_perhatian', 'Perlu Perhatian'),
        ('kritis', 'Kritis'),
        ('tidak_layak', 'Tidak Layak'),
    ], validators=[DataRequired()])
    notes = TextAreaField('Catatan', validators=[Optional()])
    submit = SubmitField('Simpan')


class EditAssetForm(FlaskForm):
    asset_name = StringField('Nama Aset', validators=[DataRequired(), Length(max=150)])
    item_code = StringField('Kode Barang', validators=[Optional(), Length(max=100)])
    specification = TextAreaField('Spesifikasi Nama Barang', validators=[Optional()])
    brand_model = StringField('Merk / Model', validators=[DataRequired(), Length(max=100)])
    serial_number = StringField('No Seri', validators=[DataRequired(), Length(max=100)])
    quantity = IntegerField('Jumlah Barang', validators=[DataRequired(), NumberRange(min=1, message='Jumlah minimal 1.')], default=1)
    unit = StringField('Satuan Barang', validators=[Optional(), Length(max=50)])
    purchase_date = DateField('Tanggal Pembelian', validators=[Optional()])
    purchase_price = DecimalField('Harga Pembelian (Rp)', validators=[Optional(), NumberRange(min=0, message='Harga tidak boleh negatif.')], places=2)
    acquisition_document_number = StringField('Nomor Dokumen/BAST', validators=[Optional(), Length(max=150)])
    funding_source = StringField('Sumber Dana', validators=[Optional(), Length(max=100)])
    condition = SelectField('Kondisi', choices=[
        ('baik', 'Baik'),
        ('perlu_perhatian', 'Perlu Perhatian'),
        ('kritis', 'Kritis'),
        ('tidak_layak', 'Tidak Layak'),
    ], validators=[DataRequired()])
    notes = TextAreaField('Catatan', validators=[Optional()])
    submit = SubmitField('Simpan Perubahan')


class RequestChangeForm(FlaskForm):
    requested_status = SelectField('Status yang Diajukan', choices=[
        ('aktif', 'Aktif'),
        ('dalam_perbaikan', 'Dalam Perbaikan'),
        ('tidak_aktif', 'Tidak Aktif'),
    ], validators=[DataRequired()])
    reason = TextAreaField('Alasan Pengajuan', validators=[
        DataRequired(),
        Length(min=20, message='Alasan minimal 20 karakter.')
    ])
    submit = SubmitField('Kirim Pengajuan')


class RepairLogForm(FlaskForm):
    action_type = SelectField('Jenis Tindakan', choices=[
        ('perbaikan', 'Perbaikan'),
        ('penggantian', 'Penggantian Komponen'),
        ('pemeriksaan_rutin', 'Pemeriksaan Rutin'),
    ], validators=[DataRequired()])
    description = TextAreaField('Deskripsi Tindakan', validators=[
        DataRequired(),
        Length(min=20, message='Deskripsi minimal 20 karakter.')
    ])
    technician_name = StringField('Nama Teknisi', validators=[Optional(), Length(max=100)])
    technician_position = StringField('Jabatan Teknisi', validators=[Optional(), Length(max=100)])
    reporter_unit = StringField('Instalasi/Unit Pelapor', validators=[Optional(), Length(max=100)])
    reporter_name = StringField('Nama Pelapor', validators=[Optional(), Length(max=100)])
    reporter_position = StringField('Jabatan Pelapor', validators=[Optional(), Length(max=100)])
    complaint = TextAreaField('Keluhan', validators=[Optional()])
    result = TextAreaField('Hasil Peninjauan', validators=[Optional()])
    recommendation = TextAreaField('Kesimpulan/Saran', validators=[Optional()])
    action_date = DateField('Tanggal Tindakan', validators=[DataRequired()])
    new_condition = SelectField('Kondisi Aset Setelah Tindakan', choices=[
        ('', '— Tidak Diubah —'),
        ('baik', 'Baik'),
        ('perlu_perhatian', 'Perlu Perhatian'),
        ('kritis', 'Kritis'),
        ('tidak_layak', 'Tidak Layak'),
    ], validators=[Optional()])
    next_maintenance_date = DateField('Jadwal Maintenance Berikutnya', validators=[Optional()])
    notes = TextAreaField('Catatan Tambahan', validators=[Optional()])
    submit = SubmitField('Simpan Catatan')

    def validate_next_maintenance_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Jadwal maintenance berikutnya tidak boleh di masa lalu.')


class PreventiveMaintenanceForm(FlaskForm):
    check_date = DateField('Tanggal Preventive', validators=[DataRequired()])
    result = TextAreaField('Hasil', validators=[
        DataRequired(),
        Length(min=3, message='Hasil preventive wajib diisi.')
    ])
    notes = TextAreaField('Keterangan', validators=[Optional()])
    recommendation = TextAreaField('Rekomendasi', validators=[Optional()])
    condition_after = SelectField('Kondisi Setelah Preventive', choices=[
        ('', 'Hitung Otomatis dari Hasil'),
        ('baik', 'Baik'),
        ('perlu_perhatian', 'Perlu Perhatian'),
        ('kritis', 'Kritis'),
        ('tidak_layak', 'Tidak Layak'),
    ], validators=[Optional()])
    next_maintenance_date = DateField('Jadwal Preventive Berikutnya', validators=[Optional()])
    submit = SubmitField('Simpan Preventive')

    def validate_next_maintenance_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Jadwal preventive berikutnya tidak boleh di masa lalu.')
