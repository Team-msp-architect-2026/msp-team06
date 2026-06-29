# HomeLens AI - 가격 분석 관련 DB 테이블 모델

from sqlalchemy import String, Integer, BigInteger, Numeric, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

# 지역별 가격 현황 스냅샷 테이블
# 국토부 실거래가 API 수집 결과
# data_base_date 변경 시 재생성
class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    avg_sale_price: Mapped[int] = mapped_column(BigInteger, nullable=True)
    avg_jeonse_price: Mapped[int] = mapped_column(BigInteger, nullable=True)
    avg_monthly_rent: Mapped[int] = mapped_column(BigInteger, nullable=True)
    avg_monthly_deposit: Mapped[int] = mapped_column(BigInteger, nullable=True)
    jeonse_ratio: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    recent_trade_count: Mapped[int] = mapped_column(Integer, nullable=True)
    price_stability_grade: Mapped[str] = mapped_column(String(10), nullable=False)
    price_level: Mapped[str] = mapped_column(String(15), nullable=False)
    data_base_date: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

# 월별 가격 추이 테이블
# 가격 분석 탭 차트 시각화용 데이터
class PriceTrend(Base):
    __tablename__ = "price_trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    deal_type: Mapped[str] = mapped_column(String(10), nullable=False)
    avg_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    trade_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

# 기간별 가격 통계 테이블 (최저/평균/최고)
# 기간: 1m/3m/1y
class PriceStat(Base):
    __tablename__ = "price_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    deal_type: Mapped[str] = mapped_column(String(10), nullable=False)
    period: Mapped[str] = mapped_column(String(5), nullable=False)
    min_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    avg_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_trade_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recent_trade_count: Mapped[int] = mapped_column(Integer, nullable=False)
    trade_signal: Mapped[str] = mapped_column(String(10), nullable=False)
    data_base_date: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())