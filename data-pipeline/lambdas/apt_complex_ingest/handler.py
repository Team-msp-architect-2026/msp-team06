"""
apt_complex_ingest/handler.py
공동주택 단지 목록 수집 및 DB 저장
"""
import json
import os
import time
import boto3
import psycopg2
import urllib.request
import urllib.parse
from datetime import datetime, timezone

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")
secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)
APT_COMPLEX_API_URL = "https://apis.data.go.kr/1613000/AptListService3"

SEOUL_SIGUNGU_CODES = {
    "종로구": "11110", "중구": "11140", "용산구": "11170",
    "성동구": "11200", "광진구": "11215", "동대문구": "11230",
    "중랑구": "11260", "성북구": "11290", "강북구": "11305",
    "도봉구": "11320", "노원구": "11350", "은평구": "11380",
    "서대문구": "11410", "마포구": "11440", "양천구": "11470",
    "강서구": "11500", "구로구": "11530", "금천구": "11545",
    "영등포구": "11560", "동작구": "11590", "관악구": "11620",
    "서초구": "11650", "강남구": "11680", "송파구": "11710",
    "강동구": "11740",
}


def get_api_key() -> str:
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
    env = os.environ.get("ENV", "dev")
    secret_name = f"homelens/{env}/rds/postgres"
    response = secretsmanager.get_secret_value(SecretId=secret_name)
    creds = json.loads(response["SecretString"])
    password = creds.get("password", "")
    if not password and creds.get("password_secret_arn"):
        pw_response = secretsmanager.get_secret_value(SecretId=creds["password_secret_arn"])
        pw_secret = json.loads(pw_response["SecretString"])
        password = pw_secret.get("password", "")
    return psycopg2.connect(
        host=creds["host"], port=int(creds["port"]),
        user=creds["username"], password=password, dbname=creds["dbname"],
    )


def fetch_apt_complex_list(sigungu_cd: str, api_key: str) -> list:
    encoded_key = urllib.parse.quote(api_key)
    url = (
        f"{APT_COMPLEX_API_URL}/getSigunguAptList3"
        f"?serviceKey={encoded_key}"
        f"&sigunguCode={sigungu_cd}"
        f"&numOfRows=1000&pageNo=1"
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


def fetch_apt_detail(kapt_code: str, api_key: str, retries: int = 2) -> str:
    """kaptCode로 단지 상세 API 호출해서 aptSeq 추출"""
    encoded_key = urllib.parse.quote(api_key)
    url = (
        f"https://apis.data.go.kr/1613000/AptListService2/getAptListDetail2"
        f"?serviceKey={encoded_key}"
        f"&kaptCode={kapt_code}"
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                item = result.get("response", {}).get("body", {}).get("item", {})
                if isinstance(item, list):
                    item = item[0] if item else {}
                apt_seq = item.get("aptSeq", "") or item.get("kaptCode", "")
                return apt_seq
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            print(f"단지 상세 API 실패 ({kapt_code}): {e}")
            return ""


def get_region_id(conn, lawd_cd: str) -> str:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM regions
            WHERE legal_dong_code = %s AND source_type = 'region'
            LIMIT 1
        """, (lawd_cd,))
        row = cur.fetchone()
        return row[0] if row else f"REGION_{lawd_cd}"


def save_location(conn, item: dict, region_id: str, api_key: str):
    address = " ".join(filter(None, [
        item.get("as1", ""), item.get("as2", ""),
        item.get("as3", ""), item.get("as4", ""),
    ]))
    kapt_code = item.get("kaptCode", "")
    loc_id = f"LOC_{kapt_code}"
    apt_seq = fetch_apt_detail(kapt_code, api_key)

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM locations WHERE id = %s", (loc_id,))
        exists = cur.fetchone()
        if exists:
            cur.execute("""
                UPDATE locations SET name = %s, address = %s, apt_seq = %s
                WHERE id = %s
            """, (item.get("kaptName", ""), address, apt_seq, loc_id))
        else:
            cur.execute("""
                INSERT INTO locations (
                    id, region_id, name, address,
                    property_type, lat, lng,
                    floors, build_year, apt_seq, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                loc_id, region_id,
                item.get("kaptName", ""),
                address, "apartment",
                0.0, 0.0, None, None,
                apt_seq,
            ))


def lambda_handler(event, context):
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
                    save_location(conn, item, region_id, api_key)
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
