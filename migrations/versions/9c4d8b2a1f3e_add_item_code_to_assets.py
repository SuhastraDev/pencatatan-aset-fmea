"""add item code to assets

Revision ID: 9c4d8b2a1f3e
Revises: e7b209e15091
Create Date: 2026-07-18 16:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c4d8b2a1f3e'
down_revision = 'e7b209e15091'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('item_code', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.drop_column('item_code')
