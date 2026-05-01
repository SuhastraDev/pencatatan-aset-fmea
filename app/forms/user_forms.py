from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from app.models.user import User


class CreateUserForm(FlaskForm):
    name = StringField('Nama Lengkap', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message='Password minimal 8 karakter.')])
    role = SelectField('Role', choices=[
        ('admin_divisi', 'Admin Divisi'),
        ('admin_ruangan', 'Admin Ruangan'),
    ], validators=[DataRequired()])
    division_id = SelectField('Divisi', coerce=int, validators=[Optional()])
    room_id = SelectField('Ruangan', coerce=int, validators=[Optional()])
    submit = SubmitField('Simpan')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email sudah digunakan.')

    def validate_division_id(self, field):
        if self.role.data == 'admin_divisi' and (not field.data or field.data == 0):
            raise ValidationError('Divisi wajib dipilih untuk Admin Divisi.')

    def validate_room_id(self, field):
        if self.role.data == 'admin_ruangan' and (not field.data or field.data == 0):
            raise ValidationError('Ruangan wajib dipilih untuk Admin Ruangan.')


class EditUserForm(FlaskForm):
    name = StringField('Nama Lengkap', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password Baru', validators=[Optional(), Length(min=8, message='Password minimal 8 karakter.')])
    role = SelectField('Role', choices=[
        ('admin_divisi', 'Admin Divisi'),
        ('admin_ruangan', 'Admin Ruangan'),
    ], validators=[DataRequired()])
    division_id = SelectField('Divisi', coerce=int, validators=[Optional()])
    room_id = SelectField('Ruangan', coerce=int, validators=[Optional()])
    submit = SubmitField('Simpan Perubahan')

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_email(self, field):
        existing = User.query.filter_by(email=field.data.lower()).first()
        if existing and existing.id != self.user_id:
            raise ValidationError('Email sudah digunakan oleh user lain.')

    def validate_division_id(self, field):
        if self.role.data == 'admin_divisi' and (not field.data or field.data == 0):
            raise ValidationError('Divisi wajib dipilih untuk Admin Divisi.')

    def validate_room_id(self, field):
        if self.role.data == 'admin_ruangan' and (not field.data or field.data == 0):
            raise ValidationError('Ruangan wajib dipilih untuk Admin Ruangan.')
