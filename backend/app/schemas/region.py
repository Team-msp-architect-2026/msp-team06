# HomeLens AI - 지역/장소 검색 API 요청/응답 데이터 형식
from pydantic import BaseModel
from typing import Optional

class RegionSearchResponse(BaseModel):
    regionId: str
    name: str
    fullAddress: str
    propertyType: str
    lat: float
    lng: float
    aptSeq: Optional[str] = None

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

class PlaceSearchResponse(BaseModel):
    placeId: str
    regionId: str
    name: str
    address: str
    propertyType: str
    lat: float