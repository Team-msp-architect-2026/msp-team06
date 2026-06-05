# HomeLens AI - 뉴스 서비스 로직
# 네이버 뉴스 API 연동

import httpx
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis import cache_get, cache_set, TTL_NEWS

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
        keyword = "서울 아파트 매매 전세 실거래 부동산"
    return await search_news(keyword, display)

async def get_news_highlights(region: str = "", limit: int = 10, category: str = "all", db: AsyncSession = None) -> dict:
    cache_key = f"news:highlights:{region}:{category}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        keyword = f"{region} 아파트 부동산" if region else "서울 아파트 매매 전세 부동산"
        data = await search_news(keyword, limit)
        items = data.get("items", [])
        SEOUL_REGIONS = ["서울", "강남", "강북", "송파", "마포", "용산", "성동", "노원", "은평", "관악", "동작", "영등포", "양천", "구로", "금천", "강서", "중랑", "성북", "도봉", "강동", "광진", "동대문", "중구", "종로", "서대문"]
        REALESTATE_KEYWORDS = ["아파트", "전세", "매매", "부동산", "분양", "재건축", "재개발", "집값", "실거래"]
        filtered_items = [
            item for item in items
            if any(kw in item.get("title", "") or kw in item.get("description", "") for kw in SEOUL_REGIONS)
            and any(kw in item.get("title", "") or kw in item.get("description", "") for kw in REALESTATE_KEYWORDS)
        ]
        result = {
            "items": [
                {
                    "newsId": f"naver_{i}",
                    "title": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                    "summary": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                    "source": item.get("originallink", ""),
                    "url": item.get("link", ""),
                    "publishedAt": item.get("pubDate", ""),
                    "category": "market",
                    "keywords": [],
                }
                for i, item in enumerate(filtered_items)
            ]
        }
        await cache_set(cache_key, result, TTL_NEWS)
        return result
    except Exception as e:
        print(f"뉴스 하이라이트 조회 실패: {e}")
        return {"items": []}


async def get_region_issues(region_id: str, region_name: str, display: int = 20, db: AsyncSession = None) -> list:
    cache_key = f"news:issues:{region_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        data = await search_real_estate_news(region_name, display)
        items = data.get("items", [])
        result = [
            {
                "issueId": f"naver_{i}",
                "type": "news",
                "title": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                "summary": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                "impactType": "neutral",
                "publishedAt": item.get("pubDate", ""),
                "url": item.get("link", ""),
            }
            for i, item in enumerate(items)
        ]
        await cache_set(cache_key, result, TTL_NEWS)
        return result
    except Exception as e:
        print(f"지역 이슈 조회 실패: {e}")
        return []