# HomeLens AI - 가격 분석 서비스 로직
# 국토부 실거래가 API 연동 및 데이터 가공

import httpx
import xmltodict
from app.core.config import settings

MOLIT_SALE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
MOLIT_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
KAKAO_COORD2REGION_URL = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"


async def get_lawd_cd(lat: float, lng: float) -> str:
    # 카카오 좌표 → 법정동 코드 앞 5자리 조회
    headers = {"Authorization": f"KakaoAK {settings.kakao_api_key}"}
    params = {"x": lng, "y": lat}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(KAKAO_COORD2REGION_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        documents = data.get("documents", [])
        for doc in documents:
            if doc.get("region_type") == "B":  # B = 법정동
                code = doc.get("code", "")
                return code[:5]  # 앞 5자리만 반환
    raise ValueError("법정동 코드 조회 실패")


async def fetch_sale_price(lawd_cd: str, deal_ymd: str) -> dict:
    # 아파트 매매 실거래가 조회 (XML 응답 파싱)
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
    # 아파트 전월세 실거래가 조회 (XML 응답 파싱)
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