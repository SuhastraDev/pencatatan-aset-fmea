"""add pengajuan_status cetak_kir to maintenance_log enum

Revision ID: e7b209e15091
Revises: 1ee6b3f4c947
Create Date: 2026-04-30 12:02:35.530604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7b209e15091'
down_revision = '1ee6b3f4c947'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE maintenance_logs MODIFY COLUMN action_type "
        "ENUM('evaluasi_fmea','perbaikan','penggantian','pemeriksaan_rutin',"
        "'approval_disetujui','approval_ditolak','pengajuan_status','cetak_kir') NOT NULL"
    )


def downgrade():
    op.execute(
        "ALTER TABLE maintenance_logs MODIFY COLUMN action_type "
        "ENUM('evaluasi_fmea','perbaikan','penggantian','pemeriksaan_rutin',"
        "'approval_disetujui','approval_ditolak') NOT NULL"
    )
