// HomeLens AI - 가격/이슈 분석 데이터 조회 훅
import { useQuery } from "@tanstack/react-query";
import {
  getIssues,
  getPrice,
  getPriceStats,
  getPriceTrend,
} from "../api/analysis";
import { useAppStore } from "../store/useAppStore";

// 가격 현황 조회 훅
export function usePrice(
  regionId: string,
  lat: number,
  lng: number,
  dealYmd: string,
  regionName?: string,
) {
  const { selectedRegion } = useAppStore();
  const aptSeq = selectedRegion?.aptSeq;

  return useQuery({
    queryKey: ["price", regionId, lat, lng, dealYmd, regionName, aptSeq],
    queryFn: () => getPrice(regionId, lat, lng, dealYmd, "all", regionName, aptSeq),
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
  const { selectedRegion } = useAppStore();
  const aptSeq = selectedRegion?.aptSeq;

  return useQuery({
    queryKey: ["price", "trend", regionId, lat, lng, period, regionName, aptSeq],
    queryFn: () => getPriceTrend(regionId, lat, lng, period, "all", regionName, aptSeq),
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
  const { selectedRegion } = useAppStore();
  const aptSeq = selectedRegion?.aptSeq;

  return useQuery({
    queryKey: ["price", "stats", regionId, lat, lng, dealYmd, period, aptSeq],
    queryFn: () => getPriceStats(regionId, lat, lng, dealYmd, "all", period, regionName, aptSeq),
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