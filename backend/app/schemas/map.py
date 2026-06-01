# HomeLens AI - 지도 마커/레이어 API 응답 데이터 형식

from pydantic import BaseModel
from typing import Optional
from datetime import date

# 지도 마커 단건 데이터 형식
# apartment/subway/school/mart/hospital 마커 포함
class MarkerResponse(BaseModel):
    markerId: str
    name: str
    address: str
    lat: float
    lng: float
    markerType: str
    avgPrice: Optional[int] = None
    priceLevel: Optional[str] = None
    distanceM: Optional[int] = None

# 지도 마커 목록 응답 형식
# GET /api/v1/map/markers 응답에 사용
class MapMarkerResponse(BaseModel):
    markers: list[MarkerResponse]

# 가격 레이어 구역 단건 데이터 형식
class PriceLayerZone(BaseModel):
    zoneId: str
    lat: float
    lng: float
    value: float
    priceGrade: int
    aptName: Optional[str] = None
    aptSeq: Optional[str] = None
    kakaoPlaceId: Optional[str] = None

# 가격 레이어 응답 형식
# GET /api/v1/map/price-layer 응답에 사용
class PriceLayerResponse(BaseModel):
    zones: list[PriceLayerZone]
    dataBaseDate: date