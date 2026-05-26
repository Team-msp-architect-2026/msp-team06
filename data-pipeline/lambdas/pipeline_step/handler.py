"""
pipeline_step/handler.py
Step Functions 단위 작업 처리
- Step Functions 워크플로우의 각 단계 실행
- 작업 유형에 따라 분기 처리
- memory: 1024MB / timeout: 300s
"""
import json
import os
import boto3
import psycopg2
from datetime import datetime, timezone

# ── AWS 클라이언트 ─────────────────────────────────────────────
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")
S3_BUCKET = os.environ.get("RAW_DATA_BUCKET", "")

s3_client = boto3.client("s3", region_name=AWS_REGION)
secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)


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


def process_price_data(event: dict) -> dict:
    """
    S3에서 실거래가 데이터 읽어서 DB 저장
    price_snapshots, price_trends 테이블에 저장
    """
    s3_key = event.get("s3_key", "")
    lawd_cd = event.get("lawd_cd", "")
    deal_type = event.get("deal_type", "")
    deal_ymd = event.get("deal_ymd", "")

    if not all([s3_key, lawd_cd, deal_type, deal_ymd]):
        return {"success": False, "error": "필수 파라미터 없음"}

    # S3에서 데이터 조회
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        price_data = json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": f"S3 조회 실패: {e}"}

    if not price_data:
        return {"success": True, "saved": 0, "message": "데이터 없음"}

    # DB 저장
    conn = None
    saved_count = 0

    try:
        conn = get_db_connection()

        # 월별 평균가 계산
        prices = []
        for item in price_data:
            if deal_type == "sale":
                amount = item.get("deal_amount", "0")
            else:
                amount = item.get("deposit", "0")

            try:
                prices.append(int(amount.replace(",", "")))
            except ValueError:
                continue

        if not prices:
            return {"success": True, "saved": 0, "message": "유효한 가격 데이터 없음"}

        avg_price = sum(prices) // len(prices)
        min_price = min(prices)
        max_price = max(prices)
        trade_count = len(prices)
        month = f"{deal_ymd[:4]}-{deal_ymd[4:6]}"
        region_id = get_region_id(conn, lawd_cd)
        data_base_date = f"{deal_ymd[:4]}-{deal_ymd[4:6]}-01"

        with conn.cursor() as cur:
            # price_trends 저장 (월별 추이)
            cur.execute("""
                INSERT INTO price_trends (
                    region_id, month, deal_type,
                    avg_price, trade_count, created_at
                ) VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
            """, (region_id, month, deal_type, avg_price, trade_count))

            # price_stats 저장 (통계)
            cur.execute("""
                INSERT INTO price_stats (
                    region_id, deal_type, period,
                    min_price, avg_price, max_price,
                    total_trade_count, recent_trade_count,
                    trade_signal, data_base_date, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (region_id, deal_type, period, data_base_date)
                DO UPDATE SET
                    min_price = EXCLUDED.min_price,
                    avg_price = EXCLUDED.avg_price,
                    max_price = EXCLUDED.max_price,
                    total_trade_count = EXCLUDED.total_trade_count,
                    recent_trade_count = EXCLUDED.recent_trade_count,
                    trade_signal = EXCLUDED.trade_signal
            """, (
                region_id, deal_type, "1m",
                min_price, avg_price, max_price,
                trade_count, trade_count,
                "active" if trade_count >= 10 else "normal" if trade_count >= 3 else "low",
                data_base_date
            ))

            saved_count = cur.rowcount

        conn.commit()
        print(f"DB 저장 완료: {region_id} {deal_type} {month} ({trade_count}건)")

    except Exception as e:
        if conn:
            conn.rollback()
        return {"success": False, "error": f"DB 저장 실패: {e}"}
    finally:
        if conn:
            conn.close()

    return {
        "success": True,
        "saved": saved_count,
        "region_id": region_id,
        "deal_type": deal_type,
        "month": month,
        "avg_price": avg_price,
        "trade_count": trade_count,
    }


def process_news_data(event: dict) -> dict:
    """
    S3에서 뉴스 데이터 읽어서 DB 저장
    news, news_keywords, news_regions 테이블에 저장
    """
    s3_key = event.get("s3_key", "")

    if not s3_key:
        return {"success": False, "error": "s3_key 없음"}

    # S3에서 데이터 조회
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        news_items = json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": f"S3 조회 실패: {e}"}

    if not news_items:
        return {"success": True, "saved": 0}

    conn = None
    saved_count = 0

    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            for item in news_items:
                news_id = item.get("news_id")
                if not news_id:
                    continue

                try:
                    # ── news 테이블 저장 ──────────────────────
                    cur.execute("""
                        INSERT INTO news (
                            id, title, summary, source,
                            url, category, published_at, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        news_id,
                        item.get("title", ""),
                        item.get("description", ""),
                        item.get("source", ""),
                        item.get("originallink", item.get("link", "")),
                        item.get("category", "market"),
                        item.get("pubDate", datetime.now(timezone.utc).isoformat()),
                    ))

                    # ── news_keywords 테이블 저장 ─────────────
                    keywords = item.get("keywords", [])
                    for idx, keyword in enumerate(keywords):
                        cur.execute("""
                            INSERT INTO news_keywords (
                                news_id, keyword, sort_order
                            ) VALUES (%s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (news_id, keyword, idx + 1))

                    # ── news_regions 테이블 저장 ──────────────
                    # 뉴스 제목/내용에서 서울 구 이름 추출해서 연결
                    region_ids = extract_region_ids(
                        conn,
                        item.get("title", "") + item.get("description", "")
                    )
                    for region_id in region_ids:
                        cur.execute("""
                            INSERT INTO news_regions (news_id, region_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, (news_id, region_id))

                    saved_count += 1

                except Exception as e:
                    print(f"뉴스 저장 실패 ({news_id}): {e}")
                    continue

        conn.commit()
        print(f"뉴스 DB 저장 완료: {saved_count}건")

    except Exception as e:
        if conn:
            conn.rollback()
        return {"success": False, "error": f"DB 저장 실패: {e}"}
    finally:
        if conn:
            conn.close()

    return {"success": True, "saved": saved_count}

def get_region_id(conn, lawd_cd: str) -> str:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM regions
            WHERE legal_dong_code = %s
            AND source_type = 'region'
            LIMIT 1
        """, (lawd_cd,))
        row = cur.fetchone()
        return row[0] if row else f"REGION_{lawd_cd}"

def extract_region_ids(conn, text: str) -> list:
    """
    뉴스 텍스트에서 서울 구/동 이름 추출 후 region_id 반환
    예: '강남구 아파트 급등' → ['REGION_11230']
    """
    region_ids = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name FROM regions
                WHERE source_type = 'region'
                AND property_type = 'area'
            """)
            rows = cur.fetchall()
            for region_id, name in rows:
                if name in text:
                    region_ids.append(region_id)
    except Exception as e:
        print(f"지역 추출 실패: {e}")

    return region_ids


def process_issues_data(event: dict) -> dict:
    """
    뉴스 데이터 기반으로 issues 테이블 자동 생성
    - 뉴스에서 이슈 생성
    - impact_type 자동 분류
    """
    s3_key = event.get("s3_key", "")

    if not s3_key:
        return {"success": False, "error": "s3_key 없음"}

    # S3에서 데이터 조회
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        news_items = json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": f"S3 조회 실패: {e}"}

    if not news_items:
        return {"success": True, "saved": 0}

    conn = None
    saved_count = 0

    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            for item in news_items:
                news_id = item.get("news_id")
                title = item.get("title", "")
                description = item.get("description", "")
                text = title + description

                # 연관 지역 추출
                region_ids = extract_region_ids(conn, text)
                if not region_ids:
                    continue

                # impact_type 자동 분류
                impact_type = classify_impact(text)

                # issue_id 생성
                import uuid
                issue_id = f"ISSUE_{uuid.uuid4().hex[:12].upper()}"

                for region_id in region_ids:
                    try:
                        cur.execute("""
                            INSERT INTO issues (
                                id, region_id, type, title,
                                summary, impact_type, published_at,
                                url, ref_id, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT DO NOTHING
                        """, (
                            f"{issue_id}_{region_id}",
                            region_id,
                            item.get("category", "news"),
                            title,
                            description[:200],
                            impact_type,
                            item.get("pubDate", datetime.now(timezone.utc).isoformat()),
                            item.get("originallink", ""),
                            news_id,
                        ))
                        saved_count += 1
                    except Exception as e:
                        print(f"이슈 저장 실패: {e}")
                        continue

        conn.commit()
        print(f"이슈 DB 저장 완료: {saved_count}건")

    except Exception as e:
        if conn:
            conn.rollback()
        return {"success": False, "error": f"DB 저장 실패: {e}"}
    finally:
        if conn:
            conn.close()

    return {"success": True, "saved": saved_count}


def classify_impact(text: str) -> str:
    """뉴스 텍스트 기반 impact_type 자동 분류"""
    positive_keywords = ["상승", "급등", "호재", "개발", "착공", "호황", "회복"]
    negative_keywords = ["하락", "급락", "악재", "규제", "침체", "위기", "하향"]

    positive_count = sum(1 for kw in positive_keywords if kw in text)
    negative_count = sum(1 for kw in negative_keywords if kw in text)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def lambda_handler(event, context):
    """
    Lambda 핸들러 - Step Functions 단위 작업

    event.step 값에 따라 작업 분기:
    - "process_price": 실거래가 데이터 DB 저장
    - "process_news": 뉴스 데이터 DB 저장
    - "process_issues": 이슈 테이블 자동 생성
    """
    print(f"pipeline_step 시작: {datetime.now(timezone.utc).isoformat()}")
    print(f"event: {json.dumps(event)}")

    step = event.get("step", "")

    if step == "process_price":
        result = process_price_data(event)
    elif step == "process_news":
        result = process_news_data(event)
    elif step == "process_issues":
        result = process_issues_data(event)
    else:
        result = {
            "success": False,
            "error": f"알 수 없는 step: {step}"
        }

    print(f"pipeline_step 완료: {result}")

    return {
        "statusCode": 200 if result.get("success") else 500,
        "body": json.dumps(result)
    }