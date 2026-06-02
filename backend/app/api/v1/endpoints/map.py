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
    type: Optional[str] = Query("sale", description="sale | jeonse | monthly"),
    db: AsyncSession = Depends(get_db),
):
    try:
        from sqlalchemy import text

        deal_type_map = {"sale": "sale", "jeonse": "jeonse", "monthly": "monthly"}
        deal_type = deal_type_map.get(type, "sale")

        result = await db.execute(text("""
            SELECT 
                r.legal_dong_code,
                r.name,
                AVG(CASE WHEN ps.avg_sale_price > 0 THEN ps.avg_sale_price END) as avg_sale,
                AVG(CASE WHEN ps.avg_jeonse_price > 0 THEN ps.avg_jeonse_price END) as avg_jeonse,
                AVG(CASE WHEN ps.avg_monthly_rent > 0 THEN ps.avg_monthly_rent END) as avg_monthly
            FROM regions r
            LEFT JOIN price_snapshots ps ON r.id = ps.region_id
            WHERE r.source_type = 'region'
            AND r.property_type = 'area'
            GROUP BY r.legal_dong_code, r.name
            HAVING COUNT(ps.id) > 0
        """))

        rows = result.fetchall()
        if not rows:
            return {"zones": [], "dataBaseDate": date.today()}

        prices = []
        for row in rows:
            if deal_type == "sale":
                val = float(row.avg_sale) if row.avg_sale else 0
            elif deal_type == "jeonse":
                val = float(row.avg_jeonse) if row.avg_jeonse else 0
            else:
                val = float(row.avg_monthly) if row.avg_monthly else 0
            prices.append((row.legal_dong_code, row.name, val))

        valid = [(c, n, v) for c, n, v in prices if v > 0]
        if not valid:
            return {"zones": [], "dataBaseDate": date.today()}

        vals = sorted([v for _, _, v in valid])
        n = len(vals)
        thresholds = [
            vals[int(n * 0.2)],
            vals[int(n * 0.4)],
            vals[int(n * 0.6)],
            vals[int(n * 0.8)],
        ]

        def get_grade(v):
            if v <= thresholds[0]: return 1
            if v <= thresholds[1]: return 2
            if v <= thresholds[2]: return 3
            if v <= thresholds[3]: return 4
            return 5

        zones = []
        for code, name, val in valid:
            zones.append({
                "zoneId": code,
                "lat": 0.0,
                "lng": 0.0,
                "value": val,
                "priceGrade": get_grade(val),
                "aptName": name,
                "aptSeq": None,
                "kakaoPlaceId": None,
            })

        return {"zones": zones, "dataBaseDate": date.today()}

    except Exception as e:
        print(f"price-layer 오류: {e}")
        raise HTTPException(status_code=503, detail=str(e))
