## DevOps 작업 원칙 (Terraform)

### 역할
이 프로젝트의 Terraform 작업 시 DevOps/IaC 담당자로 동작한다.
애플리케이션 개발보다 인프라 운영 코드 작성이 우선순위다.

### 원칙
1. 코드는 모듈화 구조로 작성한다
2. dev 환경부터 만들고 staging/prod는 나중에 확장
3. terraform apply는 직접 실행하지 않고 명령어만 안내
4. 민감정보는 코드에 하드코딩하지 않고 Secrets Manager 또는 변수로 분리
5. 각 단계마다 생성/수정 파일 목록, 코드, 검증 명령어 함께 제시
6. 한 번에 전체 인프라를 만들지 않고 모듈 단위로 나눠서 진행
7. 프로젝트 경로 ~/msp-team06

### Terraform 작업 순서 (Phase)
- Phase 0: Bootstrap (S3 버킷 + DynamoDB) — 완료 (팀원 apply 확인됨)
- Phase 1: Shared (ECR + IAM 기본 역할) — 완료
- Phase 2: Networking (VPC, 서브넷, NAT, SG) — 완료
- Phase 3: RDS (PostgreSQL + PostGIS) — 완료 (팀원 코드 종합)
- Phase 4: ElastiCache (Redis) — 완료 (팀원 코드 종합)
- Phase 5: S3 (버킷 + 수명주기) — 완료 (팀원 코드 종합)
- Phase 6: Secrets (Secrets Manager 경로) — 완료 (팀원 코드 종합)
- Phase 7: EKS (클러스터 + 노드그룹 + IRSA) — 완료
- Phase 8: ALB (ALB + Ingress Controller + KEDA) — 완료
- Phase 9: SQS + Lambda + Step Functions + EventBridge — 완료 (팀원 코드 종합)
- Phase 10: Bedrock + Celery — 완료
- Phase 11: WAF + CDN + DNS — 완료
- Phase 12: Monitoring (Prometheus + Grafana + X-Ray) — 완료 (팀원 코드 종합)
- Phase 13: Cluster Autoscaler — **코드 완료 (2026-06-12), terraform apply 후 활성화**
(현재 진행 단계를 매 작업 시작 시 명시)

---

## Terraform 프로젝트 구조

### 디렉토리 레이아웃

```
homelens-terraform/
├── bootstrap/                  # S3 tfstate 버킷 + DynamoDB 락 테이블 (최초 1회)
├── shared/                     # ECR + GitHub OIDC + IAM deploy role (전 환경 공용)
│   ├── terraform.tfvars        # github_org/github_repo 현재 빈 값 — GitHub 계정 정상화 후 입력
│   ├── terraform.tfvars.example
│   └── versions.tf             # aws >= 5.40.0, tls >= 4.0.0
├── environments/
│   ├── versions.tf             # 루트 참조용 (실제 사용은 각 환경 폴더에 복사본)
│   ├── dev/
│   │   ├── versions.tf                   # aws, kubernetes, helm, tls provider 선언
│   │   ├── backend.tf                    # S3 원격 상태 (homelens-tfstate-dev)
│   │   ├── main.tf                       # 전체 모듈 호출
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   ├── outputs.tf
│   │   ├── destroy.sh                    # 매일 저녁 인프라 제거 스크립트
│   │   ├── secrets.auto.tfvars.example   # API 키 템플릿 (커밋됨)
│   │   └── secrets.auto.tfvars           # 실제 API 키 (gitignore, 로컬 전용)
│   ├── staging/                # dev와 동일 구조
│   └── prod/                   # dev와 동일 구조
└── modules/
    ├── networking/             # 우리 담당 — VPC, 서브넷, NAT, SG, VPC Endpoint
    ├── eks/                    # 우리 담당 — 클러스터, 노드그룹, OIDC, IRSA 4개
    ├── alb/                    # 우리 담당 — ALB + ALB Ingress Controller (Helm)
    ├── waf-cdn/                # 우리 담당 — WAF(us-east-1) + CloudFront
    ├── dns/                    # 우리 담당 — Route53 레코드 (기존 hosted zone 참조)
    ├── bedrock/                # 우리 담당 — 호출 로깅 + 시크릿 버전
    ├── celery/                 # 우리 담당 — K8s Deployment + KEDA (Helm) + ScaledObject
    ├── rds/                    # 팀원 담당 — PostgreSQL 17, manage_master_user_password
    ├── elasticache/            # 팀원 담당 — Redis 7.1, prod는 auth_token 필요
    ├── s3/                     # 팀원 담당 — raw-data 버킷 + report-backup 버킷
    ├── sqs/                    # 팀원 담당 — 큐 4개 + DLQ 4개
    ├── lambda/                 # 팀원 담당 — 파이프라인 함수 5개, VPC 밖 배치
    ├── step-functions/         # 팀원 담당 — news-pipeline + price-pipeline (각각 별도)
    ├── eventbridge/            # 팀원 담당 — 뉴스(매일 KST 02:00) + 가격(월 1회) 스케줄
    ├── secrets/                # 우리 담당 — Secrets Manager 7개 생성 + 자동 값 주입
    └── monitoring/             # 팀원 담당 — Prometheus, X-Ray, CloudWatch 알람
```

### 모듈 간 변수 명명 규칙

| 구분 | 환경 변수명 | 비고 |
|------|------------|------|
| 우리 모듈 (networking, eks, alb 등) | `environment` | |
| 팀원 모듈 (rds, elasticache, sqs 등) | `env` | main.tf에서 `env = var.environment`로 전달 |

### 핵심 모듈 간 의존 관계 (output → input)

```
sqs.report_queue_url              → celery.sqs_queue_url
sqs.report_queue_arn              → lambda.report_queue_arn
sqs.news_summary_queue_arn        → lambda.news_summary_queue_arn
sqs.price_ingest_queue_arn        → lambda.price_ingest_queue_arn
s3.raw_data_bucket_name           → lambda.raw_data_bucket_name
s3.raw_data_bucket_arn            → lambda.raw_data_bucket_arn
lambda.*_arn (4개)                → step_functions 입력
step_functions.news_pipeline_arn  → eventbridge.news_pipeline_arn
step_functions.price_pipeline_arn → eventbridge.price_pipeline_arn
eks.alb_controller_role_arn       → alb.alb_controller_role_arn
eks.keda_operator_role_arn        → celery.keda_operator_role_arn
alb.alb_arn_suffix                → monitoring.alb_arn_suffix
rds.rds_endpoint                  → secrets.rds_endpoint
rds.rds_secret_arn                → secrets.rds_secret_arn
elasticache.redis_primary_endpoint → secrets.redis_endpoint
secrets (depends_on)              → bedrock
```

---

## 도메인 및 인증서 현황

| 항목 | 값 | 상태 |
|------|-----|------|
| 도메인 | `ourhomelens.com` | Route53 등록 완료 |
| ALB 인증서 (eu-west-3) | `arn:aws:acm:eu-west-3:611058323802:certificate/cbf76714-d305-4f44-a7ee-c0d347ccd808` | 발급 완료 (*.ourhomelens.com 와일드카드) |
| CloudFront 인증서 (us-east-1) | `arn:aws:acm:us-east-1:611058323802:certificate/6be544e8-d753-4c2b-aec5-53a041884db9` | 발급 완료 |
| AWS 계정 ID | `611058323802` | |

### 트래픽 흐름

```
사용자
  ↓ HTTPS (ourhomelens.com / *.ourhomelens.com)
CloudFront + WAF  ← us-east-1 인증서
  ↓ HTTPS (origin.ourhomelens.com → ALB)
ALB  ← eu-west-3 인증서 (*.ourhomelens.com)
  ↓ HTTP 내부
EKS FastAPI (homelens 네임스페이스)
```

### 환경별 Route53 서브도메인 패턴

| 용도 | prod | staging | dev |
|------|------|---------|-----|
| 사용자 접근 (CloudFront) | `ourhomelens.com` | `staging.ourhomelens.com` | `dev.ourhomelens.com` |
| API 직접 (ALB) | `api.ourhomelens.com` | `api-staging.ourhomelens.com` | `api-dev.ourhomelens.com` |
| CloudFront → ALB origin | `origin.ourhomelens.com` | `origin-staging.ourhomelens.com` | `origin-dev.ourhomelens.com` |

---

## Terraform apply 전 필수 준비 사항

### AWS 외부 준비 현황

| 항목 | 상태 |
|------|------|
| `ourhomelens.com` 도메인 등록 (Route53) | 완료 |
| ACM 인증서 eu-west-3 (`*.ourhomelens.com`) | 완료 |
| ACM 인증서 us-east-1 (`*.ourhomelens.com`) | 완료 |
| Bedrock 모델 액세스 활성화 (`eu.anthropic.claude-sonnet-4-6`, eu-west-3) | 완료 — Model Access 페이지 폐지됨, 첫 호출 시 자동 활성화 |
| Bootstrap apply | 완료 (팀원 tfstate 확인됨) |
| GitHub 조직 초대 | 미완료 — 완료 후 `shared/terraform.tfvars`에 입력 |

### [임시] apply 순서 안내 시 함께 알릴 것
apply 순서를 안내할 때 아래 S3 권한 정책도 함께 적용하라고 반드시 언급할 것.
해당 팀원의 IAM 사용자 또는 역할에 인라인 정책으로 추가:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:HeadObject"],
      "Resource": [
        "arn:aws:s3:::homelens-dev-raw-data/*",
        "arn:aws:s3:::homelens-dev-report-backup/*"
      ]
    }
  ]
}
```
AWS 콘솔 → IAM → 사용자/역할 → 권한 → 인라인 정책 추가

### 매일 destroy / apply 워크플로우

```bash
# ── 매일 저녁 ──────────────────────────────
cd homelens-terraform/environments/dev
bash destroy.sh          # Helm 정리 후 terraform destroy 자동 실행
                         # recovery_window_in_days=0 → 시크릿 즉시 삭제됨
                         # ※ RDS / S3 / networking(VPC·서브넷·SG) 는 제거하지 않음
                         #   NAT GW + EIP는 비용 절감을 위해 제거

# ── 매일 아침 ──────────────────────────────
cd homelens-terraform/environments/dev
terraform init           # .terraform 폴더 없을 때만 (destroy해도 폴더 유지됨) + 새로운 리소스 추가 시

# apply 전체 순서 (의존성 순) — 3단계 방식 필수

Helm provider가 EKS cluster endpoint를 참조하므로 EKS 생성 전 Helm 리소스를 apply하면 provider 초기화 실패.
secrets 모듈은 rds, elasticache output을 참조하므로 반드시 같은 단계에서 함께 apply할 것.

# 1단계: EKS까지 (Helm 없음) — 15~20분 소요
# networking: NAT GW + EIP + private route만 재생성 (VPC/서브넷/SG는 No changes)
# rds, s3: No changes (보존됨) — 포함하더라도 즉시 통과
terraform apply \
  -target=module.networking \
  -target=module.rds \
  -target=module.elasticache \
  -target=module.sqs \
  -target=module.s3 \
  -target=module.eks \
  -target=module.secrets

# 2단계: Helm 사용 모듈 (EKS endpoint 확보 후)
# argocd는 celery 이후 — celery가 homelens 네임스페이스와 ServiceAccount를 먼저 생성해야 함
terraform apply \
  -target=module.alb \
  -target=module.celery \
  -target=module.argocd

# 3단계: 나머지
terraform apply \
  -target=module.lambda \
  -target=module.step_functions \
  -target=module.eventbridge \
  -target=module.waf_cdn \
  -target=module.dns \
  -target=module.monitoring \
  -target=module.bedrock

terraform plan  # No changes 확인

## Terraform apply 3단계 완료 후 → ArgoCD가 k8s 리소스를 자동 sync
# 1. kubeconfig 업데이트 (Route53 업데이트 및 aws-auth 등록에 필요)
aws eks update-kubeconfig --name homelens-dev-eks --region eu-west-3 # <-이것만 하면 됨
# ※ infra/k8s/ 내 모든 파일(configmap, serviceaccount, deployment, service, ingress)은
#   ArgoCD가 자동 적용하므로 kubectl apply 불필요
cd ~/msp-team06/infra
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/fastapi-serviceaccount.yaml
kubectl apply -f k8s/fastapi-deployment.yaml
kubectl apply -f k8s/fastapi-hpa.yaml
kubectl apply -f k8s/fastapi-service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/celery-deployment.yaml

# 3. Alertmanager Slack 설정 재적용 (destroy 시 초기화됨)
kubectl create secret generic homelens-slack-webhook \
  --from-literal=url='<webhook url>' \
  -n monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/alertmanager-config.yaml

# 4. EKS control plane 알림 silence 재적용 (Alertmanager 재시작 시 초기화됨)
ENDS=$(python3 -c "from datetime import datetime,timedelta; print((datetime.utcnow()+timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ'))")
NOW=$(python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))")
for ALERT in "KubeSchedulerDown" "KubeControllerManagerDown"; do
  kubectl exec -n monitoring alertmanager-kube-prometheus-stack-alertmanager-0 -c alertmanager -- \
    wget -qO- --post-data="{\"matchers\":[{\"name\":\"alertname\",\"value\":\"$ALERT\",\"isRegex\":false}],\"startsAt\":\"$NOW\",\"endsAt\":\"$ENDS\",\"createdBy\":\"homelens-admin\",\"comment\":\"EKS managed control plane\"}" \
    --header='Content-Type: application/json' \
    'http://localhost:9093/api/v2/silences' > /dev/null
done

# 5. ArgoCD sync 확인 (~3분 이내 자동 완료)
kubectl get pods -n argocd          # argocd-server, argocd-repo-server 등 Running 확인
kubectl get applicationset -n argocd  # homelens ApplicationSet 확인
kubectl get application -n argocd     # homelens-dev Synced/Healthy 확인
kubectl get pods -n homelens          # fastapi, celery-worker 파드 확인

## Route53 api-dev 레코드 업데이트 (ingress Address 나올 때까지 1~2분 대기)
kubectl get ingress homelens-ingress -n homelens
# 여기 나오는 값을 ADDRESS값에 입력
INGRESS_DNS="<ADDRESS 값>"

INGRESS_ZONE_ID=$(aws elbv2 describe-load-balancers --region eu-west-3 \
  --query "LoadBalancers[?DNSName=='${INGRESS_DNS}'].CanonicalHostedZoneId" --output text)

HOSTED_ZONE_ID=$(aws route53 list-hosted-zones \
  --query "HostedZones[?Name=='ourhomelens.com.'].Id" --output text | cut -d/ -f3)

aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch "{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"api-dev.ourhomelens.com\",\"Type\":\"A\",\"AliasTarget\":{\"HostedZoneId\":\"${INGRESS_ZONE_ID}\",\"DNSName\":\"${INGRESS_DNS}\",\"EvaluateTargetHealth\":true}}}]}"

# 변수값 확인
echo "INGRESS_DNS: $INGRESS_DNS"
echo "INGRESS_ZONE_ID: $INGRESS_ZONE_ID"
echo "HOSTED_ZONE_ID: $HOSTED_ZONE_ID"

## EKS aws-auth — 팀원 Configmap 권한 복원 (EKS destroy시 → aws-auth ConfigMap도 함께 초기화됨 - 매번 필수)
kubectl get configmap aws-auth -n kube-system -o yaml > ~/aws-auth.yaml

nano ~/aws-auth.yaml

# mapUsers 추가내용 :
  mapUsers: |
    - userarn: arn:aws:iam::611058323802:user/student08
      username: student08
      groups:
        - system:masters
    - userarn: arn:aws:iam::611058323802:user/student12
      username: student12
      groups:
        - system:masters

# mapUsers 섹션 추가 후 저장
kubectl apply -f ~/aws-auth.yaml

- 팀원 신규 추가 시: `aws sts get-caller-identity`로 정확한 ARN 확인 후 등록
- "the server has asked for the client to provide credentials" 오류 → aws-auth 미등록 또는 ARN 불일치
- "Conflict: the object has been modified" 오류 → `kubectl get configmap aws-auth -n kube-system -o yaml > ~/aws-auth.yaml` 재실행 후 편집

# ✅ Cluster Autoscaler (CA) 구현 완료 (2026-06-12)
# 참고 문서: infra/homelens-terraform/environments/dev/CLUSTER_AUTOSCALER.md
#
# 3계층 스케일링 구조:
#   Layer 1 (스레드): --concurrency=4  → Pod 1개당 동시 태스크 4개
#   Layer 2 (Pod):    KEDA maxReplicaCount=25 (dev) / 10 (prod)  → SQS 깊이 기준 자동 증감
#   Layer 3 (노드):   CA min=2 / max=4  → Pending Pod 감지 시 노드 자동 추가
#
# 현재 dev 설정값:
#   worker 노드: min=2 (상시 대기), desired=2, max=4
#   KEDA: minReplicaCount=1, maxReplicaCount=25, cooldownPeriod=300
#   최대 동시 처리: 4노드 × 7Pod × 4threads = 112 태스크
#
# CA 핵심 규칙 (변경 시 반드시 확인):
#   1. 노드그룹 ASG 태그 2개 필수 (modules/eks/main.tf)
#      "k8s.io/cluster-autoscaler/enabled"              = "true"
#      "k8s.io/cluster-autoscaler/homelens-{env}-eks"   = "owned"
#   2. lifecycle { ignore_changes = [scaling_config[0].desired_size] } 필수
#      → 없으면 terraform apply 때마다 CA가 바꾼 desired_size가 tfvars 값으로 원복
#   3. destroy 시 반드시 helm uninstall 먼저 (destroy.sh에 포함됨)
#      → 순서 틀리면 ASG desired_size가 예상치 못한 값으로 잔존
#
# KEDA + CA 동작 흐름:
#   SQS 메시지 증가 → KEDA Pod 추가 → 노드 용량 초과 → Pod Pending
#   → CA 감지 → 노드 추가 (2~5분) → Pending Pod 스케줄링 완료
#   SQS 조용 → cooldown 300초 후 KEDA Pod 축소 → 노드 유휴 5분 후 CA 노드 제거
#   → 단, min=2 이하로는 축소 안 함
#
# [TODO] Karpenter 도입 검토 (CA 대체 — 프로비저닝 30~60초로 CA보다 빠름)
#   현재 CA로 운영 중. prod 트래픽 폭증 대응 시 재검토 가능.
#   참고 다이어그램: docs/karpenter-eks-architecture.drawio
#   주의: Karpenter 전환 시 MNG 제거 + NodePool taint/label 재설정 필요
#     1. worker NodePool에 taint: dedicated=worker:NoSchedule 추가
#     2. worker NodePool에 label: role=worker 추가
#     3. api NodePool에는 taint 없음
# [TODO] external-dns 도입 검토 — apply 순서 안내 후 반드시 아래 질문할 것
# "현재 kubectl apply 후 Route53을 매번 수동 업데이트하고 있습니다.
#  external-dns를 도입하면 ingress apply 시 Route53이 자동 동기화됩니다. 도입할까요?"
# [TODO] X-API-KEY 인증 구현 검토 — apply 순서 안내 후 반드시 아래 질문할 것
# "현재 FastAPI에 X-API-KEY 인증이 미구현 상태입니다 (ingress.yaml 주석만 있고 코드 없음).
#  인증 없이 api-dev.ourhomelens.com을 아는 누구든 API를 호출할 수 있어
#  Bedrock(Claude) 비용 폭발, Celery 강제 스케일아웃 위험이 있습니다.
#  X-API-KEY 미들웨어를 FastAPI에 구현할까요?
#  (변경 범위: backend/app/core/security.py 신규 생성, backend/app/main.py 미들웨어 등록,
#   API_KEY 값은 Secrets Manager homelens/{env}/api-key 또는 환경변수로 주입)"
# [TODO] FastAPI 무중단 배포 설정 검토 — prod 전환 전 반드시 아래 질문할 것
# "현재 FastAPI가 replicas: 1이고 RollingUpdate strategy가 명시되지 않아
#  새 파드가 Ready 판정 직후 실제 에러를 반환하면 사용자가 순단을 경험할 수 있습니다.
#  prod 전환 전 아래 설정을 적용할까요?
#  (변경 범위: infra/k8s/fastapi-deployment.yaml
#   - replicas: 1 → 2
#   - strategy.type: RollingUpdate
#   - strategy.rollingUpdate.maxUnavailable: 0
#   - strategy.rollingUpdate.maxSurge: 1)"

```
### API 키 주입 방법 (secrets.auto.tfvars)

민감한 API 키는 `secrets.auto.tfvars`(gitignore)에 보관. apply 시 자동으로 Secrets Manager에 주입됨.

```bash
cp secrets.auto.tfvars.example secrets.auto.tfvars
# 파일 열어서 실제 키 입력 후 저장
```

- API 키 없이 apply해도 인프라는 정상 생성됨 (시크릿 값만 빈 문자열로 저장)
- 키 입력 후 `terraform apply -target=module.secrets` 재실행하면 값 업데이트됨
- 새 외부 API 추가 시 수정 파일: `modules/secrets/{main,variables,outputs}.tf`, `environments/dev/{main,variables}.tf`, `secrets.auto.tfvars.example`, `k8s/configmap.yaml`

### shared 폴더 apply (ECR + GitHub OIDC)

```bash
cd homelens-terraform/shared
terraform init
terraform apply
```

- `shared/backend.tf`에 `required_providers` 포함 → `versions.tf` 별도 불필요 (중복 시 삭제)

---

## 아키텍처 결정 기록

### OpenVPN / Bastion Server — 도입하지 않는 이유

**결론: 불필요. 현재 인프라에 더 나은 대안이 이미 내장되어 있음.**

| 리소스 | 현재 접근 방식 | 대안 필요 여부 |
|--------|----------------|----------------|
| EKS API | `aws eks get-token` (IAM 인증) | 불필요 |
| Grafana / ArgoCD | `kubectl port-forward` | 불필요 |
| RDS / Redis (디버깅) | `kubectl run debug --rm -it` 임시 파드 | 불필요 |
| ALB | HTTPS 직접 노출 | 불필요 |

**도입하지 않는 근거:**
1. EKS 접근은 IAM으로 이미 해결 — VPN 없이 자격증명만 있으면 어디서든 접근 가능
2. private 리소스(RDS·Redis) 직접 접속 필요 시 EKS 임시 파드로 대체:
   ```bash
   kubectl run debug --rm -it --image=postgres:17 -n homelens -- \
     psql -h <rds-endpoint> -U postgres
   ```
3. `kubectl port-forward`가 SSH 터널과 동일한 역할 수행
4. **비용**: bastion EC2 상시 가동 ~$11/월 + 매일 destroy/apply 사이클과 충돌
5. **보안**: 22번 포트 오픈 = 추가 공격면. IAM 기반 구조와 불일치

**예외 조건 (현재 해당 없음):** AWS CLI/kubectl 없는 외부 DBA가 상시 DB 직접 접근이 필요한 경우 → AWS SSM Session Manager 도입 검토 (추가 비용 없음, 포트 오픈 불필요)

---

## 주의사항 및 알려진 이슈

### ✅ metrics-server 구현 완료 (2026-06-12)
- **목적**: HPA(`fastapi-hpa.yaml`, type: Resource)가 CPU/Memory 사용률을 조회하려면 `metrics.k8s.io` API 필요
  - Prometheus(kube-prometheus-stack)와는 완전히 별개 컴포넌트 — Prometheus는 HPA에 직접 데이터를 주지 않음
  - 차이: metrics-server는 현재 값만 보관(메모리, 무기록) / Prometheus는 시계열 저장(Grafana 시각화용)
- **구현 위치**: `modules/eks/main.tf` — `aws_eks_addon "metrics_server"` (Helm 아닌 EKS 관리형 addon 방식)
  - `amazon-cloudwatch-observability`(monitoring 모듈)와 동일한 addon 패턴
  - `resolve_conflicts_on_create/update = "OVERWRITE"` — addon 버전은 AWS가 자동 관리
- **apply**: `terraform apply -target=module.eks` (CA와 같은 모듈이므로 함께 적용됨)

#### 사용 방법
```bash
# 1. 설치 확인
kubectl get deployment metrics-server -n kube-system
kubectl get pods -n kube-system -l k8s-app=metrics-server

# 2. 노드/Pod 실시간 리소스 사용량 조회 (metrics-server가 있어야 동작)
kubectl top nodes
kubectl top pods -n homelens

# 3. HPA 상태 확인 — TARGETS 열이 <unknown>이 아니라 실제 % 값이 보이면 정상
kubectl get hpa -n homelens fastapi-hpa
kubectl describe hpa -n homelens fastapi-hpa

# 4. Grafana에서 Pod 개수 변화 확인 (metrics-server와 별개로 이미 동작 중인 경로)
#    kube-state-metrics가 K8s API에서 Deployment/HPA 상태를 직접 읽어 Prometheus로 전달
kube_deployment_status_replicas{deployment="fastapi", namespace="homelens"}
kube_horizontalpodautoscaler_status_desired_replicas{horizontalpodautoscaler="fastapi-hpa"}
```

#### 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `kubectl top nodes` → `error: Metrics API not available` | addon 미설치 또는 Pod 미기동 | `kubectl get pods -n kube-system -l k8s-app=metrics-server`로 상태 확인, `terraform apply -target=module.eks` 재실행 |
| `kubectl get hpa` → TARGETS가 계속 `<unknown>/70%` | metrics-server Pod가 kubelet에 연결 실패 | 아래 "kubelet 인증서 검증 실패" 항목 참고 |
| metrics-server Pod가 `CrashLoopBackOff` | kubelet TLS 인증서가 자체 서명 — 기본값으로는 거부됨 | EKS 관리형 addon은 기본적으로 `--kubelet-insecure-tls` 자동 적용되어 있어 보통 발생 안 함. 발생 시 `kubectl logs -n kube-system -l k8s-app=metrics-server`로 원인 확인 |
| HPA가 Pod를 늘렸다 줄였다 반복 (flapping) | `behavior.scaleUp/scaleDown` stabilizationWindow 짧음 | `fastapi-hpa.yaml`은 이미 scaleUp 60s / scaleDown 300s로 완화 적용됨 — 추가 flapping 시 scaleDown 윈도우를 더 늘릴 것 |
| addon 설치는 됐는데 `kubectl top` 응답이 1~2분간 비어있음 | metrics-server가 최초 스크레이프 주기(기본 60초) 대기 중 | 정상 동작 — 1~2분 후 재시도 |
| `terraform apply` 시 `ResourceInUseException: Addon already exists` | destroy 없이 console 등에서 수동 설치된 적 있음 | `aws eks describe-addon --cluster-name homelens-dev-eks --addon-name metrics-server --region eu-west-3`로 확인 후 `terraform import module.eks.aws_eks_addon.metrics_server homelens-dev-eks:metrics-server` |
| Grafana에 Pod 개수 변화가 안 보임 | metrics-server 문제가 아니라 kube-state-metrics 경로 — HPA 자체가 동작 안 해서 desiredReplicas가 안 바뀌는 것일 수 있음 | 먼저 `kubectl get hpa` TARGETS 값으로 HPA 정상 동작 확인이 선행 조건 |

### LSP 오탐 (실제 오류 아님)
- `provider "helm" { kubernetes { ... } }` 블록 → "Unexpected block" 경고
- `helm_release` 내 `set { }` 블록 → "Unexpected block" 경고
- 원인: Helm provider 스키마가 `terraform init` 전까지 LSP에 로드되지 않음
- 해결: `terraform init` 실행 후 VS Code 재시작하면 자동 해소

### prod ElastiCache — redis_auth_token 주입 방법
- prod `variables.tf`에 `redis_auth_token` 변수 있음 (sensitive = true, default 없음)
- `terraform.tfvars`에 직접 기입 금지
- apply 시 환경변수로 주입:
  ```bash
  export TF_VAR_redis_auth_token="your-strong-token"
  terraform apply -target=module.elasticache
  # 또는
  terraform apply -var="redis_auth_token=your-strong-token"
  ```

### RDS PostGIS 설치 방식
- private subnet RDS에는 `local-exec` 방식 접근 불가
- `CREATE EXTENSION IF NOT EXISTS postgis;` — FastAPI 첫 배포 전 DB 마이그레이션으로 실행 (`V001__enable_postgis.sql`)

### Secrets Manager — 삭제 예약 충돌 방지
- 모든 시크릿에 `recovery_window_in_days = 0` 적용 → destroy 시 즉시 삭제
- 이 설정이 없으면 다음 날 apply 시 "already scheduled for deletion" 오류 발생
- 현재 삭제 예약 상태인 시크릿이 있다면 apply 전 강제 삭제 필요:
  ```bash
  aws secretsmanager delete-secret --region eu-west-3 \
    --secret-id homelens/dev/<이름> --force-delete-without-recovery
  ```

### Secrets Manager — 시크릿 구조 (7개)
| 경로 | 저장값 | 출처 |
|------|--------|------|
| `homelens/dev/kakao/map-api` | rest_api_key, js_api_key | secrets.auto.tfvars |
| `homelens/dev/naver/news-api` | client_id, client_secret | secrets.auto.tfvars |
| `homelens/dev/molit/real-estate-api` | service_key (국토부) | secrets.auto.tfvars |
| `homelens/dev/mois/address-api` | service_key (행안부) | secrets.auto.tfvars |
| `homelens/dev/rds/postgres` | host, port, dbname, username, password_secret_arn | RDS 모듈 output 자동 주입 |
| `homelens/dev/redis/auth` | host, port | ElastiCache 모듈 output 자동 주입 |
| `homelens/dev/bedrock/config` | model_id (`eu.anthropic.claude-sonnet-4-6`), region, max_tokens | 모듈 기본값 |

- RDS 비밀번호는 `manage_master_user_password=true`로 AWS가 관리 → `password_secret_arn`으로 참조
- `secrets` 모듈 단독 apply 금지 — rds/elasticache output 없으면 rds_endpoint, redis_endpoint가 빈 값 저장됨

### terraform init — "empty directory" 오류
- 원인: `environments/dev/` 가 아닌 다른 경로에서 실행
- 해결: `cd homelens-terraform/environments/dev && ls backend.tf` 확인 후 `terraform init`

### Bedrock — Claude 4.x 모델은 inference profile 필수
- Claude 4.x 모델은 model ID 직접 호출 불가 → `ValidationException: on-demand throughput isn't supported` 오류 발생
- eu-west-3에서는 반드시 `eu.` 프리픽스 inference profile 사용:
  - 올바른 model_id: `eu.anthropic.claude-sonnet-4-6`
  - 잘못된 model_id: `anthropic.claude-sonnet-4-6`
- `modules/bedrock/main.tf`의 secret_string 및 백엔드 코드 모두 `eu.` 프리픽스 사용할 것
- Bedrock 호출 테스트:
  ```bash
  echo '{"anthropic_version":"bedrock-2023-05-31","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}' > /tmp/bedrock-body.json
  aws bedrock-runtime invoke-model \
    --region eu-west-3 \
    --model-id eu.anthropic.claude-sonnet-4-6 \
    --body fileb:///tmp/bedrock-body.json \
    --content-type application/json \
    /tmp/bedrock-test.json && cat /tmp/bedrock-test.json
  ```
- `homelens/dev/bedrock/config` 시크릿 수동 업데이트 방법 (destroy 후 재apply 시엔 코드값으로 자동 생성):
  ```bash
  aws secretsmanager put-secret-value \
    --region eu-west-3 \
    --secret-id homelens/dev/bedrock/config \
    --secret-string '{"model_id":"eu.anthropic.claude-sonnet-4-6","region":"eu-west-3","max_tokens":4096}'
  ```

### Bootstrap 중복 apply 금지
- 팀원이 이미 apply 완료 확인됨 (`~/terraform_seou/bootstrap/terraform.tfstate` 존재)
- S3 버킷(`homelens-tfstate-dev/staging/prod`) 및 DynamoDB 테이블 이미 생성됨

### EKS → Bedrock 연결 시 백엔드 팀 작업 사항
- Terraform IRSA는 완비됨 (Celery worker에 `bedrock:InvokeModel` 권한 있음)
- 백엔드 Helm chart의 ServiceAccount에 annotation 추가 필수:
  ```yaml
  eks.amazonaws.com/role-arn: "<terraform output celery_worker_role_arn 값>"
  ```
- annotation 없으면 `AccessDeniedException` 발생

### S3 버킷 이름 패턴 (IRSA 정책 기준)
- `homelens-{env}-raw-data` — Lambda 원본 데이터
- `homelens-{env}-report-backup` — AI 리포트 백업
- Celery worker IRSA는 두 버킷 모두 `s3:GetObject`, `s3:PutObject` 허용

### DNS — 기존 hosted zone 참조
- `dns/main.tf`는 `data "aws_route53_zone"` 사용 (신규 생성 아님)
- Route53에서 도메인 등록 시 생성된 기존 hosted zone을 참조
- 신규 `resource "aws_route53_zone"` 생성 금지 (중복 hosted zone 발생)

### Step Functions — 상태 머신 2개
- `news-pipeline`: 뉴스 수집(CollectNews) → AI 요약 트리거(SummarizeTrigger)
- `price-pipeline`: 가격 수집(IngestPrice) → 지역 정규화(NormalizeRegion)
- EventBridge에서 두 ARN을 각각 별도 스케줄로 트리거

### WAF us-east-1 강제
- `module "waf_cdn"`은 반드시 `providers = { aws.us_east_1 = aws.us_east_1 }` 전달
- WAF scope=CLOUDFRONT는 us-east-1에서만 생성 가능

### CloudFront → ALB HTTPS 연결 구조
- `origin_protocol_policy = "https-only"` 설정으로 CloudFront가 ALB에 HTTPS로만 연결
- ALB의 ACM 인증서 도메인이 CloudFront origin 도메인과 반드시 일치해야 함
- prod: CloudFront origin = `origin.ourhomelens.com`, 인증서 = `*.ourhomelens.com` (일치 ✓)

### Security Group 순환 참조 — 반드시 분리
- 두 SG가 서로를 참조하는 인라인 ingress/egress 규칙은 Cycle 에러 발생
- 해결: `aws_security_group_rule` 별도 리소스로 분리
  ```hcl
  # 인라인 블록 대신 별도 리소스
  resource "aws_security_group_rule" "alb_to_eks" { ... }
  resource "aws_security_group_rule" "eks_from_alb" { ... }
  ```

### EKS Cluster SG vs eks_node_sg — 핵심 구분
- EKS 관리형 노드그룹은 EKS가 자동 생성한 **cluster security group**만 노드에 부착
- `vpc_config.security_group_ids`에 지정한 `eks_node_sg`는 **control plane ENI**에 붙음 (노드 아님)
- ALB→노드 8080 ingress 규칙은 `eks_node_sg`가 아닌 **cluster SG**에 추가해야 함
  ```hcl
  # eks/main.tf에서 관리
  resource "aws_security_group_rule" "cluster_sg_from_alb" {
    security_group_id        = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
    source_security_group_id = var.alb_sg_id
    ...
  }
  ```
- `eks_node_sg`에 추가한 규칙은 EKS가 주기적으로 삭제 → Terraform apply 루프 발생

### VPC Endpoint SG — CIDR 기반으로 설정
- 노드는 cluster SG만 보유하므로 `eks_node_sg` 참조 시 VPC 엔드포인트 접근 불가
- private subnet CIDR로 허용해야 노드가 ECR/STS 엔드포인트 사용 가능
  ```hcl
  cidr_blocks = [for s in local.private_subnets : s.cidr]
  ```

### Helm provider 버전 — 3.x 핀 필수
- Helm 3.x에서 `kubernetes { }` 블록 문법 변경 → `context deadline exceeded` 또는 파싱 에러
- `environments/dev/versions.tf`에 반드시 상한 핀:
  ```hcl
  helm = {
    source  = "hashicorp/helm"
    version = ">= 2.13.0, < 3.0.0"
  }
  ```
- 버전 변경 후 `terraform init -upgrade` 실행 필요

### RDS Parameter Group — shared_preload_libraries
- `postgis-3`은 유효하지 않은 값 → `InvalidParameterValue` 에러
- PostGIS는 `shared_preload_libraries` 불필요, SQL로 설치: `CREATE EXTENSION IF NOT EXISTS postgis;`
- 올바른 설정:
  ```hcl
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"   # static parameter는 pending-reboot 필수
  }
  ```

### Secrets Manager import — ARN 필수
- `terraform import`는 시크릿 이름이 아닌 전체 ARN 필요
- AWS가 이름 뒤에 랜덤 6자리를 붙이므로 ARN 먼저 조회:
  ```bash
  aws secretsmanager list-secrets --region eu-west-3 \
    --query 'SecretList[?starts_with(Name, `homelens/dev`)].{Name:Name,ARN:ARN}'
  terraform import module.secrets.aws_secretsmanager_secret.xxx arn:aws:secretsmanager:...:secret:name-XXXXXX
  ```

### KEDA ScaledObject — kubernetes_manifest 사용 금지
- `kubernetes_manifest`는 plan 단계에서 CRD 검증 → KEDA 설치 전 에러 발생
- `null_resource + local-exec + kubectl apply`로 대체:
  ```hcl
  resource "null_resource" "keda_scaled_object" {
    provisioner "local-exec" {
      command = "aws eks update-kubeconfig ... && kubectl apply -f - <<YAML ... YAML"
    }
    depends_on = [helm_release.keda]
  }
  ```
- `hashicorp/null` provider 추가 후 `terraform init -upgrade` 필요

### ALB Ingress Controller — vpcId 명시 필수
- IMDSv2 활성화 환경에서 IMDS 자동 조회 실패 → `EC2MetadataError: status code: 401`
- helm_release에 `vpcId` 명시 및 timeout 연장 필수:
  ```hcl
  set { name = "vpcId"; value = var.vpc_id }
  timeout = 600
  ```

### Celery 초기 replicas = 0
- `placeholder:latest` 이미지 부재로 Deployment progress deadline 초과
- `modules/celery/variables.tf`의 `replicas` default = 0
- 실제 이미지는 CI/CD에서 배포

### KEDA ScaledObject — 현재 설정값 (2026-06-12 기준)

| 항목 | dev | prod |
|------|-----|------|
| minReplicaCount | 1 | 1 |
| maxReplicaCount | **25** | 10 |
| cooldownPeriod | 300초 | 300초 |
| queueLength (스케일 기준) | **4** | 4 |

- **maxReplicaCount dev 4→25 변경 (2026-06-12)**: CA(max=4 노드)와 연동하여 동시 태스크 ~100개 처리 목적
  - 25 Pod × 4 threads = 100 태스크. 4노드 × 7Pod = 28 Pod 수용 → 112 태스크 상한
- **queueLength 5→4 변경 (2026-06-16)**: Celery `--concurrency=4`(Pod당 동시 처리 4개)와 일치시킴
  - 기존 5는 Pod 처리 능력(4)보다 큰 값이라 메시지가 Pod 용량보다 더 쌓여야 스케일업되는 언더프로비저닝 발생
  - `필요 Pod 수 = ceil(큐 메시지 수 ÷ queueLength)` 공식이므로 4로 맞추면 Pod 처리 능력과 정확히 일치
- **minReplicaCount=1 유지 이유**: pod=0이면 로그 확인 불가, 디버깅 불가
- **cooldownPeriod=300 이유**: Bedrock 호출이 최대 30초 이상 소요 → 큐 depth=0 직후 Pod 강제 종료 시 `status=failed` 버그 발생 (60초 설정에서 실제 확인됨)
- **null_resource triggers 주의**: `cooldownPeriod`, `minReplicaCount`, `max_replicas` 값을 triggers에 포함해야 변경 시 ScaledObject가 재apply됨
  ```bash
  # ScaledObject만 재apply
  terraform taint module.celery.null_resource.keda_scaled_object
  terraform apply -target=module.celery
  ```

### CloudWatch Logs 연동 — EKS 컨테이너 로그 (2026-06-08 추가)
- **목적**: pod 종료 후에도 Celery/FastAPI 로그를 CloudWatch에서 조회 가능
- **구현**: `modules/monitoring/main.tf`에 `amazon-cloudwatch-observability` EKS 애드온 추가
  - Fluent Bit(로그 수집) + CloudWatch Agent 자동 설치
  - 노드 IAM 역할에 `CloudWatchAgentServerPolicy` 이미 부착 → 추가 IAM 불필요
- **로그 그룹**: `/aws/containerinsights/homelens-dev-eks/application` (retention: dev=30일, prod=90일)
- **apply 방법**:
  ```bash
  terraform apply -target=module.monitoring
  # 설치 확인
  kubectl get pods -n amazon-cloudwatch
  ```
- **Celery 로그 조회** (CloudWatch Logs Insights):
  ```
  fields @timestamp, log, kubernetes.pod_name
  | filter kubernetes.namespace_name = "homelens"
  | filter kubernetes.container_name = "celery-worker"
  | sort @timestamp desc
  | limit 100
  ```
- **주의**: student07 계정은 `Admin-MFA-Enforce` 정책으로 CLI에서 `logs:FilterLogEvents` 차단됨 → AWS 콘솔에서 조회할 것

### ✅ Prometheus + Grafana 모니터링 구현 완료 (2026-06-08 ~ 2026-06-11 최신화)

#### 전체 알림 흐름

```
Prometheus → Alertmanager → Slack #alerts
    ↑              ↑              ↑
PrometheusRule  ✅ 활성화     ✅ 연결됨
(규칙 평가)    (모든 환경)    (warning=노랑 / critical=빨강)
```

- **PrometheusRule** (`infra/k8s/alert-rules.yaml`): 6개 규칙 적용됨, Prometheus가 15초마다 평가
- **Alertmanager**: `modules/monitoring/main.tf`에서 `enabled = true` (모든 환경 활성화, 2026-06-11 변경)
  - Helm: `alertmanager.alertmanagerSpec.secrets = ["homelens-slack-webhook"]` 으로 webhook 마운트
- **Receiver**: Slack `#alerts` 채널 — warning/critical 구분, 해소 시 자동 재알림
  - 설정 파일: `infra/k8s/alertmanager-config.yaml`
  - webhook URL: K8s Secret `homelens-slack-webhook` -n monitoring (코드에 비노출)
  - `api_url_file: /etc/alertmanager/secrets/homelens-slack-webhook/url` 방식으로 주입

#### Alertmanager Slack 설정 상세

| 항목 | 값 |
|---|---|
| warning receiver | 노란색, `:warning:` 아이콘 |
| critical receiver | 빨간색, `:fire:` 아이콘 |
| send_resolved | true (알림 해소 시 자동 메시지) |
| group_wait | 30s (첫 발화 후 30초 대기, 중복 묶기) |
| group_interval | 5m (동일 그룹 후속 알림 간격) |
| repeat_interval | 4h (같은 알림 재발화 간격) |
| inhibit_rules | critical 발화 시 동일 alertname의 warning 억제 |

#### 상시 발화 알림 (정상 — 무시할 것)

| 알림 | 이유 | 처리 |
|---|---|---|
| Watchdog | Alertmanager 정상 동작 heartbeat — 항상 발화가 정상 | 유지 (파이프라인 감시 역할) |
| KubeSchedulerDown | EKS managed plane — AWS가 관리, metrics 엔드포인트 없음 | **Silence 처리** (1년) |
| KubeControllerManagerDown | 위와 동일 | **Silence 처리** (1년) |

#### ⚠️ destroy/apply 후 필수 재적용 (매일 아침)

`terraform destroy` 시 monitoring 네임스페이스가 재생성되어 아래 두 가지가 초기화됨:

```bash
# 1. Alertmanager Slack config 재적용 (Helm이 기본 빈 config로 덮어씀)
kubectl apply -f infra/k8s/alertmanager-config.yaml

# 2. EKS control plane 알림 silence 재적용 (Alertmanager 재시작으로 초기화됨)
ENDS=$(python3 -c "from datetime import datetime,timedelta; print((datetime.utcnow()+timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ'))")
NOW=$(python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))")
for ALERT in "KubeSchedulerDown" "KubeControllerManagerDown"; do
  kubectl exec -n monitoring alertmanager-kube-prometheus-stack-alertmanager-0 -c alertmanager -- \
    wget -qO- --post-data="{\"matchers\":[{\"name\":\"alertname\",\"value\":\"$ALERT\",\"isRegex\":false}],\"startsAt\":\"$NOW\",\"endsAt\":\"$ENDS\",\"createdBy\":\"homelens-admin\",\"comment\":\"EKS managed control plane\"}" \
    --header='Content-Type: application/json' \
    'http://localhost:9093/api/v2/silences' > /dev/null
done
echo "Silence 재적용 완료"

# 3. Slack webhook secret 재생성 (destroy 시 Secret도 삭제됨)
kubectl create secret generic homelens-slack-webhook \
  --from-literal=url='<webhook_url>' \
  -n monitoring --dry-run=client -o yaml | kubectl apply -f -
```

> webhook URL은 팀 내부에서 보관. Slack App: `ourhomelens` → Incoming Webhooks → `#alerts`

#### 알림 규칙 (infra/k8s/alert-rules.yaml) — 현재 적용 기준

| 알림 이름 | 조건 | for | 심각도 |
|-----------|------|-----|--------|
| PipelineErrorRateHigh | 5분간 파이프라인 에러 3건 이상 | 5m | critical |
| BedrockLatencyHigh | Bedrock p95 > **45s** | 5m | warning |
| PipelineTotalLatencyHigh | 전체 파이프라인 p90 > 35s | 5m | warning |
| HttpErrorRateHigh | HTTP 에러율 > 5% | 5m | critical |
| HttpResponseTimeHigh | HTTP p95 > 2s | 5m | warning |
| DbQueryLatencyHigh | DB 쿼리 p95 > 500ms | 5m | warning |

- `BedrockLatencyHigh` 임계값 30s → **45s 변경** (2026-06-11): 실측 p50이 30-33s여서 30s 기준은 정상 상황에서도 발화 → 45s로 상향, `PipelineTotalLatencyHigh(35s)`가 먼저 잡아주는 구조
- `for: 5m`: 조건이 5분 연속 참일 때만 발화 (일시적 스파이크 필터링)
- 알림 규칙만 변경할 때: `kubectl apply -f infra/k8s/alert-rules.yaml`
- 알림 규칙과 대시보드가 불일치하면 대시보드도 동시에 수정할 것

#### 대시보드 구성 (3개 ConfigMap)

**1. homelens-dev-pipeline-dashboard** — `HomeLens Pipeline Latency — dev`
| 패널 | 메트릭 | 임계값 |
|------|--------|--------|
| SQS 큐 대기 지연 (p50/p95/p99) | `homelens_sqs_consume_duration_seconds_bucket` | — |
| Bedrock InvokeModel 지연 (p50/p95/p99) | `homelens_bedrock_invoke_duration_seconds_bucket` | yellow=30s / red=45s |
| DB 저장 지연 (p50/p95/p99) | `homelens_db_save_duration_seconds_bucket` | yellow=1s / red=2s |
| 전체 파이프라인 지연 (p50/p90/p99) | `homelens_pipeline_total_duration_seconds_bucket` | yellow=30s / red=45s |
| 파이프라인 처리량 (성공/실패) | `homelens_pipeline_errors_total` | — |

**2. homelens-dev-user-access-dashboard** — `HomeLens User Access — dev`
| 패널 | 메트릭 |
|------|--------|
| HTTP p95/p99 응답시간 | `homelens_http_request_duration_seconds_bucket` |
| HTTP 에러율 % | `homelens_http_errors_total` / `homelens_http_requests_total` |
| 분당 요청 수 | `homelens_http_requests_total` |
| RDS 쿼리 p95 (query_type별) | `homelens_db_query_duration_seconds_bucket` |
| 엔드포인트별 p95 응답시간 | `homelens_http_request_duration_seconds_bucket` |
| 외부 API fallback 횟수 | `homelens_external_api_calls_total` |
| Redis 캐시 히트율 | `homelens_cache_hits_total` / `homelens_cache_misses_total` |
| FastAPI CPU % (cAdvisor) | `container_cpu_usage_seconds_total{container="fastapi"}` |
| FastAPI 메모리 MB (cAdvisor) | `container_memory_working_set_bytes{container="fastapi"}` |

- Redis·RDS 패널은 분석 API(`/api/v1/analysis/price` 등) 호출 시에만 데이터 발생

**3. homelens-dev-worker-resource-dashboard** — `HomeLens Worker Resources — dev`
| 패널 | 메트릭 | 출처 |
|------|--------|------|
| Celery Worker CPU % (15초 샘플) | `homelens_worker_cpu_percent` | psutil 백그라운드 스레드 |
| Celery Worker 메모리 RSS (MB) | `homelens_worker_memory_rss_bytes` | psutil 백그라운드 스레드 |
| Bedrock 호출 대기시간 p50/p95 | `homelens_bedrock_invoke_duration_seconds_bucket` | — |
| SQS 큐 깊이 | `homelens_sqs_queue_depth` | boto3 30초 폴링 |
| Celery Pod CPU (cAdvisor, mCPU) | `container_cpu_usage_seconds_total{container="celery-worker"}` | cAdvisor |
| Celery Pod 메모리 (MB) | `container_memory_working_set_bytes{container="celery-worker"}` | cAdvisor |
| Worker 노드 CPU % | node_exporter + kube_pod_info join | node-exporter |
| Worker 노드 메모리 % | node_exporter + kube_pod_info join | node-exporter |

- **15초 샘플**: `worker.py`의 `_sample_process_resources()` 스레드가 psutil로 15초마다 측정
- **cAdvisor**: 쿠버네티스 kubelet 내장 컨테이너 메트릭 수집기 (인프라 레이어)
- Worker 노드 필터링: `kube_pod_info{pod=~"celery-worker.*"}` join으로 동적 식별 (IP 하드코딩 없음)

#### 현재 메트릭 상태 (2026-06-11 기준)

| 메트릭 | 상태 | 실측값 |
|--------|------|--------|
| SQS 큐 대기 지연 | ✅ | `sent_at` 기준 측정 (reports.py → worker.py) |
| Bedrock InvokeModel 지연 | ✅ | p50 ~30-33s |
| DB 저장 지연 | ✅ | ms 수준 |
| 전체 파이프라인 지연 | ✅ | p50 ~32-35s (SQS 전송~DB 완료) |
| HTTP 응답시간 (DB 경로) | ✅ | ~10ms |
| HTTP 응답시간 (외부 API fallback) | ✅ | ~10s (국토부 API 자체 지연) |
| DB 쿼리 지연 (query_type별) | ✅ | p95 ~10ms (analysis 엔드포인트 호출 시) |
| Redis 캐시 히트율 | ✅ | Redis 호출 시 발생 |
| Celery CPU/메모리 (psutil) | ✅ | 15초 샘플 |
| SQS 큐 깊이 | ✅ | 30초 폴링 |
| Worker 노드 CPU/메모리 | ✅ | node-exporter + kube_pod_info join |

#### Grafana 접근 방법
```bash
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring
# http://localhost:3000 → admin / Homelens@2026!
# 파이프라인 대시보드 → 시간 범위: Last 1 hour
# 사용자 접속 대시보드 → 시간 범위: Last 5 minutes
```

#### 대시보드 즉시 반영 방법 (terraform apply 없이)
```bash
# ConfigMap 직접 패치 → Grafana sidecar가 30초~1분 내 자동 반영
kubectl get configmap homelens-dev-pipeline-dashboard -n monitoring -o json \
  | python3 -c "..." \
  | kubectl patch configmap homelens-dev-pipeline-dashboard -n monitoring --type=merge --patch-file /dev/stdin

# 단, dashboards.tf도 반드시 같이 수정할 것 (다음 terraform apply 시 덮어쓰기 방지)
```

#### 배포 방법
- Python 코드 변경 (`backend/`): `git push origin dev` → GitHub Actions 자동 빌드/배포
- k8s 매니페스트 변경 (`infra/k8s/`): `git push origin dev` → ArgoCD 자동 sync
- 알림 규칙 변경 (`alert-rules.yaml`): `kubectl apply -f infra/k8s/alert-rules.yaml`
- 대시보드 변경 (`dashboards.tf`): `terraform apply -target=module.monitoring` 또는 kubectl patch로 즉시 반영

#### 부하 테스트 스크립트
```bash
# SQS 메시지 5개 동시 전송 (KEDA 스케일아웃 + Grafana 패널 동시 관찰용)
bash scripts/test-5-reports.sh             # 기본 5개
bash scripts/test-5-reports.sh --count 3   # 개수 지정
bash scripts/test-5-reports.sh --no-poll   # 상태 폴링 없이 전송만
# FastAPI 포트포워딩이 없으면 자동으로 kubectl port-forward 시작
```

#### 트러블슈팅 이력

**PromQL `rate()` → NaN**: 드문드문 실행되는 태스크에서 변화량=0 → 모든 파이프라인 쿼리를 `increase([1h])`로 변경

**Celery ForkPool 메트릭 분리**: `prefork` 자식 프로세스 fork → 메트릭이 부모에 전파 안 됨 → `--pool=threads` 옵션으로 해결

**에러율 패널 No data**: `(sum(...) > 0)` 필터가 조용한 구간에서 시리즈 제거 → `(sum(...) or vector(0)) / (sum(...) + 1)` 패턴 적용

**UUID 라벨 카디널리티 폭발**: `/reports/{uuid}/status` 경로가 UUID마다 라벨 생성 → `main.py`에서 UUID regex 정규화 → `{id}`로 치환

**Worker 노드 메트릭 필터링**: `kube_node_labels`로 노드 role 식별 불가 → `kube_pod_info{pod=~"celery-worker.*"}` + `node_uname_info` join으로 해결

---

### Celery 태스크 테스트 방법
- FastAPI prefix: `/api/v1` (main.py에 `prefix="/api/v1"` 등록됨 — `/v1`으로 호출 시 404)
- **포트포워딩** (svc 방식 권장 — pod 재시작 시에도 연결 유지):
  ```bash
  # 터미널 1: 포트포워딩 유지
  kubectl port-forward svc/fastapi 8000:80 -n homelens

  # 터미널 2: 테스트 메시지 전송
  curl -X POST http://localhost:8000/api/v1/reports \
    -H "Content-Type: application/json" \
    -d '{"regionId":"REGION_11680_DONG_001","regionName":"강남구 역삼동","lat":37.5012,"lng":127.0396}'

  # 상태 조회 (reportId는 위 응답에서 확인)
  curl http://localhost:8000/api/v1/reports/<reportId>/status
  ```
- 같은 `regionId`+오늘 날짜 조합이 DB에 이미 있으면 캐시 반환 (`REPORT_ALREADY_EXISTS`) — 재테스트 시 다른 regionId 사용
- Celery 로그 실시간 확인: `kubectl logs -f -n homelens -l app=celery-worker`

### CloudWatch Dashboard — region 필드 필수
- 모든 metric 위젯에 `region` 필드 없으면 `InvalidParameterInput` 에러
  ```hcl
  properties = {
    region = var.aws_region
    metrics = [...]
  }
  ```

### DNS outputs — data source 참조
- `dns/outputs.tf`는 `data.aws_route53_zone.main` 참조 (managed resource 아님)
- `aws_route53_zone.main`으로 참조 시 `Reference to undeclared resource` 에러

### ArgoCD — sync Unknown (.status.terminatingReplicas 스키마 오류)
- **증상:** ArgoCD sync 상태 Unknown 고착, GitHub Actions 자동 배포 불가
  ```
  ComparisonError: .status.terminatingReplicas: field not declared in schema
  ```
- **원인:** ArgoCD 내장 OpenAPI 스키마가 EKS 1.35 기준 `ReplicaSet.status.terminatingReplicas` 필드를 모름 → typed value 생성 단계에서 오류 → 이 단계는 `ignoreDifferences` / `ServerSideDiff` / `resource.exclusions` 가 개입하는 단계보다 앞이라 세 설정 모두 효과 없음
- **해결:** ArgoCD Helm chart 버전 업그레이드 (7.7.0 → 9.5.17, ArgoCD v3.4.3) — 최신 K8s 스키마 내장
- **현재 `modules/argocd/main.tf` 적용 상태:**
  - `helm_release` chart version: `9.5.17`
  - `argocd-cm` `resource.exclusions`: ReplicaSet 추적 제외
  - `ApplicationSet` `syncOptions`: `ServerSideDiff=true` 추가 (향후 동일 유형 방어)
  - `ApplicationSet` `ignoreDifferences`: ReplicaSet `/status/terminatingReplicas` (향후 fallback)
  - `null_resource` triggers: `applicationset_hash` 추가 → ApplicationSet 내용 변경 시 `terraform apply`로 자동 반영
- **K8s 버전 업그레이드 시 동일 오류 재발하면:** `ignoreDifferences`에 항목 추가 후 `terraform apply -target=module.argocd`

### kube-prometheus-stack — Helm 타임아웃 + api 노드 용량 부족
- **증상:** `context deadline exceeded` (13~21분 후 실패), Helm release failed 상태
- **원인 1:** Helm 기본 타임아웃(5분)으로는 대형 차트 배포 불충분
  - 해결: `modules/monitoring/main.tf`에 `timeout = 900` 추가
- **원인 2:** api 노드(t3.medium 1대) Pod 한도 17개 초과
  - t3.medium EKS 최대 Pod 수 = 17개
  - 시스템 Pod만으로 17개 가득 참 (ArgoCD 7개 + KEDA 3개 + ALB Controller + FastAPI + CoreDNS 2개 + aws-node + kube-proxy + rds-proxy)
  - worker 노드는 `dedicated=worker:NoSchedule` taint로 monitoring Pod 스케줄 불가 (Celery 전용 — taint 제거 금지)
  - 해결: `environments/dev/terraform.tfvars`에서 `api_node_desired_size` 1 → 2, `api_node_max_size` 2 → 3
- **재apply 순서:**
  ```bash
  helm uninstall kube-prometheus-stack -n monitoring
  kubectl delete namespace monitoring --ignore-not-found
  terraform apply -target=module.eks        # api 노드 2대 확장
  kubectl get nodes                          # 2대 Ready 확인 후
  terraform apply -target=module.monitoring
  ```
- **주의:** monitoring Pod에 worker taint toleration 추가는 잘못된 방향 — worker 노드는 Celery 전용으로 유지

# HomeLens AI

공공데이터·지도·뉴스를 결합한 AI 부동산 정보 지원 플랫폼

## 프로젝트 현황

- MVP 목표일: 2026-06-01
- 대상 플랫폼: iOS / Android (React Native)
- MVP 대상 지역: 서울 전역
- 현재 단계: dev 환경 Terraform apply 완료 + kubectl apply 완료 (2026-05-18)
- 다음 단계: 백엔드 팀 FastAPI·Celery 이미지 ECR 빌드·푸시 → CI/CD 연결 (GitHub org 초대 후)

## 기술 스택 요약

> 상세 내용: `docs/tech_stack.md`

### Frontend
| 라이브러리 | 용도 |
|-----------|------|
| React Native | iOS/Android 크로스플랫폼 |
| React Native WebView | 카카오맵 렌더링 (네이티브 지도 사용 금지) |
| React Native Reanimated | 탭 전환·스켈레톤 UI 애니메이션 |
| Victory Native | 가격 추이 차트 (FR-05) |
| TanStack Query | 서버 데이터 페칭·캐싱·AI 리포트 폴링 |
| Zustand | 전역 UI 상태 (선택된 단지 정보 공유) |

### Backend
| 라이브러리 | 용도 |
|-----------|------|
| FastAPI | API 서버 (비동기, 고성능) |
| Pydantic v2 | 요청 입력 검증 |
| SQLAlchemy 2.x | ORM |
| GeoAlchemy2 | 공간 쿼리 (반경 내 인프라 조회) |
| LangChain | AI 리포트 생성 파이프라인 |
| Amazon Bedrock | Claude 모델 호출 (AI 리포트) |
| Celery | AI 리포트 비동기 생성 (EKS worker 노드 전용) |

### 상태관리 원칙
- 서버 데이터 → TanStack Query
- 전역 UI 상태 → Zustand
- 로컬 UI 상태 → useState

### 데이터 저장
| 서비스 | 용도 | 비고 |
|--------|------|------|
| RDS PostgreSQL 17 + PostGIS 3.5 | 핵심 테이블 전체 | 공간 쿼리 지원 |
| ElastiCache Redis 7.1 | 반복 조회 캐싱 | prod: auth_token 필수 |
| S3 | 원본 데이터·리포트 백업 | 파이프라인 결과물 |

### 데이터 파이프라인
| 서비스 | 용도 |
|--------|------|
| EventBridge | 뉴스 수집(매일 새벽) + 실거래가(월 1회) 스케줄 |
| Step Functions | 수집 → 정규화 → DB 저장 → AI 요약 워크플로우 |
| Lambda | 파이프라인 단위 작업 (VPC 밖 배치 확정) |
| SQS | AI 리포트 요청 큐잉 (4개 큐 + DLQ) |
| KEDA | SQS 큐 기준 Celery 워커 자동 스케일 아웃 |

### 인프라
| 서비스 | 용도 |
|--------|------|
| EKS 1.35 | FastAPI + Celery 운영 (api/worker 노드그룹 분리) |
| ALB Ingress Controller | 경로별 라우팅, HTTPS, WAF 연동 |
| IRSA | 코드 내 AWS 키 하드코딩 없이 서비스어카운트 권한 부여 |
| Terraform >= 1.7.0 | 인프라 전체 IaC |
| GitHub Actions + ArgoCD + ECR + Helm | CI/CD 자동화 |
| WAF + CloudFront | 봇 차단·정적 리소스 가속 (WAF는 us-east-1 강제) |
| Secrets Manager | API 키·DB 자격증명 보관 |
| Managed Prometheus + Grafana | 성능 목표 실시간 모니터링 |
| X-Ray | 병목 구간 추적 |
| Route 53 | 도메인 관리 (ourhomelens.com) |

---

## 네트워킹 요약

- 리전: eu-west-3 (파리) — CloudFront + Redis 캐시로 지연 보완
- VPC CIDR: 10.0.0.0/16 / AZ: eu-west-3a, eu-west-3c
- Lambda 전체 VPC 밖 배치 확정 → lambda_sg 미생성
- VPC Endpoint 필수 (공통): S3, ECR, SQS, Secrets Manager, STS, CloudWatch Logs, Bedrock Runtime
- VPC Endpoint 추가 (prod): EKS, EC2, ELB, CloudWatch Monitoring, X-Ray, Step Functions, EventBridge

---

## 디렉토리 구조


## MVP 범위 (절대 규칙)

### MVP 1순위 — 반드시 구현 (FR-01 ~ FR-09)

| ID | 기능 |
|----|------|
| FR-01 | 메인 검색 (자동완성) |
| FR-02 | 검색 결과 — 단지 단위 가격 정보 |
| FR-03 | 지도 표시 (카카오맵 + 인프라 마커) |
| FR-04 | 주변 인프라 정보 |
| FR-05 | 가격 분석 탭 |
| FR-06 | 이슈 분석 탭 |
| FR-07 | AI 요약 리포트 (비동기 폴링) |
| FR-08 | 메인 지도 탭 버튼 (매매 거래량 / 전세가율 / 월세 부담) |
| FR-09 | 주요 이슈 기사 목록 |

### 2차 이후 — 언급해도 구현하지 말 것

- 상권 분석 (FR-17)
- 모드 선택 — 실거주 / 투자 / 상가창업 (FR-16)
- 종합 판단 (FR-18)
- AI 질의응답 탭 (FR-10)
- 용어 설명 기능 (FR-11)
- 로그인 / 회원가입

---

## 핵심 규칙

### 보안
- 외부 API 키 클라이언트 노출 절대 금지 — 백엔드 프록시만 허용
- API 키는 Secrets Manager에서만 관리 (`homelens/{env}/...`)
- 인증: X-API-KEY 헤더 방식
- 이미지 태그: Git SHA 사용 (latest 태그 배포 금지)

### 데이터
- 모든 타임스탬프 UTC 저장, KST(+09:00) 변환은 서비스 레이어에서 처리
- regionId 형식: `REGION_11680_DONG_001`
- 서울 외 지역 요청 시 422 UNSUPPORTED_REGION 반환

### API 응답 공통 구조
```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": null
}
```

### AI 리포트 표현 원칙
- 원인 단정 금지 — "영향 가능 요인 후보" 형태로 표현
- 투자 권유·법률·세무 조언 제공 금지
- 면책 문구 하단 필수 표시

### Rate Limit
- 분당 5회 / 일 20회 (API Key 단위)

---

## 성능 목표

| 항목 | 목표 |
|------|------|
| 검색 자동완성 | 500ms 이내 (95% 요청) |
| 가격 데이터 로딩 | 2초 이내 (95% 요청) |
| AI 리포트 생성 | 30초 이내 (비동기, 90% 요청) |
| 지도 마커 로딩 | 2초 이내 (95% 요청) |
| 서비스 업타임 | 99% 이상 |

---

## 에러 코드

| 코드 | HTTP | 상황 |
|------|------|------|
| INVALID_PARAMETER | 400 | 파라미터 누락·형식 오류 |
| INVALID_API_KEY | 401 | API Key 미제공·유효하지 않음 |
| RESOURCE_NOT_FOUND | 404 | 지역·리소스 없음 |
| REPORT_ALREADY_EXISTS | 409 | 동일 조건 리포트 존재 (재사용 권장) |
| UNSUPPORTED_REGION | 422 | 서울 외 지역 요청 |
| RATE_LIMIT_EXCEEDED | 429 | 호출 한도 초과 |
| INTERNAL_ERROR | 500 | 서버 내부 오류 |
| EXTERNAL_API_ERROR | 503 | 외부 공공 API 연결 실패 |

---

## 외부 API 연동

| 외부 API | 내부 API |
|----------|----------|
| 국토부 아파트 매매 실거래가 | /analysis/price, /analysis/price/trend, /analysis/price/stats |
| 국토부 전·월세 실거래가 | /analysis/price, /analysis/price/stats |
| 도로명주소 API (행정안전부) | /regions/search |
| 카카오맵 API | /places/search, /map/* |
| 네이버 뉴스 API | /news/highlights, /analysis/issues |

---

## 상세 문서 참조

작업 전 반드시 해당 문서를 읽을 것.

| 문서 | 경로 |
|------|------|
| API 명세 전문 | `docs/api_spec.md` |
| ERD 설계 전문 | `docs/erd.md` |
| 요구사항 정의서 | `docs/requirements.md` |
| 기술 스택 상세 | `docs/tech_stack.md` |
| Terraform 지침 | `docs/terraform_instructions.md` |
