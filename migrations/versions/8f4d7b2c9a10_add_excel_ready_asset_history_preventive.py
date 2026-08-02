"""add excel ready asset history preventive

Revision ID: 8f4d7b2c9a10
Revises: e7b209e15091
Create Date: 2026-08-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '8f4d7b2c9a10'
down_revision = 'e7b209e15091'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assets') as batch_op:
        batch_op.add_column(sa.Column('specification', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('unit', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('acquisition_document_number', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('funding_source', sa.String(length=100), nullable=True))

    with op.batch_alter_table('maintenance_logs') as batch_op:
        batch_op.add_column(sa.Column('reporter_unit', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('reporter_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('reporter_position', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('complaint', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('inspection_unit', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('technician_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('technician_position', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('result', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('recommendation', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('condition_after', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('ai_recommendation', sa.Text(), nullable=True))

    op.create_table(
        'preventive_maintenance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('checked_by', sa.Integer(), nullable=False),
        sa.Column('check_date', sa.Date(), nullable=False),
        sa.Column('room_name_snapshot', sa.String(length=100), nullable=True),
        sa.Column('result', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('condition_after', sa.String(length=50), nullable=True),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.ForeignKeyConstraint(['checked_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('assets') as batch_op:
        batch_op.alter_column('quantity', server_default=None)


def downgrade():
    op.drop_table('preventive_maintenance')

    with op.batch_alter_table('maintenance_logs') as batch_op:
        batch_op.drop_column('ai_recommendation')
        batch_op.drop_column('condition_after')
        batch_op.drop_column('recommendation')
        batch_op.drop_column('result')
        batch_op.drop_column('technician_position')
        batch_op.drop_column('technician_name')
        batch_op.drop_column('inspection_unit')
        batch_op.drop_column('complaint')
        batch_op.drop_column('reporter_position')
        batch_op.drop_column('reporter_name')
        batch_op.drop_column('reporter_unit')

    with op.batch_alter_table('assets') as batch_op:
        batch_op.drop_column('funding_source')
        batch_op.drop_column('acquisition_document_number')
        batch_op.drop_column('unit')
        batch_op.drop_column('quantity')
        batch_op.drop_column('specification')
