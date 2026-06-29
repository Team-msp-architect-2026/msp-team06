"""
summarize_news/handler.py
Bedrock Claude로 뉴스 1~2줄 AI 요약 생성
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
    env = os.environ.get("ENV", "dev")
    response = secretsmanager.get_secret_value(SecretId=f"homelens/{env}/rds/postgres")
    creds = json.loads(response["SecretString"])
    password = creds.get("password", "")
    if not password and creds.get("password_secret_arn"):
        pw_response = secretsmanager.get_secret_value(SecretId=creds["password_secret_arn"])
        password = json.loads(pw_response["SecretString"]).get("password", "")
    return psycopg2.connect(
        host=creds["host"], port=int(creds["port"]),
        user=creds["username"], password=password, dbname=creds["dbname"],
    )


def get_bedrock_model_id() -> str:
    env = os.environ.get("ENV", "dev")
    try:
        response = secretsmanager.get_secret_value(SecretId=f"homelens/{env}/bedrock/config")
        return json.loads(response["SecretString"]).get("model_id", "eu.anthropic.claude-sonnet-4-6")
    except:
        return "eu.anthropic.claude-sonnet-4-6"


def generate_summary(title: str, description: str, model_id: str) -> str:
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
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        result = json.loads(response["body"].read())
        summary = result["content"][0]["text"].strip()
        print(f"AI 요약 생성 완료: {summary[:50]}...")
        return summary
    except Exception as e:
        print(f"Bedrock 호출 실패: {e}")
        return description[:100] if description else title


def upsert_news(conn, news_id: str, title: str, description: str,
                url: str, source: str, published_at: str, category: str, summary: str):
    """news 테이블에 INSERT 또는 UPDATE"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO news (id, title, summary, source, url, category, published_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                summary = EXCLUDED.summary,
                title = EXCLUDED.title
        """, (
            news_id, title, summary,
            source or "네이버뉴스",
            url or "",
            category or "market",
            published_at or datetime.now(timezone.utc).isoformat(),
        ))


def lambda_handler(event, context):
    print(f"뉴스 AI 요약 시작: {datetime.now(timezone.utc).isoformat()}")

    records = event.get("Records", [])
    if not records:
        records = [{"body": json.dumps(event)}]

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
                url = body.get("url", "")
                source = body.get("source", "")
                published_at = body.get("published_at", "")
                category = body.get("category", "market")

                if not news_id or not title:
                    print(f"필수 파라미터 없음: {body}")
                    failed_count += 1
                    continue

                # AI 요약 생성
                summary = generate_summary(title, description, model_id)

                # DB INSERT OR UPDATE
                upsert_news(conn, news_id, title, description,
                           url, source, published_at, category, summary)
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
