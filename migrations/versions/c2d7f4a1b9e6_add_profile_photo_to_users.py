"""add profile photo to users

Revision ID: c2d7f4a1b9e6
Revises: 8f4d7b2c9a10
Create Date: 2026-08-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'c2d7f4a1b9e6'
down_revision = '8f4d7b2c9a10'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_photo', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('profile_photo')
