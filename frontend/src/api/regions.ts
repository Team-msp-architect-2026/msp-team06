// HomeLens AI - 지역 검색 API 호출 함수
// GET /api/v1/regions/search

import { apiGet } from './client';

export interface RegionSearchItem {
  regionId: string;
  name: string;
  fullAddress: string;
  propertyType: string;
  lat: number;
  lng: number;
  aptSeq?: string;
}

// 동·단지 자동완성 검색
export async function searchRegions(
  q: string,
  limit: number = 10
): Promise<RegionSearchItem[]> {
  return apiGet<RegionSearchItem[]>('/regions/search', { q, limit });
}