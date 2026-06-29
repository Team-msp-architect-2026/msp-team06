# HomeLens AI — AI 리포트 생성 파이프라인 상세 설명서

> 기준: dev 환경 / 최대 동시 태스크 100개 시나리오 / 2026-06-17

---

## 1. 전체 파이프라인 구조

```
[React Native App]
       │  POST /api/v1/reports
       ▼
[CloudFront + WAF]
       │
       ▼
[ALB (HTTPS 443)] ─── ACM 인증서 (*.ourhomelens.com)
       │
       ▼  HTTP 8080 내부
[FastAPI Pod — api 노드그룹]
       │  ① reportId 반환 (즉시, ~20ms)
       │  ② SQS SendMessage
       ▼
[SQS report-generation-queue]
       │  visibility_timeout=180s / maxReceiveCount=5 / DLQ=Yes
       ▼
[Celery Worker Pod — worker 노드그룹]
       │  ③ 메시지 수신
       │  ④ RDS 데이터 수집 (price + news + infra)
       │  ⑤ LangChain 프롬프트 구성
       │  ⑥ Bedrock (Claude Sonnet 4.6) 호출
       │  ⑦ RDS 결과 저장 (status=completed)
       ▼
[App Polling: GET /reports/{id}/status  (2~3초 간격)]
       │  completed 확인 후
       ▼
[GET /reports/{id}  → 4섹션 리포트 반환]
```

---

## 2. 노드 스펙 기반 수용 용량 계산

### 2-1. Worker 노드 스펙 (dev 기준: t3.medium)

| 항목 | 값 |
|------|----|
| 인스턴스 타입 | t3.medium |
| vCPU | 2 (2,000m) |
| 메모리 | 4 GiB (4,096 MiB) |
| 네트워크 ENI | 3개, ENI당 6 IP |
| EKS 최대 Pod 수 | 17개 (= 3 × (6-1) + 2) |

#### EKS 시스템 예약 리소스 (t3.medium)

| 항목 | 예약량 | 근거 |
|------|--------|------|
| CPU (kubelet + system) | 80m | EKS 기본 system-reserved |
| 메모리 (kubelet) | 640 MiB | 25% of first 4GiB = 1,024MiB 기준, EKS 실제 할당 ~640MiB |
| 메모리 (eviction threshold) | 100 MiB | kubelet 강제 eviction 기준 |
| **CPU 가용 (Allocatable)** | **1,920m** | 2,000 - 80 |
| **메모리 가용 (Allocatable)** | **3,356 MiB** | 4,096 - 640 - 100 |

#### Worker 노드 DaemonSet 소비량

worker 노드는 `dedicated=worker:NoSchedule` 테인트가 있어 시스템 DaemonSet만 스케줄됨:

| DaemonSet | CPU request | Memory request |
|-----------|-------------|----------------|
| aws-node (VPC CNI) | 25m | 64 MiB |
| kube-proxy | 10m | 64 MiB |
| amazon-cloudwatch-agent (Fluent Bit) | 50m | 100 MiB |
| **DaemonSet 합계** | **85m** | **228 MiB** |

#### Celery Pod 가용 리소스

| 항목 | 계산 | 결과 |
|------|------|------|
| 가용 CPU | 1,920m - 85m | **1,835m** |
| 가용 메모리 | 3,356 MiB - 228 MiB | **3,128 MiB** |

---

### 2-2. Pod 1개당 처리 가능한 태스크 수

#### Celery Pod 리소스 설정 ([infra/k8s/celery-deployment.yaml](../infra/k8s/celery-deployment.yaml))

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"   # 버스트 허용 (최대 1 코어)
    memory: "1Gi"  # 메모리 상한

command: ["celery", "-A", "app.worker", "worker",
          "--loglevel=info",
          "--concurrency=4",   # ← 핵심: Pod 1개당 동시 4 스레드
          "--pool=threads"]    # 스레드 풀 (prefork 대신)
```

> **Pod 1개 = 동시 태스크 4개**
>
> - `--concurrency=4` → 4개의 스레드가 독립적으로 Bedrock 호출
> - `--pool=threads` 선택 이유: Bedrock InvokeModel은 I/O 대기 시간이 대부분(~32s)
>   → 스레드 풀이 GIL 문제 없이 I/O 병렬화에 유리
> - prefork(프로세스 풀) 대비 메모리 효율 4배 이상

#### 스레드 동시성 상세

```
[Celery Worker Pod]
├── Thread 1: SQS 메시지 → Bedrock 호출 → DB 저장
├── Thread 2: SQS 메시지 → Bedrock 호출 → DB 저장
├── Thread 3: SQS 메시지 → Bedrock 호출 → DB 저장
└── Thread 4: SQS 메시지 → Bedrock 호출 → DB 저장

CPU: 4 스레드가 I/O 대기 중에는 250m 이하 소비
     Bedrock 응답 파싱·DB 저장 순간에만 CPU 사용
메모리: 512Mi request (각 스레드 ~128Mi 할당)
```

---

### 2-3. 노드 1개당 생성 가능한 Pod 수

#### 제약 조건별 최대 Pod 수

| 제약 조건 | 계산 | 최대 Pod 수 |
|-----------|------|-------------|
| CPU (request 기준) | 1,835m ÷ 250m | **7개** |
| 메모리 (request 기준) | 3,128 MiB ÷ 512 MiB | **6개** |
| EKS 네트워크 (ENI) | 17 - 3(DaemonSet) | 14개 |

> **실효 상한: 노드 1개당 Celery Pod 6개 (메모리 제약)**
>
> - CPU는 7개 허용이지만, 메모리가 먼저 소진 → **6개가 바인딩 제약**
> - 7번째 Pod 스케줄 시도 시: `0/1 nodes are schedulable: Insufficient memory`
>   → CA(Cluster Autoscaler)가 새 노드 추가 트리거

#### 노드별·전체 수용 용량 (dev 기준)

| 구분 | 공식 | 결과 |
|------|------|------|
| 노드당 Pod | 메모리 제약 | 6개 |
| 최대 노드 수 (CA) | max=4 | 4노드 |
| 이론적 최대 Pod | 4 × 6 | **24개** |
| 이론적 최대 태스크 | 24 × 4 | **96개** |
| KEDA maxReplica | 25 (≤ 24 제약) | → **실효 24개** |
| 실효 최대 동시 태스크 | 24 × 4 | **96개** |

> **NOTE:** CLAUDE.md의 "4노드 × 7Pod = 28 Pod" 계산은 CPU 기준 상한.
> 실 운용에서는 메모리가 먼저 소진되어 노드당 6개가 안전한 기준.
> 100태스크 목표 달성을 위해서는 아래 중 하나:
> - worker 노드를 t3.large로 업그레이드 (8GB → 노드당 8~9 Pod)
> - celery memory request를 384Mi로 축소 (노드당 7 Pod, 총 112태스크)

---

## 3. 스케일링 3계층 구조

```
Layer 1 — 스레드 (즉시)
  └─ Celery --concurrency=4
     Pod 1개 내에서 동시 4 태스크 처리

Layer 2 — Pod (30초~2분)
  └─ KEDA ScaledObject
     SQS 큐 깊이 ÷ 4 = 필요 Pod 수
     min=1, max=25

Layer 3 — 노드 (2~4분)
  └─ Cluster Autoscaler
     Pending Pod 감지 시 노드 자동 추가
     min=2, max=4
```

---

### 3-1. KEDA ScaledObject 설정 상세

#### 설정값 ([infra/homelens-terraform/modules/celery/main.tf](../infra/homelens-terraform/modules/celery/main.tf))

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-worker-scaledobject
  namespace: homelens
spec:
  scaleTargetRef:
    name: celery-worker
  minReplicaCount: 1        # 항상 1 Pod 대기 (디버깅·로그 확인 목적)
  maxReplicaCount: 25       # dev: 25 / prod: 10
  cooldownPeriod: 300       # 큐 depth=0 후 300초 유지 (Bedrock 30s 완충)
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: <report-generation-queue URL>
      queueLength: "4"      # Pod당 처리 용량과 일치 (--concurrency=4)
      awsRegion: eu-west-3
      identityOwner: operator
```

#### KEDA 스케일 공식

```
필요 Pod 수 = ceil(현재 SQS 메시지 수 ÷ queueLength)

예시:
  - 메시지  4개 → ceil(4÷4)  = 1 Pod  → 태스크 처리 100%
  - 메시지 20개 → ceil(20÷4) = 5 Pod  → 태스크 처리 100%
  - 메시지 100개→ ceil(100÷4)= 25 Pod → min(25, maxReplica=25) = 25 Pod
```

#### queueLength=4 설정 근거

| queueLength 값 | 효과 | 문제 |
|----------------|------|------|
| **4 (현재)** | Pod 처리 용량(4 스레드)과 정확히 일치 → 최적 프로비저닝 | — |
| 5 이상 | Pod 1개가 5개 처리 능력인 것처럼 계산 → 실제 4개뿐이라 처리 지연 | 언더프로비저닝 |
| 2 이하 | 필요 이상 Pod 생성 → 비용 낭비 | 오버프로비저닝 |

#### cooldownPeriod=300 설정 근거

```
Bedrock 호출 소요 최대 ~35s
큐 depth=0 감지 직후 Pod 종료 시 → 진행 중 스레드가 강제 종료
→ DB에 status=completed 저장 불가 → 리포트 유실

cooldown 300s:
큐 depth=0 ↓ [300초 대기] → Pod 안전 종료
이 시간 동안 진행 중인 4개 태스크 모두 완료 가능 (35s × 여유 8배)
```

#### KEDA 스케일아웃 타임라인 (100개 태스크 유입 시나리오)

```
T+0s    : 사용자 100개 POST /reports → SQS에 100개 메시지 적재
T+10s   : KEDA 폴링 주기 도래 → 큐 depth=100 감지
           → 필요 Pod=25, 현재 Pod=1 → 24개 추가 결정
T+10s   : Deployment replicas 1→25 로 업데이트
T+10~40s: ECR에서 이미지 pull (캐시 있으면 ~10s, cold start ~40s)
T+40~60s: Celery 워커 초기화, SQS 연결 확립
T+60s   : 25 Pod 가동 → 100 태스크 처리 시작 (각 Pod 4 태스크)
           → 단, 노드 6대 필요 / 현재 노드 2대 → Pending 발생 → CA 트리거
```

---

### 3-2. HPA 설정 상세 (FastAPI)

#### 설정값 ([infra/k8s/fastapi-hpa.yaml](../infra/k8s/fastapi-hpa.yaml))

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: homelens
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi
  minReplicas: 2    # 최소 2개 (HA 보장)
  maxReplicas: 6    # api 노드그룹 내 최대

  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70    # Pod 평균 CPU 70% 초과 시 스케일아웃
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80    # Pod 평균 메모리 80% 초과 시 스케일아웃

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60    # 60s 안정화 후 스케일아웃 (flapping 방지)
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60               # 60초마다 최대 2개씩 증가
    scaleDown:
      stabilizationWindowSeconds: 300   # 5분 안정화 후 스케일다운
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120              # 2분마다 최대 1개씩 감소
```

#### FastAPI Pod 스펙 대비 스케일 조건

| FastAPI Pod 스펙 | request cpu=250m / memory=256Mi |
|---|---|
| CPU 70% 초과 기준 | 250m × 70% = 175m 이상 지속 |
| 메모리 80% 초과 기준 | 256Mi × 80% = 205Mi 이상 지속 |
| 측정 주체 | metrics-server (EKS 관리형 addon) |
| 데이터 소스 | kubelet → metrics.k8s.io API |

> HPA와 KEDA는 **완전히 독립 동작**
> - HPA: FastAPI(api 노드) CPU/메모리 기반 → 검색·가격 API 트래픽 대응
> - KEDA: Celery(worker 노드) SQS 큐 깊이 기반 → AI 리포트 태스크 대응

---

### 3-3. Cluster Autoscaler 설정 상세

#### 설정값 ([infra/homelens-terraform/modules/eks/cluster_autoscaler.tf](../infra/homelens-terraform/modules/eks/cluster_autoscaler.tf))

```yaml
# Helm values (cluster-autoscaler chart 9.43.0)
autoDiscovery.clusterName: homelens-dev-eks
awsRegion: eu-west-3

extraArgs:
  scale-down-delay-after-add: "5m"      # 노드 추가 후 최소 5분 유지
  scale-down-unneeded-time: "5m"        # 유휴 노드 5분 후 제거
```

#### ASG 태그 (CA 자동 탐색 필수)

```hcl
# modules/eks/main.tf — worker 노드그룹
tags = {
  "k8s.io/cluster-autoscaler/enabled"              = "true"
  "k8s.io/cluster-autoscaler/homelens-dev-eks"     = "owned"
}
```

#### Worker 노드그룹 스케일링 범위 (dev)

| 항목 | 값 |
|------|----|
| min_size | 2 (상시 대기 — 콜드스타트 방지) |
| desired_size | 2 (CA가 동적 제어, `ignore_changes` 설정) |
| max_size | 4 |
| 인스턴스 타입 | t3.medium |

```hcl
lifecycle {
  ignore_changes = [scaling_config[0].desired_size]
  # 없으면 CA가 조정한 desired_size를 terraform apply 시마다 원복
}
```

#### CA 동작 흐름 (100 태스크 유입 시)

```
[1단계 — Pending Pod 감지]
  KEDA가 Deployment replicas=25로 설정
  현재 2노드 수용 가능 Pod: 2 × 6 = 12개
  → 13번째 Pod부터 Pending 상태

[2단계 — CA 스케일아웃 판단]
  CA 감지 주기: 10s
  Pending Pod 감지 → 추가 필요 노드 수 계산:
    필요 총 Pod: 25
    노드당 Pod: 6
    필요 노드: ceil(25/6) = 5 → min(5, max=4) = 4노드
  ASG desired_size: 2 → 4로 조정 (API 호출)

[3단계 — 노드 프로비저닝]
  EC2 인스턴스 기동: 60~90s
  EKS 노드 등록 (aws-node, kube-proxy 시작): 30~60s
  총 노드 추가 소요: 2~4분

[4단계 — Pod 스케줄링 완료]
  신규 노드 Ready → Pending Pod 스케줄링
  최종 상태: 4노드 × 6Pod = 24 Pod 가동
```

#### CA 스케일다운 조건

```
조건 1: SQS 큐 depth=0 → KEDA cooldown 300s 후 Pod 축소
조건 2: 노드에 스케줄된 Pod 없음 (DaemonSet 제외) + 5분 경과
조건 3: 남은 Pod가 다른 노드로 이동 가능한 경우

scale-down-unneeded-time=5m: 태스크 처리 중 노드 제거 방지
scale-down-delay-after-add=5m: 스케일아웃 후 즉시 다운 방지 (flapping 억제)

최소 유지: min=2 → 2노드 이하로 절대 축소 안 함
```

---

## 4. EKS 내 리소스별 소요시간 및 전체 파이프라인 타임라인

### 4-1. 단계별 소요시간 (태스크 1개 기준)

| # | 단계 | 담당 리소스 | 소요시간 | 비고 |
|---|------|-------------|---------|------|
| ① | 앱 → FastAPI HTTP 수신 | ALB + FastAPI Pod | ~10ms | |
| ② | Pydantic 입력 검증 | FastAPI (CPU) | ~5ms | regionId 형식, 필수필드 |
| ③ | Redis 캐시 중복 확인 | ElastiCache Redis | ~2ms | 동일 조건 리포트 조회 |
| ④ | DB 중복 확인 (RDS) | RDS PostgreSQL | ~10ms | reports 테이블 SELECT |
| ⑤ | SQS SendMessage | SQS (VPC Endpoint) | ~20ms | reportId + sent_at 포함 |
| ⑥ | FastAPI 응답 반환 | FastAPI Pod | ~5ms | reportId + status=pending |
| **소계** | **FastAPI 처리** | | **~52ms** | |
| ⑦ | SQS 큐 대기 | SQS | 0~수초 | 큐 깊이에 따라 가변 |
| ⑧ | Celery 메시지 수신 | Celery Worker Thread | ~100ms | Long-polling 20s 주기 |
| ⑨ | 가격 데이터 조회 | RDS (price_snapshots) | ~50ms | 최근 3개월 집계 쿼리 |
| ⑩ | 뉴스/이슈 데이터 조회 | RDS (news + issues) | ~30ms | regionId 기준 필터 |
| ⑪ | 인프라 정보 조회 | RDS (PostGIS 공간쿼리) | ~80ms | 반경 1km 내 지하철/학교 |
| ⑫ | LangChain 프롬프트 구성 | Celery Worker (CPU) | ~200ms | 4섹션 템플릿 조립 |
| ⑬ | **Bedrock InvokeModel** | **Amazon Bedrock (Claude Sonnet 4.6)** | **~32,000ms** | **지배적 단계 (실측 p50)** |
| ⑭ | 응답 파싱 (4섹션) | Celery Worker (CPU) | ~100ms | JSON 파싱 + 검증 |
| ⑮ | DB 저장 (reports) | RDS PostgreSQL | ~80ms | INSERT + status=completed |
| ⑯ | 리포트 백업 | S3 (VPC Endpoint) | ~200ms | 비동기, 응답과 무관 |
| **소계** | **Celery Worker 처리** | | **~32,840ms** | |
| ⑰ | 앱 폴링 GET status | FastAPI + RDS | ~15ms × 횟수 | 2~3초 간격, 평균 11회 |
| ⑱ | 앱 GET 결과 조회 | FastAPI + RDS | ~50ms | 전체 리포트 조회 |

### 4-2. 예상 전체 파이프라인 시간

```
[시작] 사용자 POST /reports
       │
       ▼ ~52ms
[FastAPI] SQS 적재 + reportId 반환
       │
       ▼ (큐 대기: 0ms ~ 수s, 부하에 따라)
       │
       ▼ ~32,840ms  ←── 이 구간이 전체의 98%
[Celery Worker] 데이터 수집 → Bedrock → DB 저장
       │
       ▼ 2~3초 간격 폴링
[App] completed 확인 → 결과 수신
       │
       ▼
[완료]

────────────────────────────────────────
정상 경로 (큐 비어있음):
  P50: ~32~35s
  P90: ~35~38s (목표치: 45s 이내)

트래픽 폭증 (100개 동시):
  Pod 대기 없으면 : P90 ~38s
  Pod/노드 콜드스타트: P90 ~5분
────────────────────────────────────────
```

> **Bedrock(~32s)가 전체의 98%를 차지**
> 병목 최적화 방향:
> - max_tokens 축소 (현재 4,096) → 리포트 품질 트레이드오프
> - Bedrock Provisioned Throughput 도입 → 응답 시간 안정화 (추가 비용)
> - 캐시 히트율 향상: 동일 regionId 당일 리포트 재사용 (현재 409 REPORT_ALREADY_EXISTS 반환)

---

## 5. IRSA (IAM Roles for Service Accounts) 상세

### 5-1. IRSA 개념 및 필요성

```
[기존 방식 — 보안 문제]
EC2 Node IAM Role → 노드 위의 모든 Pod가 동일 권한
→ FastAPI Pod도 Bedrock 호출 가능, 권한 최소화 불가

[IRSA 방식 — 최소 권한]
Pod의 ServiceAccount ←→ IAM Role 1:1 매핑
→ FastAPI Pod: SQS SendMessage만 허용
→ Celery Pod: Bedrock + S3 + SQS ReceiveMessage만 허용
→ 코드에 AWS Access Key 하드코딩 없음
```

### 5-2. IRSA 동작 원리

```
[IRSA 인증 흐름]

①  Pod 시작 시 kubelet이 OIDC 토큰 생성
    → /var/run/secrets/eks.amazonaws.com/serviceaccount/token 마운트

②  Celery Worker가 boto3.client("bedrock-runtime") 호출 시
    → boto3가 토큰 파일을 읽어 STS AssumeRoleWithWebIdentity 요청

③  STS가 OIDC Provider에 토큰 검증 요청
    → EKS OIDC Issuer URL로 공개 키 확인

④  검증 성공 → STS가 임시 자격증명 발급 (15분 TTL, 자동 갱신)

⑤  boto3가 임시 자격증명으로 Bedrock 호출
    → IAM Role 정책 기준으로 bedrock:InvokeModel 허용
```

### 5-3. IRSA 역할별 권한 매핑

| 역할 이름 | ServiceAccount | Namespace | 허용 권한 |
|-----------|---------------|-----------|-----------|
| `homelens-dev-fastapi-api-role` | `fastapi` | `homelens` | `sqs:SendMessage`, `sqs:GetQueueAttributes`, `sqs:GetQueueUrl`, `secretsmanager:GetSecretValue` |
| `homelens-dev-celery-worker-role` | `celery-worker` | `homelens` | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:ChangeMessageVisibility`, `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `s3:GetObject`, `s3:PutObject`, `secretsmanager:GetSecretValue` |
| `homelens-dev-alb-controller-role` | `aws-load-balancer-controller` | `kube-system` | ALB/TargetGroup/Listener 관리 전체 |
| `homelens-dev-keda-operator-role` | `keda-operator` | `keda` | `sqs:GetQueueAttributes`, `sqs:GetQueueUrl`, `sqs:ReceiveMessage` (큐 깊이 읽기) |
| `homelens-dev-cluster-autoscaler-role` | `cluster-autoscaler` | `kube-system` | `autoscaling:Describe*`, `autoscaling:SetDesiredCapacity`, `autoscaling:TerminateInstanceInAutoScalingGroup` |

### 5-4. IRSA Terraform 구현 구조

```hcl
# 1단계: EKS OIDC Provider 생성 (modules/eks/main.tf)
resource "aws_iam_openid_connect_provider" "eks" {
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
}

# 2단계: IAM Role에 신뢰 정책 설정 (modules/eks/irsa.tf)
# 조건: namespace=homelens, serviceaccount=celery-worker 인 Pod만 Assume 가능
data "aws_iam_policy_document" "celery_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:homelens:celery-worker"]  # 핵심 제약
    }
  }
}

# 3단계: K8s ServiceAccount에 Role ARN 어노테이션 (modules/celery/main.tf)
resource "kubernetes_service_account" "celery_worker" {
  metadata {
    name      = "celery-worker"
    namespace = "homelens"
    annotations = {
      "eks.amazonaws.com/role-arn" = var.celery_worker_role_arn  # ← IRSA 연결
    }
  }
}
```

### 5-5. IRSA 미설정 시 발생하는 에러

```
# celery-worker ServiceAccount에 어노테이션 없을 때
AccessDeniedException: User: arn:aws:sts::611058323802:assumed-role/
  homelens-dev-eks-node-role/i-0abc... is not authorized to perform:
  bedrock:InvokeModel on resource: *

# 원인: Pod가 IRSA 대신 노드 IAM 역할 사용 → Bedrock 권한 없음
# 해결: ServiceAccount 어노테이션 추가 후 Pod 재시작
```

---

## 6. Ingress 설정 상세

### 6-1. 전체 트래픽 흐름

```
[사용자 모바일 앱]
       │ HTTPS (ourhomelens.com)
       ▼
[Route 53]  →  CNAME → CloudFront 도메인
       │
       ▼
[CloudFront + WAF (us-east-1)]
  - WAF Rule: AWSManagedRulesCommonRuleSet (봇/스크래핑 차단)
  - Rate Limit: 5분 내 동일 IP 2,000 req 초과 시 차단
  - Origin: origin.ourhomelens.com → ALB (HTTPS)
       │
       ▼ HTTPS (origin.ourhomelens.com)
[ALB — eu-west-3]
  - ACM 인증서: *.ourhomelens.com (eu-west-3)
  - Listener: HTTP 80 → 301 HTTPS 443
  - Target Type: IP (Pod IP 직접 연결)
       │
       ▼ HTTP 8080 (내부)
[EKS FastAPI Pod]
```

### 6-2. Ingress 리소스 설정

#### 설정값 ([infra/k8s/ingress.yaml](../infra/k8s/ingress.yaml))

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: homelens-ingress
  namespace: homelens
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing       # 공개 ALB
    alb.ingress.kubernetes.io/target-type: ip               # Pod IP 직접 연결
    alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:eu-west-3:..."
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"           # HTTP → HTTPS 강제
spec:
  rules:
  - host: api-dev.ourhomelens.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi
            port:
              number: 80     # fastapi Service (ClusterIP :80 → Pod :8080)
```

#### target-type: ip 선택 이유

```
[instance 모드 (기본)]
  ALB → NodePort → kube-proxy → Pod
  - kube-proxy가 SNAT으로 클라이언트 IP 손실
  - 노드를 거치는 홉 추가

[ip 모드 (현재 설정)]
  ALB → Pod IP 직접
  - 실제 클라이언트 IP 보존 (X-Forwarded-For)
  - 홉 감소 → 지연시간 단축
  - ALB가 Target Group에 Pod IP를 직접 등록
  - 요건: VPC CNI (aws-node) 필수 (EKS 기본 설치)
```

#### ALB Ingress Controller IRSA

```
[동작 원리]
ALB Ingress Controller Pod
  └─ ServiceAccount: aws-load-balancer-controller (kube-system)
  └─ IRSA 어노테이션 → homelens-dev-alb-controller-role
  └─ 권한: elasticloadbalancing:*, ec2:Describe*, acm:*, wafv2:*

[Ingress 리소스 apply 시 자동 처리]
K8s Ingress 리소스 생성
→ Ingress Controller가 API 감지
→ ALB 생성 (aws_alb)
→ Listener 생성 (80/443)
→ Target Group 생성 (Pod IP 기반)
→ WAF ACL 연동
→ Ingress .status.loadBalancer.ingress[0].hostname 업데이트
```

### 6-3. SSL/TLS 처리 구조

```
[외부 구간] CloudFront ↔ 사용자: TLS 1.3 (us-east-1 인증서)
[중간 구간] ALB ↔ CloudFront: TLS (*.ourhomelens.com, eu-west-3 인증서)
[내부 구간] ALB ↔ FastAPI Pod: HTTP (VPC 내부 — 암호화 불필요)

origin_protocol_policy = "https-only"
→ CloudFront가 ALB에 항상 HTTPS로 연결
→ ALB의 ACM 인증서 도메인(*.ourhomelens.com)과
  CloudFront origin 도메인(origin.ourhomelens.com) 일치 필수
```

---

## 7. 100개 동시 태스크 전체 시나리오 요약

```
[T+0s]    사용자 100명 동시에 POST /reports
           ↓ FastAPI가 각각 ~52ms 내 SQS 적재 + reportId 반환
           SQS report-generation-queue: 100개 메시지

[T+10s]   KEDA 폴링 → 큐 depth=100 감지
           → 필요 Pod=ceil(100÷4)=25, 현재=1
           → Deployment replicas 1→25 조정

[T+10~50s] 신규 Pod 24개 기동 (ECR 이미지 pull)
           2노드 수용: 12 Pod → 13번째부터 Pending
           → CA 감지 → ASG desired 2→4 조정 (API)

[T+50s~3m] EC2 t3.medium 2대 추가 기동
           노드 등록 완료 → Pending Pod 스케줄링
           최종: 4노드 × 6Pod = 24 Pod 가동
           → 96개 태스크 동시 처리 시작 (4개는 큐 대기)

[T+3m~33m] 각 Pod의 4 스레드가 독립적으로:
            RDS 조회(~160ms) → Bedrock(~32s) → DB 저장(~80ms)
           약 30~33초 간격으로 태스크 완료

[T+33m]   마지막 태스크 완료 예상
           사용자 앱: 폴링으로 completed 수신

[T+33m+5m] KEDA cooldown 만료 → Pod 25→1로 축소
[T+38m+5m] CA scale-down-unneeded-time 만료 → 노드 4→2로 축소

────────────────────────────────────────────────────────
핵심 병목:
  1위. Bedrock InvokeModel: ~32s (98%)
  2위. CA 노드 추가: 2~4분 (콜드스타트 시)
  3위. Pod 이미지 pull: ~40s (cold start)

첫 100개 태스크 완료까지:
  Pod 이미 준비된 경우: ~32~38s
  Pod+노드 콜드스타트: ~3~5분 (CA 포함)
────────────────────────────────────────────────────────
```

---

## 8. 설정값 요약표

| 컴포넌트 | 항목 | dev 값 | prod 값 |
|----------|------|--------|---------|
| Worker 노드 | 인스턴스 | t3.medium | t3.large |
| Worker 노드 | min/max | 2/4 | 1/5 |
| Celery Pod | cpu request/limit | 250m / 1,000m | 250m / 1,000m |
| Celery Pod | memory request/limit | 512Mi / 1Gi | 512Mi / 1Gi |
| Celery Pod | concurrency | 4 스레드 | 4 스레드 |
| KEDA | minReplicaCount | 1 | 1 |
| KEDA | maxReplicaCount | **25** | 10 |
| KEDA | queueLength | 4 | 4 |
| KEDA | cooldownPeriod | 300s | 300s |
| HPA (FastAPI) | min/max replicas | 2/6 | 2/6 |
| HPA (FastAPI) | CPU 임계 | 70% | 70% |
| HPA (FastAPI) | Memory 임계 | 80% | 80% |
| CA | scale-down-unneeded-time | 5m | 5m |
| CA | scale-down-delay-after-add | 5m | 5m |
| SQS | visibility_timeout | 180s | 180s |
| SQS | maxReceiveCount (DLQ) | 5 | 5 |
| Bedrock | model_id | eu.anthropic.claude-sonnet-4-6 | eu.anthropic.claude-sonnet-4-6 |
| Bedrock | max_tokens | 4,096 | 4,096 |

---

*HomeLens AI Internal Architecture Document | 2026-06-17*
