# HomeLens AI - AI 리포트 생성 서비스 로직
# LangChain + Amazon Bedrock Claude 연동

import json
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from app.core.config import settings

MODEL_ID = "eu.anthropic.claude-sonnet-4-6"

llm = ChatBedrock(
    model_id=MODEL_ID,
    region_name="eu-west-3",
    model_kwargs={
        "max_tokens": 2500,
        "temperature": 0.3,
    },
)

DISCLAIMER = (
    "본 리포트는 국토교통부 실거래가·카카오맵·네이버 뉴스 데이터를 기반으로 "
    "AI가 생성한 참고 자료이며, 부동산 중개나 투자자문이 아닙니다. "
    "AI 생성 내용은 부정확할 수 있으므로 실제 거래 시에는 공인중개사 등 "
    "전문가 상담을 권장하며, 거래 결정과 결과에 대한 책임은 이용자에게 있습니다. "
    "데이터 출처: 국토교통부 실거래가 공개시스템"
)


def build_prompt(region_name: str, price_data: dict, news_data: dict, infra_data: dict) -> str:
    return f"""당신은 부동산 정보 분석 AI입니다. 아래 데이터를 기반으로 {region_name} 지역의 부동산 분석 리포트를 작성해주세요.

[가격 데이터]
{json.dumps(price_data, ensure_ascii=False)}

[뉴스/이슈 데이터]
{json.dumps(news_data, ensure_ascii=False)}

[인프라 데이터]
{json.dumps(infra_data, ensure_ascii=False)}

다음 JSON 형식으로만 응답해주세요. 다른 텍스트 없이 JSON만 출력:
{{
  "summary": "2문장 이내. 이 지역이 어떤 곳인지, 지금 시장 분위기가 어떤지 핵심만.",
  "sections": [
    {{
      "sectionKey": "price_trend",
      "sectionTitle": "가격 동향",
      "content": "마크다운 형식으로 작성. **소제목**으로 단락 구분, - 항목으로 목록 표현. 가격 흐름과 배경을 수치 활용해 설명. 데이터 없으면 지역 특성 기반으로 서술.",
      "sortOrder": 1
    }},
    {{
      "sectionKey": "life_env",
      "sectionTitle": "생활 환경",
      "content": "마크다운 형식으로 작성. **소제목**으로 단락 구분, - 항목으로 목록 표현. 교통·학교·편의시설 등 실생활 핵심 시설 설명.",
      "sortOrder": 2
    }},
    {{
      "sectionKey": "local_issues",
      "sectionTitle": "지역 이슈",
      "content": "마크다운 형식으로 작성. **소제목**으로 단락 구분, - 항목으로 목록 표현. 재개발·교통 호재·규제 등 가격과 생활에 영향을 줄 이슈 설명.",
      "sortOrder": 3
    }},
    {{
      "sectionKey": "overall",
      "sectionTitle": "종합 의견",
      "content": "마크다운 형식으로 작성. **소제목**으로 단락 구분, - 항목으로 목록 표현. 거주·매매 고려 시 알아야 할 핵심 사항. 장단점 균형 있게 서술.",
      "sortOrder": 4
    }}
  ]
}}

작성 원칙:
- 부동산 초보자도 이해할 수 있는 쉬운 표현 사용
- 원인 단정 금지. '~가능성이 있습니다', '~요인 중 하나로 볼 수 있습니다' 형태로 표현
- 투자 권유·법률·세무 조언 절대 미제공
- 'API 연동 필요', '데이터 연동' 등 개발 관련 문구 절대 사용 금지
- 데이터 부족 시 지역 특성과 공개된 정보를 바탕으로 자연스럽게 서술
- summary는 반드시 2문장 이내
- 쓸데없는 반복이나 불필요한 문장 없이 핵심 위주로 작성
- content는 반드시 마크다운 형식으로 작성 (**소제목**, - 목록 활용)
- JSON 형식 외 다른 텍스트 출력 금지"""


async def generate_report(
    region_name: str,
    price_data: dict,
    news_data: dict,
    infra_data: dict,
):
    try:
        prompt = build_prompt(region_name, price_data, news_data, infra_data)
        
        response = await llm.ainvoke(
            [HumanMessage(content=prompt)],
            config={"timeout": 60}
        )
        
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())

        return {
            "summary": result.get("summary", ""),
            "sections": result.get("sections", []),
            "disclaimer": DISCLAIMER,
        }

    except Exception as e:
        print(f"LangChain/Bedrock 오류: {e}")
        return {
            "summary": f"{region_name} 부동산 분석 리포트 (데이터 준비 중)",
            "sections": [
                {"sectionKey": "price_trend", "sectionTitle": "가격 동향", "content": "데이터를 불러오지 못했습니다.", "sortOrder": 1},
                {"sectionKey": "life_env", "sectionTitle": "생활 환경", "content": "데이터를 불러오지 못했습니다.", "sortOrder": 2},
                {"sectionKey": "local_issues", "sectionTitle": "지역 이슈", "content": "데이터를 불러오지 못했습니다.", "sortOrder": 3},
                {"sectionKey": "overall", "sectionTitle": "종합 의견", "content": "데이터를 불러오지 못했습니다.", "sortOrder": 4},
            ],
            "disclaimer": DISCLAIMER,
        }