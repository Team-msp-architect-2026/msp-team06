// HomeLens AI - AI 리포트 API 호출 함수
// POST /api/v1/reports
// GET /api/v1/reports/{reportId}/status
// GET /api/v1/reports/{reportId}

import { apiGet, apiPost } from './client';

export interface ReportCreateResponse {
  reportId: string;
  status: string;
  estimatedSeconds: number | null;
  cachedAt: string | null;
}

export interface ReportStatusResponse {
  reportId: string;
  status: string;
  progressPct: number | null;
  completedAt: string | null;
  failReason: string | null;
}

export interface ReportSection {
  sectionKey: string;
  sectionTitle: string;
  content: string;
  sortOrder: number;
}

export interface ReportResponse {
  reportId: string;
  regionId: string;
  summary: string;
  sections: ReportSection[];
  disclaimer: string;
  generatedAt: string;
  dataBaseDate: string;
}

// AI 리포트 생성 요청
export async function createReport(
  regionId: string,
  regionName?: string,
  lat?: number,
  lng?: number,
): Promise<ReportCreateResponse> {
  return apiPost<ReportCreateResponse>('/reports', { regionId, regionName, lat, lng });
}

// AI 리포트 생성 상태 조회 (Polling)
export async function getReportStatus(reportId: string): Promise<ReportStatusResponse> {
  return apiGet<ReportStatusResponse>(`/reports/${reportId}/status`);
}

// AI 리포트 결과 조회
export async function getReport(reportId: string): Promise<ReportResponse> {
  return apiGet<ReportResponse>(`/reports/${reportId}`);
}