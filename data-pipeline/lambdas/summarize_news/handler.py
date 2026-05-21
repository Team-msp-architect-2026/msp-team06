"""
summarize_news/handler.py
Bedrock Claude로 뉴스 1~2줄 AI 요약 생성
- SQS news-summary-queue에서 메시지 수신
- Bedrock Claude 호출 → AI 요약 생성
- news 테이블 summary 업데이트
- memory: 1024MB / timeout: 180s
"""
import json
import os
import boto3
import psycopg2
from datetime import datetime, timezone

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")

secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)
bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def get_db_connection():
    """Secrets Manager에서 DB 연결 정보 조회 후 연결"""
    env = os.environ.get("ENV", "dev")
    secret_name = f"homelens/{env}/rds/postgres"

    response = secretsmanager.get_secret_value(SecretId=secret_name)
    creds = json.loads(response["SecretString"])

    # password_secret_arn에서 실제 비밀번호 조회
    password = creds.get("password", "")
    if not password and creds.get("password_secret_arn"):
        pw_response = secretsmanager.get_secret_value(
            SecretId=creds["password_secret_arn"]
        )
        pw_secret = json.loads(pw_response["SecretString"])
        password = pw_secret.get("password", "")

    return psycopg2.connect(
        host=creds["host"],
        port=int(creds["port"]),
        user=creds["username"],
        password=password,
        dbname=creds["dbname"],
    )


def get_bedrock_model_id() -> str:
    """Secrets Manager에서 Bedrock 모델 ID 조회"""
    env = os.environ.get("ENV", "dev")
    secret_name = f"homelens/{env}/bedrock/config"

    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        return secret.get("model_id", "anthropic.claude-3-5-haiku-20241022-v1:0")
    except Exception as e:
        print(f"Bedrock 모델 ID 조회 실패: {e}")
        return "anthropic.claude-3-5-haiku-20241022-v1:0"


def generate_summary(title: str, description: str, model_id: str) -> str:
    """Bedrock Claude로 뉴스 AI 요약 생성"""
    prompt = f"""다음 부동산 뉴스를 1~2줄로 간결하게 요약해주세요.
핵심 내용만 포함하고, 투자 권유나 단정적 표현은 피해주세요.

제목: {title}
내용: {description}

요약:"""

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )

        result = json.loads(response["body"].read())
        summary = result["content"][0]["text"].strip()
        print(f"AI 요약 생성 완료: {summary[:50]}...")
        return summary

    except Exception as e:
        print(f"Bedrock 호출 실패: {e}")
        # 실패 시 description 앞 100자 사용
        return description[:100] if description else title


def update_news_summary(conn, news_id: str, summary: str):
    """news 테이블 summary 업데이트"""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE news
            SET summary = %s
            WHERE id = %s
        """, (summary, news_id))


def lambda_handler(event, context):
    """Lambda 핸들러 - 뉴스 AI 요약 생성"""
    print(f"뉴스 AI 요약 시작: {datetime.now(timezone.utc).isoformat()}")

    # SQS에서 전달받은 메시지
    records = event.get("Records", [])

    if not records:
        # Step Functions에서 직접 호출 시
        records = [{
            "body": json.dumps(event)
        }]

    model_id = get_bedrock_model_id()
    conn = None
    success_count = 0
    failed_count = 0

    try:
        conn = get_db_connection()

        for record in records:
            try:
                body = json.loads(record.get("body", "{}"))
                news_id = body.get("news_id")
                title = body.get("title", "")
                description = body.get("description", "")

                if not news_id or not title:
                    print(f"필수 파라미터 없음: {body}")
                    failed_count += 1
                    continue

                # AI 요약 생성
                summary = generate_summary(title, description, model_id)

                # DB 업데이트
                update_news_summary(conn, news_id, summary)
                conn.commit()

                success_count += 1
                print(f"요약 완료: {news_id}")

            except Exception as e:
                print(f"뉴스 요약 실패: {e}")
                if conn:
                    conn.rollback()
                failed_count += 1
                continue

    except Exception as e:
        print(f"DB 연결 실패: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        if conn:
            conn.close()

    print(f"AI 요약 완료: 성공 {success_count}건 / 실패 {failed_count}건")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "success": success_count,
            "failed": failed_count,
            "total": len(records),
        })
    }