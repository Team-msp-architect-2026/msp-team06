# HomeLens AI - 가격 분석 서비스 로직
# 조회 순서: DB → Redis → 외부 API
import re
import httpx
import xmltodict
from difflib import SequenceMatcher
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
from datetime import date
from app.core.config import settings
from app.core.redis import cache_get, cache_set, TTL_PRICE
from app.models.price import PriceSnapshot, PriceTrend, PriceStat

MOLIT_SALE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
MOLIT_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
KAKAO_COORD2REGION_URL = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
KAPT_LIST_URL = "https://apis.data.go.kr/1613000/AptListService3/getLegaldongAptList3"


def clean_name(name: str) -> str:
    # 괄호 안 내용 제거 + 공백 정리
    name = re.sub(r'\(.*?\)', '', name).strip()
    name = re.sub(r'\s+', '', name)  # 공백 제거
    return name


def name_similarity(a: str, b: str) -> float:
    a = clean_name(a)
    b = clean_name(b)
    return SequenceMatcher(None, a, b).ratio()


def filter_by_name(items: list, region_name: str, threshold: float = 0.7) -> list:
    # 1순위: 완전 포함 매칭
    exact = [i for i in items if region_name in str(i.get("aptNm", ""))
             or str(i.get("aptNm", "")) in region_name]
    if exact:
        return exact

    # 2순위: 유사도 매칭
    scored = [
        (i, name_similarity(region_name, str(i.get("aptNm", ""))))
        for i in items
    ]
    filtered = [i for i, score in scored if score >= threshold]
    return filtered if filtered else []


async def get_lawd_cd(lat: float, lng: float) -> tuple[str, str]:
    # 카카오 좌표 → 법정동 코드 5자리 + 10자리 반환
    headers = {"Authorization": f"KakaoAK {settings.kakao_api_key}"}
    params = {"x": lng, "y": lat}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(KAKAO_COORD2REGION_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        documents = data.get("documents", [])
        for doc in documents:
            if doc.get("region_type") == "B":
                code = doc.get("code", "")
                return code[:5], code  # (5자리, 10자리)
    raise ValueError("법정동 코드 조회 실패")


async def get_kapt_name(bjd_code: str, region_name: str) -> str | None:
    # 단지목록 API로 국토부 공식 단지명 조회
    # Redis 캐시 적용 (동 단위 단지 목록은 자주 안 바뀜)
    cache_key = f"kapt:list:{bjd_code}"
    cached = await cache_get(cache_key)

    if cached:
        kapt_list = cached
    else:
        try:
            params = {
                "serviceKey": settings.molit_api_key,
                "bjdCode": bjd_code,
                "pageNo": 1,
                "numOfRows": 100,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(KAPT_LIST_URL, params=params)
                response.raise_for_status()
                data = response.json()
                items = data.get("response", {}).get("body", {}).get("items", [])
                kapt_list = items if items else []
            await cache_set(cache_key, kapt_list, 60 * 60 * 24 * 7)  # 7일 캐시
        except Exception as e:
            print(f"단지목록 API 오류: {e}")
            return None

    if not kapt_list:
        return None

    # 카카오맵 단지명과 가장 유사한 kaptName 찾기
    scored = [
        (item.get("kaptName", ""), name_similarity(region_name, item.get("kaptName", "")))
        for item in kapt_list
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    if scored and scored[0][1] >= 0.6:
        print(f"단지명 매칭: {region_name} → {scored[0][0]} (유사도: {scored[0][1]:.2f})")
        return scored[0][0]

    return None


async def fetch_sale_price(lawd_cd: str, deal_ymd: str) -> dict:
    params = {
        "serviceKey": settings.molit_api_key,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(MOLIT_SALE_URL, params=params)
        response.raise_for_status()
        return xmltodict.parse(response.text)


async def fetch_rent_price(lawd_cd: str, deal_ymd: str) -> dict:
    params = {
        "serviceKey": settings.molit_api_key,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(MOLIT_RENT_URL, params=params)
        response.raise_for_status()
        return xmltodict.parse(response.text)


async def get_price_snapshot(region_id: str, db: AsyncSession) -> dict | None:
    cache_key = f"price:snapshot:{region_id}"

    cached = await cache_get(cache_key)
    if cached:
        cached["source"] = "redis"
        return cached

    try:
        result = await db.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.region_id == region_id)
            .order_by(desc(PriceSnapshot.data_base_date))
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if snapshot:
            data = {
                "avg_sale_price": snapshot.avg_sale_price,
                "avg_jeonse_price": snapshot.avg_jeonse_price,
                "avg_monthly_rent": snapshot.avg_monthly_rent,
                "avg_monthly_deposit": snapshot.avg_monthly_deposit,
                "jeonse_ratio": float(snapshot.jeonse_ratio) if snapshot.jeonse_ratio else None,
                "recent_trade_count": snapshot.recent_trade_count,
                "price_stability_grade": snapshot.price_stability_grade,
                "price_level": snapshot.price_level,
                "data_base_date": str(snapshot.data_base_date),
                "source": "db",
            }
            await cache_set(cache_key, data, TTL_PRICE)
            return data
    except Exception as e:
        print(f"DB 조회 실패 (fallback 진행): {e}")

    return None


async def get_price_trend(region_id: str, deal_type: str, period: str, db: AsyncSession) -> list | None:
    cache_key = f"price:trend:{region_id}:{deal_type}:{period}"

    cached = await cache_get(cache_key)
    if cached:
        print(f"[trend] Redis 캐시 히트: {cache_key}")
        return cached

    try:
        result = await db.execute(
            select(PriceTrend)
            .where(
                PriceTrend.region_id == region_id,
                PriceTrend.deal_type == deal_type,
            )
            .order_by(desc(PriceTrend.month))
            .limit(12 if period == "1y" else 3 if period == "3m" else 1)
        )
        trends = result.scalars().all()
        if trends:
            data = [
                {
                    "month": t.month,
                    "avg_price": t.avg_price,
                    "deal_type": t.deal_type,
                    "trade_count": t.trade_count,
                }
                for t in trends
            ]
            await cache_set(cache_key, data, TTL_PRICE)
            return data
    except Exception as e:
        print(f"DB 조회 실패 (fallback 진행): {e}")
    
    print(f"[trend] DB/Redis 없음, None 반환")
    return None


async def get_price_stats(region_id: str, deal_type: str, period: str, db: AsyncSession) -> dict | None:
    cache_key = f"price:stats:{region_id}:{deal_type}:{period}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        result = await db.execute(
            select(PriceStat)
            .where(
                PriceStat.region_id == region_id,
                PriceStat.deal_type == deal_type,
                PriceStat.period == period,
            )
            .order_by(desc(PriceStat.data_base_date))
            .limit(1)
        )
        stat = result.scalar_one_or_none()
        if stat:
            data = {
                "min_price": stat.min_price,
                "avg_price": stat.avg_price,
                "max_price": stat.max_price,
                "total_trade_count": stat.total_trade_count,
                "recent_trade_count": stat.recent_trade_count,
                "trade_signal": stat.trade_signal,
                "data_base_date": str(stat.data_base_date),
                "source": "db",
            }
            await cache_set(cache_key, data, TTL_PRICE)
            return data
    except Exception as e:
        print(f"DB 조회 실패 (fallback 진행): {e}")

    return None

async def fetch_price_trend_from_api(
    lat: float, lng: float, region_name: str = None
) -> list:
    import asyncio
    from datetime import datetime

    now = datetime.now()
    months = []
    for i in range(12):
        year = now.year
        month = now.month - i
        if month <= 0:
            month += 12
            year -= 1
        months.append(f"{year}{str(month).zfill(2)}")

    lawd_cd_5, lawd_cd_10 = await get_lawd_cd(lat, lng)

    matched_name = None
    if region_name:
        matched_name = await get_kapt_name(lawd_cd_10, region_name)
    filter_name = matched_name or region_name

    # 12개월 병렬 호출
    sale_tasks = [fetch_sale_price(lawd_cd_5, m) for m in months]
    rent_tasks = [fetch_rent_price(lawd_cd_5, m) for m in months]

    sale_results = await asyncio.gather(*sale_tasks, return_exceptions=True)
    rent_results = await asyncio.gather(*rent_tasks, return_exceptions=True)

    # 첫 번째 달에서 aptSeq 찾기
    apt_seq = None
    for result in sale_results:
        if isinstance(result, Exception):
            continue
        items = result.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        if not items:
            continue
        if filter_name:
            for item in items:
                score = name_similarity(filter_name, str(item.get("aptNm", "")))
                if score >= 0.7:
                    apt_seq = item.get("aptSeq")
                    print(f"[trend] aptSeq 확보: {apt_seq} ({item.get('aptNm')})")
                    break
        if apt_seq:
            break

    trend = []
    for i, month in enumerate(months):
        # 매매 처리
        if not isinstance(sale_results[i], Exception):
            items = sale_results[i].get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(items, dict):
                items = [items]

            # aptSeq로 필터링 (있으면 우선), 없으면 단지명 필터링
            if apt_seq:
                filtered = [x for x in items if x.get("aptSeq") == apt_seq]
            elif filter_name:
                filtered = filter_by_name(items, filter_name)
            else:
                filtered = items

            if filtered:
                avg = int(sum(
                    int(str(x.get("dealAmount", "0")).replace(",", ""))
                    for x in filtered
                ) / len(filtered))
                trend.append({
                    "month": f"{month[:4]}-{month[4:]}",
                    "avgPrice": avg,
                    "dealType": "sale",
                    "tradeCount": len(filtered),
                })

        # 전월세 처리
        if not isinstance(rent_results[i], Exception):
            items = rent_results[i].get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(items, dict):
                items = [items]

            # aptSeq로 필터링
            if apt_seq:
                filtered_rent = [x for x in items if x.get("aptSeq") == apt_seq]
            elif filter_name:
                filtered_rent = filter_by_name(items, filter_name)
            else:
                filtered_rent = items

            # 전세
            jeonse = [x for x in filtered_rent if str(x.get("monthlyRent", "0")) == "0"]
            if jeonse:
                avg = int(sum(
                    int(str(x.get("deposit", "0")).replace(",", ""))
                    for x in jeonse
                ) / len(jeonse))
                trend.append({
                    "month": f"{month[:4]}-{month[4:]}",
                    "avgPrice": avg,
                    "dealType": "jeonse",
                    "tradeCount": len(jeonse),
                })

            # 월세
            monthly = [x for x in filtered_rent if str(x.get("monthlyRent", "0")) != "0"]
            if monthly:
                avg_rent = int(sum(
                    int(str(x.get("monthlyRent", "0")).replace(",", ""))
                    for x in monthly
                ) / len(monthly))
                avg_deposit = int(sum(
                    int(str(x.get("deposit", "0")).replace(",", ""))
                    for x in monthly
                ) / len(monthly))
                trend.append({
                    "month": f"{month[:4]}-{month[4:]}",
                    "avgPrice": avg_rent,
                    "avgDeposit": avg_deposit,
                    "dealType": "monthly",
                    "tradeCount": len(monthly),
                })

    trend.sort(key=lambda x: x["month"], reverse=True)
    return trend

async def get_price_snapshot_by_apt_seq(apt_seq: str, db: AsyncSession) -> dict | None:
    """apt_seq 기반 가격 현황 조회"""
    cache_key = f"price:snapshot:apt:{apt_seq}"
    
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        result = await db.execute(
            text("""
                SELECT 
                    deal_type,
                    avg_price,
                    trade_count,
                    month
                FROM price_trends
                WHERE apt_seq = :apt_seq
                AND apt_seq IS NOT NULL
                ORDER BY month DESC
                LIMIT 10
            """),
            {"apt_seq": apt_seq}
        )
        rows = result.fetchall()
        if not rows:
            return None

        sale_rows = [r for r in rows if r[0] == "sale"]
        jeonse_rows = [r for r in rows if r[0] == "jeonse"]
        monthly_rows = [r for r in rows if r[0] == "monthly"]

        data = {
            "avgSalePrice": sale_rows[0][1] if sale_rows else None,
            "avgJeonsePrice": jeonse_rows[0][1] if jeonse_rows else None,
            "avgMonthlyRent": monthly_rows[0][1] if monthly_rows else None,
            "avgMonthlyDeposit": None,
            "jeonseRatio": round(jeonse_rows[0][1] / sale_rows[0][1] * 100, 2)
                if jeonse_rows and sale_rows and sale_rows[0][1] else None,
            "recentTradeCount": sale_rows[0][2] if sale_rows else 0,
            "priceStabilityGrade": "normal",
            "priceLevel": "avg",
            "dataBaseDate": sale_rows[0][3] + "-01" if sale_rows else str(date.today()),
            "source": "db_apt_seq",
        }
        await cache_set(cache_key, data, TTL_PRICE)
        return data
    except Exception as e:
        print(f"apt_seq 기반 가격 조회 실패: {e}")
        return None


async def get_price_trend_by_apt_seq(apt_seq: str, deal_type: str, period: str, db: AsyncSession) -> list | None:
    """apt_seq 기반 가격 추이 조회"""
    cache_key = f"price:trend:apt:{apt_seq}:{deal_type}:{period}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        limit = 12 if period == "1y" else 3 if period == "3m" else 1

        if deal_type == "all":
            result = await db.execute(
                text("""
                    SELECT month, avg_price, deal_type, trade_count
                    FROM price_trends
                    WHERE apt_seq = :apt_seq
                    AND apt_seq IS NOT NULL
                    ORDER BY month DESC
                    LIMIT :limit
                """),
                {"apt_seq": apt_seq, "limit": limit * 3}
            )
        else:
            result = await db.execute(
                text("""
                    SELECT month, avg_price, deal_type, trade_count
                    FROM price_trends
                    WHERE apt_seq = :apt_seq
                    AND deal_type = :deal_type
                    AND apt_seq IS NOT NULL
                    ORDER BY month DESC
                    LIMIT :limit
                """),
                {"apt_seq": apt_seq, "deal_type": deal_type, "limit": limit}
            )

        rows = result.fetchall()
        if not rows:
            return None

        data = [
            {
                "month": r[0],
                "avgPrice": r[1],
                "dealType": r[2],
                "tradeCount": r[3],
            }
            for r in rows
        ]
        await cache_set(cache_key, data, TTL_PRICE)
        return data
    except Exception as e:
        print(f"apt_seq 기반 추이 조회 실패: {e}")
        return None


async def get_price_stats_by_apt_seq(apt_seq: str, deal_type: str, period: str, db: AsyncSession) -> dict | None:
    """apt_seq 기반 가격 통계 조회"""
    cache_key = f"price:stats:apt:{apt_seq}:{deal_type}:{period}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        if deal_type == "all":
            result = await db.execute(
                text("""
                    SELECT MIN(avg_price), AVG(avg_price), MAX(avg_price), SUM(trade_count)
                    FROM price_trends
                    WHERE apt_seq = :apt_seq
                    AND apt_seq IS NOT NULL
                """),
                {"apt_seq": apt_seq}
            )
        else:
            result = await db.execute(
                text("""
                    SELECT MIN(avg_price), AVG(avg_price), MAX(avg_price), SUM(trade_count)
                    FROM price_trends
                    WHERE apt_seq = :apt_seq
                    AND deal_type = :deal_type
                    AND apt_seq IS NOT NULL
                """),
                {"apt_seq": apt_seq, "deal_type": deal_type}
            )

        row = result.fetchone()
        if not row or not row[0]:
            return None

        trade_count = int(row[3]) if row[3] else 0
        data = {
            "minPrice": int(row[0]),
            "avgPrice": int(row[1]),
            "maxPrice": int(row[2]),
            "totalTradeCount": trade_count,
            "recentTradeCount": trade_count,
            "tradeSignal": "active" if trade_count >= 10 else "normal" if trade_count >= 3 else "low",
            "dataBaseDate": str(date.today()),
            "source": "db_apt_seq",
        }
        await cache_set(cache_key, data, TTL_PRICE)
        return data
    except Exception as e:
        print(f"apt_seq 기반 통계 조회 실패: {e}")
        return None