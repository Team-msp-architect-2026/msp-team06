// HomeLens AI - 지도 데이터 조회 훅
// TanStack Query로 캐시 및 로딩 상태 관리

import { useQuery } from "@tanstack/react-query";
import { getMapMarkers, getPriceLayer } from "../api/map";

// 지도 마커 조회 훅 (아파트 + 인프라 마커)
export function useMapMarkers(
  regionId: string,
  lat: number,
  lng: number,
  type: string = "all",
  infraRadius: number = 1500,
) {
  return useQuery({
    queryKey: ["map", "markers", regionId, lat, lng, type, infraRadius],
    queryFn: () => getMapMarkers(regionId, lat, lng, type, infraRadius),
    enabled: !!regionId && !!lat && !!lng,
  });
}

// 메인 지도 가격 레이어 조회 훅
export function usePriceLayer(regionId: string, type: string = "sale_count") {
  return useQuery({
    queryKey: ["map", "price-layer", regionId, type],
    queryFn: () => getPriceLayer(regionId, type),
    enabled: !!regionId,
  });
}
