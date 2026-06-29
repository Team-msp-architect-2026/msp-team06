# HomeLens AI - 지역/위치 관련 DB 테이블 모델

from sqlalchemy import String, Integer, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

# 행정구역 마스터 테이블
# 모든 분석 API의 핵심 참조 테이블
class Region(Base):
    __tablename__ = "regions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_address: Mapped[str] = mapped_column(String(300), nullable=False)
    legal_dong_code: Mapped[str] = mapped_column(String(20), nullable=False)
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    property_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

# 건물/단지 위치 마스터 테이블
# Region의 하위 개념 (한 지역에 여러 건물/단지)
class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    property_type: Mapped[str] = mapped_column(String(20), nullable=False)
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    floors: Mapped[int] = mapped_column(Integer, nullable=True)
    build_year: Mapped[int] = mapped_column(Integer, nullable=True)
    total_households: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

# 카카오맵 장소 검색 결과 캐시 테이블
# 주변 인프라 정보 및 지도 마커에 활용
class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    region_id: Mapped[str] = mapped_column(String(50), nullable=False)
    kakao_place_id: Mapped[str] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    place_type: Mapped[str] = mapped_column(String(20), nullable=False)
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    distance_m: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())