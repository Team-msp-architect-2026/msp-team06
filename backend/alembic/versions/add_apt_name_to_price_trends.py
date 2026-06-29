"""add apt_name to price_trends

Revision ID: add_apt_name_001
Revises: add_apt_seq_001
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_apt_name_001'
down_revision = 'add_apt_seq_001'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('price_trends',
        sa.Column('apt_name', sa.String(200), nullable=True)
    )
    op.create_index('idx_price_trends_apt_name', 'price_trends', ['apt_name'])

def downgrade():
    op.drop_index('idx_price_trends_apt_name', 'price_trends')
    op.drop_column('price_trends', 'apt_name')
