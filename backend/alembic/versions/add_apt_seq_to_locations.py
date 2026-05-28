"""add apt_seq to locations

Revision ID: add_apt_seq_loc_001
Revises: add_apt_name_001
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_apt_seq_loc_001'
down_revision = 'add_apt_name_001'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('locations',
        sa.Column('apt_seq', sa.String(50), nullable=True)
    )
    op.create_index('idx_locations_apt_seq', 'locations', ['apt_seq'])

def downgrade():
    op.drop_index('idx_locations_apt_seq', 'locations')
    op.drop_column('locations', 'apt_seq')
