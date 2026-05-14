# HomeLens AI - API v1 라우터 통합 등록

from fastapi import APIRouter
from app.api.v1.endpoints import regions, places, analysis, reports, map, news

router = APIRouter()

# 지역 검색 라우터 등록 (/api/v1/regions)
router.include_router(regions.router, prefix="/regions", tags=["regions"])

# 장소 검색 라우터 등록 (/api/v1/places)
router.include_router(places.router, prefix="/places", tags=["places"])

# 가격/이슈 분석 라우터 등록 (/api/v1/analysis)
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])

# AI 리포트 라우터 등록 (/api/v1/reports)
router.include_router(reports.router, prefix="/reports", tags=["reports"])

# 지도 시각화 라우터 등록 (/api/v1/map)
router.include_router(map.router, prefix="/map", tags=["map"])

# 뉴스 라우터 등록 (/api/v1/news)
router.include_router(news.router, prefix="/news", tags=["news"])