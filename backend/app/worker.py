# HomeLens AI - Celery Worker
# SQS 브로커 기반 AI 리포트 비동기 생성 → RDS 저장

import os
import asyncio
import time
from datetime import datetime, date
from celery import Celery
from app.services.report import generate_report
from app.services.news import get_region_issues
from app.services.map import search_all_nearby_infra
from app.metrics import (
    BEDROCK_INVOKE_LATENCY,
    DB_SAVE_LATENCY,
    PIPELINE_TOTAL_LATENCY,
    PIPELINE_ERRORS,
    start_metrics_server,
)
start_metrics_server()

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
def generate_report_task(report_id: str, region_id: str, region_name: str, lat: float, lng: float):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db = get_db_session()

    try:
        from app.models.report import Report, ReportSection

        # 상태 업데이트: processing
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            print(f"[Celery] 리포트 없음: {report_id}")
            return
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

        # Bedrock 호출
        pipeline_start = time.time()
        with BEDROCK_INVOKE_LATENCY.time():
            result = loop.run_until_complete(generate_report(region_name, {}, news_data, infra_data))

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

        PIPELINE_TOTAL_LATENCY.observe(time.time() - pipeline_start)
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