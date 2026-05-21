# HomeLens AI - AI 리포트 API 엔드포인트
# 비동기 생성 방식: POST → Polling → GET

import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from app.core.database import get_db
from app.schemas.report import (
    ReportCreateRequest,
    ReportCreateResponse,
    ReportStatusResponse,
    ReportResponse,
)
from app.services.report import generate_report
from app.services.price import get_price_snapshot, fetch_sale_price, get_lawd_cd
from app.services.news import get_region_issues
from app.services.map import search_all_nearby_infra

router = APIRouter()

# 임시 리포트 저장소 (DB 연동 전 메모리 캐시)
_report_store = {}


async def _generate_report_async(report_id: str, region_id: str, region_name: str, lat: float, lng: float):
    print(f"[리포트] 생성 시작: {report_id} / {region_name}")
    try:
        _report_store[report_id]["status"] = "processing"
        print(f"[리포트] processing 설정 완료")

        # 1. 가격 데이터 수집 (db 없이)
        price_data = {}

        _report_store[report_id]["progressPct"] = 40
        print(f"[리포트] 뉴스 수집 시작")

        # 2. 뉴스/이슈 데이터 수집 (db 없이)
        news_data = {}
        try:
            issues = await get_region_issues(region_id, region_name)
            print(f"[리포트] 뉴스 수집 완료: {len(issues) if issues else 0}건")
            if issues:
                news_data = {"items": issues[:5]}
        except Exception as e:
            print(f"뉴스 데이터 수집 실패: {e}")

        _report_store[report_id]["progressPct"] = 70

        # 3. 인프라 데이터 수집
        infra_data = {}
        try:
            markers = await search_all_nearby_infra(lat, lng, 1500)
            if markers:
                marker_list = markers.get("markers", []) if isinstance(markers, dict) else markers
                infra_data = {"markers": [{"name": m.get("name"), "type": m.get("markerType"), "distance": m.get("distanceM")} for m in marker_list[:10]]}
        except Exception as e:
            print(f"인프라 데이터 수집 실패: {e}")

        _report_store[report_id]["progressPct"] = 80

        # 4. AI 리포트 생성
        result = await generate_report(region_name, price_data, news_data, infra_data)

        _report_store[report_id].update({
            "status": "completed",
            "progressPct": 100,
            "summary": result.get("summary", ""),
            "sections": result.get("sections", []),
            "disclaimer": result.get("disclaimer", ""),
            "generatedAt": datetime.now().isoformat(),
            "dataBaseDate": str(date.today()),
            "completedAt": datetime.now().isoformat(),
        })

    except Exception as e:
        print(f"리포트 생성 실패: {e}")
        _report_store[report_id]["status"] = "failed"
        _report_store[report_id]["failReason"] = str(e)


@router.post("", response_model=ReportCreateResponse)
async def create_report(
    request: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    report_id = str(uuid.uuid4())
    region_name = getattr(request, "regionName", "") or ""
    lat = getattr(request, "lat", 0.0) or 0.0
    lng = getattr(request, "lng", 0.0) or 0.0
    _report_store[report_id] = {
        "status": "pending",
        "regionId": request.regionId,
        "regionName": region_name,
        "lat": lat,
        "lng": lng,
        "createdAt": datetime.now().isoformat(),
        "progressPct": 0,
    }
    asyncio.ensure_future(
        _generate_report_async(report_id, request.regionId, region_name, lat, lng)
    )
    return {
        "reportId": report_id,
        "status": "pending",
        "estimatedSeconds": 30,
    }


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    report = _report_store.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    return {
        "reportId": report_id,
        "status": report.get("status", "pending"),
        "progressPct": report.get("progressPct"),
        "completedAt": report.get("completedAt"),
        "failReason": report.get("failReason"),
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    report = _report_store.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    if report.get("status") != "completed":
        raise HTTPException(status_code=404, detail="리포트가 아직 생성 중입니다")
    return {
        "reportId": report_id,
        "regionId": report.get("regionId", ""),
        "summary": report.get("summary", ""),
        "sections": report.get("sections", []),
        "disclaimer": report.get("disclaimer", ""),
        "generatedAt": report.get("generatedAt", datetime.now().isoformat()),
        "dataBaseDate": report.get("dataBaseDate", str(date.today())),
    }