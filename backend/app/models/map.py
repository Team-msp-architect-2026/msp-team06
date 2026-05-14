# HomeLens AI - 지도 마커 캐시 DB 테이블 모델

from sqlalchemy import String, Integer, BigInteger, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

# 지도 마커 캐시 테이블
# 카카오맵 마커 위치 및 가격 수준
# locations 테이블과 병행 운영 (지도 렌더링 전용 최적화)
class MapMarker(Base):
    __tablename__ = "map_markers"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    marker_type: Mapped[str] = mapped_column(String(20), nullable=False)
    avg_price: Mapped[int] = mapped_column(BigInteger, nullable=True)
    price_level: Mapped[str] = mapped_column(String(10), nullable=True)
    trade_count: Mapped[int] = mapped_column(Integer, nullable=True)
    jeonse_ratio: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())