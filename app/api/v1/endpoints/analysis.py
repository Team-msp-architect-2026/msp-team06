# HomeLens AI - 가격/이슈 분석 API 엔드포인트

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
from app.schemas.analysis import (
    PriceResponse,
    PriceTrendResponse,
    PriceStatResponse,
    IssueResponse,
)
from app.services.price import fetch_sale_price, fetch_rent_price
from app.services.news import search_real_estate_news
from app.utils.classify import classify_category

router = APIRouter()


@router.get("/price", response_model=PriceResponse)
async def get_price(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    lawdCd: str = Query(..., description="법정동 코드 앞 5자리 (예: 11680)"),
    dealYmd: str = Query(..., description="조회 계약년월 (YYYYMM 형식)"),
    dealType: Optional[str] = Query("all", description="sale | jeonse | monthly | all"),
    db: AsyncSession = Depends(get_db),
):
    # 국토부 실거래가 API로 가격 현황 조회
    try:
        sale_data = await fetch_sale_price(lawdCd, dealYmd)
        rent_data = await fetch_rent_price(lawdCd, dealYmd)

        # 매매 평균가 계산
        sale_items = sale_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(sale_items, dict):
            sale_items = [sale_items]
        avg_sale = int(sum(
            int(str(i.get("dealAmount", "0")).replace(",", ""))
            for i in sale_items
        ) / len(sale_items)) if sale_items else None

        return {
            "avgSalePrice": avg_sale,
            "avgJeonsePrice": None,
            "avgMonthlyRent": None,
            "avgMonthlyDeposit": None,
            "jeonseRatio": None,
            "recentTradeCount": len(sale_items),
            "priceStabilityGrade": "normal",
            "priceLevel": "avg",
            "dataBaseDate": date.today(),
        }
    except Exception as e:
        print(f"국토부 API 오류: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/price/trend", response_model=PriceTrendResponse)
async def get_price_trend(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    period: Optional[str] = Query("1y", description="1m | 3m | 1y"),
    dealType: Optional[str] = Query("all", description="sale | jeonse | monthly | all"),
    db: AsyncSession = Depends(get_db),
):
    # TODO: 기간별 가격 추이 데이터 구현 필요
    return {
        "trend": [],
        "changeRate1m": 0.0,
        "changeRate3m": 0.0,
        "changeRate1y": 0.0,
        "dataBaseDate": date.today(),
    }


@router.get("/price/stats", response_model=PriceStatResponse)
async def get_price_stats(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    lawdCd: str = Query(..., description="법정동 코드 앞 5자리"),
    dealYmd: str = Query(..., description="조회 계약년월 (YYYYMM 형식)"),
    dealType: Optional[str] = Query("all", description="sale | jeonse | monthly | all"),
    period: Optional[str] = Query("1m", description="1m | 3m | 1y"),
    db: AsyncSession = Depends(get_db),
):
    # 국토부 실거래가 API로 가격 통계 (최저/평균/최고) 조회
    try:
        sale_data = await fetch_sale_price(lawdCd, dealYmd)
        sale_items = sale_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(sale_items, dict):
            sale_items = [sale_items]

        # 거래가 목록 추출
        prices = [
            int(str(i.get("dealAmount", "0")).replace(",", ""))
            for i in sale_items
        ]

        if not prices:
            raise HTTPException(status_code=404, detail="거래 데이터 없음")

        return {
            "minPrice": min(prices),
            "avgPrice": int(sum(prices) / len(prices)),
            "maxPrice": max(prices),
            "totalTradeCount": len(prices),
            "recentTradeCount": len(prices),
            "tradeSignal": "normal",
            "dataBaseDate": date.today(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail="외부 API 연결 실패")


@router.get("/issues", response_model=IssueResponse)
async def get_issues(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    regionName: str = Query(..., description="지역명 (뉴스 검색용)"),
    limit: int = Query(20, description="반환 건수"),
    db: AsyncSession = Depends(get_db),
):
    # 네이버 뉴스 API로 지역 관련 이슈/뉴스 조회
    try:
        result = await search_real_estate_news(regionName, display=50)
        items = result.get("items", [])
        issue_list = []
        seen_categories = set()

        for item in items:
            title = item.get("title", "").replace("<b>", "").replace("</b>", "")
            category = classify_category(title)

            if category in seen_categories:
                continue
            seen_categories.add(category)

            issue_list.append({
                "issueId": item.get("link", ""),
                "type": category,
                "title": title,
                "summary": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                "impactType": "neutral",
                "publishedAt": item.get("pubDate", ""),
                "url": item.get("link", ""),
            })

            if len(issue_list) >= 5:
                break

        return {"items": issue_list}
    except Exception as e:
        raise HTTPException(status_code=503, detail="외부 API 연결 실패")