# HomeLens AI - 가격/이슈 분석 API 엔드포인트
# 조회 순서: DB → Redis → 외부 API

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
from app.utils.classify import classify_category
from app.services.price import (
    fetch_sale_price,
    fetch_rent_price,
    get_lawd_cd,
    get_price_snapshot,
    get_price_trend,
    get_price_stats,
    get_kapt_name,
    filter_by_name,
    fetch_price_trend_from_api,
)
from app.services.news import get_region_issues

router = APIRouter()


@router.get("/price", response_model=PriceResponse)
async def get_price(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    dealYmd: str = Query(..., description="조회 계약년월 (YYYYMM 형식)"),
    regionName: Optional[str] = Query(None, description="단지명 필터링용"),
    dealType: Optional[str] = Query("all", description="sale | jeonse | monthly | all"),
    db: AsyncSession = Depends(get_db),
):
    # 1순위: DB → Redis 조회
    snapshot = await get_price_snapshot(regionId, db)
    if snapshot:
        return {
            "avgSalePrice": snapshot.get("avg_sale_price"),
            "avgJeonsePrice": snapshot.get("avg_jeonse_price"),
            "avgMonthlyRent": snapshot.get("avg_monthly_rent"),
            "avgMonthlyDeposit": snapshot.get("avg_monthly_deposit"),
            "jeonseRatio": snapshot.get("jeonse_ratio"),
            "recentTradeCount": snapshot.get("recent_trade_count") or 0,
            "priceStabilityGrade": snapshot.get("price_stability_grade", "normal"),
            "priceLevel": snapshot.get("price_level", "avg"),
            "dataBaseDate": snapshot.get("data_base_date", str(date.today())),
        }

    # 2순위: 외부 API 직접 호출 (fallback)
    try:
        lawd_cd_5, lawd_cd_10 = await get_lawd_cd(lat, lng)

        # 단지목록 API로 공식 단지명 조회
        matched_name = None
        if regionName:
            matched_name = await get_kapt_name(lawd_cd_10, regionName)
            if matched_name:
                print(f"최종 사용 단지명: {matched_name}")

        sale_data = await fetch_sale_price(lawd_cd_5, dealYmd)
        rent_data = await fetch_rent_price(lawd_cd_5, dealYmd)

        # 매매 데이터 파싱
        sale_items = sale_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(sale_items, dict):
            sale_items = [sale_items]

        # 단지명 필터링 (공식 단지명 우선, 없으면 카카오맵 단지명)
        filter_name = matched_name or regionName
        if filter_name and sale_items:
            filtered = filter_by_name(sale_items, filter_name)
            if filtered:
                sale_items = filtered

        avg_sale = int(sum(
            int(str(i.get("dealAmount", "0")).replace(",", ""))
            for i in sale_items
        ) / len(sale_items)) if sale_items else None

        # 전월세 데이터 파싱
        rent_items = rent_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(rent_items, dict):
            rent_items = [rent_items]

        if filter_name and rent_items:
            filtered_rent = filter_by_name(rent_items, filter_name)
            if filtered_rent:
                rent_items = filtered_rent

        jeonse_items = [i for i in rent_items if str(i.get("monthlyRent", "0")) == "0"]
        monthly_items = [i for i in rent_items if str(i.get("monthlyRent", "0")) != "0"]

        avg_jeonse = int(sum(
            int(str(i.get("deposit", "0")).replace(",", ""))
            for i in jeonse_items
        ) / len(jeonse_items)) if jeonse_items else None

        avg_monthly_rent = int(sum(
            int(str(i.get("monthlyRent", "0")).replace(",", ""))
            for i in monthly_items
        ) / len(monthly_items)) if monthly_items else None

        avg_monthly_deposit = int(sum(
            int(str(i.get("deposit", "0")).replace(",", ""))
            for i in monthly_items
        ) / len(monthly_items)) if monthly_items else None

        jeonse_ratio = round(avg_jeonse / avg_sale * 100, 2) if avg_jeonse and avg_sale else None

        return {
            "avgSalePrice": avg_sale,
            "avgJeonsePrice": avg_jeonse,
            "avgMonthlyRent": avg_monthly_rent,
            "avgMonthlyDeposit": avg_monthly_deposit,
            "jeonseRatio": jeonse_ratio,
            "recentTradeCount": len(sale_items),
            "priceStabilityGrade": "normal",
            "priceLevel": "avg",
            "dataBaseDate": date.today(),
        }
    except Exception as e:
        print(f"국토부 API 오류: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/price/trend", response_model=PriceTrendResponse)
async def get_price_trend_endpoint(
    regionId: str = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    period: Optional[str] = Query("1y"),
    dealType: Optional[str] = Query("all"),
    regionName: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # DB → Redis 조회
    trend = await get_price_trend(regionId, dealType, period, db)
    if trend:
        return {
            "trend": trend,
            "changeRate1m": 0.0,
            "changeRate3m": 0.0,
            "changeRate1y": 0.0,
            "dataBaseDate": date.today(),
        }

    # 외부 API fallback
    try:
        print(f"[trend] fetch_price_trend_from_api 호출 시작")
        all_trend = await fetch_price_trend_from_api(lat, lng, regionName)
        print(f"[trend] 결과: {len(all_trend)}건")
        
        # dealType별로 각각 최근 6개월
        if dealType == "all":
            sale = [t for t in all_trend if t["dealType"] == "sale"][:6]
            jeonse = [t for t in all_trend if t["dealType"] == "jeonse"][:6]
            monthly = [t for t in all_trend if t["dealType"] == "monthly"][:6]
            recent = sale + jeonse + monthly
        else:
            recent = [t for t in all_trend if t["dealType"] == dealType][:6]

        return {
            "trend": recent,
            "changeRate1m": 0.0,
            "changeRate3m": 0.0,
            "changeRate1y": 0.0,
            "dataBaseDate": date.today(),
        }
    except Exception as e:
        print(f"가격 추이 API 오류: {e}")
        print(traceback.format_exc())
        return {
            "trend": [],
            "changeRate1m": 0.0,
            "changeRate3m": 0.0,
            "changeRate1y": 0.0,
            "dataBaseDate": date.today(),
        }

@router.get("/price/stats", response_model=PriceStatResponse)
async def get_price_stats_endpoint(
    regionId: str = Query(..., description="서비스 내부 지역 ID"),
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    dealYmd: str = Query(..., description="조회 계약년월 (YYYYMM 형식)"),
    dealType: Optional[str] = Query("all", description="sale | jeonse | monthly | all"),
    period: Optional[str] = Query("1m", description="1m | 3m | 1y"),
    regionName: Optional[str] = Query(None, description="단지명 필터링용"),
    db: AsyncSession = Depends(get_db),
):
    # 1순위: DB → Redis 조회
    stats = await get_price_stats(regionId, dealType, period, db)
    if stats:
        return {
            "minPrice": stats.get("min_price"),
            "avgPrice": stats.get("avg_price"),
            "maxPrice": stats.get("max_price"),
            "totalTradeCount": stats.get("total_trade_count"),
            "recentTradeCount": stats.get("recent_trade_count"),
            "tradeSignal": stats.get("trade_signal", "normal"),
            "dataBaseDate": stats.get("data_base_date", str(date.today())),
        }

    # 2순위: 외부 API fallback
    try:
        lawd_cd_5, lawd_cd_10 = await get_lawd_cd(lat, lng)
        matched_name = None
        if regionName:
            matched_name = await get_kapt_name(lawd_cd_10, regionName)
        filter_name = matched_name or regionName

        sale_data = await fetch_sale_price(lawd_cd_5, dealYmd)
        sale_items = sale_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(sale_items, dict):
            sale_items = [sale_items]

        if filter_name and sale_items:
            filtered = filter_by_name(sale_items, filter_name)
            if filtered:
                sale_items = filtered

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
    # DB → Redis → 네이버 API 순서
    try:
        result = await get_region_issues(regionId, regionName, limit, db)

        # 네이버 API 직접 호출 응답인 경우 가공
        if isinstance(result, list):
            issue_list = []
            seen_categories = set()
            for item in result:
                title = item.get("title", "").replace("<b>", "").replace("</b>", "")
                category = classify_category(title)
                if category in seen_categories:
                    continue
                seen_categories.add(category)
                issue_list.append({
                    "issueId": item.get("url", ""),
                    "type": category,
                    "title": title,
                    "summary": item.get("summary", "").replace("<b>", "").replace("</b>", ""),
                    "impactType": "neutral",
                    "publishedAt": item.get("publishedAt", ""),
                    "url": item.get("url", ""),
                })
                if len(issue_list) >= 5:
                    break
            return {"items": issue_list}
        return {"items": result.get("items", [])}
    except Exception as e:
        print(f"이슈 API 오류: {e}")
        raise HTTPException(status_code=503, detail="외부 API 연결 실패")
