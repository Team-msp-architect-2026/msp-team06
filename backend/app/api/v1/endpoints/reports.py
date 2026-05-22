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

    # regions 테이블에 없으면 먼저 삽입 (외래키 제약 해결)
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