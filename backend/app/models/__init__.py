# HomeLens AI - 전체 DB 모델 통합 import
# Alembic 마이그레이션 시 모든 모델 인식하도록 등록

from app.models.region import Region, Location, Place
from app.models.news import News, NewsKeyword, NewsRegion, Issue
from app.models.price import PriceSnapshot, PriceTrend, PriceStat
from app.models.report import Report, ReportSection
from app.models.map import MapMarker

__all__ = [
    "Region", "Location", "Place",
    "News", "NewsKeyword", "NewsRegion", "Issue",
    "PriceSnapshot", "PriceTrend", "PriceStat",
    "Report", "ReportSection",
    "MapMarker",
]