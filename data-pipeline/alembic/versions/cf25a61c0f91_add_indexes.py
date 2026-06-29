
"""add_indexes

Revision ID: cf25a61c0f91
Revises: 5f5837a9aef4
Create Date: 2026-04-30

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'cf25a61c0f91'
down_revision: Union[str, None] = '5f5837a9aef4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── regions ───────────────────────────────────────────────
    # 검색 자동완성 500ms 목표 (FR-01)
    op.create_index('ix_regions_name', 'regions', ['name'])
    op.create_index('ix_regions_legal_dong_code', 'regions', ['legal_dong_code'])
    op.create_index('ix_regions_property_type', 'regions', ['property_type'])

    # ── locations ─────────────────────────────────────────────
    op.create_index('ix_locations_region_id', 'locations', ['region_id'])
    op.create_index('ix_locations_name', 'locations', ['name'])
    op.create_index('ix_locations_property_type', 'locations', ['property_type'])

    # ── places ────────────────────────────────────────────────
    # 주변 인프라 검색 (FR-04)
    op.create_index('ix_places_region_id', 'places', ['region_id'])
    op.create_index('ix_places_place_type', 'places', ['place_type'])
    op.create_index('ix_places_kakao_place_id', 'places', ['kakao_place_id'])

    # ── news ──────────────────────────────────────────────────
    # 뉴스 목록 조회 (FR-09)
    op.create_index('ix_news_published_at', 'news', ['published_at'])
    op.create_index('ix_news_category', 'news', ['category'])

    # ── news_keywords ─────────────────────────────────────────
    op.create_index('ix_news_keywords_news_id', 'news_keywords', ['news_id'])

    # ── news_regions ──────────────────────────────────────────
    op.create_index('ix_news_regions_region_id', 'news_regions', ['region_id'])

    # ── issues ────────────────────────────────────────────────
    # 이슈 분석 탭 (FR-06)
    op.create_index('ix_issues_region_id', 'issues', ['region_id'])
    op.create_index('ix_issues_published_at', 'issues', ['published_at'])
    op.create_index('ix_issues_type', 'issues', ['type'])
    op.create_index('ix_issues_impact_type', 'issues', ['impact_type'])

    # ── price_snapshots ───────────────────────────────────────
    # 가격 현황 조회 (FR-02, FR-05) - 캐시 무효화 기준
    op.create_index('ix_price_snapshots_region_id', 'price_snapshots', ['region_id'])
    op.create_index('ix_price_snapshots_data_base_date', 'price_snapshots', ['data_base_date'])
    op.create_index(
        'ix_price_snapshots_region_date',
        'price_snapshots',
        ['region_id', 'data_base_date']
    )

    # ── price_trends ──────────────────────────────────────────
    # 가격 추이 차트 (FR-05)
    op.create_index('ix_price_trends_region_id', 'price_trends', ['region_id'])
    op.create_index('ix_price_trends_month', 'price_trends', ['month'])
    op.create_index('ix_price_trends_deal_type', 'price_trends', ['deal_type'])
    op.create_index(
        'ix_price_trends_region_deal_month',
        'price_trends',
        ['region_id', 'deal_type', 'month']
    )

    # ── price_stats ───────────────────────────────────────────
    # 가격 통계 (FR-05)
    op.create_index('ix_price_stats_region_id', 'price_stats', ['region_id'])
    op.create_index('ix_price_stats_deal_type', 'price_stats', ['deal_type'])
    op.create_index('ix_price_stats_period', 'price_stats', ['period'])
    op.create_index(
        'ix_price_stats_region_deal_period_date',
        'price_stats',
        ['region_id', 'deal_type', 'period', 'data_base_date']
    )

    # ── map_markers ───────────────────────────────────────────
    # 지도 마커 (FR-03, FR-08)
    op.create_index('ix_map_markers_region_id', 'map_markers', ['region_id'])
    op.create_index('ix_map_markers_marker_type', 'map_markers', ['marker_type'])
    op.create_index('ix_map_markers_price_level', 'map_markers', ['price_level'])

    # ── reports ───────────────────────────────────────────────
    # AI 리포트 상태 조회 Polling (FR-07)
    op.create_index('ix_reports_region_id', 'reports', ['region_id'])
    op.create_index('ix_reports_status', 'reports', ['status'])
    op.create_index('ix_reports_data_base_date', 'reports', ['data_base_date'])
    op.create_index(
        'ix_reports_region_date',
        'reports',
        ['region_id', 'data_base_date']
    )
    
    # ── report_sections ───────────────────────────────────────
    op.create_index('ix_report_sections_report_id', 'report_sections', ['report_id'])
    op.create_index('ix_report_sections_section_key', 'report_sections', ['section_key'])
    op.create_index(
        'uq_reports_region_date',
        'reports',
        ['region_id', 'data_base_date'],
        unique=True
    )

def downgrade() -> None:
    # ── report_sections ───────────────────────────────────────
    op.drop_index('uq_reports_region_date', table_name='reports')
    op.drop_index('ix_report_sections_section_key', 'report_sections')
    op.drop_index('ix_report_sections_report_id', 'report_sections')

    # ── reports ───────────────────────────────────────────────
    op.drop_index('ix_reports_region_date', 'reports')
    op.drop_index('ix_reports_data_base_date', 'reports')
    op.drop_index('ix_reports_status', 'reports')
    op.drop_index('ix_reports_region_id', 'reports')

    # ── map_markers ───────────────────────────────────────────
    op.drop_index('ix_map_markers_price_level', 'map_markers')
    op.drop_index('ix_map_markers_marker_type', 'map_markers')
    op.drop_index('ix_map_markers_region_id', 'map_markers')

    # ── price_stats ───────────────────────────────────────────
    op.drop_index('ix_price_stats_region_deal_period_date', 'price_stats')
    op.drop_index('ix_price_stats_period', 'price_stats')
    op.drop_index('ix_price_stats_deal_type', 'price_stats')
    op.drop_index('ix_price_stats_region_id', 'price_stats')

    # ── price_trends ──────────────────────────────────────────
    op.drop_index('ix_price_trends_region_deal_month', 'price_trends')
    op.drop_index('ix_price_trends_deal_type', 'price_trends')
    op.drop_index('ix_price_trends_month', 'price_trends')
    op.drop_index('ix_price_trends_region_id', 'price_trends')

    # ── price_snapshots ───────────────────────────────────────
    op.drop_index('ix_price_snapshots_region_date', 'price_snapshots')
    op.drop_index('ix_price_snapshots_data_base_date', 'price_snapshots')
    op.drop_index('ix_price_snapshots_region_id', 'price_snapshots')

    # ── issues ────────────────────────────────────────────────
    op.drop_index('ix_issues_impact_type', 'issues')
    op.drop_index('ix_issues_type', 'issues')
    op.drop_index('ix_issues_published_at', 'issues')
    op.drop_index('ix_issues_region_id', 'issues')

    # ── news_regions ──────────────────────────────────────────
    op.drop_index('ix_news_regions_region_id', 'news_regions')

    # ── news_keywords ─────────────────────────────────────────
    op.drop_index('ix_news_keywords_news_id', 'news_keywords')

    # ── news ──────────────────────────────────────────────────
    op.drop_index('ix_news_category', 'news')
    op.drop_index('ix_news_published_at', 'news')

    # ── places ────────────────────────────────────────────────
    op.drop_index('ix_places_kakao_place_id', 'places')
    op.drop_index('ix_places_place_type', 'places')
    op.drop_index('ix_places_region_id', 'places')

    # ── locations ─────────────────────────────────────────────
    op.drop_index('ix_locations_property_type', 'locations')
    op.drop_index('ix_locations_name', 'locations')
    op.drop_index('ix_locations_region_id', 'locations')

    # ── regions ───────────────────────────────────────────────
    op.drop_index('ix_regions_property_type', 'regions')
    op.drop_index('ix_regions_legal_dong_code', 'regions')
    op.drop_index('ix_regions_name', 'regions')