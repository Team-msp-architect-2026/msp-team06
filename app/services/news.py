# HomeLens AI - 뉴스 서비스 로직
# 네이버 뉴스 API 연동

import httpx
from app.core.config import settings

# 네이버 뉴스 API 엔드포인트
NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"


async def search_news(keyword: str, display: int = 10) -> dict:
    # 네이버 뉴스 API로 키워드 검색
    headers = {
        "X-Naver-Client-Id": settings.naver_client_id,
        "X-Naver-Client-Secret": settings.naver_client_secret,
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": "date",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(NAVER_NEWS_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


async def search_real_estate_news(region_name: str = None, display: int = 50) -> dict:
    if region_name:
        keyword = f"{region_name} 아파트 부동산 매매 전세"
    else:
        keyword = "아파트 매매 전세 실거래 부동산시장"
    return await search_news(keyword, display)