from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class FmeaEvaluationForm(FlaskForm):
    failure_mode = StringField('Mode Kegagalan', validators=[DataRequired()])
    failure_effect = TextAreaField('Efek Kegagalan', validators=[DataRequired()])
    severity = IntegerField('Severity (S)', validators=[
        DataRequired(),
        NumberRange(min=1, max=10, message='Nilai harus antara 1-10.')
    ])
    occurrence = IntegerField('Occurrence (O)', validators=[
        DataRequired(),
        NumberRange(min=1, max=10, message='Nilai harus antara 1-10.')
    ])
    detection = IntegerField('Detection (D)', validators=[
        DataRequired(),
        NumberRange(min=1, max=10, message='Nilai harus antara 1-10.')
    ])
    evaluation_date = DateField('Tanggal Evaluasi', validators=[DataRequired()])
    notes = TextAreaField('Catatan Tambahan', validators=[Optional()])
    submit = SubmitField('Simpan Evaluasi')
