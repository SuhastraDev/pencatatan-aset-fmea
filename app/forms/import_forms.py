from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField


class PreventiveImportForm(FlaskForm):
    file = FileField(
        'File Excel Preventive',
        validators=[
            FileAllowed(
                ['xlsx'],
                message='File harus berformat Excel .xlsx.',
            ),
        ],
    )


class AssetKibImportForm(FlaskForm):
    file = FileField(
        'File Excel KIB B',
        validators=[
            FileAllowed(
                ['xlsx'],
                message='File harus berformat Excel .xlsx.',
            ),
        ],
    )
