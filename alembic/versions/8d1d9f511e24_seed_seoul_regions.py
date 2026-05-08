"""seed_seoul_regions

Revision ID: 8d1d9f511e24
Revises: cf25a61c0f91
Create Date: 2026-05-07 14:25:43.737985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d1d9f511e24'
down_revision: Union[str, None] = 'cf25a61c0f91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass