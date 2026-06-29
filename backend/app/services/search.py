# HomeLens AI - 검색 서비스 로직
# 도로명주소 API + 카카오맵 API 연동

import httpx
from app.core.config import settings

# 도로명주소 API 엔드포인트
JUSO_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"

# 카카오맵 API 엔드포인트
KAKAO_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_ADDRESS_URL = "https://dapi.kakao.com/v2/local/search/address.json"


async def search_address(keyword: str) -> dict:
    # 도로명주소 API로 주소 검색
    params = {
        "confmKey": settings.juso_api_key,
        "currentPage": 1,
        "countPerPage": 10,
        "keyword": keyword,
        "resultType": "json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(JUSO_URL, params=params)
        response.raise_for_status()
        return response.json()


async def search_kakao_keyword(keyword: str, lat: float = None, lng: float = None) -> dict:
    # 카카오맵 키워드 검색
    headers = {"Authorization": f"KakaoAK {settings.kakao_api_key}"}
    # 서울 중심 좌표 고정 (MVP 서울 전용)
    params = {"query": keyword}
    if lat and lng:
        params["y"] = lat
        params["x"] = lng
    async with httpx.AsyncClient() as client:
        response = await client.get(KAKAO_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


async def search_kakao_address(address: str) -> dict:
    # 카카오맵 주소 검색 (주소 → 좌표 변환)
    headers = {"Authorization": f"KakaoAK {settings.kakao_api_key}"}
    params = {"query": address}
    async with httpx.AsyncClient() as client:
        response = await client.get(KAKAO_ADDRESS_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()