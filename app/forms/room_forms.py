from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.room import Room


class CreateRoomForm(FlaskForm):
    division_id = SelectField('Divisi', coerce=int, validators=[DataRequired(message='Divisi wajib dipilih.')])
    room_code = StringField('Kode Ruangan', validators=[DataRequired(), Length(max=20)])
    room_name = StringField('Nama Ruangan', validators=[DataRequired(), Length(max=100)])
    floor = StringField('Lantai', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Deskripsi', validators=[Optional()])
    submit = SubmitField('Simpan')

    def validate_division_id(self, field):
        if not field.data or field.data == 0:
            raise ValidationError('Divisi wajib dipilih.')

    def validate_room_code(self, field):
        if Room.query.filter_by(room_code=field.data.upper()).first():
            raise ValidationError('Kode ruangan sudah digunakan.')


class EditRoomForm(FlaskForm):
    division_id = SelectField('Divisi', coerce=int, validators=[DataRequired(message='Divisi wajib dipilih.')])
    room_code = StringField('Kode Ruangan', validators=[DataRequired(), Length(max=20)])
    room_name = StringField('Nama Ruangan', validators=[DataRequired(), Length(max=100)])
    floor = StringField('Lantai', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Deskripsi', validators=[Optional()])
    submit = SubmitField('Simpan Perubahan')

    def __init__(self, room_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = room_id

    def validate_division_id(self, field):
        if not field.data or field.data == 0:
            raise ValidationError('Divisi wajib dipilih.')

    def validate_room_code(self, field):
        existing = Room.query.filter_by(room_code=field.data.upper()).first()
        if existing and existing.id != self.room_id:
            raise ValidationError('Kode ruangan sudah digunakan oleh ruangan lain.')
