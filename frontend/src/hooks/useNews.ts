// HomeLens AI - 뉴스 데이터 조회 훅
// TanStack Query로 캐시 및 로딩 상태 관리

import { useQuery } from "@tanstack/react-query";
import { getNewsHighlights } from "../api/news";

// 메인화면 주요 뉴스 목록 조회 훅
export function useNewsHighlights(region: string = "", limit: number = 10) {
  return useQuery({
    queryKey: ["news", "highlights", region, limit],
    queryFn: () => getNewsHighlights(region, limit),
  });
}
