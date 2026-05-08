# HomeLens AI - AI 리포트 API 엔드포인트
# 비동기 생성 방식: POST → Polling → GET

import uuid
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

router = APIRouter()

# 임시 리포트 저장소 (DB 연동 전 메모리 캐시)
_report_store = {}


@router.post("", response_model=ReportCreateResponse)
async def create_report(
    request: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    # 리포트 생성 요청
    # 동일 조건 캐시 존재 시 409 반환
    report_id = str(uuid.uuid4())
    _report_store[report_id] = {
        "status": "pending",
        "regionId": request.regionId,
        "createdAt": datetime.now(),
    }
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
    # 리포트 생성 상태 조회 (Polling)
    # 권장 Polling 간격: 2~3초
    report = _report_store.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    return {
        "reportId": report_id,
        "status": report.get("status", "pending"),
        "progressPct": None,
        "completedAt": None,
        "failReason": None,
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    # 완성된 리포트 결과 조회
    report = _report_store.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    if report.get("status") != "completed":
        raise HTTPException(status_code=404, detail="리포트가 아직 생성 중입니다")
    return report