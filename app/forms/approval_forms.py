from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional, DataRequired, Length


class ApproveForm(FlaskForm):
    reviewer_notes = TextAreaField('Catatan Reviewer (opsional)', validators=[Optional()])
    submit = SubmitField('Setujui Pengajuan')


class RejectForm(FlaskForm):
    reviewer_notes = TextAreaField('Alasan Penolakan', validators=[
        DataRequired(message='Alasan penolakan wajib diisi.'),
        Length(min=10, message='Alasan penolakan minimal 10 karakter.'),
    ])
    submit = SubmitField('Tolak Pengajuan')
