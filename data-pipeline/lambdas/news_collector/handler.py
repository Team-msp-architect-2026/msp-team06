"""
news_collector/handler.py
네이버 뉴스 API에서 부동산 뉴스 수집 후 S3 저장
- 매일 새벽 EventBridge 스케줄로 실행
- 수집한 뉴스 원본을 S3에 저장
- news-summary-queue로 AI 요약 요청 전송
"""
import json
import os
import uuid
import boto3
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# 환경변수
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
S3_BUCKET = os.environ.get("RAW_DATA_BUCKET", "")
SQS_NEWS_SUMMARY_URL = os.environ.get("SQS_NEWS_SUMMARY_URL", "")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")

# 부동산 검색 키워드
SEARCH_KEYWORDS = [
    "서울 아파트 실거래가",
    "서울 부동산 시장",
    "아파트 전세 월세",
    "부동산 정책",
    "재개발 재건축",
    "서울 아파트 매매",
]

s3_client = boto3.client("s3", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)
secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)


def get_naver_credentials() -> tuple[str, str]:
    """Secrets Manager에서 네이버 API 키 조회"""
    env = os.environ.get("ENVIRONMENT", "dev")
    secret_name = f"homelens/{env}/naver/news-api"

    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        return secret["client_id"], secret["client_secret"]
    except Exception as e:
        print(f"Secrets Manager 조회 실패: {e}")
        # 환경변수 fallback
        return NAVER_CLIENT_ID, NAVER_CLIENT_SECRET


def search_naver_news(keyword: str, client_id: str, client_secret: str, display: int = 10) -> list:
    """네이버 뉴스 API 검색"""
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_keyword}&display={display}&sort=date"

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("items", [])
    except Exception as e:
        print(f"네이버 뉴스 API 오류 (keyword: {keyword}): {e}")
        return []


def categorize_news(title: str, description: str) -> str:
    """뉴스 카테고리 분류"""
    text = (title + description).lower()

    if any(kw in text for kw in ["정책", "법안", "규제", "세금", "취득세", "양도세"]):
        return "policy"
    elif any(kw in text for kw in ["재개발", "재건축", "개발", "공사", "착공"]):
        return "development"
    elif any(kw in text for kw in ["법원", "판결", "소송", "분쟁"]):
        return "law"
    else:
        return "market"


def save_to_s3(news_items: list, collected_at: str) -> str:
    """수집한 뉴스 원본을 S3에 저장"""
    key = f"raw/news/{collected_at[:10]}/news_{collected_at}.json"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(news_items, ensure_ascii=False),
        ContentType="application/json",
    )
    print(f"S3 저장 완료: s3://{S3_BUCKET}/{key}")
    return key


def send_to_summary_queue(news_items: list) -> int:
    """AI 요약 요청을 SQS news-summary-queue로 전송"""
    sent_count = 0

    for item in news_items:
        try:
            message = {
                "news_id": item.get("news_id"),
                "title": item.get("title"),
                "description": item.get("description"),
                "url": item.get("originallink", item.get("link")),
                "source": item.get("source", ""),
                "published_at": item.get("pubDate"),
                "category": item.get("category", "market"),
            }

            sqs_client.send_message(
                QueueUrl=SQS_NEWS_SUMMARY_URL,
                MessageBody=json.dumps(message, ensure_ascii=False),
                MessageGroupId="news-summary",  # FIFO 큐 사용 시
            )
            sent_count += 1
        except Exception as e:
            print(f"SQS 전송 실패: {e}")

    return sent_count


def lambda_handler(event, context):
    """Lambda 핸들러 - 네이버 뉴스 수집"""
    print(f"뉴스 수집 시작: {datetime.now(timezone.utc).isoformat()}")

    # 네이버 API 키 조회
    client_id, client_secret = get_naver_credentials()
    if not client_id or not client_secret:
        return {
            "statusCode": 500,
            "body": "네이버 API 키 없음"
        }

    collected_at = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    all_news = []
    seen_urls = set()

    # 키워드별 뉴스 수집
    for keyword in SEARCH_KEYWORDS:
        items = search_naver_news(keyword, client_id, client_secret)
        print(f"키워드 '{keyword}': {len(items)}건 수집")

        for item in items:
            url = item.get("originallink", item.get("link", ""))

            # 중복 제거
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # 뉴스 ID 생성
            news_id = f"NEWS_{uuid.uuid4().hex[:12].upper()}"

            # HTML 태그 제거
            title = item.get("title", "").replace("<b>", "").replace("</b>", "")
            description = item.get("description", "").replace("<b>", "").replace("</b>", "")

            all_news.append({
                "news_id": news_id,
                "title": title,
                "description": description,
                "originallink": url,
                "link": item.get("link", ""),
                "source": item.get("source", ""),
                "pubDate": item.get("pubDate", ""),
                "category": categorize_news(title, description),
            })

    print(f"총 수집: {len(all_news)}건 (중복 제거 후)")

    if not all_news:
        return {
            "statusCode": 200,
            "body": json.dumps({"collected": 0, "message": "수집된 뉴스 없음"})
        }

    # S3 저장
    s3_key = save_to_s3(all_news, collected_at)

    # SQS 전송 (AI 요약 요청)
    sent_count = send_to_summary_queue(all_news)

    result = {
        "statusCode": 200,
        "body": json.dumps({
            "collected": len(all_news),
            "s3_key": s3_key,
            "queued_for_summary": sent_count,
            "collected_at": collected_at,
        })
    }

    print(f"뉴스 수집 완료: {result}")
    return result