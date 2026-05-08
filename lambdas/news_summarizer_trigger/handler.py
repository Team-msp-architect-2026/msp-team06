"""
news_summarizer_trigger/handler.py
뉴스 AI 요약 요청 분배
- S3에 저장된 수집 뉴스를 읽어서
- news-summary-queue로 AI 요약 요청 분배
- Step Functions에서 호출
- memory: 1024MB / timeout: 180s
"""
import json
import os
import boto3
from datetime import datetime, timezone

# ── AWS 클라이언트 ─────────────────────────────────────────────
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")
S3_BUCKET = os.environ.get("S3_BUCKET", "")
SQS_NEWS_SUMMARY_URL = os.environ.get("SQS_NEWS_SUMMARY_URL", "")

s3_client = boto3.client("s3", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)


def get_news_from_s3(s3_key: str) -> list:
    """S3에서 수집된 뉴스 원본 조회"""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        news_items = json.loads(response["Body"].read().decode("utf-8"))
        print(f"S3 조회 완료: {s3_key} ({len(news_items)}건)")
        return news_items
    except Exception as e:
        print(f"S3 조회 실패 ({s3_key}): {e}")
        return []


def send_to_summary_queue(news_item: dict) -> bool:
    """news-summary-queue로 AI 요약 요청 전송"""
    try:
        message = {
            "news_id": news_item.get("news_id"),
            "title": news_item.get("title"),
            "description": news_item.get("description"),
            "url": news_item.get("originallink", news_item.get("link", "")),
            "source": news_item.get("source", ""),
            "published_at": news_item.get("pubDate", ""),
            "category": news_item.get("category", "market"),
        }

        sqs_client.send_message(
            QueueUrl=SQS_NEWS_SUMMARY_URL,
            MessageBody=json.dumps(message, ensure_ascii=False),
        )
        return True
    except Exception as e:
        print(f"SQS 전송 실패: {e}")
        return False


def lambda_handler(event, context):
    """Lambda 핸들러 - 뉴스 요약 요청 분배"""
    print(f"뉴스 요약 분배 시작: {datetime.now(timezone.utc).isoformat()}")

    # Step Functions에서 전달받은 S3 키
    s3_key = event.get("s3_key", "")

    # s3_key 없으면 오늘 날짜로 자동 생성
    if not s3_key:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        s3_key = f"raw/news/{today[:10]}"
        print(f"s3_key 없음 - 오늘 날짜로 조회: {s3_key}")

    # S3에서 뉴스 목록 조회
    news_items = get_news_from_s3(s3_key)

    if not news_items:
        return {
            "statusCode": 200,
            "body": json.dumps({
                "queued": 0,
                "message": "뉴스 없음"
            })
        }

    # 뉴스별 SQS 전송
    queued_count = 0
    failed_count = 0

    for item in news_items:
        success = send_to_summary_queue(item)
        if success:
            queued_count += 1
        else:
            failed_count += 1

    print(f"분배 완료: 성공 {queued_count}건 / 실패 {failed_count}건")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "queued": queued_count,
            "failed": failed_count,
            "total": len(news_items),
            "s3_key": s3_key,
        })
    }