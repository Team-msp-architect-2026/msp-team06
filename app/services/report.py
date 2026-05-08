# # HomeLens AI - AI 리포트 생성 서비스 로직
# # Anthropic API 연동 (Claude 모델 사용)

# import anthropic
# from app.core.config import settings

# # Anthropic 클라이언트 초기화
# client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# # AI 리포트 면책 고지 문구
# DISCLAIMER = (
#     "본 리포트는 국토교통부 실거래가·카카오맵·네이버 뉴스 데이터를 기반으로 "
#     "AI가 생성한 참고 자료이며, 부동산 중개나 투자자문이 아닙니다. "
#     "AI 생성 내용은 부정확할 수 있으므로 실제 거래 시에는 공인중개사 등 "
#     "전문가 상담을 권장하며, 거래 결정과 결과에 대한 책임은 이용자에게 있습니다."
# )


# def build_prompt(region_name: str, price_data: dict, news_data: dict, infra_data: dict) -> str:
#     # AI 리포트 생성을 위한 프롬프트 구성
#     return f"""
# 당신은 부동산 정보 분석 AI입니다. 아래 데이터를 기반으로 {region_name} 지역의 부동산 분석 리포트를 작성해주세요.

# [가격 데이터]
# {price_data}

# [뉴스/이슈 데이터]
# {news_data}

# [인프라 데이터]
# {infra_data}

# 다음 4개 섹션으로 작성해주세요.
# 1. 가격 동향: 최근 가격 변화 흐름 및 변동 요인 후보
# 2. 생활 환경: 교통, 학교, 편의시설 등 인프라 종합
# 3. 지역 이슈: 관련 뉴스 및 개발 이슈 요약
# 4. 종합 의견: 실거주·매매 관점 종합 정리

# 주의사항:
# - 원인 단정 금지. '영향 가능 요인 후보' 형태로 표현
# - 투자 권유·법률·세무 조언 미제공
# - 각 섹션은 3~5문장으로 작성
# """


# async def generate_report(
#     region_name: str,
#     price_data: dict,
#     news_data: dict,
#     infra_data: dict,
# ) -> dict:
#     # Claude API로 AI 리포트 생성
#     prompt = build_prompt(region_name, price_data, news_data, infra_data)

#     message = client.messages.create(
#         model="claude-opus-4-6",
#         max_tokens=2000,
#         messages=[
#             {"role": "user", "content": prompt}
#         ],
#     )

#     # 응답 텍스트 파싱
#     content = message.content[0].text

#     return {
#         "content": content,
#         "disclaimer": DISCLAIMER,
#     }

#-------------------------------------------------------------------------

# HomeLens AI - AI 리포트 생성 서비스 로직
# 현재 mock 응답 반환 (Bedrock 연동 후 교체 예정)

# AI 리포트 면책 고지 문구
DISCLAIMER = (
    "본 리포트는 국토교통부 실거래가·카카오맵·네이버 뉴스 데이터를 기반으로 "
    "AI가 생성한 참고 자료이며, 부동산 중개나 투자자문이 아닙니다. "
    "AI 생성 내용은 부정확할 수 있으므로 실제 거래 시에는 공인중개사 등 "
    "전문가 상담을 권장하며, 거래 결정과 결과에 대한 책임은 이용자에게 있습니다."
)

# mock 리포트 섹션 데이터
MOCK_SECTIONS = [
    {
        "sectionKey": "price_trend",
        "sectionTitle": "가격 동향",
        "content": "최근 6개월간 매매 평균가가 완만한 상승세를 보이고 있습니다. 거래량도 전월 대비 증가하는 추세로 실수요자 유입이 지속되는 것으로 보입니다.",
        "sortOrder": 1,
    },
    {
        "sectionKey": "life_env",
        "sectionTitle": "생활 환경",
        "content": "대중교통 접근성이 우수하며 주변 생활 편의시설이 잘 갖춰져 있습니다. 학군 및 의료 환경도 양호한 수준입니다.",
        "sortOrder": 2,
    },
    {
        "sectionKey": "local_issues",
        "sectionTitle": "지역 이슈",
        "content": "해당 지역 관련 개발 계획 논의가 진행 중입니다. 다만 실현 시기가 불확실하므로 단기 의사결정에 과도하게 반영하는 것은 바람직하지 않습니다.",
        "sortOrder": 3,
    },
    {
        "sectionKey": "overall",
        "sectionTitle": "종합 의견",
        "content": "실거주 목적의 수요자에게 긍정적인 지역으로 판단됩니다. 가격 상승세가 지속되고 있어 진입 시점에 대한 신중한 검토가 필요합니다.",
        "sortOrder": 4,
    },
]


async def generate_report(
    region_name: str,
    price_data: dict,
    news_data: dict,
    infra_data: dict,
) -> dict:
    # mock 리포트 반환 (Bedrock 연동 후 실제 AI 생성으로 교체)
    return {
        "content": f"{region_name} 부동산 분석 리포트",
        "sections": MOCK_SECTIONS,
        "disclaimer": DISCLAIMER,
    }    