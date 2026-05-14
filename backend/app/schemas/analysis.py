# HomeLens AI - 가격/이슈 분석 API 응답 데이터 형식

from pydantic import BaseModel
from typing import Optional
from datetime import date

# 가격 현황 응답 형식
# GET /api/v1/analysis/price 응답에 사용
class PriceResponse(BaseModel):
    avgSalePrice: Optional[int] = None
    avgJeonsePrice: Optional[int] = None
    avgMonthlyRent: Optional[int] = None
    avgMonthlyDeposit: Optional[int] = None
    jeonseRatio: Optional[float] = None
    recentTradeCount: int
    priceStabilityGrade: str
    priceLevel: str
    dataBaseDate: date

# 가격 추이 단건 데이터 형식
class PriceTrendItem(BaseModel):
    month: str
    avgPrice: int
    dealType: str
    tradeCount: int

# 가격 추이 응답 형식
# GET /api/v1/analysis/price/trend 응답에 사용
class PriceTrendResponse(BaseModel):
    trend: list[PriceTrendItem]
    changeRate1m: float
    changeRate3m: float
    changeRate1y: Optional[float] = None
    dataBaseDate: date

# 가격 통계 응답 형식 (최저/평균/최고)
# GET /api/v1/analysis/price/stats 응답에 사용
class PriceStatResponse(BaseModel):
    minPrice: int
    avgPrice: int
    maxPrice: int
    totalTradeCount: int
    recentTradeCount: int
    tradeSignal: str
    dataBaseDate: date

# 이슈 단건 데이터 형식
class IssueItem(BaseModel):
    issueId: str
    type: str
    title: str
    summary: str
    impactType: str
    publishedAt: str
    url: Optional[str] = None

# 이슈/뉴스 목록 응답 형식
# GET /api/v1/analysis/issues 응답에 사용
class IssueResponse(BaseModel):
    items: list[IssueItem]