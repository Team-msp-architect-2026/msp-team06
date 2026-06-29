// HomeLens AI - 뉴스 API 호출 함수
// GET /api/v1/news/highlights

import { apiGet } from './client';

export interface NewsItem {
  newsId: string;
  title: string;
  summary: string;
  source: string;
  url: string;
  publishedAt: string;
  category: string;
  keywords: string[] | null;
}

export interface NewsHighlightResponse {
  items: NewsItem[];
}

// 메인화면 주요 뉴스 목록 조회
export async function getNewsHighlights(
  region: string = '서울',
  limit: number = 10,
  category: string = 'all'
): Promise<NewsHighlightResponse> {
  return apiGet<NewsHighlightResponse>('/news/highlights', {
    region,
    limit,
    category,
  });
}