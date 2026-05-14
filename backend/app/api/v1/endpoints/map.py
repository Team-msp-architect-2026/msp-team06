# HomeLens AI - 지도 시각화 API 엔드포인트

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
from app.schemas.map import MapMarkerResponse, PriceLayerResponse
from app.services.map import search_all_nearby_infra, CATEGORY_CODES

router = APIRouter()

# 카테고리별 한국어 이름
CATEGORY_NAMES = {
    "subway": "지하철",
    "mart": "대형마트",
    "department": "백화점",
    "hospital": "종합병원",
    "school": "학교",
}


@router.get("/markers", response_model=MapMarkerResponse)
async def get_map_markers(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    lat: float = Query(..., description="중심 위도"),
    lng: float = Query(..., description="중심 경도"),
    type: Optional[str] = Query("all", description="apartment | infra | all"),
    infraRadius: Optional[int] = Query(1000, description="주변 인프라 검색 반경 (미터)"),
    db: AsyncSession = Depends(get_db),
):
    # 카카오맵 API로 주변 인프라 마커 조회
    try:
        markers = []
        if type in ("infra", "all"):
            infra_result = await search_all_nearby_infra(lat, lng, infraRadius)
            for category, result in infra_result.items():
                documents = result.get("documents", [])
                if documents:
                    # 결과 있으면 마커 추가
                    for doc in documents:
                        markers.append({
                            "markerId": f"{category}_{doc.get('id', '')}",
                            "name": doc.get("place_name", ""),
                            "address": doc.get("road_address_name") or doc.get("address_name", ""),
                            "lat": float(doc.get("y", 0)),
                            "lng": float(doc.get("x", 0)),
                            "markerType": category,
                            "distanceM": int(doc.get("distance", 0)),
                        })
                else:
                    # 결과 없으면 "없음" 마커 추가
                    markers.append({
                        "markerId": f"{category}_none",
                        "name": f"반경 내 {CATEGORY_NAMES.get(category, category)} 없음",
                        "address": "",
                        "lat": lat,
                        "lng": lng,
                        "markerType": category,
                        "distanceM": None,
                    })
        return {"markers": markers}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/price-layer", response_model=PriceLayerResponse)
async def get_price_layer(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    type: Optional[str] = Query("sale_count", description="sale_count | jeonse_ratio | monthly_burden"),
    db: AsyncSession = Depends(get_db),
):
    # TODO: 국토부 실거래가 API 연동 구현 필요
    return {"zones": [], "dataBaseDate": date.today()}