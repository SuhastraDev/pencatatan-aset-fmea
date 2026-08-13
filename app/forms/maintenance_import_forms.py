from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField


class MaintenanceImportForm(FlaskForm):
    file = FileField(
        'File Excel Riwayat Maintenance',
        validators=[
            FileAllowed(
                ['xlsx'],
                message='File harus berformat Excel .xlsx.',
            ),
        ],
    )
