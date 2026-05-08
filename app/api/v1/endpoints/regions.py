"""
regions.py
지역 검색 API
- GET /regions/search  (자동완성)
- GET /regions/{regionId}  (지역 기본 정보)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.db.session import get_db
from app.models.region import Region

router = APIRouter()


@router.get("/search")
def search_regions(
    q: str = Query(..., min_length=1, description="검색 키워드"),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    지역 검색 자동완성 (FR-01)
    구·동·아파트명으로 검색
    """
    if not q:
        raise HTTPException(status_code=400, detail={
            "success": False,
            "error": {
                "code": "INVALID_PARAMETER",
                "message": "검색어를 입력해주세요"
            }
        })

    # 서울 지역만 지원
    results = db.query(Region).filter(
        or_(
            Region.name.ilike(f"%{q}%"),
            Region.full_address.ilike(f"%{q}%"),
        ),
        Region.full_address.ilike("서울%"),
    ).limit(limit).all()

    return {
        "success": True,
        "data": [
            {
                "regionId": r.id,
                "name": r.name,
                "fullAddress": r.full_address,
                "propertyType": r.property_type,
                "lat": float(r.lat),
                "lng": float(r.lng),
            }
            for r in results
        ],
        "meta": {
            "total": len(results),
            "hasNext": len(results) == limit,
        }
    }


@router.get("/{region_id}")
def get_region(
    region_id: str,
    db: Session = Depends(get_db),
):
    """지역 기본 정보 조회"""
    region = db.query(Region).filter(Region.id == region_id).first()

    if not region:
        raise HTTPException(status_code=404, detail={
            "success": False,
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "요청한 지역을 찾을 수 없습니다"
            }
        })

    return {
        "success": True,
        "data": {
            "regionId": region.id,
            "name": region.name,
            "fullAddress": region.full_address,
            "legalDongCode": region.legal_dong_code,
            "lat": float(region.lat),
            "lng": float(region.lng),
            "propertyType": region.property_type,
            "sourceType": region.source_type,
        }
    }