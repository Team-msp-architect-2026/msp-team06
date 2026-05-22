# HomeLens AI 기술 스택 정의서

## 선정 원칙

| 원칙 | 내용 |
|------|------|
| 성능 목표 달성 | 검색 자동완성 500ms, 가격 데이터 2초, AI 리포트 30초 이내 — Redis 캐시 + FastAPI 비동기 + EKS 오토스케일링 조합 |
| 보안 및 안정성 | WAF + Secrets Manager + IRSA로 API 키와 데이터 보호. 외부 API 키 클라이언트 노출 금지 |

---

## 프론트엔드

### React Native
- iOS / Android 앱을 단일 코드베이스로 개발 (개발 인력 2배 절감)

### React Native WebView
- 카카오맵은 JavaScript 웹 방식으로만 제공 → WebView로 앱 안에 임베드
- 네이티브 지도 라이브러리 사용 금지

### React Native Reanimated
- 가격 분석 탭 전환, AI 리포트 탭 전환, 스켈레톤 로딩 UI 애니메이션
- 부드러운 인터랙션은 앱 완성도 첫인상 결정 → 필수

### Victory Native
- FR-05 가격 분석 탭: 매매·전세·월세 1개월/3개월/1년 추이 차트
- React Native 전용 최적화 → 성능 저하 없이 차트 렌더링

### TanStack Query
- 서버 데이터 페칭·캐싱·동기화 전담
- AI 리포트 Polling (2~3초 간격) 처리
- 없으면 가격 데이터, 이슈 목록, 리포트 상태 처리를 전부 직접 코딩해야 함

### Zustand
- 전역 UI 상태 관리 (검색 결과에서 선택한 단지 정보 → 가격 분석 탭, AI 리포트 탭 공유)
- 서버 데이터는 TanStack Query, 전역 UI 상태만 Zustand로 분리

---

## 백엔드

### FastAPI
- Python 웹 프레임워크 중 가장 빠른 처리 속도
- 검색 자동완성 500ms, 가격 데이터 2초 성능 목표 달성에 적합
- LangChain·GeoAlchemy2 등 AI/지도 Python 라이브러리와 자연스럽게 연동

### Pydantic v2
- 요청 입력 검증 (regionId 형식, dealType 값 등)
- 잘못된 요청을 서버 내부 진입 전에 차단 → 개발 중 버그 조기 발견

### SQLAlchemy 2.x
- Python 코드로 DB 쿼리 작성 (ORM)
- GeoAlchemy2와 함께 사용 → 위치 좌표 기반 쿼리 처리

### LangChain
- AI 요약 리포트(FR-07) 생성 파이프라인 관리
- 가격 데이터 + 뉴스 기사 + 인프라 정보를 취합 → 구조화된 프롬프트 생성 → 4섹션 결과 파싱

### Amazon Bedrock (Claude 모델)
- AI 요약 리포트 생성에 Claude 모델 사용
- 서버 관리 없이 사용한 만큼만 비용 지불
- AWS 내부 네트워크 호출 → 보안·속도 우수
- VPC Endpoint (bedrock-runtime) 필수 설정

### GeoAlchemy2
- FR-04 주변 인프라: 단지 중심 반경 내 지하철역·학교·병원 목록 조회
- PostGIS와 함께 사용 → 거리 계산을 DB 레벨에서 처리

### Celery
- AI 리포트(FR-07) 비동기 생성 담당
- 사용자 요청 시 즉시 응답 → 실제 AI 생성은 백그라운드에서 처리
- EKS worker 노드그룹에 별도 배포 (FastAPI와 분리)

---

## 데이터 저장

### Amazon RDS PostgreSQL 17 + PostGIS 3.5
- 핵심 테이블 전체 저장 (regions, price_snapshots, reports 등)
- PostGIS: '단지에서 반경 500m 안의 지하철역' 같은 공간 쿼리를 SQL 한 줄로 처리
- dev: db.t4g.small / staging: db.t4g.medium / prod: db.t4g.medium Multi-AZ

### Amazon ElastiCache Redis 7.1
- 반복 조회 데이터 캐싱 (같은 지역 가격 정보 등)
- 검색 자동완성 500ms, 가격 데이터 2초 이내 성능 목표 달성의 핵심
- dev/staging: 단일 노드 / prod: primary 1 + replica 1
- prod: auth_token 필수 적용

### Amazon S3
- 국토부 공공 API 원본 데이터 파일 보관
- AI 리포트 원문 백업
- 데이터 파이프라인 처리 결과물 임시 저장
- DB 저장 전 원본 보관 → 데이터 오류 발생 시 복구 가능

---

## 데이터 파이프라인

### Amazon EventBridge
- 뉴스 수집: 매일 새벽 스케줄
- 국토부 실거래가: 월 1회 업데이트 감지
- 스케줄 자동 관리 → 수동 실행 불필요

### AWS Step Functions
- 파이프라인 단계 연결: 국토부 API 수집 → 데이터 정규화 → DB 저장 → AI 뉴스 요약 생성
- 단계별 실패 시 해당 단계만 재실행 가능
- ASL 워크플로우 정의: `modules/step-functions/definition.asl.json`

### AWS Lambda (VPC 밖 배치 확정)
- 배치 작업 시간에만 비용 발생
- lambda_sg 미생성 / RDS·Redis 직접 접근 없음 (SQS·S3 경유)

| 함수 이름 | 역할 | 메모리 | 타임아웃 |
|-----------|------|--------|----------|
| news-collector | 뉴스 수집 | 512MB | 180s |
| news-summarizer-trigger | 뉴스 요약 요청 분배 | 1024MB | 180s |
| molit-price-ingest | 국토부 실거래가 수집 | 1024MB | 900s |
| region-normalizer | 법정동코드·지역 정규화 | 512MB | 180s |
| pipeline-step | Step Functions 단위 작업 | 1024MB | 300s |

### Amazon SQS
- AI 리포트 요청 급증 시 큐에 적재 → 순서대로 처리
- 서버 다운 없이 안정적 처리

| 큐 이름 | visibility_timeout | maxReceiveCount | DLQ |
|---------|--------------------|-----------------|-----|
| report-generation-queue | 180s | 5 | Yes |
| news-summary-queue | 120s | 5 | Yes |
| price-ingest-queue | 300s | 3 | Yes |
| external-api-retry-queue | 300s | 5 | Yes |

### KEDA / HPA
- SQS 큐 적재량 기준으로 Celery 워커 자동 스케일 아웃
- 부동산 이슈 급증 시 AI 리포트 요청 폭증 대응

---

## 인프라 / 운영

### Amazon EKS 1.35
- FastAPI 서버, Celery 워커 운영
- 노드 장애 시 자동 재시작, 무중단 배포
- AMI: AL2023_x86_64_STANDARD
- api 노드그룹 / worker 노드그룹 분리 운영

| 노드그룹 | dev | staging | prod |
|----------|-----|---------|------|
| api | t3.medium (1~2) | t3.medium (1~3) | t3.large (2~4) |
| worker | t3.medium (0~2) | t3.medium (0~3) | t3.large (1~5) |

### ALB Ingress Controller
- API 경로별 서버 그룹 라우팅 (/analysis/price, /reports 등)
- HTTPS 인증서 관리, WAF 연동
- IRSA: alb-controller-role

### IRSA (IAM Roles for Service Accounts)
- 코드에 AWS 접근 키 하드코딩 없이 자동 권한 부여
- FastAPI, Celery Worker, ALB Controller 각각 별도 역할

| Role | 대상 | 주요 권한 |
|------|------|-----------|
| fastapi-api-role | FastAPI ServiceAccount | sqs:SendMessage, secretsmanager:GetSecretValue |
| celery-worker-role | Celery Worker ServiceAccount | sqs:ReceiveMessage/Delete, bedrock:InvokeModel, s3:GetObject/PutObject |
| alb-controller-role | ALB Controller ServiceAccount | ALB·TargetGroup·Listener 관리 |

### Terraform
- 인프라 전체 코드화 (IaC)
- dev/staging/prod 환경 동일하게 복제 가능
- 변경 이력 Git으로 관리
- 버전: >= 1.7.0 / AWS Provider: >= 5.40.0

### GitHub Actions + ECR + Helm
- 코드 푸시 → 자동 테스트·빌드·배포
- ECR 레포: homelens-fastapi, homelens-celeryworker
- 이미지 태그: Git SHA 사용 (latest 태그 배포 금지)
- OIDC Provider: token.actions.githubusercontent.com

### AWS WAF + CloudFront
- WAF: 봇 트래픽·스크래핑 차단 (AWSManagedRulesCommonRuleSet)
- Rate Limit: 5분 내 동일 IP 2000 req 초과 시 차단
- CloudFront: 정적 리소스 로딩 속도 향상
- WAF 리소스는 us-east-1 강제 → 별도 provider 설정 필요
- TTL: min 0s / default 60s / max 300s

### Secrets Manager
- 카카오맵·네이버 뉴스·국토부 API 키 등 민감정보 보관
- 경로 규칙: `homelens/{env}/{서비스}`

| 경로 | 내용 |
|------|------|
| homelens/{env}/kakao/map-api | 카카오맵 REST API Key, JavaScript API Key |
| homelens/{env}/naver/news-api | 네이버 뉴스 API Client ID / Secret |
| homelens/{env}/molit/real-estate-api | 국토부 공공데이터 API Key |
| homelens/{env}/rds/postgres | username, password, host, port, dbname |
| homelens/{env}/redis/auth | Redis auth token (prod 필수 / dev·staging 선택) |
| homelens/{env}/bedrock/config | Bedrock 모델 ID, 리전 등 설정값 |

### Managed Prometheus + Grafana + X-Ray
- 성능 목표 실시간 모니터링 (자동완성 500ms, 가격 2초)
- 이상 징후 발생 시 즉시 알림
- X-Ray: AI 리포트 30초 초과·가격 API 2초 초과 시 병목 단계 파악
- Grafana 대시보드: `modules/monitoring/dashboards.tf`

### Route 53
- 도메인: homelens.ai
- Terraform 신규 생성 (aws_route53_zone)
- api.homelens.ai → ALB DNS / CloudFront

---

## VPC / 네트워킹

- 리전: eu-west-3 (파리) — 서비스 대상(서울)과 불일치는 팀 규정에 의해 감안, CloudFront + Redis 캐시로 보완
- VPC CIDR: 10.0.0.0/16
- AZ: eu-west-3a, eu-west-3c

| 서브넷 | AZ | CIDR | 용도 |
|--------|----|------|------|
| public_az_a | eu-west-3a | 10.0.10.0/24 | ALB, NAT GW |
| public_az_c | eu-west-3c | 10.0.110.0/24 | ALB, NAT GW |
| private_az_a | eu-west-3a | 10.0.20.0/24 | EKS 노드 |
| private_az_c | eu-west-3c | 10.0.120.0/24 | EKS 노드 |
| db_az_a | eu-west-3a | 10.0.30.0/24 | RDS, ElastiCache |
| db_az_c | eu-west-3c | 10.0.130.0/24 | RDS Multi-AZ |

### VPC Endpoint (dev/staging/prod 공통 필수)
S3 Gateway, ECR API, ECR DKR, SQS, Secrets Manager, STS, CloudWatch Logs, Bedrock Runtime

### VPC Endpoint (prod 추가)
EKS, EC2, ELB, CloudWatch Monitoring, X-Ray, Step Functions, EventBridge
