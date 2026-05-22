# HomeLens AI - Celery Worker
# SQS 브로커 기반 AI 리포트 비동기 생성

import os
import asyncio
import json
from datetime import datetime, date
from celery import Celery
from app.services.report import generate_report
from app.services.news import get_region_issues
from app.services.map import search_all_nearby_infra
from app.core.redis import report_set, report_get

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
    },
    task_default_queue="homelens-dev-report-generation",
)
celery_app.conf.broker_connection_retry_on_startup = True

@app.task(name="generate_report_task")
def generate_report_task(report_id: str, region_id: str, region_name: str, lat: float, lng: float):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        data = report_get(report_id) or {}
        data["status"] = "processing"
        data["progressPct"] = 10
        report_set(report_id, data)

        # 뉴스 수집
        news_data = {}
        try:
            issues = loop.run_until_complete(get_region_issues(region_id, region_name))
            if issues:
                news_data = {"items": issues[:5]}
        except Exception as e:
            print(f"뉴스 수집 실패: {e}")

        data["progressPct"] = 70
        report_set(report_id, data)

        # 인프라 수집
        infra_data = {}
        try:
            markers = loop.run_until_complete(search_all_nearby_infra(lat, lng, 1500))
            if markers:
                marker_list = markers.get("markers", []) if isinstance(markers, dict) else markers
                infra_data = {"markers": [{"name": m.get("name"), "type": m.get("markerType")} for m in marker_list[:10]]}
        except Exception as e:
            print(f"인프라 수집 실패: {e}")

        data["progressPct"] = 80
        report_set(report_id, data)

        # Bedrock 호출
        result = loop.run_until_complete(generate_report(region_name, {}, news_data, infra_data))

        data.update({
            "status": "completed",
            "progressPct": 100,
            "summary": result.get("summary", ""),
            "sections": result.get("sections", []),
            "disclaimer": result.get("disclaimer", ""),
            "generatedAt": datetime.now().isoformat(),
            "dataBaseDate": str(date.today()),
            "completedAt": datetime.now().isoformat(),
        })
        report_set(report_id, data)
        print(f"[Celery] 리포트 완료: {report_id}")

    except Exception as e:
        print(f"[Celery] 리포트 실패: {e}")
        data = report_get(report_id) or {}
        data["status"] = "failed"
        data["failReason"] = str(e)
        report_set(report_id, data)
    finally:
        loop.close()