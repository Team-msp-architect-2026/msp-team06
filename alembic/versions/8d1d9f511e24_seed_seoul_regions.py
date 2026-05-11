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


SEOUL_GU_DATA = [
    ("11110", "종로구", "서울특별시 종로구",       37.5730, 126.9794),
    ("11140", "중구",   "서울특별시 중구",          37.5640, 126.9975),
    ("11170", "용산구", "서울특별시 용산구",         37.5324, 126.9904),
    ("11200", "성동구", "서울특별시 성동구",         37.5634, 127.0369),
    ("11215", "광진구", "서울특별시 광진구",         37.5384, 127.0823),
    ("11230", "동대문구","서울특별시 동대문구",      37.5744, 127.0396),
    ("11260", "중랑구", "서울특별시 중랑구",         37.6063, 127.0927),
    ("11290", "성북구", "서울특별시 성북구",         37.5894, 127.0167),
    ("11305", "강북구", "서울특별시 강북구",         37.6397, 127.0257),
    ("11320", "도봉구", "서울특별시 도봉구",         37.6688, 127.0471),
    ("11350", "노원구", "서울특별시 노원구",         37.6543, 127.0568),
    ("11380", "은평구", "서울특별시 은평구",         37.6027, 126.9291),
    ("11410", "서대문구","서울특별시 서대문구",      37.5791, 126.9368),
    ("11440", "마포구", "서울특별시 마포구",         37.5663, 126.9014),
    ("11470", "양천구", "서울특별시 양천구",         37.5170, 126.8666),
    ("11500", "강서구", "서울특별시 강서구",         37.5509, 126.8496),
    ("11530", "구로구", "서울특별시 구로구",         37.4954, 126.8877),
    ("11545", "금천구", "서울특별시 금천구",         37.4600, 126.9001),
    ("11560", "영등포구","서울특별시 영등포구",      37.5264, 126.8962),
    ("11590", "동작구", "서울특별시 동작구",         37.5124, 126.9395),
    ("11620", "관악구", "서울특별시 관악구",         37.4784, 126.9516),
    ("11650", "서초구", "서울특별시 서초구",         37.4837, 127.0324),
    ("11680", "강남구", "서울특별시 강남구",         37.4980, 127.0276),
    ("11710", "송파구", "서울특별시 송파구",         37.5145, 127.1059),
    ("11740", "강동구", "서울특별시 강동구",         37.5301, 127.1238),
]


def upgrade() -> None:
    conn = op.get_bind()
    for legal_dong_code, name, full_address, lat, lng in SEOUL_GU_DATA:
        conn.execute(
            sa.text("""
                INSERT INTO regions (
                    id, name, full_address, legal_dong_code,
                    lat, lng, property_type, source_type,
                    created_at, updated_at
                ) VALUES (
                    :id, :name, :full_address, :legal_dong_code,
                    :lat, :lng, 'area', 'region',
                    NOW(), NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    full_address = EXCLUDED.full_address,
                    legal_dong_code = EXCLUDED.legal_dong_code,
                    lat = EXCLUDED.lat,
                    lng = EXCLUDED.lng,
                    updated_at = NOW()
            """),
            {
                "id": f"seoul-{legal_dong_code}",
                "name": name,
                "full_address": full_address,
                "legal_dong_code": legal_dong_code,
                "lat": lat,
                "lng": lng,
            }
        )


def downgrade() -> None:
    conn = op.get_bind()
    ids = [f"seoul-{code}" for code, *_ in SEOUL_GU_DATA]
    conn.execute(
        sa.text("DELETE FROM regions WHERE id = ANY(:ids)"),
        {"ids": ids}
    )