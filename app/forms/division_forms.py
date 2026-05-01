from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.division import Division


class CreateDivisionForm(FlaskForm):
    division_name = StringField('Nama Divisi', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Deskripsi', validators=[Optional()])
    submit = SubmitField('Simpan')

    def validate_division_name(self, field):
        if Division.query.filter_by(division_name=field.data).first():
            raise ValidationError('Nama divisi sudah digunakan.')


class EditDivisionForm(FlaskForm):
    division_name = StringField('Nama Divisi', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Deskripsi', validators=[Optional()])
    submit = SubmitField('Simpan Perubahan')

    def __init__(self, division_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.division_id = division_id

    def validate_division_name(self, field):
        existing = Division.query.filter_by(division_name=field.data).first()
        if existing and existing.id != self.division_id:
            raise ValidationError('Nama divisi sudah digunakan oleh divisi lain.')
