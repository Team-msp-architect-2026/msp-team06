# HomeLens AI - AI 리포트 API 엔드포인트
# 비동기 생성 방식: POST → Celery → RDS → GET
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime, date
from app.core.database import get_db
from app.models.report import Report, ReportSection
from app.models.region import Region
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

    existing_result = await db.execute(
        select(Report).where(
            Report.region_id == request.regionId,
            Report.data_base_date == date.today()
        )
    )
    existing_report = existing_result.scalar_one_or_none()
    if existing_report:
        return {
            "reportId": existing_report.id,
            "status": existing_report.status,
            "estimatedSeconds": 30,
        }

    region_stmt = pg_insert(Region).values(
        id=request.regionId,
        name=region_name or request.regionId,
        full_address=region_name or "",
        legal_dong_code="",
        lat=lat,
        lng=lng,
        property_type="apartment",
        source_type="complex",
    ).on_conflict_do_nothing(index_elements=["id"])
    await db.execute(region_stmt)

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

    try:
        from app.worker import generate_report_task
        generate_report_task.delay(report_id, request.regionId, region_name, lat, lng)
        print(f"[Report] SQS 태스크 전송 성공: {report_id}")
    except Exception as e:
        print(f"[Report] SQS 태스크 전송 실패: {e}")

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
