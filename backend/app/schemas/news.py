# HomeLens AI - 뉴스 API 응답 데이터 형식

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 뉴스 단건 응답 형식
# 제목/AI요약/링크만 포함 (저작권 준수)
class NewsResponse(BaseModel):
    newsId: str
    title: str
    summary: str
    source: str
    url: str
    publishedAt: str
    category: str
    keywords: Optional[list[str]] = None

# 뉴스 목록 응답 형식
# GET /api/v1/news/highlights 응답에 사용
class NewsHighlightResponse(BaseModel):
    items: list[NewsResponse]