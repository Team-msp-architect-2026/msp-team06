// HomeLens AI - 가격/이슈 분석 API 호출 함수
// GET /api/v1/analysis/price
// GET /api/v1/analysis/price/trend
// GET /api/v1/analysis/price/stats
// GET /api/v1/analysis/issues

import { apiGet } from "./client";

export interface PriceResponse {
  avgSalePrice: number | null;
  avgJeonsePrice: number | null;
  avgMonthlyRent: number | null;
  avgMonthlyDeposit: number | null;
  jeonseRatio: number | null;
  recentTradeCount: number;
  priceStabilityGrade: string;
  priceLevel: string;
  dataBaseDate: string;
}

export interface PriceTrendItem {
  month: string;
  avgPrice: number;
  dealType: string;
  tradeCount: number;
}

export interface PriceTrendResponse {
  trend: PriceTrendItem[];
  changeRate1m: number;
  changeRate3m: number;
  changeRate1y: number | null;
  dataBaseDate: string;
}

export interface PriceStatResponse {
  minPrice: number;
  avgPrice: number;
  maxPrice: number;
  totalTradeCount: number;
  recentTradeCount: number;
  tradeSignal: string;
  dataBaseDate: string;
}

export interface IssueItem {
  issueId: string;
  type: string;
  title: string;
  summary: string;
  impactType: string;
  publishedAt: string;
  url: string | null;
}

export interface IssueResponse {
  items: IssueItem[];
}

// 가격 현황 조회
export async function getPrice(
  regionId: string,
  lat: number,
  lng: number,
  dealYmd: string,
  dealType: string = "all",
  regionName?: string,
): Promise<PriceResponse> {
  return apiGet<PriceResponse>("/analysis/price", {
    regionId,
    lat,
    lng,
    dealYmd,
    dealType,
    regionName,
  });
}

// 가격 추이 조회
export async function getPriceTrend(
  regionId: string,
  lat: number,
  lng: number,
  period: string = "1y",
  dealType: string = "all",
  regionName?: string,
): Promise<PriceTrendResponse> {
  return apiGet<PriceTrendResponse>("/analysis/price/trend", {
    regionId,
    lat,
    lng,
    period,
    dealType,
    regionName,
  });
}

// 가격 통계 조회 (최저/평균/최고)
export async function getPriceStats(
  regionId: string,
  lat: number,
  lng: number,
  dealYmd: string,
  dealType: string = "all",
  period: string = "1m",
  regionName?: string,
): Promise<PriceStatResponse> {
  return apiGet<PriceStatResponse>("/analysis/price/stats", {
    regionId,
    lat,
    lng,
    dealYmd,
    dealType,
    period,
    regionName,
  });
}

// 이슈/뉴스 목록 조회
export async function getIssues(
  regionId: string,
  regionName: string,
  limit: number = 20,
): Promise<IssueResponse> {
  return apiGet<IssueResponse>("/analysis/issues", {
    regionId,
    regionName,
    limit,
  });
}
