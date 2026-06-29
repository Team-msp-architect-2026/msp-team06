import json
import os
import boto3
import psycopg2
from datetime import datetime, timezone

AWS_REGION = os.environ.get("AWS_REGION", "eu-west-3")
S3_BUCKET = os.environ.get("RAW_DATA_BUCKET", "")

s3_client = boto3.client("s3", region_name=AWS_REGION)
secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)

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
        host=creds["host"],
        port=int(creds["port"]),
        user=creds["username"],
        password=password,
        dbname=creds["dbname"],
    )

def get_region_id(conn, lawd_cd: str) -> str:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM regions
            WHERE LEFT(legal_dong_code, 5) = %s
            AND source_type = 'region'
            LIMIT 1
        """, (lawd_cd,))
        row = cur.fetchone()
        return row[0] if row else f"REGION_{lawd_cd}"

def parse_prices(price_data: list, deal_type: str) -> dict:
    prices = []
    apt_seq_groups = {}
    dong_groups = {}

    for item in price_data:
        apt_seq = item.get("apt_seq", "")
        dong = item.get("dong", "")
        try:
            if deal_type == "sale":
                amount = int(str(item.get("deal_amount", "0")).replace(",", ""))
            elif deal_type == "jeonse":
                amount = int(str(item.get("deposit", "0")).replace(",", ""))
            elif deal_type == "monthly":
                raw = item.get("monthly_rent", "0") or "0"
                amount = int(str(raw).replace(",", ""))
                if amount <= 0:
                    continue
            else:
                amount = 0

            if amount <= 0:
                continue

            prices.append(amount)

            if apt_seq:
                if apt_seq not in apt_seq_groups:
                    apt_seq_groups[apt_seq] = {
                        "prices": [], "deposits": [],
                        "apt_name": item.get("apt_name", ""), "dong": dong
                    }
                apt_seq_groups[apt_seq]["prices"].append(amount)
                if deal_type == "monthly":
                    raw_dep = item.get("deposit", "0") or "0"
                    deposit = int(str(raw_dep).replace(",", ""))
                    apt_seq_groups[apt_seq]["deposits"].append(deposit)

            if dong:
                if dong not in dong_groups:
                    dong_groups[dong] = []
                dong_groups[dong].append(amount)

        except (ValueError, AttributeError) as e:
            print(f"[Parsing Error] deal_type: {deal_type}, item: {item}, error: {e}")
            continue

    if not prices:
        return {}

    min_p = min(prices)
    max_p = max(prices)
    avg_p = sum(prices) // len(prices)
    mid_p = (min_p + max_p) / 2
    volatility = (max_p - min_p) / avg_p if avg_p else 0

    if volatility < 0.2:
        price_stability_grade = "stable"
    elif volatility < 0.5:
        price_stability_grade = "normal"
    else:
        price_stability_grade = "volatile"

    if avg_p < mid_p * 0.9:
        price_level = "low"
    elif avg_p > mid_p * 1.1:
        price_level = "high"
    else:
        price_level = "avg"

    return {
        "min_price": min_p,
        "max_price": max_p,
        "avg_price": avg_p,
        "trade_count": len(prices),
        "price_stability_grade": price_stability_grade,
        "price_level": price_level,
        "trade_signal": "active" if len(prices) >= 10 else "normal" if len(prices) >= 3 else "low",
        "apt_seq_groups": apt_seq_groups,
        "dong_groups": dong_groups,
    }

def save_by_apt_seq(conn, apt_seq_groups: dict, deal_type: str, month: str):
    with conn.cursor() as cur:
        for apt_seq, data in apt_seq_groups.items():
            prices = data["prices"]
            if not prices:
                continue
            avg_price = sum(prices) // len(prices)
            trade_count = len(prices)
            deposits = data.get("deposits", [])
            avg_deposit = sum(deposits) // len(deposits) if deposits else None
            apt_name = data.get("apt_name", "")
            cur.execute("""
                INSERT INTO price_trends (
                    region_id, month, deal_type,
                    avg_price, trade_count, apt_seq, apt_name, deposit, created_at
                ) VALUES (
                    (SELECT id FROM regions WHERE legal_dong_code LIKE %s LIMIT 1),
                    %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                ON CONFLICT DO NOTHING
            """, (
                apt_seq[:5] + "%",
                month, deal_type, avg_price, trade_count,
                apt_seq, apt_name, avg_deposit,
            ))

def save_by_dong(conn, lawd_cd: str, dong_groups: dict, deal_type: str, month: str):
    with conn.cursor() as cur:
        for dong, prices in dong_groups.items():
            if not prices:
                continue
            avg_price = sum(prices) // len(prices)
            trade_count = len(prices)
            cur.execute("""
                INSERT INTO price_trends (
                    region_id, month, deal_type,
                    avg_price, trade_count, created_at
                )
                SELECT id, %s, %s, %s, %s, NOW()
                FROM regions
                WHERE name = %s AND LEFT(legal_dong_code, 5) = %s
                LIMIT 1
                ON CONFLICT DO NOTHING
            """, (month, deal_type, avg_price, trade_count, dong, lawd_cd))

def save_price_snapshot(conn, region_id: str, stats: dict, deal_type: str, data_base_date: str):
    with conn.cursor() as cur:
        if deal_type == "sale":
            cur.execute("""
                INSERT INTO price_snapshots (
                    region_id, avg_sale_price, recent_trade_count,
                    price_stability_grade, price_level, data_base_date
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (region_id, data_base_date)
                DO UPDATE SET
                    avg_sale_price = EXCLUDED.avg_sale_price,
                    recent_trade_count = EXCLUDED.recent_trade_count
            """, (region_id, stats["avg_price"], stats["trade_count"],
                  stats["price_stability_grade"], stats["price_level"], data_base_date))
        elif deal_type == "jeonse":
            cur.execute("""
                INSERT INTO price_snapshots (
                    region_id, avg_jeonse_price, recent_trade_count,
                    price_stability_grade, price_level, data_base_date
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (region_id, data_base_date)
                DO UPDATE SET
                    avg_jeonse_price = EXCLUDED.avg_jeonse_price
            """, (region_id, stats["avg_price"], stats["trade_count"],
                  stats["price_stability_grade"], stats["price_level"], data_base_date))
        elif deal_type == "monthly":
            cur.execute("""
                INSERT INTO price_snapshots (
                    region_id, avg_monthly_rent, recent_trade_count,
                    price_stability_grade, price_level, data_base_date
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (region_id, data_base_date)
                DO UPDATE SET
                    avg_monthly_rent = EXCLUDED.avg_monthly_rent
            """, (region_id, stats["avg_price"], stats["trade_count"],
                  stats["price_stability_grade"], stats["price_level"], data_base_date))

def save_price_trend(conn, region_id: str, stats: dict, deal_type: str, month: str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO price_trends (
                region_id, month, deal_type,
                avg_price, trade_count, created_at
            ) VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (region_id, month, deal_type, stats["avg_price"], stats["trade_count"]))

def save_price_stats(conn, region_id: str, stats: dict, deal_type: str, data_base_date: str):
    with conn.cursor() as cur:
        for period in ["1m", "3m", "1y"]:
            cur.execute("""
                INSERT INTO price_stats (
                    region_id, deal_type, period,
                    min_price, avg_price, max_price,
                    total_trade_count, recent_trade_count,
                    trade_signal, data_base_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (region_id, deal_type, period, data_base_date)
                DO UPDATE SET
                    min_price = EXCLUDED.min_price,
                    avg_price = EXCLUDED.avg_price,
                    max_price = EXCLUDED.max_price,
                    total_trade_count = EXCLUDED.total_trade_count,
                    recent_trade_count = EXCLUDED.recent_trade_count,
                    trade_signal = EXCLUDED.trade_signal
            """, (region_id, deal_type, period,
                  stats["min_price"], stats["avg_price"], stats["max_price"],
                  stats["trade_count"], stats["trade_count"],
                  stats["trade_signal"], data_base_date))

def lambda_handler(event, context):
    print(f"가격 데이터 정규화 시작: {datetime.now(timezone.utc).isoformat()}")

    s3_key = event.get("s3_key", "")
    lawd_cd = event.get("lawd_cd", "")
    deal_type = event.get("deal_type", "")
    deal_ymd = event.get("deal_ymd", "")

    if not all([s3_key, lawd_cd, deal_type, deal_ymd]):
        return {"statusCode": 400, "body": json.dumps({"error": "필수 파라미터 없음"})}

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        price_data = json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": f"S3 조회 실패: {e}"})}

    if not price_data:
        return {"statusCode": 200, "body": json.dumps({"saved": 0, "message": "데이터 없음"})}

    stats = parse_prices(price_data, deal_type)
    if not stats:
        return {"statusCode": 200, "body": json.dumps({"saved": 0, "message": "유효한 가격 없음"})}

    data_base_date = f"{deal_ymd[:4]}-{deal_ymd[4:6]}-01"
    month = f"{deal_ymd[:4]}-{deal_ymd[4:6]}"

    conn = None
    try:
        conn = get_db_connection()
        region_id = get_region_id(conn, lawd_cd)
        save_price_snapshot(conn, region_id, stats, deal_type, data_base_date)
        save_price_trend(conn, region_id, stats, deal_type, month)
        save_price_stats(conn, region_id, stats, deal_type, data_base_date)
        save_by_apt_seq(conn, stats.get("apt_seq_groups", {}), deal_type, month)
        save_by_dong(conn, lawd_cd, stats.get("dong_groups", {}), deal_type, month)
        conn.commit()
        print(f"저장 완료: {region_id} {deal_type} {month}")
    except Exception as e:
        if conn:
            conn.rollback()
        import traceback
        print(traceback.format_exc())
        return {"statusCode": 500, "body": json.dumps({"error": f"DB 저장 실패: {e}"})}
    finally:
        if conn:
            conn.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "region_id": region_id,
            "deal_type": deal_type,
            "month": month,
            "avg_price": stats["avg_price"],
            "trade_count": stats["trade_count"],
        })
    }
