"""add deposit to price_trends

Revision ID: add_deposit_001
Revises: add_kakao_place_id_001
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_deposit_001'
down_revision = 'add_kakao_place_id_001'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('price_trends',
        sa.Column('deposit', sa.BigInteger(), nullable=True)
    )

def downgrade():
    op.drop_column('price_trends', 'deposit')
