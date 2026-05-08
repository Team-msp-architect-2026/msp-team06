"""
detect_data_update/handler.py
dataBaseDate 변경 감지 → Redis 캐시 무효화
- 국토부 실거래가 데이터 갱신 시 실행
- Redis 캐시 키 무효화
- memory: 512MB / timeout: 180s
"""
import json
import os
import boto3
import psycopg2
import redis
from datetime import datetime, timezone

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")

secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)


def get_db_connection():
    """Secrets Manager에서 DB 연결 정보 조회"""
    env = os.environ.get("ENVIRONMENT", "dev")
    secret_name = f"homelens/{env}/rds/postgres"

    response = secretsmanager.get_secret_value(SecretId=secret_name)
    creds = json.loads(response["SecretString"])

    return psycopg2.connect(
        host=creds["host"],
        port=creds["port"],
        user=creds["username"],
        password=creds["password"],
        dbname=creds["dbname"],
    )


def get_redis_client():
    """Secrets Manager에서 Redis 연결 정보 조회"""
    env = os.environ.get("ENVIRONMENT", "dev")
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))

    # prod 환경은 auth token 사용
    if env == "prod":
        try:
            secret_name = f"homelens/{env}/redis/auth"
            response = secretsmanager.get_secret_value(SecretId=secret_name)
            secret = json.loads(response["SecretString"])
            auth_token = secret.get("auth_token", "")

            return redis.Redis(
                host=redis_host,
                port=redis_port,
                password=auth_token,
                ssl=True,
                decode_responses=True,
            )
        except Exception as e:
            print(f"Redis auth token 조회 실패: {e}")

    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
    )


def get_latest_data_base_date(conn, region_id: str) -> str:
    """DB에서 최신 data_base_date 조회"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT data_base_date
            FROM price_snapshots
            WHERE region_id = %s
            ORDER BY data_base_date DESC
            LIMIT 1
        """, (region_id,))
        row = cur.fetchone()
        return str(row[0]) if row else None


def invalidate_cache(redis_client, region_id: str) -> int:
    """Redis 캐시 무효화 - 해당 지역 관련 캐시 키 전체 삭제"""
    patterns = [
        f"price:*:{region_id}:*",
        f"analysis:*:{region_id}:*",
        f"report:*:{region_id}:*",
        f"map:*:{region_id}:*",
    ]

    deleted_count = 0
    for pattern in patterns:
        try:
            keys = redis_client.keys(pattern)
            if keys:
                deleted_count += redis_client.delete(*keys)
                print(f"캐시 삭제: {pattern} ({len(keys)}개)")
        except Exception as e:
            print(f"캐시 삭제 실패 ({pattern}): {e}")

    return deleted_count


def lambda_handler(event, context):
    """Lambda 핸들러 - dataBaseDate 변경 감지 및 Redis 캐시 무효화"""
    print(f"캐시 무효화 시작: {datetime.now(timezone.utc).isoformat()}")

    # Step Functions에서 전달받은 데이터
    region_ids = event.get("region_ids", [])
    deal_ymd = event.get("deal_ymd", "")

    if not region_ids:
        # region_ids 없으면 DB에서 전체 지역 조회
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT id FROM regions
                    WHERE source_type = 'region'
                    AND property_type = 'area'
                """)
                rows = cur.fetchall()
                region_ids = [row[0] for row in rows]
        except Exception as e:
            print(f"지역 목록 조회 실패: {e}")
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
        finally:
            if conn:
                conn.close()

    # Redis 캐시 무효화
    total_deleted = 0
    try:
        redis_client = get_redis_client()

        for region_id in region_ids:
            deleted = invalidate_cache(redis_client, region_id)
            total_deleted += deleted
            print(f"캐시 무효화 완료: {region_id} ({deleted}개 삭제)")

    except Exception as e:
        print(f"Redis 연결 실패: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": f"Redis 연결 실패: {e}"})}

    print(f"전체 캐시 무효화 완료: {total_deleted}개 삭제")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "invalidated_regions": len(region_ids),
            "deleted_cache_keys": total_deleted,
            "deal_ymd": deal_ymd,
        })
    }