# HomeLens AI - Celery Worker
# SQS 브로커 기반 AI 리포트 비동기 생성 → RDS 저장

import os
import asyncio
import time
import threading
import psutil
from datetime import datetime, date
from celery import Celery
from app.services.report import generate_report
from app.services.news import get_region_issues
from app.services.map import search_all_nearby_infra
from app.metrics import (
    SQS_CONSUME_LATENCY,
    BEDROCK_INVOKE_LATENCY,
    DB_SAVE_LATENCY,
    PIPELINE_TOTAL_LATENCY,
    PIPELINE_ERRORS,
    WORKER_CPU_PERCENT,
    WORKER_MEMORY_RSS_BYTES,
    SQS_QUEUE_DEPTH,
    start_metrics_server,
)
start_metrics_server()


def _sample_process_resources():
    """15초 간격으로 프로세스 CPU(%)·메모리(RSS)를 Gauge에 기록한다."""
    proc = psutil.Process(os.getpid())
    proc.cpu_percent()  # 첫 호출은 항상 0.0 — 기준값 초기화용
    while True:
        try:
            cpu = proc.cpu_percent(interval=15)  # 15초 블록 후 평균 CPU% 반환
            WORKER_CPU_PERCENT.set(cpu)
            WORKER_MEMORY_RSS_BYTES.set(proc.memory_info().rss)
        except Exception:
            time.sleep(15)


def _poll_sqs_queue_depth():
    """30초마다 SQS 큐의 대기 메시지 수를 Gauge에 기록한다."""
    import boto3
    region = os.getenv("AWS_REGION", "eu-west-3")
    queue_url = (
        f"https://sqs.{region}.amazonaws.com"
        f"/611058323802/homelens-dev-report-generation"
    )
    sqs = boto3.client("sqs", region_name=region)
    while True:
        try:
            resp = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["ApproximateNumberOfMessages"],
            )
            depth = int(resp["Attributes"].get("ApproximateNumberOfMessages", 0))
            SQS_QUEUE_DEPTH.set(depth)
        except Exception:
            pass
        time.sleep(30)


threading.Thread(target=_sample_process_resources, daemon=True, name="resource-sampler").start()
threading.Thread(target=_poll_sqs_queue_depth, daemon=True, name="sqs-depth-poller").start()

AWS_REGION = os.getenv("AWS_REGION", "eu-west-3")

celery_app = Celery(
    "homelens",
    broker="sqs://",
    broker_transport_options={
        "region": "eu-west-3",
        "predefined_queues": {
            "homelens-dev-report-generation": {
                "url": "https://sqs.eu-west-3.amazonaws.com/611058323802/homelens-dev-report-generation"
            }
        },
        "is_secure": True,
        "connect_timeout": 5,  
        "read_timeout": 30, 
    },
    task_default_queue="homelens-dev-report-generation",
)
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.broker_transport = "sqs"
celery_app.conf.task_always_eager = False  


def get_db_session():
    import boto3, json, os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # 매번 시크릿에서 직접 읽기
    client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'eu-west-3'))
    rds_info = json.loads(client.get_secret_value(SecretId=os.getenv('RDS_SECRET_NAME', 'homelens/dev/rds/postgres'))['SecretString'])
    pw_info = json.loads(client.get_secret_value(SecretId=rds_info['password_secret_arn'])['SecretString'])

    db_url = f"postgresql+psycopg2://{rds_info['username']}:{pw_info['password']}@{rds_info['host']}:{rds_info['port']}/{rds_info['dbname']}?sslmode=require"

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


@celery_app.task(name="generate_report_task")
def generate_report_task(report_id: str, region_id: str, region_name: str, lat: float, lng: float, sent_at: float = None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db = get_db_session()

    # 전체 파이프라인 측정 기준점:
    # - sent_at 있으면 SQS 전송 시각부터 (큐 대기 포함)
    # - 없으면 Celery 태스크 진입 시각부터 (news/infra/price/Bedrock/DB 전부 포함)
    task_start = time.time()
    pipeline_origin = sent_at if sent_at else task_start

    try:
        from app.models.report import Report, ReportSection

        # 상태 업데이트: processing
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            print(f"[Celery] 리포트 없음: {report_id}")
            return

        # SQS 대기 지연 측정 (SQS 전송 ~ Celery 태스크 시작)
        try:
            if sent_at:
                SQS_CONSUME_LATENCY.observe(task_start - sent_at)
        except Exception:
            pass

        report.status = "processing"
        report.progress_pct = 10
        db.commit()

        # 뉴스 수집
        news_data = {}
        try:
            issues = loop.run_until_complete(get_region_issues(region_id, region_name))
            if issues:
                news_data = {"items": issues[:5]}
        except Exception as e:
            print(f"뉴스 수집 실패: {e}")

        report.progress_pct = 70
        db.commit()

        # 인프라 수집
        infra_data = {}
        try:
            markers = loop.run_until_complete(search_all_nearby_infra(lat, lng, 1500))
            if markers:
                marker_list = markers.get("markers", []) if isinstance(markers, dict) else markers
                infra_data = {"markers": [{"name": m.get("name"), "type": m.get("markerType")} for m in marker_list[:10]]}
        except Exception as e:
            print(f"인프라 수집 실패: {e}")

        report.progress_pct = 80
        db.commit()

        # 가격 데이터 수집
        price_data = {}
        try:
            from app.services.price import get_price_trend_by_dong_name
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from app.core.config import settings

            async def fetch_price():
                engine = create_async_engine(settings.database_url)
                async with AsyncSession(engine) as async_db:
                    data = await get_price_trend_by_dong_name(region_name, "all", "3m", async_db)
                    return data

            price_result = loop.run_until_complete(fetch_price())
            if price_result:
                price_data = price_result
        except Exception as e:
            print(f"가격 데이터 수집 실패: {e}")

        report.progress_pct = 90
        db.commit()

        # Bedrock 호출
        with BEDROCK_INVOKE_LATENCY.time():
            result = loop.run_until_complete(generate_report(region_name, price_data, news_data, infra_data))

        # 리포트 완료 저장
        with DB_SAVE_LATENCY.time():
            report.status = "completed"
            report.progress_pct = 100
            report.summary = result.get("summary", "")
            report.disclaimer = result.get("disclaimer", "")
            report.generated_at = datetime.now()
            report.completed_at = datetime.now()
            report.data_base_date = date.today()
            db.commit()

            # 섹션 저장
            for section in result.get("sections", []):
                db.add(ReportSection(
                    report_id=report_id,
                    section_key=section.get("sectionKey", ""),
                    section_title=section.get("sectionTitle", ""),
                    content=section.get("content", ""),
                    sort_order=section.get("sortOrder", 0),
                ))
            db.commit()

        # 전체 파이프라인 지연: SQS 전송(또는 태스크 시작) ~ DB 완료
        PIPELINE_TOTAL_LATENCY.observe(time.time() - pipeline_origin)
        print(f"[Celery] 리포트 완료: {report_id}")

    except Exception as e:
        PIPELINE_ERRORS.inc()
        print(f"[Celery] 리포트 실패: {e}")
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.status = "failed"
                report.fail_reason = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
        loop.close()

app = celery_app  # Celery CLI -A app.worker 호환