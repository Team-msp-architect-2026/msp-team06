# HomeLens AI - AI 리포트 API 요청/응답 데이터 형식
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
# 리포트 생성 요청 형식
# POST /api/v1/reports 요청에 사용
class ReportCreateRequest(BaseModel):
    regionId: str
    regionName: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    aptSeq: Optional[str] = None
# 리포트 생성 응답 형식
# pending/cached 상태 반환
class ReportCreateResponse(BaseModel):
    reportId: str
    status: str
    estimatedSeconds: Optional[int] = None
    cachedAt: Optional[datetime] = None
# 리포트 상태 조회 응답 형식
# GET /api/v1/reports/{report_id}/status 응답에 사용 (Polling)
class ReportStatusResponse(BaseModel):
    reportId: str
    status: str
    progressPct: Optional[int] = None
    completedAt: Optional[datetime] = None
    failReason: Optional[str] = None
# 리포트 섹션 단건 데이터 형식
class ReportSectionResponse(BaseModel):
    sectionKey: str
    sectionTitle: str
    content: str
    sortOrder: int
# 리포트 결과 조회 응답 형식
# GET /api/v1/reports/{report_id} 응답에 사용
class ReportResponse(BaseModel):
    reportId: str
    regionId: str
    summary: str
    sections: list[ReportSectionResponse]
    disclaimer: str
    generatedAt: datetime
    dataBaseDate: date
