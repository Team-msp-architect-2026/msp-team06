# HomeLens AI - 뉴스 API 엔드포인트

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.news import NewsHighlightResponse
from app.services.news import search_real_estate_news
from app.utils.classify import classify_category

router = APIRouter()

@router.get("/highlights", response_model=NewsHighlightResponse)
async def get_news_highlights(
    limit: int = Query(10, le=20, description="반환 건수"),
    category: Optional[str] = Query("all", description="all | policy | market | development | law"),
    region: Optional[str] = Query("서울", description="검색할 지역명"),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await search_real_estate_news(region, display=50)
        items = result.get("items", [])
        news_list = []
        seen_categories = set()

        for item in items:
            title = item.get("title", "").replace("<b>", "").replace("</b>", "")
            category = classify_category(title)
            
            # 카테고리별 1개씩만
            if category in seen_categories:
                continue
            seen_categories.add(category)
            
            news_list.append({
                "newsId": item.get("link", ""),
                "title": title,
                "summary": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                "source": "네이버 뉴스",
                "url": item.get("link", ""),
                "publishedAt": item.get("pubDate", ""),
                "category": category,
                "keywords": None,
            })

        return {"items": news_list}
    except Exception as e:
        raise HTTPException(status_code=503, detail="외부 API 연결 실패")