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

def is_apartment(doc: dict) -> bool:
    """카카오 검색 결과가 아파트인지 확인"""
    category = doc.get("category_name", "")
    return "아파트" in category

async def get_apt_seq_by_kakao_id(kakao_place_id: str, db: AsyncSession) -> str | None:
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

async def get_apt_seq_by_name(name: str, db: AsyncSession) -> str | None:
    try:
        clean_name = name.replace("아파트", "").replace(" ", "").strip()
        result = await db.execute(
            text("""
                SELECT apt_seq FROM price_trends
                WHERE REPLACE(apt_name, ' ', '') ILIKE :name
                AND apt_seq IS NOT NULL
                AND apt_name IS NOT NULL
                LIMIT 1
            """),
            {"name": f"%{clean_name}%"}
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

        # 1순위: 동 단위 검색 (카카오 주소 검색 API)
        DONG_SUFFIXES = ["동", "읍", "면", "리", "가"]
        if any(q.endswith(suffix) for suffix in DONG_SUFFIXES):
            try:
                kakao_addr_result = await search_kakao_address(q)
                addr_docs = kakao_addr_result.get("documents", [])
                for doc in addr_docs[:3]:
                    address = doc.get("address", {})
                    name = address.get("region_3depth_name", "")
                    full_address = f"서울특별시 {address.get('region_1depth_name', '')} {address.get('region_2depth_name', '')} {name}"
                    if name and name not in seen_names and name.endswith(tuple(DONG_SUFFIXES)):
                        seen_names.add(name)
                        results.append({
                            "regionId": f"KAKAO_DONG_{doc.get('x', '')}_{doc.get('y', '')}",
                            "name": name,
                            "fullAddress": full_address,
                            "propertyType": "area",
                            "lat": float(doc.get("y", 0)),
                            "lng": float(doc.get("x", 0)),
                            "aptSeq": None,
                        })

                apt_result = await search_kakao_keyword(f"{q} 아파트")
                apt_docs = apt_result.get("documents", [])
                for doc in apt_docs[:5]:
                    name = doc.get("place_name", "")
                    kakao_place_id = doc.get("id", "")
                    if not name or name in seen_names or not is_apartment(doc):
                        continue
                    seen_names.add(name)
                    apt_seq = await get_apt_seq_by_kakao_id(kakao_place_id, db)
                    if not apt_seq:
                        apt_seq = await get_apt_seq_by_name(name, db)
                    results.append({
                        "regionId": f"KAKAO_{kakao_place_id}",
                        "name": name,
                        "fullAddress": doc.get("road_address_name") or doc.get("address_name", ""),
                        "propertyType": "complex",
                        "lat": float(doc.get("y", 0)),
                        "lng": float(doc.get("x", 0)),
                        "aptSeq": apt_seq,
                    })
            except Exception:
                pass

        # 2순위: 아파트 단지 검색 (카카오 API - 아파트만 필터링)
        kakao_result = await search_kakao_keyword(q)
        documents = kakao_result.get("documents", [])
        for doc in documents[:limit]:
            name = doc.get("place_name", "")
            kakao_place_id = doc.get("id", "")

            if not name or name in seen_names:
                continue

            # 아파트가 아니면 스킵
            if not is_apartment(doc):
                continue

            seen_names.add(name)

            apt_seq = await get_apt_seq_by_kakao_id(kakao_place_id, db)
            if not apt_seq:
                apt_seq = await get_apt_seq_by_name(name, db)

            results.append({
                "regionId": f"KAKAO_{kakao_place_id}",
                "name": name,
                "fullAddress": doc.get("road_address_name") or doc.get("address_name", ""),
                "propertyType": "complex",
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