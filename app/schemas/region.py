# HomeLens AI - 지역/장소 검색 API 요청/응답 데이터 형식

from pydantic import BaseModel
from typing import Optional

# 지역 검색 응답 형식
# GET /api/v1/regions/search 응답에 사용
class RegionSearchResponse(BaseModel):
    regionId: str
    name: str
    fullAddress: str
    propertyType: str
    lat: float
    lng: float

# 건물/단지 상세 정보 응답 형식
# GET /api/v1/locations/{locationId} 응답에 사용
class LocationResponse(BaseModel):
    locationId: str
    regionId: str
    name: str
    address: str
    propertyType: str
    lat: float
    lng: float
    floors: Optional[int] = None
    buildYear: Optional[int] = None
    totalHouseholds: Optional[int] = None

# 장소 검색 응답 형식
# GET /api/v1/places/search 응답에 사용
class PlaceSearchResponse(BaseModel):
    placeId: str
    regionId: str
    name: str
    address: str
    propertyType: str
    lat: float
    lng: float