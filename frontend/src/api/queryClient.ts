// HomeLens AI - TanStack Query 클라이언트 설정
// 캐시 시간, 재시도 횟수 등 전역 설정

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 데이터 신선도 유지 시간 (5분)
      staleTime: 1000 * 60 * 5,
      // 캐시 유지 시간 (10분)
      gcTime: 1000 * 60 * 10,
      // 실패 시 재시도 횟수
      retry: 1,
      // 창 포커스 시 자동 재조회 비활성화
      refetchOnWindowFocus: false,
    },
  },
});