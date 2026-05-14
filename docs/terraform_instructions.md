# HomeLens AI

## Terraform 프로젝트 지침서

Infrastructure as Code — 확정 변수 정의서

|         |                |
| ------- | -------------- |
| **문서 버전** | v1.0           |
| **작성일** | 2026-04-30     |
| **리전**  | eu-west-3 (파리) |
| **MVP 목표일** | 2026-06-01     |
| **적용 범위** | Terraform 전 모듈 |

## 1. 리전 및 글로벌 설정

|      |                                                                                                              |
| ---- | ------------------------------------------------------------------------------------------------------------ |
| **팀 규정** | 서비스 대상(서울)과 리전(파리) 불일치는 팀 규정에 의해 감안하고 eu-west-3으로 진행. 검색 자동완성 500ms 이내 성능 목표는 CloudFront + Redis 캐시 최적화로 보완. |

|                      |                        |
| -------------------- | ---------------------- |
| **aws_region**       | eu-west-3              |
| **project_name**     | homelens               |
| **tf_state_bucket**  | homelens-tfstate-{env} |
| **tf_state_lock_table** | homelens-tfstate-lock  |
| **terraform_version** | >= 1.7.0               |
| **aws_provider_version** | >= 5.40.0              |

## 2. VPC / 네트워킹

### 2-1. VPC CIDR

|                    |                        |
| ------------------ | ---------------------- |
| **vpc_cidr**       | 10.0.0.0/16            |
| **availability_zones** | eu-west-3a, eu-west-3c |

### 2-2. 서브넷 구성

| **서브넷**             | **AZ**     | **CIDR**      | **용도**                 |
| ------------------- | ---------- | ------------- | ---------------------- |
| public_subnet_az_a  | eu-west-3a | 10.0.10.0/24  | ALB, NAT GW (공개)       |
| public_subnet_az_c  | eu-west-3c | 10.0.110.0/24 | ALB, NAT GW (공개)       |
| private_subnet_az_a | eu-west-3a | 10.0.20.0/24  | EKS 노드, VPC Endpoint   |
| private_subnet_az_c | eu-west-3c | 10.0.120.0/24 | EKS 노드, VPC Endpoint   |
| db_subnet_az_a      | eu-west-3a | 10.0.30.0/24  | RDS, ElastiCache       |
| db_subnet_az_c      | eu-west-3c | 10.0.130.0/24 | RDS Multi-AZ (prod 필수) |

### 2-3. NAT Gateway

|                  |                                                                     |
| ---------------- | ------------------------------------------------------------------- |
| **nat_gateway_az_a** | Public Subnet az-a (10.0.10.0/24) 에 1개                              |
| **nat_gateway_az_c** | Public Subnet az-c (10.0.110.0/24) 에 1개                             |
| **용도**           | 외부 공공 API / 네이버 / 카카오 호출 (Lambda VPC 밖 → NAT 불필요, EKS 노드 기타 외부 통신용) |

### 2-4. VPC Endpoint

**필수 (dev / staging / prod 공통)**

| **Endpoint 이름** | **타입**    | **서비스명**                                | **비고**             |
| --------------- | --------- | --------------------------------------- | ------------------ |
| S3 Gateway      | Gateway   | com.amazonaws.eu-west-3.s3              | Route table 연결     |
| ECR API         | Interface | com.amazonaws.eu-west-3.ecr.api         | vpc_endpoint_sg 연결 |
| ECR DKR         | Interface | com.amazonaws.eu-west-3.ecr.dkr         | vpc_endpoint_sg 연결 |
| SQS             | Interface | com.amazonaws.eu-west-3.sqs             | vpc_endpoint_sg 연결 |
| Secrets Manager | Interface | com.amazonaws.eu-west-3.secretsmanager  | vpc_endpoint_sg 연결 |
| STS             | Interface | com.amazonaws.eu-west-3.sts             | vpc_endpoint_sg 연결 |
| CloudWatch Logs | Interface | com.amazonaws.eu-west-3.logs            | vpc_endpoint_sg 연결 |
| Bedrock Runtime | Interface | com.amazonaws.eu-west-3.bedrock-runtime | vpc_endpoint_sg 연결 |

**prod 추가 Endpoint**

| **Endpoint 이름**       | **타입**    | **서비스명**                                     | **비고**             |
| --------------------- | --------- | -------------------------------------------- | ------------------ |
| EKS                   | Interface | com.amazonaws.eu-west-3.eks                  | vpc_endpoint_sg 연결 |
| EC2                   | Interface | com.amazonaws.eu-west-3.ec2                  | vpc_endpoint_sg 연결 |
| ELB                   | Interface | com.amazonaws.eu-west-3.elasticloadbalancing | vpc_endpoint_sg 연결 |
| CloudWatch Monitoring | Interface | com.amazonaws.eu-west-3.monitoring           | vpc_endpoint_sg 연결 |
| X-Ray                 | Interface | com.amazonaws.eu-west-3.xray                 | vpc_endpoint_sg 연결 |
| Step Functions        | Interface | com.amazonaws.eu-west-3.states               | vpc_endpoint_sg 연결 |
| EventBridge           | Interface | com.amazonaws.eu-west-3.events               | vpc_endpoint_sg 연결 |

## 3. Security Group

※ Lambda 전체가 VPC 밖 배치로 확정됨. lambda_sg 제거. rds_sg의 lambda_sg inbound 규칙 제거.

| **SG 이름**       | **방향**   | **포트**      | **소스/대상**                           | **비고**                   |
| --------------- | -------- | ----------- | ----------------------------------- | ------------------------ |
| alb_sg          | Inbound  | TCP 443     | 0.0.0.0/0 또는 CloudFront Prefix List | HTTPS 수신                 |
| alb_sg          | Inbound  | TCP 80      | 0.0.0.0/0                           | HTTP → HTTPS redirect    |
| alb_sg          | Outbound | TCP 8080    | eks_node_sg                         | EKS API 서비스 포트           |
| eks_node_sg     | Inbound  | TCP 8080    | alb_sg                              | ALB → FastAPI            |
| eks_node_sg     | Inbound  | All Traffic | self (eks_node_sg)                  | 노드 간 통신                  |
| eks_node_sg     | Outbound | All         | 0.0.0.0/0                           | RDS/Redis/SQS/ECR/외부 API |
| rds_sg          | Inbound  | TCP 5432    | eks_node_sg                         | EKS 노드 → PostgreSQL      |
| rds_sg          | Outbound | 제한 또는 기본    | -                                   | -                        |
| redis_sg        | Inbound  | TCP 6379    | eks_node_sg                         | EKS 노드 → Redis           |
| redis_sg        | Outbound | 제한 또는 기본    | -                                   | -                        |
| vpc_endpoint_sg | Inbound  | TCP 443     | eks_node_sg                         | Interface Endpoint 전용    |
| vpc_endpoint_sg | Outbound | All         | 기본 허용                               | -                        |

## 4. EKS 클러스터

### 4-1. 클러스터 공통

|                 |                                                                |
| --------------- | -------------------------------------------------------------- |
| **cluster_version** | 1.35 (지원 확인 완료)                                                |
| **ami_type**    | AL2023_x86_64_STANDARD                                         |
| **system 노드그룹** | api 노드그룹에 통합 (CoreDNS, metrics-server, ALB Ingress Controller) |

### 4-2. api 노드그룹

| **환경**  | **instance_type** | **min_size** | **desired_size** | **max_size** |
| ------- | ------------- | -------- | ------------ | -------- |
| dev     | t3.medium     | 1        | 1            | 2        |
| staging | t3.medium     | 1        | 2            | 3        |
| prod    | t3.large      | 2        | 2            | 4        |

### 4-3. worker 노드그룹

| **환경**  | **instance_type** | **min_size** | **desired_size** | **max_size** |
| ------- | ------------- | -------- | ------------ | -------- |
| dev     | t3.medium     | 0        | 1            | 2        |
| staging | t3.medium     | 0        | 1            | 3        |
| prod    | t3.large      | 1        | 2            | 5        |

### 4-4. worker 노드그룹 Label / Taint 및 Pod 스케줄링

| **구분**                    | **키**     | **값**             | **설명**                                    |
| ------------------------- | --------- | ----------------- | ----------------------------------------- |
| Node Label                | role      | worker            | worker 노드그룹에 적용                           |
| Node Taint                | dedicated | worker:NoSchedule | worker 노드그룹에 적용                           |
| Celery Pod — nodeSelector | role      | worker            | worker 노드에만 스케줄링                          |
| Celery Pod — toleration   | dedicated | worker:NoSchedule | taint 허용                                  |
| FastAPI Pod               | (없음)      | -                 | worker taint toleration 미설정 → api 노드에만 배치 |

## 5. IAM Role (총 10개)

※ github-actions-deploy-role의 OIDC Provider 리소스는 shared/ 모듈에 포함.

| **Role 이름**                | **연결 대상**                           | **권한 범위**                                                                                                                            |
| -------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| eks-cluster-role           | EKS 클러스터                            | EKS 제어 플레인 기본 권한 (AmazonEKSClusterPolicy)                                                                                            |
| eks-node-role              | EKS Managed Node Group              | ECR pull, CloudWatch Logs, CNI (AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy, AmazonEC2ContainerRegistryReadOnly)                 |
| alb-controller-role        | AWS Load Balancer Controller IRSA   | ALB, TargetGroup, Listener, SecurityGroup 일부 관리                                                                                      |
| fastapi-api-role           | FastAPI ServiceAccount (IRSA)       | sqs:SendMessage, secretsmanager:GetSecretValue, s3:GetObject (필요 시)                                                                  |
| celery-worker-role         | Celery Worker ServiceAccount (IRSA) | sqs:ReceiveMessage/DeleteMessage/ChangeMessageVisibility, bedrock:InvokeModel, s3:GetObject/PutObject, secretsmanager:GetSecretValue |
| lambda-ingest-role         | 데이터 수집 Lambda                       | s3:PutObject, secretsmanager:GetSecretValue, logs:*, sqs:SendMessage (필요 시)                                                          |
| step-functions-role        | Step Functions                      | lambda:InvokeFunction, sqs:SendMessage                                                                                               |
| eventbridge-role           | EventBridge Scheduler               | states:StartExecution                                                                                                                |
| github-actions-deploy-role | GitHub OIDC (shared/)               | ECR push, EKS deploy 최소 권한 — OIDC Provider: token.actions.githubusercontent.com                                                      |
| monitoring-role            | Prometheus / Grafana / X-Ray        | 메트릭·트레이스 조회 및 기록 (CloudWatchReadOnlyAccess, AWSXRayDaemonWriteAccess)                                                                |

## 6. RDS — PostgreSQL

|                        |                                                                |
| ---------------------- | -------------------------------------------------------------- |
| **engine**             | postgres                                                       |
| **engine_version**     | 17                                                             |
| **postgis_version**    | 3.5                                                            |
| **parameter_group_family** | postgres17                                                     |
| **db_subnet_group**    | db_subnet_az_a (10.0.30.0/24) + db_subnet_az_c (10.0.130.0/24) |

| **환경**  | **instance_class** | **multi_az** | **storage_type** | **allocated_storage** | **max_allocated_storage** |
| ------- | -------------- | -------- | ------------ | ----------------- | --------------------- |
| dev     | db.t4g.small   | false    | gp3          | 20 GB             | 30 GB                 |
| staging | db.t4g.medium  | false    | gp3          | 50 GB             | 50 GB                 |
| prod    | db.t4g.medium  | true     | gp3          | 100 GB            | 200 GB (autoscaling)  |

## 7. ElastiCache — Redis

|                |                 |
| -------------- | --------------- |
| **engine**     | redis           |
| **engine_version** | 7.1             |
| **cluster_mode** | disabled (전 환경) |

| **환경**  | **node_type**                       | **num_cache_nodes** | **replica** | **비고**                |
| ------- | ----------------------------------- | --------------- | ------- | --------------------- |
| dev     | cache.t4g.micro                     | 1               | 0       | 단일 노드                 |
| staging | cache.t4g.small                     | 1               | 0       | 단일 노드                 |
| prod    | cache.t4g.small 또는 cache.t4g.medium | 1               | 1       | primary 1 + replica 1 |

※ prod redis/auth auth_token 필수 적용. dev/staging은 선택.

## 8. Lambda 함수

|        |                                                                          |
| ------ | ------------------------------------------------------------------------ |
| **VPC 배치** | 전체 Lambda 함수 VPC 밖 배치 확정. lambda_sg 미생성. RDS/Redis 직접 접근 없음 (SQS/S3 경유). |

※ Provisioned Concurrency: MVP 단계 미사용.

| **함수 이름**               | **역할**               | **runtime** | **memory** | **timeout**       |
| ----------------------- | -------------------- | ---------- | ------- | ----------------- |
| news-collector          | 뉴스 수집                | python3.12 | 512 MB  | 180 s             |
| news-summarizer-trigger | 뉴스 요약 요청 분배          | python3.12 | 1024 MB | 180 s             |
| molit-price-ingest      | 국토부 실거래가 수집          | python3.12 | 1024 MB | 900 s (Lambda 최대) |
| region-normalizer       | 법정동코드/지역 정규화         | python3.12 | 512 MB  | 180 s             |
| pipeline-step           | Step Functions 단위 작업 | python3.12 | 1024 MB | 300 s             |

※ AI 리포트 생성은 Lambda 아닌 EKS Celery Worker 담당 (Bedrock 호출/DB 저장/재시도 관리).

## 9. SQS 큐

| **큐 이름**                 | **타입**   | **visibility_timeout** | **maxReceiveCount** | **DLQ** | **용도**        |
| ------------------------ | -------- | ------------------ | --------------- | --- | ------------- |
| report-generation-queue  | Standard | 180 s              | 5               | Yes | AI 리포트 생성 요청  |
| news-summary-queue       | Standard | 120 s              | 5               | Yes | 뉴스 AI 요약 작업   |
| price-ingest-queue       | Standard | 300 s              | 3               | Yes | 가격 데이터 수집/정규화 |
| external-api-retry-queue | Standard | 300 s              | 5               | Yes | 외부 API 실패 재시도 |

※ 각 큐에 DLQ 1개씩 쌍으로 생성. DLQ 이름: {큐 이름}-dlq.

## 10. ECR 레포지터리 (shared/ 모듈)

|                 |                                 |
| --------------- | ------------------------------- |
| **레포 이름 1**     | homelens-fastapi                |
| **레포 이름 2**     | homelens-celeryworker           |
| **scan_on_push** | true                            |
| **encryption_type** | AES256                          |
| **이미지 태그 전략**   | Git SHA 태그 사용 (latest 태그 배포 금지) |

**수명주기 정책**

| **태그 패턴**            | **보관 정책**  |
| -------------------- | ---------- |
| untagged (태그 없는 이미지) | 7일 후 자동 삭제 |
| prod-* 태그            | 최근 30개 보관  |
| staging-* 태그         | 최근 20개 보관  |
| dev-* 태그             | 최근 10개 보관  |

## 11. Secrets Manager — 시크릿 경로

※ dev / staging / prod 각각 환경명만 치환. staging 환경도 동일 패턴 적용.

| **시크릿 경로 (예: dev)**                  | **내용**                                 | **필수 여부**                |
| ------------------------------------ | -------------------------------------- | ------------------------ |
| homelens/{env}/kakao/map-api         | 카카오맵 REST API Key, JavaScript API Key  | 필수                       |
| homelens/{env}/naver/news-api        | 네이버 뉴스 API Client ID / Secret          | 필수                       |
| homelens/{env}/molit/real-estate-api | 국토부 공공데이터 API Key                      | 필수                       |
| homelens/{env}/rds/postgres          | username, password, host, port, dbname | 필수                       |
| homelens/{env}/redis/auth            | Redis auth token                       | prod 필수 / dev·staging 선택 |
| homelens/{env}/bedrock/config        | Bedrock 모델 ID, 리전 등 설정값                | 필수                       |

※ {env} = dev | staging | prod

## 12. CloudFront + WAF

|             |                                                 |
| ----------- | ----------------------------------------------- |
| **origin**  | ALB — Terraform alb 모듈의 alb_dns_name output 참조  |
| **default_ttl** | 60 s                                            |
| **max_ttl** | 300 s                                           |
| **min_ttl** | 0 s                                             |
| **캐시 대상**   | 정적 성격이 강한 조회 API (가격 현황, 뉴스 목록 등)               |
| **WAF 연결**  | CloudFront에 연결 (us-east-1 WAF 리소스 필요)           |
| **WAF Rule 1** | AWS Managed Rule — AWSManagedRulesCommonRuleSet |
| **WAF Rule 2** | Rate Limit Rule — 5분 내 동일 IP 2000 req 초과 시 차단   |
| **지오 제한**   | 비활성화                                            |

## 13. Route 53

|                  |                                        |
| ---------------- | -------------------------------------- |
| **hosted_zone_name** | homelens.ai                            |
| **생성 방식**        | Terraform 신규 생성 (aws_route53_zone)     |
| **레코드 예시**       | api.homelens.ai → ALB DNS / CloudFront |

## 14. 검증 이슈 처리 내역

※ Terraform 코드 작성 전 교차 검증에서 발견된 이슈 및 처리 결과

| **ID**  | **이슈**                        | **처리 내용**                                              | **상태** |
| ------- | ----------------------------- | ------------------------------------------------------ | ----- |
| **ISSUE-1** | IAM Role 개수 오표기               | 9개 → 10개 정정 (monitoring-role 포함)                       | 처리 완료 |
| **ISSUE-2** | lambda_sg 불필요                 | Lambda VPC 밖 확정 → lambda_sg 제거                         | 처리 완료 |
| **ISSUE-3** | rds_sg lambda 규칙              | Lambda VPC 밖 → rds_sg inbound lambda 규칙 제거             | 처리 완료 |
| **ISSUE-4** | Secrets Manager staging 누락    | dev/prod와 동일 패턴 staging 추가                             | 처리 완료 |
| **ISSUE-5** | redis/auth 필수 여부              | prod 필수, dev/staging 선택으로 확정                           | 처리 완료 |
| **ISSUE-6** | CloudFront TTL 수치 미정          | min 0s / default 60s / max 300s 확정                     | 처리 완료 |
| **ISSUE-7** | molit-price-ingest timeout 범위 | 300~900s → 900s(Lambda 최대값) 단일값 확정                     | 처리 완료 |
| **ISSUE-8** | 메모리 범위값                       | news-summarizer-trigger, pipeline-step → 1024MB 단일값 확정 | 처리 완료 |
