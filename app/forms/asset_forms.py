from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError


class CreateAssetForm(FlaskForm):
    asset_name = StringField('Nama Aset', validators=[DataRequired(), Length(max=150)])
    category_id = SelectField('Kategori', coerce=int, validators=[DataRequired()])
    brand = StringField('Merek', validators=[DataRequired(), Length(max=100)])
    model = StringField('Model', validators=[DataRequired(), Length(max=100)])
    serial_number = StringField('Nomor Seri', validators=[Optional(), Length(max=100)])
    purchase_date = DateField('Tanggal Pembelian', validators=[Optional()])
    purchase_price = DecimalField('Harga Pembelian (Rp)', validators=[Optional(), NumberRange(min=0, message='Harga tidak boleh negatif.')], places=2)
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
    category_id = SelectField('Kategori', coerce=int, validators=[DataRequired()])
    brand = StringField('Merek', validators=[DataRequired(), Length(max=100)])
    model = StringField('Model', validators=[DataRequired(), Length(max=100)])
    serial_number = StringField('Nomor Seri', validators=[Optional(), Length(max=100)])
    purchase_date = DateField('Tanggal Pembelian', validators=[Optional()])
    purchase_price = DecimalField('Harga Pembelian (Rp)', validators=[Optional(), NumberRange(min=0, message='Harga tidak boleh negatif.')], places=2)
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
