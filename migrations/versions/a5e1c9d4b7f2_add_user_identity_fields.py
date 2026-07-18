"""add user identity fields

Revision ID: a5e1c9d4b7f2
Revises: 9c4d8b2a1f3e
Create Date: 2026-07-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'a5e1c9d4b7f2'
down_revision = '9c4d8b2a1f3e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nip', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('jabatan', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('tanggal_lahir', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('tanggal_lahir')
        batch_op.drop_column('jabatan')
        batch_op.drop_column('nip')
