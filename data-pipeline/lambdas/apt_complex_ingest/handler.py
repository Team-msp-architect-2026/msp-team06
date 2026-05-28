"""
apt_complex_ingest/handler.py
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
    try:
        response = secretsmanager.get_secret_value(SecretId=f"homelens/{env}/molit/real-estate-api")
        return json.loads(response["SecretString"])["api_key"]
    except Exception as e:
        print(f"API 키 조회 실패: {e}")
        return ""


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


def get_region_id(conn, lawd_cd: str) -> str:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM regions
            WHERE legal_dong_code = %s AND source_type = 'region'
            LIMIT 1
        """, (lawd_cd,))
        row = cur.fetchone()
        return row[0] if row else f"REGION_{lawd_cd}"


def save_location(conn, item: dict, region_id: str):
    address = " ".join(filter(None, [
        item.get("as1", ""), item.get("as2", ""),
        item.get("as3", ""), item.get("as4", ""),
    ]))
    kapt_code = item.get("kaptCode", "")
    loc_id = f"LOC_{kapt_code}"

    # kaptCode를 apt_seq로 직접 사용 (단지 상세 API 500 오류로 우회)
    apt_seq = kapt_code

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
    if event.get("debug_kapt_code"):
        fetch_apt_detail_debug(event["debug_kapt_code"], api_key)
        return {"statusCode": 200, "body": "debug done"}

    api_key = get_api_key()
    if not api_key:
        return {"statusCode": 500, "body": json.dumps({"error": "API 키 없음"})}

    if event.get("debug_kapt_code"):
        fetch_apt_detail_debug(event["debug_kapt_code"], api_key)
        return {"statusCode": 200, "body": "debug done"}

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

def fetch_apt_detail_debug(kapt_code: str, api_key: str):
    """디버그용 - 단지 상세 API 응답 RAW 출력"""
    encoded_key = urllib.parse.quote(api_key)
    url = (
        f"https://apis.data.go.kr/1613000/AptListService2/getAptListDetail2"
        f"?serviceKey={encoded_key}"
        f"&kaptCode={kapt_code}"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            raw = response.read().decode("utf-8")
            print(f"[DEBUG] kaptCode={kapt_code}")
            print(f"[DEBUG] RAW 응답: {raw}")
            result = json.loads(raw)
            item = result.get("response", {}).get("body", {}).get("item", {})
            print(f"[DEBUG] item keys: {list(item.keys()) if isinstance(item, dict) else type(item)}")
    except Exception as e:
        print(f"[DEBUG] API 실패: {e}")

def fetch_apt_detail_debug(kapt_code: str, api_key: str):
    """디버그용 - 단지 상세 API 응답 RAW 출력"""
    encoded_key = urllib.parse.quote(api_key)
    url = (
        f"https://apis.data.go.kr/1613000/AptListService2/getAptListDetail2"
        f"?serviceKey={encoded_key}"
        f"&kaptCode={kapt_code}"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            raw = response.read().decode("utf-8")
            print(f"[DEBUG] kaptCode={kapt_code}")
            print(f"[DEBUG] RAW 응답: {raw}")
            result = json.loads(raw)
            item = result.get("response", {}).get("body", {}).get("item", {})
            print(f"[DEBUG] item keys: {list(item.keys()) if isinstance(item, dict) else type(item)}")
    except Exception as e:
        print(f"[DEBUG] API 실패: {e}")
