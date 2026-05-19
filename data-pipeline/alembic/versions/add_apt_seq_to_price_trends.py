"""add apt_seq to price_trends

Revision ID: add_apt_seq_001
Revises: cf25a61c0f91
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_apt_seq_001'
down_revision = 'cf25a61c0f91'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('price_trends',
        sa.Column('apt_seq', sa.String(20), nullable=True)
    )
    op.create_index('idx_price_trends_apt_seq', 'price_trends', ['apt_seq'])

def downgrade():
    op.drop_index('idx_price_trends_apt_seq', 'price_trends')
    op.drop_column('price_trends', 'apt_seq')
