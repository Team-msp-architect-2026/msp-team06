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
    try:
        from sqlalchemy import text

        if type == "sale_count":
            # 매매 거래량 top3
            result = await db.execute(text("""
                SELECT pt.apt_name, pt.apt_seq, pt.avg_price, pt.trade_count,
                       l.lat, l.lng, l.kakao_place_id
                FROM price_trends pt
                JOIN locations l ON pt.apt_seq = l.apt_seq
                WHERE pt.deal_type = 'sale'
                AND pt.month = TO_CHAR(CURRENT_DATE - INTERVAL '1 month', 'YYYY-MM')
                AND l.lat IS NOT NULL AND l.lng IS NOT NULL
                ORDER BY pt.trade_count DESC
                LIMIT 3
            """))

        elif type == "jeonse_ratio":
            # 전세가율 낮은 top3
            result = await db.execute(text("""
                SELECT pt.apt_name, pt.apt_seq, pt.avg_price, pt.trade_count,
                       l.lat, l.lng, l.kakao_place_id
                FROM price_trends pt
                JOIN locations l ON pt.apt_seq = l.apt_seq
                JOIN price_trends pt2 ON pt.apt_seq = pt2.apt_seq
                    AND pt2.deal_type = 'sale'
                    AND pt2.month = pt.month
                WHERE pt.deal_type = 'jeonse'
                AND pt.month = TO_CHAR(CURRENT_DATE - INTERVAL '1 month', 'YYYY-MM')
                AND l.lat IS NOT NULL AND l.lng IS NOT NULL
                AND pt2.avg_price > 0
                ORDER BY (pt.avg_price::float / pt2.avg_price::float) ASC
                LIMIT 3
            """))

        elif type == "monthly_burden":
            # 월세 부담 낮은 top3
            result = await db.execute(text("""
                SELECT pt.apt_name, pt.apt_seq, pt.avg_price, pt.trade_count,
                       l.lat, l.lng, l.kakao_place_id
                FROM price_trends pt
                JOIN locations l ON pt.apt_seq = l.apt_seq
                WHERE pt.deal_type = 'monthly'
                AND pt.month = TO_CHAR(CURRENT_DATE - INTERVAL '1 month', 'YYYY-MM')
                AND l.lat IS NOT NULL AND l.lng IS NOT NULL
                AND pt.avg_price > 0
                ORDER BY pt.avg_price ASC
                LIMIT 3
            """))

        else:
            return {"zones": [], "dataBaseDate": date.today()}

        rows = result.fetchall()
        zones = []
        for i, row in enumerate(rows):
            zones.append({
                "zoneId": f"{type}_{row.apt_seq}",
                "lat": float(row.lat),
                "lng": float(row.lng),
                "value": float(row.avg_price),
                "priceGrade": i + 1,
                "aptName": row.apt_name,
                "aptSeq": row.apt_seq,
                "kakaoPlaceId": row.kakao_place_id,
            })

        return {"zones": zones, "dataBaseDate": date.today()}

    except Exception as e:
        print(f"price-layer 오류: {e}")
        raise HTTPException(status_code=503, detail=str(e))