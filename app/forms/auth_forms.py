from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='Email wajib diisi.'), Email(message='Format email tidak valid.')])
    password = PasswordField('Password', validators=[DataRequired(message='Password wajib diisi.')])
    submit = SubmitField('Masuk')


class ProfileForm(FlaskForm):
    name = StringField('Nama Lengkap', validators=[DataRequired(message='Nama wajib diisi.'), Length(max=100)])
    current_password = PasswordField('Password Saat Ini', validators=[Optional()])
    new_password = PasswordField('Password Baru', validators=[Optional(), Length(min=8, message='Password minimal 8 karakter.')])
    confirm_password = PasswordField('Konfirmasi Password Baru', validators=[
        Optional(),
        EqualTo('new_password', message='Konfirmasi password tidak cocok.')
    ])
    submit = SubmitField('Simpan Perubahan')
