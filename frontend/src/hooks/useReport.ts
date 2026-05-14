// HomeLens AI - AI 리포트 데이터 조회 훅
// TanStack Query로 캐시 및 Polling 상태 관리

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createReport, getReport, getReportStatus } from '../api/reports';

// AI 리포트 생성 요청 훅
export function useCreateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (regionId: string) => createReport(regionId),
    onSuccess: (data) => {
      // 생성 성공 시 상태 조회 캐시 초기화
      queryClient.invalidateQueries({ queryKey: ['report', 'status', data.reportId] });
    },
  });
}

// AI 리포트 생성 상태 조회 훅 (Polling)
export function useReportStatus(reportId: string | null) {
  return useQuery({
    queryKey: ['report', 'status', reportId],
    queryFn: () => getReportStatus(reportId!),
    enabled: !!reportId,
    // 2초마다 상태 조회 (Polling)
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // completed 또는 failed 상태면 Polling 중단
      if (status === 'completed' || status === 'failed') return false;
      return 2000;
    },
  });
}

// AI 리포트 결과 조회 훅
export function useReport(reportId: string | null) {
  return useQuery({
    queryKey: ['report', reportId],
    queryFn: () => getReport(reportId!),
    // reportId 있을 때만 실행
    enabled: !!reportId,
  });
}