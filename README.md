<div align="center">

# 🏠 HomeLens AI

### 서울 부동산 AI 분석 서비스

실거래가 기반 시세 조회, AI 뉴스 요약, 맞춤형 분석 리포트를 제공하는 모바일 백엔드 플랫폼

<br>

**Backend**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.x-E92063?style=flat-square&logo=pydantic&logoColor=white)

**Frontend**

![React Native](https://img.shields.io/badge/React_Native-Expo-20232A?style=flat-square&logo=react&logoColor=61DAFB)

**Database & Cache**

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17%20+%20PostGIS-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-Migration-6BA539?style=flat-square&logo=sqlalchemy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

**Async / Messaging**

![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=flat-square&logo=celery&logoColor=white)
![AWS SQS](https://img.shields.io/badge/AWS-SQS%20+%20Step%20Functions-FF9900?style=flat-square&logo=amazonsqs&logoColor=white)

**AWS Infrastructure**

![AWS Lambda](https://img.shields.io/badge/AWS-Lambda%20×9-FF9900?style=flat-square&logo=awslambda&logoColor=white)
![AWS EKS](https://img.shields.io/badge/AWS-EKS-FF9900?style=flat-square&logo=amazoneks&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS-S3%20+%20ElastiCache-FF9900?style=flat-square&logo=amazons3&logoColor=white)
![AWS EventBridge](https://img.shields.io/badge/AWS-EventBridge-FF9900?style=flat-square&logo=amazonaws&logoColor=white)
![KEDA](https://img.shields.io/badge/KEDA-Autoscaling-326CE5?style=flat-square&logo=kubernetes&logoColor=white)

**AI**

![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude-FF9900?style=flat-square&logo=amazonaws&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-AWS-1C3C3C?style=flat-square&logo=langchain&logoColor=white)

**Observability**

![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?style=flat-square&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-Dashboard-F46800?style=flat-square&logo=grafana&logoColor=white)

</div>

---

## 📑 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [아키텍처](#아키텍처)
3. [기술 스택](#기술-스택)
4. [디렉터리 구조](#디렉터리-구조)
5. [로컬 개발 환경 구성](#로컬-개발-환경-구성)
6. [환경 변수](#환경-변수)
7. [API 사용법](#api-사용법)
8. [데이터 파이프라인](#데이터-파이프라인)
9. [캐시 정책](#캐시-정책)
10. [DB 마이그레이션](#db-마이그레이션)
11. [위키 문서](#위키-문서)

---

## 📖 프로젝트 개요

HomeLens AI는 서울 아파트 실거래가 데이터를 수집·가공하여 모바일 앱(React Native / Expo)에 제공하는 백엔드 서비스입니다.

**핵심 기능**

- 🏘️ **실거래가 조회** — 국토부 API 기반 매매·전세·월세 시세, 월별 가격 추이
- 🗺️ **지도 데이터** — 지역별 평균 시세 히트맵, 아파트 단지 위치 정보
- 📰 **AI 뉴스 요약** — 네이버 뉴스 수집 후 AWS Bedrock(Claude)으로 1~2줄 요약
- 🤖 **AI 분석 리포트** — 특정 지역 맞춤 부동산 시장 분석 리포트 비동기 생성
- 🔔 **이슈 알림** — 재개발·규제 등 부동산 관련 이슈 자동 분류 및 제공

---

## 🏗 아키텍처

```mermaid
flowchart TD
    A[React Native 앱<br/>Expo] -->|HTTPS + X-API-KEY| B[FastAPI 백엔드]
    B -->|캐시 조회| C[Redis Cache<br/>ElastiCache]
    C -->|Cache Miss| D[RDS PostgreSQL 17<br/>+ PostGIS]
    D -->|결과 반환| B
```

**데이터 파이프라인 1 — 정기 배치 (EventBridge 스케줄)**

```mermaid
flowchart LR
    A[EventBridge] --> B[Lambda] --> C[S3] --> D[Step Functions] --> E[Lambda] --> F[RDS]
```

**데이터 파이프라인 2 — AI 리포트 (사용자 요청 시 온디맨드)**

```mermaid
flowchart LR
    A["POST /reports"] --> B[SQS] --> C[Celery Worker] --> D[Bedrock] --> E[RDS]
```

**주요 설계 원칙**

- API 요청 시 Redis → DB → 외부 API 순으로 조회 (Cache-Aside 패턴)
- 데이터 수집 파이프라인은 EventBridge 스케줄로 백엔드와 완전 분리 실행
- AI 리포트 생성은 SQS + Celery 를 통해 비동기 처리 (응답 지연 없음)
- 모든 시크릿(DB 비밀번호, API 키)은 AWS Secrets Manager로 관리

---

## 🛠 기술 스택

| 영역 | 기술 |
|------|------|
| **백엔드** | Python 3.11, FastAPI 0.115, uvicorn |
| **ORM / DB** | SQLAlchemy 2.x (async), asyncpg, Alembic |
| **데이터베이스** | Amazon RDS PostgreSQL 17 + PostGIS 3.2 |
| **캐시** | Redis 7 (AWS ElastiCache, eu-west-3) |
| **큐 / 비동기** | AWS SQS, Celery 5.4 |
| **AI** | AWS Bedrock — `eu.anthropic.claude-sonnet-4-6` |
| **데이터 파이프라인** | AWS Lambda (×9), Step Functions, EventBridge |
| **스토리지** | AWS S3 (원시 수집 데이터 임시 저장) |
| **시크릿 관리** | AWS Secrets Manager |
| **모니터링** | Prometheus (`prometheus-client`) |
| **모바일 프론트** | React Native (Expo) |
| **로컬 개발** | Docker Compose (PostGIS 17-3.5, Redis 7) |

---

## 📂 디렉터리 구조

```
msp-team06/
├── app/                          # React Native (Expo) 앱
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 진입점, 라우터 등록, CORS 설정
│   │   ├── worker.py             # Celery 워커 (AI 리포트 비동기 생성)
│   │   ├── metrics.py            # Prometheus 메트릭
│   │   ├── core/
│   │   │   ├── config.py         # AWS Secrets Manager 기반 설정
│   │   │   ├── database.py       # SQLAlchemy 비동기 엔진
│   │   │   └── redis.py          # Redis 연결 및 TTL 상수
│   │   ├── api/v1/endpoints/
│   │   │   ├── analysis.py       # 가격 분석 API
│   │   │   ├── places.py         # 지도·단지 API
│   │   │   └── news.py           # 뉴스 API
│   │   ├── models/               # SQLAlchemy ORM 모델
│   │   ├── services/             # 비즈니스 로직 (Redis → DB → 외부 API)
│   │   ├── schemas/              # Pydantic 요청/응답 스키마
│   │   └── utils/classify.py     # 뉴스 impact_type 분류 유틸
│   ├── Dockerfile
│   ├── docker-compose.yml        # 로컬 개발용 (DB + Redis)
│   └── requirements.txt
└── data-pipeline/
    ├── alembic/                  # DB 마이그레이션 (5개)
    └── lambdas/                  # AWS Lambda 함수 (9개)
        ├── molit_price_ingest/       # 국토부 실거래가 수집
        ├── normalize_price_data/     # S3 → DB 정규화
        ├── apt_complex_ingest/       # 아파트 단지 정보 수집
        ├── news_collector/           # 네이버 뉴스 수집
        ├── news_summarizer_trigger/  # S3 뉴스 → SQS 분배
        ├── summarize_news/           # Bedrock AI 뉴스 요약
        ├── pipeline_step/            # Step Functions 범용 처리기
        ├── detect_data_update/       # Redis 캐시 무효화
        └── region_normalizer/        # 법정동코드 정규화
```

---

## 💻 로컬 개발 환경 구성

### 사전 요구사항

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (프론트엔드 실행 시)
- AWS CLI (데이터 파이프라인 실행 시)

### 1. 저장소 클론

```bash
git clone https://github.com/Team-msp-architect-2026/msp-team06.git
cd msp-team06
```

### 2. 백엔드 패키지 설치

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`backend/.env` 파일을 생성합니다. (아래 [환경 변수](#환경-변수) 섹션 참고)

### 4. 로컬 DB · Redis 실행

```bash
# backend/ 디렉터리에서 실행
docker-compose up -d
```

| 서비스 | 이미지 | 포트 |
|--------|--------|------|
| PostgreSQL 17 + PostGIS | `postgis/postgis:17-3.5` | 5432 |
| Redis 7 | `redis:7` | 6379 |

### 5. DB 마이그레이션

```bash
cd data-pipeline
alembic upgrade head
```

### 6. 백엔드 서버 실행

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버 시작 후 API 문서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 7. Celery 워커 실행 (AI 리포트 기능 필요 시)

```bash
cd backend
celery -A app.worker worker --loglevel=info
```

### 8. 프론트엔드 실행

```bash
# 루트 디렉터리에서
npm install
npx expo start
```

---

## 🔑 환경 변수

`backend/.env` 파일에 아래 변수를 설정합니다.

```dotenv
# ── 실행 환경 ──────────────────────────────────────────
ENV=dev                          # dev | prod

# ── 데이터베이스 (로컬 개발) ───────────────────────────
DATABASE_URL=postgresql+asyncpg://homelens:homelens@localhost:5432/homelens

# ── Redis (로컬 개발) ──────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── AWS ────────────────────────────────────────────────
AWS_REGION=eu-west-3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# ── SQS (Celery 브로커) ────────────────────────────────
SQS_REPORT_URL=https://sqs.eu-west-3.amazonaws.com/{account}/homelens-dev-report-generation
CELERY_BROKER_URL=sqs://

# ── 외부 API ───────────────────────────────────────────
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
MOLIT_API_KEY=your_molit_api_key          # 국토부 실거래가
ADDRESS_API_KEY=your_address_api_key       # 행정안전부 도로명주소

# ── API 보안 ───────────────────────────────────────────
API_KEY=your_x_api_key
```

> **프로덕션 환경**에서는 `.env` 대신 AWS Secrets Manager를 사용합니다.
> 시크릿 경로: `homelens/{ENV}/rds/postgres`, `homelens/{ENV}/redis`, `homelens/{ENV}/api-keys`

---

## 🌐 API 사용법

### Base URL

```
https://api.homelens.ai/api/v1
```

### 인증

모든 요청에 `X-API-KEY` 헤더가 필요합니다.

```
X-API-KEY: {your_api_key}
```

**Rate Limit:** 분당 5회 / 일 20회

### 주요 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/analysis/price` | 지역 실거래가 조회 |
| `GET` | `/analysis/price/trend` | 월별 가격 추이 |
| `GET` | `/analysis/price/stats` | 가격 통계 (최저·평균·최고) |
| `POST` | `/analysis/report` | AI 분석 리포트 생성 요청 |
| `GET` | `/analysis/report/{report_id}` | 리포트 조회 |
| `GET` | `/places/map` | 지도 히트맵 데이터 |
| `GET` | `/places/apartments` | 아파트 단지 목록 |
| `GET` | `/places/apartments/{apt_seq}` | 단지 상세 정보 |
| `GET` | `/news` | 뉴스 목록 (AI 요약 포함) |
| `GET` | `/news/issues` | 부동산 이슈 목록 |

### 요청 예시

```bash
# 성수동 아파트 매매 시세 조회
curl -H "X-API-KEY: your_key" \
  "https://api.homelens.ai/api/v1/analysis/price?region_id=REGION_11680_DONG_001&deal_type=sale"

# AI 분석 리포트 생성 (비동기 — report_id 반환 후 폴링)
curl -X POST -H "X-API-KEY: your_key" \
  -H "Content-Type: application/json" \
  -d '{"region_id": "REGION_11680_DONG_001"}' \
  "https://api.homelens.ai/api/v1/analysis/report"

# 리포트 결과 조회
curl -H "X-API-KEY: your_key" \
  "https://api.homelens.ai/api/v1/analysis/report/{report_id}"
```

> 전체 요청/응답 스펙은 [Wiki: API 명세서 v5.0](./API-명세서.md) 참고

---

## 🔄 데이터 파이프라인

Lambda 함수 9개가 두 가지 파이프라인으로 동작합니다.

### 파이프라인 1 — 실거래가 수집 (매월 1일)

```
EventBridge (매월 1일)
    └→ molit_price_ingest        # 국토부 API → S3 원시 저장
        └→ Step Functions
            ├→ region_normalizer       # 법정동코드 정규화 → regions 테이블
            └→ normalize_price_data    # S3 → price_snapshots / price_trends / price_stats
```

### 파이프라인 2 — 뉴스 수집 및 AI 요약 (매일 새벽)

```
EventBridge (매일 새벽)
    └→ news_collector             # 네이버 뉴스 6개 키워드 → S3
        └→ Step Functions
            ├→ news_summarizer_trigger   # S3 뉴스 목록 → SQS (news-summary-queue)
            │       └→ summarize_news    # Bedrock Claude 1~2줄 요약 → DB
            └→ pipeline_step             # 뉴스·이슈 DB 저장, impact_type 분류
```

### AI 리포트 생성 (온디맨드)

```
POST /analysis/report
    └→ FastAPI → SQS (homelens-dev-report-generation)
                    └→ Celery Worker
                            └→ AWS Bedrock (claude-sonnet-4-6)
                                    └→ reports 테이블 저장
```

> Lambda 스펙·메모리·타임아웃 상세는 [Wiki: 배치작업 명세서](./배치작업-명세서.md) 참고

---

## ⚡ 캐시 정책

Redis (AWS ElastiCache, `eu-west-3`)를 Cache-Aside 패턴으로 사용합니다.

| 데이터 종류 | TTL | 키 패턴 예시 |
|-------------|-----|-------------|
| 실거래가 | **24시간** | `price:{region_id}:{deal_type}` |
| 뉴스 | **2시간** | `news:{region_id}` |
| 지도 데이터 | **12시간** | `map:{region_id}:{zoom}` |
| AI 리포트 | **2시간** | `report:{report_id}` |
| 아파트 단지 목록 | **7일** | `kapt:list:{bjd_code}` |

**조회 순서:** Redis 캐시 → PostgreSQL → 외부 API

**캐시 무효화:** `detect_data_update` Lambda가 데이터 업데이트 감지 시 관련 Redis 키를 자동 삭제합니다.

> 상세 정책은 [Wiki: 캐시 & 갱신정책](./캐시-갱신정책.md) 참고

---

## 🗃 DB 마이그레이션

Alembic으로 스키마를 관리합니다. 마이그레이션 파일은 `data-pipeline/alembic/versions/`에 위치합니다.

```bash
# 최신 스키마로 업그레이드
cd data-pipeline
alembic upgrade head

# 현재 버전 확인
alembic current

# 한 단계 롤백
alembic downgrade -1
```

**마이그레이션 적용 순서**

```
initial_schema
    └→ add_price_tables
        └→ add_news_tables
            └→ add_report_table
                └→ v5_add_apt_seq_columns
```

> 전체 스키마(13개 테이블, 55개 인덱스)는 [Wiki: DB 스키마](./DB-스키마.md) 참고

---

## 📚 위키 문서

| 문서 | 내용 |
|------|------|
| [API 명세서](./API-명세서.md) | 전체 14개 엔드포인트 요청/응답 스펙, v5.0 변경이력 |
| [DB 스키마](./DB-스키마.md) | 13개 테이블 컬럼 정의, 인덱스, 마이그레이션 이력 |
| [캐시 & 갱신정책](./캐시-갱신정책.md) | TTL 정책, Redis 키 패턴, 무효화 전략 |
| [배치작업 명세서](./배치작업-명세서.md) | Lambda 9개 스펙, Step Functions 파이프라인 흐름 |

---

<div align="center">

### 팀

**MSP Architect Team 06** · 2026

</div>
