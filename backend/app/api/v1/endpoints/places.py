# HomeLens AI - 장소 검색 API 엔드포인트

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.region import PlaceSearchResponse

router = APIRouter()

# 건물/단지명 검색 (카카오맵 API 프록시)
# 주변 인프라 검색에도 동일 엔드포인트 활용
# TODO: 카카오맵 API 연동 구현 필요
@router.get("/search", response_model=list[PlaceSearchResponse])
async def search_places(
    q: str = Query(..., min_length=1, description="검색 키워드"),
    type: Optional[str] = Query(None, description="apartment | all"),
    lat: Optional[float] = Query(None, description="현재 위치 위도"),
    lng: Optional[float] = Query(None, description="현재 위치 경도"),
    limit: int = Query(10, le=20, description="반환 최대 건수"),
    db: AsyncSession = Depends(get_db),
):
    # TODO: 카카오맵 API 연동
    return []