# HomeLens AI - 지도 서비스 로직
# 카카오맵 API 연동 (주변 인프라 검색)

import httpx
from app.core.config import settings

KAKAO_CATEGORY_URL = "https://dapi.kakao.com/v2/local/search/category.json"
KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

# 카테고리 검색 코드 (지하철, 마트, 학교만)
CATEGORY_CODES = {
    "subway": "SW8",
    "mart":   "MT1",
    "school": "SC4",
}

# 키워드 검색 목록 (백화점, 병원)
KEYWORD_SEARCH = {
    "department": ["현대백화점", "롯데백화점", "신세계백화점", "갤러리아백화점", "AK백화점", "더현대"],
    "hospital":   ["종합병원", "대학병원", "의료원", "병원"],
}

CATEGORY_CONFIG = {
    "subway":     {"radius": 1500, "limit": 3},
    "mart":       {"radius": 1500, "limit": 2},
    "department": {"radius": 1500, "limit": 1},
    "hospital":   {"radius": 1500, "limit": 2},
    "school":     {"radius": 1500, "limit": 5},
}

# 대형마트 정확한 이름 매칭
EXACT_MART_NAMES = [
    "이마트", "홈플러스", "롯데마트", "코스트코",
    "이마트 트레이더스", "트레이더스",
    "농협하나로마트", "하나로마트",
    "메가마트", "롯데 빅마켓", "빅마켓",
]

# 대형마트 제외 키워드
MART_EXCLUDE_KEYWORDS = [
    "이마트24", "이마트에브리데이",
    "홈플러스익스프레스", "홈플러스 익스프레스",
    "롯데슈퍼", "GS더프레시", "GS슈퍼",
    "노브랜드", "익스프레스", "슈퍼마켓",
]

# 학교 타입 분류
SCHOOL_TYPES = {
    "초등학교": "elementary",
    "중학교":   "middle",
    "고등학교": "high",
}

# 학교 타입별 표시 텍스트
SCHOOL_TYPE_LABELS = {
    "elementary": "초등학교",
    "middle": "중학교",
    "high": "고등학교",
}

# 대학 제외 키워드
UNIVERSITY_KEYWORDS = ["대학교", "대학원", "전문대"]


async def search_by_keyword(
    lat: float,
    lng: float,
    keyword: str,
    radius: int,
) -> list:
    # 키워드 검색 API 호출
    headers = {"Authorization": f"KakaoAK {settings.kakao_api_key}"}
    params = {
        "query": keyword,
        "y": lat,
        "x": lng,
        "radius": radius,
        "size": 5,
        "sort": "distance",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(KAKAO_KEYWORD_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("documents", [])


async def search_nearby_places(
    lat: float,
    lng: float,
    category: str,
    radius: int = None,
    limit: int = None,
) -> dict:
    config = CATEGORY_CONFIG.get(category, {"radius": 1000, "limit": 3})
    _radius = radius or config["radius"]
    _limit = limit or config["limit"]
    headers = {"Authorization": f"KakaoAK {settings.kakao_api_key}"}

    # 백화점/병원은 키워드 검색으로 처리
    if category in KEYWORD_SEARCH:
        all_docs = []
        seen_ids = set()
        for keyword in KEYWORD_SEARCH[category]:
            docs = await search_by_keyword(lat, lng, keyword, _radius)
            for doc in docs:
                if doc.get("id") not in seen_ids:
                    seen_ids.add(doc.get("id"))
                    all_docs.append(doc)

        # 병원은 소규모 의원 제외
        HOSPITAL_INCLUDE_CATEGORIES = ["종합병원", "대학병원", "요양병원"]

        if category == "hospital":
            all_docs = [
                doc for doc in all_docs
                if any(kw in doc.get("category_name", "") for kw in HOSPITAL_INCLUDE_CATEGORIES)
            ]

        DEPARTMENT_BRAND_NAMES = [
            "현대백화점", "롯데백화점", "신세계백화점",
            "갤러리아백화점", "갤러리아", "AK백화점",
            "AK플라자", "더현대",
        ]

        if category == "department":
            filtered = []
            seen_brands = set()
            for doc in all_docs:
                for brand in DEPARTMENT_BRAND_NAMES:
                    if brand in doc.get("place_name", "") and brand not in seen_brands:
                        doc["place_name"] = brand
                        seen_brands.add(brand)
                        filtered.append(doc)
                        break
            all_docs = filtered

        # 거리순 정렬
        all_docs.sort(key=lambda x: int(x.get("distance", 0)))
        return {"documents": all_docs[:_limit]}

    # 지하철/마트/학교는 카테고리 검색
    params = {
        "category_group_code": CATEGORY_CODES.get(category, "SW8"),
        "y": lat,
        "x": lng,
        "radius": _radius,
        "size": 15,
        "sort": "distance",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(KAKAO_CATEGORY_URL, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()

    documents = result.get("documents", [])

    if category == "mart":
        documents = [
            doc for doc in documents
            if not any(kw in doc.get("place_name", "") for kw in MART_EXCLUDE_KEYWORDS)
            and any(
                doc.get("place_name", "").startswith(name + " ")
                or doc.get("place_name", "") == name
                for name in EXACT_MART_NAMES
            )
        ]
        # 브랜드명만 추출 (지점명 제거)
        for doc in documents:
            for name in EXACT_MART_NAMES:
                if doc.get("place_name", "").startswith(name):
                    doc["place_name"] = name
                    break
        result["documents"] = documents[:_limit]

    elif category == "school":
        documents = [
            doc for doc in documents
            if not any(kw in doc.get("place_name", "") for kw in UNIVERSITY_KEYWORDS)
        ]
        selected = {}
        for doc in documents:
            category_name = doc.get("category_name", "")
            for school_type, key in SCHOOL_TYPES.items():
                if school_type in category_name and key not in selected:
                    doc["school_type"] = key  # elementary / middle / high
                    # place_name은 그대로 유지 (학교 실제 이름)
                    selected[key] = doc
                    break
        result["documents"] = list(selected.values())

    else:
        result["documents"] = documents[:_limit]

    return result


async def search_all_nearby_infra(lat: float, lng: float, radius: int = None) -> dict:
    results = {}
    all_categories = list(CATEGORY_CODES.keys()) + list(KEYWORD_SEARCH.keys())
    for category in all_categories:
        results[category] = await search_nearby_places(lat, lng, category, radius)
    return results