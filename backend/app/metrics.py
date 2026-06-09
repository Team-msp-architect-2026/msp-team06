from prometheus_client import Histogram, Counter, start_http_server

# ── 시나리오 1: SQS → Celery → Bedrock → DB 파이프라인 ─────────────────────
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

# ── 시나리오 2: 사용자 접속 (HTTP + DB 쿼리) ───────────────────────────────
HTTP_REQUEST_DURATION = Histogram(
    "homelens_http_request_duration_seconds",
    "HTTP 요청 응답시간",
    labelnames=["method", "endpoint", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)
HTTP_REQUESTS_TOTAL = Counter(
    "homelens_http_requests_total",
    "HTTP 요청 총 횟수",
    labelnames=["method", "endpoint", "status_code"],
)
HTTP_ERRORS_TOTAL = Counter(
    "homelens_http_errors_total",
    "HTTP 4xx/5xx 에러 총 횟수",
    labelnames=["method", "endpoint", "status_code"],
)
DB_QUERY_LATENCY = Histogram(
    "homelens_db_query_duration_seconds",
    "apt_seq 기반 DB 쿼리 응답시간",
    labelnames=["query_type"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1],
)
EXTERNAL_API_CALLS_TOTAL = Counter(
    "homelens_external_api_calls_total",
    "DB 조회 실패 후 외부 API fallback 호출 횟수",
    labelnames=["api_type"],
)

def start_metrics_server():
    start_http_server(8000)
