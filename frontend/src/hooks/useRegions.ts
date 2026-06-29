// HomeLens AI - 지역 검색 데이터 조회 훅
// TanStack Query로 캐시 및 로딩 상태 관리

import { useQuery } from "@tanstack/react-query";
import { searchRegions } from "../api/regions";

// 동·단지 자동완성 검색 훅
export function useRegionSearch(q: string) {
  return useQuery({
    queryKey: ["regions", "search", q],
    queryFn: () => searchRegions(q),
    enabled: q.length > 0,
    staleTime: 0, // 캐시 즉시 만료
    gcTime: 0, // 캐시 즉시 제거
  });
}
