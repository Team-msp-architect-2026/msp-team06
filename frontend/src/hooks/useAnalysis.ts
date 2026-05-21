// HomeLens AI - 가격/이슈 분석 데이터 조회 훅
// TanStack Query로 캐시 및 로딩 상태 관리

import { useQuery } from "@tanstack/react-query";
import {
  getIssues,
  getPrice,
  getPriceStats,
  getPriceTrend,
} from "../api/analysis";

// 가격 현황 조회 훅
export function usePrice(
  regionId: string,
  lat: number,
  lng: number,
  dealYmd: string,
  regionName?: string,
) {
  return useQuery({
    queryKey: ["price", regionId, lat, lng, dealYmd, regionName],
    queryFn: () => getPrice(regionId, lat, lng, dealYmd, "all", regionName),
    enabled: !!regionId && !!lat && !!lng && !!dealYmd,
  });
}

// 가격 추이 조회 훅
export function usePriceTrend(
  regionId: string,
  lat: number,
  lng: number,
  period: string = "1y",
  regionName?: string,
) {
  return useQuery({
    queryKey: ["price", "trend", regionId, lat, lng, period, regionName],
    queryFn: () => getPriceTrend(regionId, lat, lng, period, "all", regionName),
    enabled: !!regionId && !!lat && !!lng,
  });
}

// 가격 통계 조회 훅 (최저/평균/최고)
export function usePriceStats(
  regionId: string,
  lat: number,
  lng: number,
  dealYmd: string,
  period: string = "1m",
  regionName?: string,
) {
  return useQuery({
    queryKey: ["price", "stats", regionId, lat, lng, dealYmd, period],
    queryFn: () => getPriceStats(regionId, lat, lng, dealYmd, "all", period, regionName),
    enabled: !!regionId && !!lat && !!lng && !!dealYmd,
  });
}
// 이슈/뉴스 목록 조회 훅
export function useIssues(regionId: string, regionName: string) {
  return useQuery({
    queryKey: ["issues", regionId, regionName],
    queryFn: () => getIssues(regionId, regionName),
    enabled: !!regionId && !!regionName,
  });
}
