"""
apt_complex_ingest/handler.py
공동주택 단지 목록 수집 및 DB 저장
- 국토부 공동주택 단지 목록제공 서비스 API 호출 (getSigunguAptList3)
- 단지 코드 + 단지명 + 주소 조회
- locations 테이블에 저장
- memory: 1024MB / timeout: 300s
"""
import json
import os
import boto3
import psycopg2
import urllib.request
import urllib.parse
from datetime import datetime, timezone

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")

secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)

# 공동주택 단지 목록 API 엔드포인트
APT_COMPLEX_API_URL = "https://apis.data.go.kr/1613000/AptListService3"

# 서울 25개 구 코드
SEOUL_SIGUNGU_CODES = {
    "종로구": "11010",
    "중구": "11020",
    "용산구": "11030",
    "성동구": "11040",
    "광진구": "11050",
    "동대문구": "11060",
    "중랑구": "11070",
    "성북구": "11080",
    "강북구": "11090",
    "도봉구": "11100",
    "노원구": "11110",
    "은평구": "11120",
    "서대문구": "11130",
    "마포구": "11140",
    "양천구": "11150",
    "강서구": "11160",
    "구로구": "11170",
    "금천구": "11180",
    "영등포구": "11190",
    "동작구": "11200",
    "관악구": "11210",
    "서초구": "11220",
    "강남구": "11230",
    "송파구": "11240",
    "강동구": "11250",
}


def get_api_key() -> str:
    """Secrets Manager에서 국토부 API 키 조회"""
    env = os.environ.get("ENV", "dev")
    secret_name = f"homelens/{env}/molit/real-estate-api"

    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        return secret["api_key"]
    except Exception as e:
        print(f"API 키 조회 실패: {e}")
        return os.environ.get("MOLIT_API_KEY", "")


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


def fetch_apt_complex_list(sigungu_cd: str, api_key: str) -> list:
    """공동주택 단지 목록 API 호출"""
    encoded_key = urllib.parse.quote(api_key)
    url = (
        f"{APT_COMPLEX_API_URL}/getSigunguAptList3"
        f"?serviceKey={encoded_key}"
        f"&sigunguCode={sigungu_cd}"
        f"&numOfRows=1000"
        f"&pageNo=1"
    )

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            items = result.get("response", {}).get("body", {}).get("items", [])
            if isinstance(items, dict):
                items = [items]
            return items
    except Exception as e:
        print(f"API 호출 실패 ({sigungu_cd}): {e}")
        return []


def get_region_id(conn, sigungu_cd: str) -> str:
    """법정동 코드로 region_id 조회"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM regions
                WHERE LEFT(legal_dong_code, 5) = %s
                AND source_type = 'region'
                LIMIT 1
            """, (sigungu_cd,))
            row = cur.fetchone()
            return row[0] if row else f"REGION_{sigungu_cd}"
    except Exception as e:
        print(f"region_id 조회 실패: {e}")
        return f"REGION_{sigungu_cd}"


def save_location(conn, item: dict, region_id: str):
    """locations 테이블에 단지 정보 저장"""
    address = " ".join(filter(None, [
        item.get("as1", ""),
        item.get("as2", ""),
        item.get("as3", ""),
        item.get("as4", ""),
    ]))

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO locations (
                id, region_id, name, address,
                property_type, lat, lng,
                floors, build_year, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                address = EXCLUDED.address
        """, (
            f"LOC_{item.get('kaptCode', '')}",
            region_id,
            item.get("kaptName", ""),
            address,
            "apartment",
            None,
            None,
            None,
            None,
        ))


def lambda_handler(event, context):
    """Lambda 핸들러 - 공동주택 단지 목록 수집 및 DB 저장"""
    print(f"단지 목록 수집 시작: {datetime.now(timezone.utc).isoformat()}")

    api_key = get_api_key()
    if not api_key:
        return {"statusCode": 500, "body": json.dumps({"error": "API 키 없음"})}

    target_gu = event.get("target_gu", list(SEOUL_SIGUNGU_CODES.keys()))

    conn = None
    total_saved = 0
    total_failed = 0

    try:
        conn = get_db_connection()

        for gu_name in target_gu:
            sigungu_cd = SEOUL_SIGUNGU_CODES.get(gu_name)
            if not sigungu_cd:
                print(f"구 코드 없음: {gu_name}")
                continue

            items = fetch_apt_complex_list(sigungu_cd, api_key)
            print(f"{gu_name}: {len(items)}개 단지 조회")

            if not items:
                continue

            region_id = get_region_id(conn, sigungu_cd)

            for item in items:
                try:
                    save_location(conn, item, region_id)
                    total_saved += 1
                except Exception as e:
                    print(f"단지 저장 실패 ({item.get('kaptName')}): {e}")
                    total_failed += 1
                    continue

            conn.commit()
            print(f"{gu_name} 저장 완료: {len(items)}개")

    except Exception as e:
        if conn:
            conn.rollback()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        if conn:
            conn.close()

    print(f"전체 완료: 저장 {total_saved}개 / 실패 {total_failed}개")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "total_saved": total_saved,
            "total_failed": total_failed,
            "target_gu_count": len(target_gu),
        })
    }