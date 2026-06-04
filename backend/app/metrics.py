from prometheus_client import Histogram, Counter, start_http_server

SQS_CONSUME_LATENCY = Histogram(
    "homelens_sqs_consume_duration_seconds",
    "SQS 메시지 전송 ~ Celery task 시작 지연",
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60]
)
BEDROCK_INVOKE_LATENCY = Histogram(
    "homelens_bedrock_invoke_duration_seconds",
    "Bedrock InvokeModel 소요시간",
    buckets=[1, 3, 5, 10, 15, 20, 30, 60]
)
DB_SAVE_LATENCY = Histogram(
    "homelens_db_save_duration_seconds",
    "DB INSERT→COMMIT 소요시간",
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)
PIPELINE_TOTAL_LATENCY = Histogram(
    "homelens_pipeline_total_duration_seconds",
    "SQS 전송 ~ DB 완료 전체 파이프라인 지연",
    buckets=[5, 10, 15, 20, 25, 30, 45, 60]
)
PIPELINE_ERRORS = Counter(
    "homelens_pipeline_errors_total",
    "파이프라인 에러 총 횟수"
)

def start_metrics_server():
    start_http_server(8000)
