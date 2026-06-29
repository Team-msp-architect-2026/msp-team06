# HomeLens AI - 뉴스/이슈 관련 DB 테이블 모델

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

# 네이버 뉴스 API 수집 결과 테이블
# AI 요약 처리 후 제목/요약/링크만 저장 (저작권 준수)
class News(Base):
    __tablename__ = "news"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    published_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

# 뉴스 키워드 테이블 (News 자식)
class NewsKeyword(Base):
    __tablename__ = "news_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[str] = mapped_column(String(50), nullable=False)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

# 뉴스-지역 다대다 연결 테이블
# 뉴스 1건이 여러 지역에 연관될 수 있음
class NewsRegion(Base):
    __tablename__ = "news_regions"

    news_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region_id: Mapped[str] = mapped_column(String(50), primary_key=True)

# 통합 이슈 타임라인 테이블
# 뉴스/정책/교통 이슈를 통합해서 관리
class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    impact_type: Mapped[str] = mapped_column(String(20), nullable=False)
    published_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=True)
    ref_id: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())