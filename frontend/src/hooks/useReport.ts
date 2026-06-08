// HomeLens AI - AI 리포트 데이터 조회 훅
// TanStack Query로 캐시 및 Polling 상태 관리

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createReport, getReport, getReportStatus } from '../api/reports';

// AI 리포트 생성 요청 훅
export function useCreateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { regionId: string; regionName?: string; lat?: number; lng?: number }) =>
      createReport(params.regionId, params.regionName, params.lat, params.lng),
    onSuccess: (data) => {
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
    retry: false,
    // 2초마다 상태 조회 (Polling)
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      if (query.state.error) return false;
      // 3분(180초) 이상 polling 중이면 중단
      const fetchCount = query.state.fetchStatus === 'fetching' ? 1 : 0;
      const dataUpdatedAt = query.state.dataUpdatedAt;
      if (dataUpdatedAt && Date.now() - dataUpdatedAt > 180000) return false;
      return 2000;
    },
  });
}

// AI 리포트 결과 조회 훅
export function useReport(reportId: string | null, status?: string) {
  return useQuery({
    queryKey: ['report', reportId],
    queryFn: () => getReport(reportId!),
    // reportId 있고 completed 상태일 때만 실행
    enabled: !!reportId && status === 'completed',
  });
}