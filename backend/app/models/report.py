# HomeLens AI - AI 리포트 관련 DB 테이블 모델

from sqlalchemy import String, Integer, Text, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

# AI 리포트 생성 요청 및 상태 관리 테이블
# 비동기 생성 방식 (pending/processing/completed/failed)
# 동일 region_id + data_base_date 조합 캐시 재사용
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=True)
    fail_reason: Mapped[str] = mapped_column(Text, nullable=True)
    data_base_date: Mapped[Date] = mapped_column(Date, nullable=True)
    cached_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    generated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

# AI 리포트 4섹션 저장 테이블
# 가격동향/생활환경/지역이슈/종합의견
class ReportSection(Base):
    __tablename__ = "report_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(50), nullable=False)
    section_key: Mapped[str] = mapped_column(String(30), nullable=False)
    section_title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)