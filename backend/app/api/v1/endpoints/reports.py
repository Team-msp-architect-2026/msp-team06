# HomeLens AI - AI 리포트 API 엔드포인트
# 비동기 생성 방식: POST → Celery → Redis → GET

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from app.core.database import get_db
from app.core.redis import report_set, report_get
from app.schemas.report import (
    ReportCreateRequest,
    ReportCreateResponse,
    ReportStatusResponse,
    ReportResponse,
)

router = APIRouter()


@router.post("", response_model=ReportCreateResponse)
async def create_report(
    request: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    report_id = str(uuid.uuid4())
    region_name = getattr(request, "regionName", "") or ""
    lat = getattr(request, "lat", 0.0) or 0.0
    lng = getattr(request, "lng", 0.0) or 0.0

    # Redis에 초기 상태 저장
    report_set(report_id, {
        "status": "pending",
        "regionId": request.regionId,
        "regionName": region_name,
        "lat": lat,
        "lng": lng,
        "createdAt": datetime.now().isoformat(),
        "progressPct": 0,
    })

    # Celery 태스크 호출
    from app.worker import generate_report_task
    generate_report_task.delay(report_id, request.regionId, region_name, lat, lng)

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
    report = report_get(report_id)
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
    report = report_get(report_id)
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