// HomeLens AI - 지도 API 호출 함수
// GET /api/v1/map/markers
// GET /api/v1/map/price-layer

import { apiGet } from "./client";

export interface MarkerItem {
  markerId: string;
  name: string;
  address: string;
  lat: number;
  lng: number;
  markerType: string;
  avgPrice: number | null;
  priceLevel: string | null;
  distanceM: number | null;
}

export interface MapMarkerResponse {
  markers: MarkerItem[];
}

export interface PriceLayerZone {
  zoneId: string;
  lat: number;
  lng: number;
  value: number;
  priceGrade: number;
}

export interface PriceLayerResponse {
  zones: PriceLayerZone[];
  dataBaseDate: string;
}

// 지도 마커 조회 (아파트 + 인프라 마커)
export async function getMapMarkers(
  regionId: string,
  lat: number,
  lng: number,
  type: string = "all",
  infraRadius: number = 1500,
): Promise<MapMarkerResponse> {
  return apiGet<MapMarkerResponse>("/map/markers", {
    regionId,
    lat,
    lng,
    type,
    infraRadius,
  });
}

// 메인 지도 가격 레이어 조회
export async function getPriceLayer(
  regionId: string,
  type: string = "sale_count",
): Promise<PriceLayerResponse> {
  return apiGet<PriceLayerResponse>("/map/price-layer", {
    regionId,
    type,
  });
}
