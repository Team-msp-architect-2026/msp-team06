"""
molit_price_ingest/handler.py
국토부 아파트 실거래가 수집
- 매매/전세/월세 실거래가 API 호출
- 수집 데이터 S3 저장
- price-ingest-queue로 DB 저장 요청 전송
- timeout: 900s (Lambda 최대)

배포 전 1회 수동 작업:
  공공데이터포털(data.go.kr)에서 API 키 발급 후 Secrets Manager에 저장
  aws secretsmanager put-secret-value \
    --secret-id homelens/{env}/molit/real-estate-api \
    --secret-string '{"api_key":"발급받은키"}'
"""
import json
import os
import boto3
import psycopg2
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ── AWS 클라이언트 ─────────────────────────────────────────────
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")
S3_BUCKET = os.environ.get("RAW_DATA_BUCKET", "")
SQS_PRICE_INGEST_URL = os.environ.get("SQS_PRICE_INGEST_URL", "")

s3_client = boto3.client("s3", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)
secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)

# 1..........국토부 실거래가 API 엔드포인트 (공공데이터포털 RTMSDataSvc 계열)
MOLIT_API_URLS = {
    "sale":    "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev",  # 매매
    "jeonse":  "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent",      # 전세
    "monthly": "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent",      # 월세 (같은 엔드포인트)
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


def get_gu_codes_from_db() -> dict:
    """서울 25개 구 법정동 코드 반환"""
    return {
        "종로구": "11010", "중구": "11020", "용산구": "11030",
        "성동구": "11040", "광진구": "11050", "동대문구": "11060",
        "중랑구": "11070", "성북구": "11080", "강북구": "11090",
        "도봉구": "11100", "노원구": "11110", "은평구": "11120",
        "서대문구": "11130", "마포구": "11140", "양천구": "11150",
        "강서구": "11160", "구로구": "11170", "금천구": "11180",
        "영등포구": "11190", "동작구": "11200", "관악구": "11210",
        "서초구": "11220", "강남구": "11230", "송파구": "11240",
        "강동구": "11250",
    }

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, legal_dong_code
                FROM regions
                WHERE source_type = 'region'
                AND property_type = 'area'
                AND LENGTH(legal_dong_code) >= 5
            """)
            rows = cur.fetchall()
            if rows:
                return {row[0]: row[1][:5] for row in rows}
            else:
                print("DB에 지역 데이터 없음 → 기본 구 코드 사용")
                return DEFAULT_GU_CODES
    except Exception as e:
        print(f"DB 구 코드 조회 실패: {e} → 기본 구 코드 사용")
        return DEFAULT_GU_CODES
    finally:
        if conn:
            conn.close()


def fetch_molit_data(deal_type, lawd_cd, deal_ymd, api_key):
    """국토부 실거래가 API 호출"""
    base_url = MOLIT_API_URLS.get(deal_type, "")
    encoded_key = urllib.parse.quote(api_key)
    url = (
        f"{base_url}/getRTMSDataSvcAptTradeDev"
        f"?serviceKey={encoded_key}"
        f"&LAWD_CD={lawd_cd}"
        f"&DEAL_YMD={deal_ymd}"
        f"&numOfRows=1000"
        f"&pageNo=1"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_data = response.read().decode("utf-8")
            return parse_xml_response(xml_data, deal_type)
    except Exception as e:
        print(f"국토부 API 오류 ({deal_type}, {lawd_cd}, {deal_ymd}): {e}")
        return []


def parse_xml_response(xml_data: str, deal_type: str) -> list:
    """XML 응답 파싱"""
    try:
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        result = []

        for item in items:
            def get_text(tag):
                el = item.find(tag)
                return el.text.strip() if el is not None and el.text else ""

            if deal_type == "sale":
                result.append({
                    "deal_type": "sale",
                    "apt_name": get_text("아파트"),
                    "apt_seq": get_text("aptSeq"),        # 추가
                    "deal_amount": get_text("거래금액").replace(",", ""),
                    "area": get_text("전용면적"),
                    "floor": get_text("층"),
                    "build_year": get_text("건축년도"),
                    "deal_year": get_text("년"),
                    "deal_month": get_text("월"),
                    "deal_day": get_text("일"),
                    "dong": get_text("법정동"),
                    "jibun": get_text("지번"),
                })
            else:
                result.append({
                    "deal_type": deal_type,
                    "apt_name": get_text("아파트"),
                    "apt_seq": get_text("aptSeq"),        # 추가
                    "deposit": get_text("보증금액").replace(",", ""),
                    "monthly_rent": get_text("월세금액").replace(",", ""),
                    "area": get_text("전용면적"),
                    "floor": get_text("층"),
                    "build_year": get_text("건축년도"),
                    "deal_year": get_text("년"),
                    "deal_month": get_text("월"),
                    "deal_day": get_text("일"),
                    "dong": get_text("법정동"),
                })

        return result
    except Exception as e:
        print(f"XML 파싱 오류: {e}")
        return []


def save_to_s3(data: list, deal_type: str, lawd_cd: str, deal_ymd: str) -> str:
    """수집 데이터 S3 저장"""
    key = f"raw/price/{deal_ymd}/{deal_type}/{lawd_cd}_{deal_ymd}.json"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False),
        ContentType="application/json",
    )
    print(f"S3 저장: s3://{S3_BUCKET}/{key} ({len(data)}건)")
    return key


def send_to_queue(s3_key: str, lawd_cd: str, deal_type: str, deal_ymd: str):
    """price-ingest-queue로 DB 저장 요청"""
    message = {
        "s3_key": s3_key,
        "lawd_cd": lawd_cd,
        "deal_type": deal_type,
        "deal_ymd": deal_ymd,
        "bucket": S3_BUCKET,
    }

    sqs_client.send_message(
        QueueUrl=SQS_PRICE_INGEST_URL,
        MessageBody=json.dumps(message),
    )


def lambda_handler(event, context):
    """Lambda 핸들러 - 국토부 실거래가 수집"""
    print(f"실거래가 수집 시작: {datetime.now(timezone.utc).isoformat()}")

    # 1. Secrets Manager에서 API 키 자동 조회
    api_key = get_api_key()
    if not api_key:
        return {"statusCode": 500, "body": "API 키 없음 - Secrets Manager 확인 필요"}

    # 2. DB에서 법정동 코드 조회
    gu_codes = get_gu_codes_from_db()
    if not gu_codes:
        return {"statusCode": 500, "body": "구 코드 조회 실패 - regions 테이블 확인 필요"}

    # 3. 수집 대상 월 (기본: 현재 월)
    now = datetime.now(timezone.utc)
    deal_ymd = event.get("deal_ymd", now.strftime("%Y%m"))

    # 4. 수집 대상 구/거래유형
    target_gu = event.get("target_gu", list(gu_codes.keys()))
    deal_types = event.get("deal_types", ["sale", "jeonse", "monthly"])

    total_collected = 0
    results = []

    # 5. 구별 실거래가 수집
    for gu_name in target_gu:
        lawd_cd = gu_codes.get(gu_name)
        if not lawd_cd:
            print(f"구 코드 없음: {gu_name}")
            continue

        for deal_type in deal_types:
            data = fetch_molit_data(deal_type, lawd_cd, deal_ymd, api_key)

            if not data:
                continue

            s3_key = save_to_s3(data, deal_type, lawd_cd, deal_ymd)
            send_to_queue(s3_key, lawd_cd, deal_type, deal_ymd)

            total_collected += len(data)
            results.append({
                "gu": gu_name,
                "deal_type": deal_type,
                "count": len(data),
                "s3_key": s3_key,
            })
            print(f"수집 완료: {gu_name} {deal_type} {len(data)}건")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "total_collected": total_collected,
            "deal_ymd": deal_ymd,
            "results": results,
        })
    }