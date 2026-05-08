# HomeLens AI - 가격 분석 서비스 로직
# 국토부 실거래가 API 연동 및 데이터 가공

import httpx
from app.core.config import settings

# 국토부 API 엔드포인트
MOLIT_SALE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev"
MOLIT_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent"


async def fetch_sale_price(lawd_cd: str, deal_ymd: str) -> dict:
    # 아파트 매매 실거래가 조회
    params = {
        "serviceKey": settings.molit_api_key,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(MOLIT_SALE_URL, params=params)
        response.raise_for_status()
        return response.json()


async def fetch_rent_price(lawd_cd: str, deal_ymd: str) -> dict:
    # 아파트 전월세 실거래가 조회
    params = {
        "serviceKey": settings.molit_api_key,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": 1000,
        "pageNo": 1,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(MOLIT_RENT_URL, params=params)
        response.raise_for_status()
        return response.json()