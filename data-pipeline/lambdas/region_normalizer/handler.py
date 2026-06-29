"""
region_normalizer/handler.py
법정동코드/지역 정규화
- 도로명주소 API로 법정동 코드 조회
- regions 테이블에 지역 데이터 저장
- Step Functions에서 호출
"""
import json
import os
import boto3
import urllib.request
import urllib.parse
import psycopg2
from datetime import datetime, timezone

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")

secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)


def get_db_credentials() -> dict:
    """Secrets Manager에서 DB 연결 정보 조회"""
    env = os.environ.get("ENV", "dev")
    secret_name = f"homelens/{env}/rds/postgres"

    response = secretsmanager.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


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


def search_address_api(keyword: str, confm_key: str) -> list:
    """행정안전부 도로명주소 API 검색"""
    encoded_keyword = urllib.parse.quote(keyword, encoding='utf-8')
    encoded_key = urllib.parse.quote(confm_key, encoding='utf-8')
    url = (
        f"https://business.juso.go.kr/addrlink/addrLinkApi.do"
        f"?currentPage=1&countPerPage=10&keyword={encoded_keyword}"
        f"&confmKey={encoded_key}&resultType=json"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("results", {}).get("juso", [])
    except Exception as e:
        print(f"도로명주소 API 오류: {e}")
        return []


def upsert_region(conn, region_data: dict):
    """regions 테이블에 지역 데이터 삽입 또는 업데이트"""
    sql = """
        INSERT INTO regions (
            id, name, full_address, legal_dong_code,
            lat, lng, property_type, source_type,
            created_at, updated_at
        ) VALUES (
            %(id)s, %(name)s, %(full_address)s, %(legal_dong_code)s,
            %(lat)s, %(lng)s, %(property_type)s, %(source_type)s,
            NOW(), NOW()
        )
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            full_address = EXCLUDED.full_address,
            legal_dong_code = EXCLUDED.legal_dong_code,
            lat = EXCLUDED.lat,
            lng = EXCLUDED.lng,
            updated_at = NOW()
    """
    with conn.cursor() as cur:
        cur.execute(sql, region_data)
    conn.commit()


def normalize_legal_dong_code(addr_info: dict) -> str:
    """법정동 코드 정규화 (10자리)"""
    # 행정동코드 앞 10자리 = 법정동코드
    admin_code = addr_info.get("admCd", "")
    return admin_code[:10] if len(admin_code) >= 10 else admin_code


def lambda_handler(event, context):
    """Lambda 핸들러 - 지역 정규화"""
    print(f"지역 정규화 시작: {datetime.now(timezone.utc).isoformat()}")

    # Step Functions에서 전달받은 데이터
    regions_to_normalize = event.get("regions", [])
    confm_key = event.get("confm_key", os.environ.get("ADDRESS_API_KEY", ""))

    if not regions_to_normalize:
        return {
            "statusCode": 200,
            "body": json.dumps({"normalized": 0, "message": "정규화할 지역 없음"})
        }

    conn = None
    normalized_count = 0
    failed_count = 0

    try:
        conn = get_db_connection()

        for region in regions_to_normalize:
            keyword = region.get("keyword", "")
            region_id = region.get("region_id", "")

            if not keyword or not region_id:
                continue

            # 도로명주소 API 검색
            results = search_address_api(keyword, confm_key)

            if not results:
                print(f"검색 결과 없음: {keyword}")
                failed_count += 1
                continue

            # 첫 번째 결과 사용
            addr = results[0]
            legal_dong_code = normalize_legal_dong_code(addr)

            region_data = {
                "id": region_id,
                "name": region.get("name", keyword),
                "full_address": addr.get("jibunAddr", keyword),
                "legal_dong_code": legal_dong_code,
                "lat": region.get("lat", 37.5665),
                "lng": region.get("lng", 126.9780),
                "property_type": region.get("property_type", "area"),
                "source_type": "region",
            }

            upsert_region(conn, region_data)
            normalized_count += 1
            print(f"정규화 완료: {keyword} → {legal_dong_code}")

    except Exception as e:
        print(f"지역 정규화 오류: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
    finally:
        if conn:
            conn.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "normalized": normalized_count,
            "failed": failed_count,
            "total": len(regions_to_normalize),
        })
    }