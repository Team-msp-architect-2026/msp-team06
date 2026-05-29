"""add kakao_place_id to locations

Revision ID: add_kakao_place_id_001
Revises: add_apt_seq_loc_001
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_kakao_place_id_001'
down_revision = 'add_apt_seq_loc_001'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('locations',
        sa.Column('kakao_place_id', sa.String(50), nullable=True)
    )
    op.create_index('idx_locations_kakao_place_id', 'locations', ['kakao_place_id'])

def downgrade():
    op.drop_index('idx_locations_kakao_place_id', 'locations')
    op.drop_column('locations', 'kakao_place_id')
