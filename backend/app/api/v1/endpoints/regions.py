# HomeLens AI - 지역 검색 API 엔드포인트
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.schemas.region import RegionSearchResponse
from app.services.search import search_address, search_kakao_keyword, search_kakao_address

router = APIRouter()

DONG_KEYWORDS = ["동", "읍", "면", "리", "가"]

def is_dong(name: str) -> bool:
    return any(name.endswith(kw) for kw in DONG_KEYWORDS)

async def get_apt_seq_by_kakao_id(kakao_place_id: str, db: AsyncSession) -> str | None:
    """kakao_place_id로 locations에서 apt_seq 조회"""
    try:
        result = await db.execute(
            text("""
                SELECT apt_seq FROM locations
                WHERE kakao_place_id = :kakao_place_id
                AND apt_seq IS NOT NULL
                LIMIT 1
            """),
            {"kakao_place_id": kakao_place_id}
        )
        row = result.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"kakao_place_id 기반 apt_seq 조회 실패: {e}")
        return None

async def get_apt_seq_by_name(name: str, lat: float, lng: float, db: AsyncSession) -> str | None:
    """단지명 + 구코드로 price_trends에서 apt_seq 조회 (fallback)"""
    try:
        clean_name = name.replace("아파트", "").replace(" ", "").strip()
        from app.services.price import get_lawd_cd
        lawd_cd_5, _ = await get_lawd_cd(lat, lng)
        result = await db.execute(
            text("""
                SELECT apt_seq FROM price_trends
                WHERE LEFT(apt_seq, 5) = :lawd_cd
                AND REPLACE(apt_name, ' ', '') ILIKE :name
                AND apt_seq IS NOT NULL
                AND apt_name IS NOT NULL
                LIMIT 1
            """),
            {"lawd_cd": lawd_cd_5, "name": f"%{clean_name}%"}
        )
        row = result.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"apt_seq 조회 실패: {e}")
        return None

@router.get("/search", response_model=list[RegionSearchResponse])
async def search_regions(
    q: str = Query(..., min_length=1, description="검색 키워드"),
    limit: int = Query(10, le=20, description="반환 최대 건수"),
    db: AsyncSession = Depends(get_db),
):
    try:
        results = []
        seen_names = set()

        DONG_SUFFIXES = ["동", "읍", "면", "리", "가"]
        if any(q.endswith(suffix) for suffix in DONG_SUFFIXES):
            try:
                juso_result = await search_address(q)
                juso_items = juso_result.get("results", {}).get("juso", []) or []
                for item in juso_items[:5]:
                    name = item.get("emdNm", "") or item.get("liNm", "")
                    full_address = item.get("roadAddr", "") or item.get("jibunAddr", "")
                    if name and name not in seen_names:
                        coord = await search_kakao_address(full_address)
                        coord_docs = coord.get("documents", [])
                        lat = float(coord_docs[0].get("y", 0)) if coord_docs else 0.0
                        lng = float(coord_docs[0].get("x", 0)) if coord_docs else 0.0
                        seen_names.add(name)
                        results.append({
                            "regionId": f"JUSO_{item.get('bdMgtSn', '')}",
                            "name": name,
                            "fullAddress": full_address,
                            "propertyType": "area",
                            "lat": lat,
                            "lng": lng,
                            "aptSeq": None,
                        })
            except Exception:
                pass

        kakao_result = await search_kakao_keyword(q)
        documents = kakao_result.get("documents", [])
        for doc in documents[:limit]:
            name = doc.get("place_name", "")
            kakao_place_id = doc.get("id", "")
            if name and name not in seen_names:
                seen_names.add(name)
                property_type = "area" if is_dong(name) else "complex"

                apt_seq = None
                if property_type == "complex":
                    # 1순위: kakao_place_id로 locations에서 조회
                    apt_seq = await get_apt_seq_by_kakao_id(kakao_place_id, db)
                    # 2순위: 단지명 + 구코드로 price_trends에서 조회 (fallback)
                    if not apt_seq:
                        lat = float(doc.get("y", 0))
                        lng = float(doc.get("x", 0))
                        apt_seq = await get_apt_seq_by_name(name, lat, lng, db)

                results.append({
                    "regionId": f"KAKAO_{kakao_place_id}",
                    "name": name,
                    "fullAddress": doc.get("road_address_name") or doc.get("address_name", ""),
                    "propertyType": property_type,
                    "lat": float(doc.get("y", 0)),
                    "lng": float(doc.get("x", 0)),
                    "aptSeq": apt_seq,
                })

        return results[:limit]
    except Exception as e:
        print(f"검색 오류: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="외부 API 연결 실패")


@router.get("/{region_id}", response_model=RegionSearchResponse)
async def get_region(
    region_id: str,
    db: AsyncSession = Depends(get_db),
):
    raise HTTPException(status_code=404, detail="지역을 찾을 수 없습니다")
