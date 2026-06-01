"""add kakao_place_id to locations
Revision ID: add_kakao_place_id_001
Revises: add_apt_seq_loc_001
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'add_kakao_place_id_001'
down_revision = 'add_apt_seq_loc_001'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('locations')]
    if 'kakao_place_id' not in columns:
        op.add_column('locations',
            sa.Column('kakao_place_id', sa.String(50), nullable=True)
        )
    indices = [i['name'] for i in inspector.get_indexes('locations')]
    if 'idx_locations_kakao_place_id' not in indices:
        op.create_index('idx_locations_kakao_place_id', 'locations', ['kakao_place_id'])

def downgrade():
    op.drop_index('idx_locations_kakao_place_id', 'locations')
    op.drop_column('locations', 'kakao_place_id')
