# HomeLens 모니터링 가이드

## 목차
1. [빠른 시작 — Grafana 접속](#1-빠른-시작--grafana-접속)
2. [시나리오 1: SQS→Celery→Bedrock→DB 파이프라인](#2-시나리오-1-sqscelerybedrockdb-파이프라인)
3. [시나리오 2: 사용자 접속 (HTTP + DB + 외부 API)](#3-시나리오-2-사용자-접속-http--db--외부-api)
4. [대시보드 보는 법](#4-대시보드-보는-법)
5. [알림 규칙과 대응 방법](#5-알림-규칙과-대응-방법)
6. [테스트 시나리오 재현 명령어](#6-테스트-시나리오-재현-명령어)
7. [문제 발생 시 진단 흐름](#7-문제-발생-시-진단-흐름)

---

## 1. 빠른 시작 — Grafana 접속

```bash
# 터미널 1: Grafana 포트포워딩 (닫지 말 것)
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring

# 브라우저 접속
# URL: http://localhost:3000
# 계정: admin / Homelens@2026!
```

접속 후 왼쪽 사이드바 **Dashboards** → 아래 두 대시보드 확인:
- `HomeLens Pipeline Latency — dev` (시나리오 1)
- `HomeLens User Access — dev` (시나리오 2)

---

## 2. 시나리오 1: SQS→Celery→Bedrock→DB 파이프라인

### 흐름 요약

```
사용자 → POST /api/v1/reports
           │
           ▼
       FastAPI (report 생성, status=pending)
           │
           ▼ SQS 큐 전송 (sent_at 타임스탬프 포함)
           │
           ▼
       Celery Worker (SQS에서 메시지 소비)
           │
           ├─ ① SQS_CONSUME_LATENCY 측정 시작  ← sent_at ~ task_start
           ├─ ② 뉴스/인프라/가격 데이터 수집    ← ~3–5s
           ├─ ③ BEDROCK_INVOKE_LATENCY 측정    ← Bedrock InvokeModel ~25–33s
           ├─ ④ DB_SAVE_LATENCY 측정           ← INSERT+COMMIT ~30ms
           └─ ⑤ PIPELINE_TOTAL_LATENCY 기록   ← sent_at(or task_start) ~ DB완료
```

### 메트릭 정의

| 메트릭 이름 | 타입 | 측정 구간 | 단위 |
|------------|------|----------|------|
| `homelens_sqs_consume_duration_seconds` | Histogram | SQS 전송 → Celery 태스크 시작 | s |
| `homelens_bedrock_invoke_duration_seconds` | Histogram | Bedrock API 호출 시작 → 응답 완료 | s |
| `homelens_db_save_duration_seconds` | Histogram | DB INSERT 시작 → COMMIT 완료 | s |
| `homelens_pipeline_total_duration_seconds` | Histogram | SQS 전송(또는 태스크 시작) → DB 완료 전체 | s |
| `homelens_pipeline_errors_total` | Counter | 파이프라인 예외 발생 횟수 | 건 |

> **주의**: `SQS_CONSUME_LATENCY`는 `sent_at` 파라미터가 API 요청에 포함될 때만 기록됩니다.
> `PIPELINE_TOTAL_LATENCY`는 `sent_at` 있으면 SQS 전송 시각부터, 없으면 태스크 시작 시각부터 측정합니다.

### 실측 기준값 (2026-06-10 기준, 1회 샘플)

| 구간 | 실측값 |
|------|--------|
| Bedrock InvokeModel | ~28–33s |
| DB 저장 | ~30ms |
| 전체 파이프라인 (태스크 기준) | ~32.8s |

---

## 3. 시나리오 2: 사용자 접속 (HTTP + DB + 외부 API)

### 흐름 요약

```
사용자 → GET /api/v1/analysis/price?regionId=...
           │
           ▼
       FastAPI 미들웨어 (HTTP_REQUEST_DURATION 타이머 시작)
           │
           ├─ apt_seq 있는 경우 → DB 쿼리  ← DB_QUERY_LATENCY 측정 (~10–50ms)
           │
           └─ apt_seq 없는 경우 → 국토부 API fallback
                                    ├─ EXTERNAL_API_CALLS_TOTAL 카운터 증가
                                    └─ ~5–10s 지연 (외부 API 자체 지연)
           │
           ▼
       HTTP 응답 (HTTP_REQUEST_DURATION, HTTP_REQUESTS_TOTAL 기록)
           └─ 4xx/5xx인 경우 HTTP_ERRORS_TOTAL 추가 기록
```

### 메트릭 정의

| 메트릭 이름 | 라벨 | 측정 내용 |
|------------|------|----------|
| `homelens_http_request_duration_seconds` | method, endpoint, status_code | HTTP 요청 전체 응답시간 |
| `homelens_http_requests_total` | method, endpoint, status_code | 요청 총 횟수 |
| `homelens_http_errors_total` | method, endpoint, status_code | 4xx/5xx 에러 횟수 |
| `homelens_db_query_duration_seconds` | query_type | DB 쿼리별 응답시간 |
| `homelens_external_api_calls_total` | api_type | 외부 API fallback 호출 횟수 |

### query_type 값 의미

| query_type 값 | 실행 쿼리 |
|--------------|---------|
| `price_snapshot` | 현재 시세 조회 |
| `price_trend` | 실거래가 추이 조회 |
| `price_stats` | 가격 통계 조회 |

### 실측 기준값 (2026-06-10 기준)

| 엔드포인트 | p95 | 경로 분기 |
|-----------|-----|---------|
| `/api/v1/analysis/price/trend` | ~93ms | DB 쿼리 경로 |
| `/api/v1/analysis/price/stats` | ~48ms | DB 쿼리 경로 |
| `/api/v1/reports/{id}/status` | ~12ms | DB 단순 조회 |
| `/api/v1/analysis/price` | ~5s | 외부 API fallback 발생 시 |
| `/api/v1/map/markers` | ~5s+ | 카카오맵 API 호출 |
| `/api/v1/regions/search` | ~3.3s | 도로명주소 API 호출 |

> **참고**: 외부 API 경로의 p95가 5s로 표시되는 건 Histogram 버킷 상한(5s)에서 클리핑된 값입니다.
> 실제 응답시간은 국토부 API 기준 ~10s, 도로명주소 API ~3–5s입니다.
> DB 직접 경로(apt_seq 있을 때)는 모두 100ms 이내로 목표치를 달성하고 있습니다.

---

## 4. 대시보드 보는 법

### 4-1. HomeLens Pipeline Latency 대시보드

**접근**: Dashboards → HomeLens Pipeline Latency — dev  
**시간 범위**: `Last 1 hour` (기본값 유지, 파이프라인 실행이 드물기 때문)

#### 패널별 해석법

**패널 1 — SQS 큐 대기 지연 (SQS→Celery)**
```
정상: p50 < 5s, p95 < 10s
주의(노란색): > 5s
위험(빨간색): > 10s

No data 표시 이유: API 요청 시 sent_at 파라미터가 없으면 메트릭이 기록되지 않음
```

**패널 2 — Bedrock InvokeModel 지연**
```
정상: p50 < 20s, p95 < 30s
주의(노란색): > 20s   → BedrockLatencyHigh 알림 pending 시작
위험(빨간색): > 30s   → BedrockLatencyHigh 알림 5분 후 발화

확인할 것: 값이 지속적으로 30s를 초과하면 Bedrock 리전 트래픽 폭주 또는
           Claude 모델 응답 저하 가능성 → AWS 콘솔 Bedrock 모니터링 확인
```

**패널 3 — DB 저장 지연 (INSERT→COMMIT)**
```
정상: p50 < 50ms, p95 < 1s
주의(노란색): > 1s
위험(빨간색): > 2s

이 값이 높으면: RDS 부하 또는 커넥션 풀 고갈 확인
kubectl exec 로 Celery pod 접속 → DB 연결 로그 확인
```

**패널 4 — 전체 파이프라인 지연 (SQS→DB 완료)**
```
정상: p50 < 30s, p90 < 35s
주의(노란색): > 30s
위험(빨간색): > 45s   → PipelineTotalLatencyHigh 알림 발화 기준

p90이 35s를 넘으면 PipelineTotalLatencyHigh 알림 전송됨
- Bedrock 패널도 함께 확인 (Bedrock이 느리면 전체도 느림)
- news/infra 수집 단계 지연 여부는 Celery 로그에서 확인:
  kubectl logs -n homelens -l app=celery-worker --tail=50
```

**패널 5 — 파이프라인 처리량 (성공/실패)**
```
에러 라인이 올라가면: PIPELINE_ERRORS_TOTAL 증가 → 로그 확인
- 정상 상태: 에러 0
- 에러 급증 시: PipelineErrorRateHigh 알림 발화 (5분간 3건 이상)
```

### 4-2. HomeLens User Access 대시보드

**접근**: Dashboards → HomeLens User Access — dev  
**시간 범위**: `Last 5 minutes` (트래픽이 실시간으로 들어올 때) 또는 `Last 1 hour`

#### 패널별 해석법

**패널 1 — 요청 처리량 (req/min, 엔드포인트별)**
```
여러 엔드포인트 라인이 함께 표시됨
- 특정 엔드포인트 폭증: 비정상 트래픽 또는 클라이언트 반복 폴링
- 전체 0: 서비스 다운 또는 스크레이프 중단
```

**패널 2 — 에러율 (%)**
```
정상: 1% 미만 (초록색)
주의(노란색): > 1%
위험(빨간색): > 5%   → HttpErrorRateHigh 알림 발화 기준

에러율 급증 시 확인 순서:
1. 어떤 엔드포인트에서 에러 발생?  → 패널 5 (엔드포인트별 p95) 확인
2. 503 에러면: 외부 API fallback 실패 → 국토부/카카오 API 상태 확인
3. 500 에러면: FastAPI 내부 예외 → kubectl logs 확인
```

**패널 3 — HTTP 응답시간 분위수 (p50/p95/p99)**
```
목표: p95 < 2s
주의(노란색): > 1s
위험(빨간색): > 2s   → HttpResponseTimeHigh 알림 발화 기준

p95가 2s를 넘어도 '외부 API fallback이 많이 일어났을 뿐'일 수 있음
→ 패널 6 (외부 API fallback 횟수)를 함께 확인

외부 API 없이 DB 경로만의 성능은 패널 4 (DB 쿼리 지연)를 보는 것이 정확함
```

**패널 4 — apt_seq DB 쿼리 지연 (query_type별)**
```
정상: p95 < 100ms (초록색)
주의(노란색): > 250ms
위험(빨간색): > 500ms   → DbQueryLatencyHigh 알림 발화 기준

query_type 라인별 의미:
- price_snapshot: 현재 시세 조회 (가장 자주 실행)
- price_trend: 실거래가 추이 (조인 쿼리, 약간 느릴 수 있음)
- price_stats: 가격 통계

p95가 높으면: RDS CPU 또는 연결 수 확인
```

**패널 5 — 엔드포인트별 p95 응답시간 (막대 그래프)**
```
가로 막대 형식으로 현재 순간의 p95를 표시
→ 어떤 엔드포인트가 가장 느린지 한눈에 파악

/api/v1/analysis/price 와 /api/v1/map/markers 가
항상 5s 이상 표시되는 것은 외부 API 의존 때문으로 정상 범위임
→ DB 경로 엔드포인트(/price/trend, /price/stats, /reports/status 등)만
  2s 이하인지 집중 확인
```

**패널 6 — 외부 API fallback 호출 횟수 (주황색)**
```
api_type=molit_price: 국토부 실거래가 API fallback
(apt_seq가 없어 DB에서 데이터를 못 찾고 외부 API를 직접 호출한 경우)

이 수치가 높을수록:
- DB에 apt_seq 매핑 데이터가 부족한 상태
- HTTP p95가 높게 나오는 원인
- 국토부 API 호출 비용 증가

대응: apt_seq 없는 단지 목록을 파악하여 DB 데이터 보완
```

---

## 5. 알림 규칙과 대응 방법

### 알림 상태 확인

```bash
# Prometheus 알림 규칙 상태
curl -s http://localhost:9090/api/v1/rules | python3 -c "
import sys,json; d=json.load(sys.stdin)
for g in d['data']['groups']:
    if 'homelens' in g['name']:
        for r in g['rules']:
            print(f\"[{r.get('state','?'):8s}] {r['name']}\")
"
# 상태값: inactive(정상), pending(조건 충족, 발화 대기), firing(알림 발화)
```

### 알림별 대응 방법

| 알림 이름 | 조건 | 즉시 확인할 것 |
|-----------|------|--------------|
| `PipelineErrorRateHigh` | 5분간 에러 3건↑ | `kubectl logs -n homelens -l app=celery-worker` |
| `BedrockLatencyHigh` | Bedrock p95 > 30s | AWS 콘솔 → Bedrock → 모델 사용량 및 가용성 |
| `PipelineTotalLatencyHigh` | 전체 p90 > 35s | Bedrock 지연 + `kubectl logs` 로 각 단계 확인 |
| `HttpErrorRateHigh` | HTTP 에러율 > 5% | 에러 엔드포인트 확인 → FastAPI 로그 |
| `HttpResponseTimeHigh` | HTTP p95 > 2s | 외부 API fallback 패널 + DB 쿼리 패널 |
| `DbQueryLatencyHigh` | DB p95 > 500ms | RDS CloudWatch 지표 (CPU, 연결 수) 확인 |

---

## 6. 테스트 시나리오 재현 명령어

### 사전 준비 (터미널 두 개 열기)

```bash
# 터미널 1: FastAPI 포트포워딩
kubectl port-forward svc/fastapi 8000:80 -n homelens

# 터미널 2: Grafana 포트포워딩
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
```

### 시나리오 1: 파이프라인 트리거 + 모니터링

```bash
# 1단계: 새 regionId로 파이프라인 트리거
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{"regionId":"REGION_11110_DONG_001_TEST","regionName":"종로구 청운효자동","lat":37.5843,"lng":126.9714}'
# → reportId 복사

# 2단계: 상태 폴링 (10초마다)
REPORT_ID="<복사한 reportId>"
watch -n 10 "curl -s http://localhost:8000/api/v1/reports/${REPORT_ID}/status | python3 -c 'import sys,json; d=json.load(sys.stdin); r=d.get(\"data\",d); print(r.get(\"status\"), r.get(\"progressPct\",\"\"))'"

# 3단계: Grafana에서 확인
# → HomeLens Pipeline Latency 대시보드 → 시간범위 Last 1 hour
# → 패널 2(Bedrock), 패널 3(DB), 패널 4(전체) 에 데이터 점 생성 확인

# 4단계: Celery 로그에서 처리 시간 확인
kubectl logs -n homelens -l app=celery-worker --tail=20
```

### 시나리오 2: 사용자 접속 + HTTP 메트릭 확인

```bash
# DB 경로 (apt_seq 있는 단지명 사용)
curl "http://localhost:8000/api/v1/analysis/price/trend?regionId=REGION_11680_DONG_001&regionName=역삼동&period=3m"
curl "http://localhost:8000/api/v1/analysis/price/stats?regionId=REGION_11680_DONG_001&regionName=역삼동"

# 외부 API fallback 경로 (apt_seq 없는 조회)
curl "http://localhost:8000/api/v1/analysis/price?regionId=REGION_11680_DONG_001&regionName=역삼동"

# Grafana에서 확인
# → HomeLens User Access 대시보드 → 시간범위 Last 5 minutes
# → 패널 1(처리량), 패널 3(응답시간), 패널 6(외부 API 호출) 변화 관찰
```

### Prometheus 직접 쿼리 (포트포워딩 필요)

```bash
# Prometheus 포트포워딩
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring

# 유용한 PromQL 예시
# HTTP p95 응답시간 (엔드포인트별, 최근 5분)
curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,sum+by+(le,endpoint)(increase(homelens_http_request_duration_seconds_bucket[5m])))"

# Bedrock p95 지연 (최근 10분)
curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,sum(increase(homelens_bedrock_invoke_duration_seconds_bucket[10m]))+by+(le))"

# 전체 파이프라인 p90 (최근 1시간)
curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.90,sum(increase(homelens_pipeline_total_duration_seconds_bucket[1h]))+by+(le))"

# 외부 API fallback 횟수 (최근 5분)
curl "http://localhost:9090/api/v1/query?query=increase(homelens_external_api_calls_total[5m])"

# HTTP 에러율 % (최근 5분)
curl "http://localhost:9090/api/v1/query?query=100*(sum(increase(homelens_http_errors_total[5m]))+or+vector(0))/(sum(increase(homelens_http_requests_total[5m]))+1)"
```

---

## 7. 문제 발생 시 진단 흐름

### 패턴 A: 파이프라인이 갑자기 느려짐

```
1. Pipeline Latency 대시보드 열기
2. 패널 4 (전체 지연) → 언제부터 느려졌나 확인
3. 패널 2 (Bedrock) 확인
   - Bedrock도 같이 느림 → Bedrock/Claude 리전 문제
   - Bedrock은 정상   → 패널 3 (DB) 또는 news/infra 수집 단계 문제
4. Celery 로그 확인:
   kubectl logs -n homelens -l app=celery-worker --tail=100 | grep -E "완료|실패|error|Error"
```

### 패턴 B: HTTP 에러율이 올라감

```
1. User Access 대시보드 → 패널 2 (에러율) 확인
2. 패널 5 (엔드포인트별 p95) 에서 어떤 엔드포인트인지 확인
3. FastAPI 로그:
   kubectl logs -n homelens -l app=fastapi --tail=100 | grep -E "503|500|Error"
4. 503이 많으면: 국토부 API 상태 확인 (외부 API 장애)
5. 500이 많으면: DB 연결 문제 또는 코드 예외 → 상세 로그 확인
```

### 패턴 C: Grafana에 데이터가 안 보임 (No data)

```bash
# 1. FastAPI 메트릭 엔드포인트 직접 확인
kubectl port-forward svc/fastapi 8000:80 -n homelens
curl http://localhost:8000/metrics | grep "^homelens_"

# 2. Prometheus scrape 대상 확인
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
# http://localhost:9090/targets 에서 homelens job 상태 확인

# 3. Celery worker 메트릭 포트 확인 (port 8000에서 prometheus_client 서버 실행 중인지)
kubectl exec -n homelens -l app=celery-worker -- curl -s localhost:8000 | head -5
```

---

## Prometheus 메트릭 scrape 구조

```
Prometheus (kube-prometheus-stack)
  │
  ├── FastAPI pod (10.0.x.x:8080)
  │     └── /metrics 엔드포인트
  │         └── homelens_http_*, homelens_db_query_*, homelens_external_api_*
  │             (HTTP 미들웨어에서 기록 — 파이프라인 메트릭은 항상 0)
  │
  └── Celery worker pod (10.0.x.x:8000)
        └── prometheus_client.start_http_server(8000)
            └── homelens_bedrock_*, homelens_db_save_*, homelens_pipeline_*,
                homelens_sqs_consume_* (태스크 실행 시 기록)

PromQL에서 sum() 필수:
  sum(increase(homelens_bedrock_invoke_duration_seconds_bucket[1h])) by (le)
  → FastAPI(0) + Celery(실제값) = 실제값
```
