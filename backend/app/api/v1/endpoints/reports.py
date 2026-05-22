# HomeLens AI - AI 리포트 API 엔드포인트
# 비동기 생성 방식: POST → Celery → RDS → GET

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date
from app.core.database import get_db
from app.models.report import Report, ReportSection
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

    # RDS에 초기 상태 저장
    report = Report(
        id=report_id,
        region_id=request.regionId,
        status="pending",
        progress_pct=0,
        data_base_date=date.today(),
        created_at=datetime.now(),
    )
    db.add(report)
    await db.commit()

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
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    return {
        "reportId": report_id,
        "status": report.status,
        "progressPct": report.progress_pct,
        "completedAt": report.completed_at.isoformat() if report.completed_at else None,
        "failReason": report.fail_reason,
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    if report.status != "completed":
        raise HTTPException(status_code=404, detail="리포트가 아직 생성 중입니다")

    sections_result = await db.execute(
        select(ReportSection)
        .where(ReportSection.report_id == report_id)
        .order_by(ReportSection.sort_order)
    )
    sections = sections_result.scalars().all()

    return {
        "reportId": report_id,
        "regionId": report.region_id,
        "summary": report.summary or "",
        "sections": [
            {
                "sectionKey": s.section_key,
                "sectionTitle": s.section_title,
                "content": s.content,
                "sortOrder": s.sort_order,
            }
            for s in sections
        ],
        "disclaimer": report.disclaimer or "",
        "generatedAt": report.generated_at.isoformat() if report.generated_at else datetime.now().isoformat(),
        "dataBaseDate": str(report.data_base_date) if report.data_base_date else str(date.today()),
    }