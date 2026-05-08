from fastapi import APIRouter
from app.api.v1.endpoints import (
    regions,
    places,
    news,
    analysis,
    map,
    reports,
)

router = APIRouter()

router.include_router(regions.router, prefix="/regions", tags=["regions"])
router.include_router(places.router, prefix="/places", tags=["places"])
router.include_router(news.router, prefix="/news", tags=["news"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
router.include_router(map.router, prefix="/map", tags=["map"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])