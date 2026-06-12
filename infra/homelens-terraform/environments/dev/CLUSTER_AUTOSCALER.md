# Cluster Autoscaler 구현 가이드

> 작성일: 2026-06-11 / 구현 완료: 2026-06-12  
> 현재 상태: **구현 완료** — terraform apply 후 활성화됨

---

## 도입 배경

| 항목 | 내용 |
|------|------|
| 목적 | worker 노드를 SQS 부하에 따라 1→3대 자동 확장/축소 |
| 비용 효과 | t3.medium 고정 2대($66.8/월) → CA 동적(~$40/월) — 월 **$26 절감** |
| 구현 대상 | worker 노드그룹 (api 노드그룹도 동일하게 적용) |

### CA가 필요한 이유

```
현재: worker MNG desired=1 고정
      KEDA가 Pod를 1→5개로 늘려도 노드는 1대 그대로
      → 2번째 Pod부터 Pending 가능성 (노드 용량 초과 시)

CA 도입 후: Pod Pending 감지 → worker 노드 자동 추가
           노드 유휴 감지 → 자동 제거 (비용 절감)
```

---

## 수집된 프로젝트 정보

```
클러스터 이름:  homelens-dev-eks  (= ${project_name}-${environment}-eks)
AWS 리전:      eu-west-3
EKS 버전:      1.35
AWS 계정 ID:   611058323802

OIDC local 변수: local.oidc_issuer  (modules/eks/irsa.tf에 이미 선언됨)
Helm provider:   >= 2.13.0, < 3.0.0 (versions.tf — 이미 있음, 추가 불필요)

현재 worker 노드그룹 (terraform.tfvars):
  instance_type: t3.medium
  min_size:      2   (상시 대기 2대)
  desired_size:  2
  max_size:      4   (최대 4대 → 동시 태스크 ~100개)

현재 api 노드그룹 (terraform.tfvars):
  instance_type: t3.medium
  min_size:      1
  desired_size:  2
  max_size:      3
```

---

## 변경 파일 목록 (5개)

| 파일 | 작업 종류 |
|------|----------|
| `modules/eks/main.tf` | 수정 — 노드그룹 태그 + lifecycle 추가 |
| `modules/eks/irsa.tf` | 수정 — CA IRSA 블록 추가 |
| `modules/eks/outputs.tf` | 수정 — CA role ARN output 추가 |
| `modules/eks/cluster_autoscaler.tf` | **신규** — CA Helm release |
| `environments/dev/destroy.sh` | 수정 — helm uninstall 1줄 추가 |

**변경 불필요한 파일:**
- `modules/networking/main.tf` — private subnet에 `kubernetes.io/cluster/...` 태그 이미 있음
- `environments/dev/versions.tf` — helm provider 이미 있음
- `environments/dev/main.tf` — CA Helm을 eks 모듈 내부에 두므로 변경 불필요
- `environments/dev/terraform.tfvars` — min/desired/max 값 그대로 유지

---

## 구현 코드

### 1. `modules/eks/main.tf` 수정

**api 노드그룹**에 아래 두 가지 추가:

```hcl
# 수정 전
resource "aws_eks_node_group" "api" {
  # ...
  tags = { Name = "${local.name_prefix}-api-node-group" }
}

# 수정 후
resource "aws_eks_node_group" "api" {
  # ...
  tags = {
    Name                                                     = "${local.name_prefix}-api-node-group"
    "k8s.io/cluster-autoscaler/enabled"                      = "true"
    "k8s.io/cluster-autoscaler/${local.name_prefix}-eks"     = "owned"
  }

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}
```

**worker 노드그룹**에 동일하게 추가:

```hcl
# 수정 전
resource "aws_eks_node_group" "worker" {
  # ...
  tags = { Name = "${local.name_prefix}-worker-node-group" }
}

# 수정 후
resource "aws_eks_node_group" "worker" {
  # ...
  tags = {
    Name                                                     = "${local.name_prefix}-worker-node-group"
    "k8s.io/cluster-autoscaler/enabled"                      = "true"
    "k8s.io/cluster-autoscaler/${local.name_prefix}-eks"     = "owned"
  }

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}
```

> **lifecycle 이유**: CA가 스케일 이벤트마다 desired_size를 변경함.
> 이 설정 없으면 다음 `terraform apply` 시 desired_size가 tfvars 값으로 원복되어 CA와 충돌.

---

### 2. `modules/eks/irsa.tf` 수정

파일 맨 아래에 추가:

```hcl
# ---------------------------------------------------------------------------
# IRSA — Cluster Autoscaler
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "cluster_autoscaler_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:kube-system:cluster-autoscaler"]
    }
  }
}

resource "aws_iam_role" "cluster_autoscaler" {
  name               = "${local.name_prefix}-cluster-autoscaler-role"
  assume_role_policy = data.aws_iam_policy_document.cluster_autoscaler_assume.json
}

resource "aws_iam_role_policy" "cluster_autoscaler" {
  name = "cluster-autoscaler-policy"
  role = aws_iam_role.cluster_autoscaler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
          "autoscaling:DescribeTags",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:DescribeImages",
          "ec2:GetInstanceTypesFromInstanceRequirements",
          "eks:DescribeNodegroup",
        ]
        Resource = "*"
      }
    ]
  })
}
```

---

### 3. `modules/eks/outputs.tf` 수정

파일 맨 아래에 추가:

```hcl
output "cluster_autoscaler_role_arn" {
  description = "IRSA role ARN for Cluster Autoscaler"
  value       = aws_iam_role.cluster_autoscaler.arn
}
```

---

### 4. `modules/eks/cluster_autoscaler.tf` 신규 생성

```hcl
# ---------------------------------------------------------------------------
# Cluster Autoscaler — Helm
# EKS 1.35 호환: chart 9.43.0 (CA app version 1.35.x)
# ---------------------------------------------------------------------------
resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  version    = "9.43.0"
  namespace  = "kube-system"

  set {
    name  = "autoDiscovery.clusterName"
    value = aws_eks_cluster.main.name
  }
  set {
    name  = "awsRegion"
    value = var.aws_region
  }
  set {
    name  = "rbac.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.cluster_autoscaler.arn
  }
  set {
    name  = "rbac.serviceAccount.name"
    value = "cluster-autoscaler"
  }
  # 스케일 다운 후 노드 삭제까지 대기 시간 (기본 10분 → 5분으로 단축)
  set {
    name  = "extraArgs.scale-down-delay-after-add"
    value = "5m"
  }
  # Celery task 실행 중 강제 종료 방지 — 스케일 다운 전 유예 시간
  set {
    name  = "extraArgs.scale-down-unneeded-time"
    value = "5m"
  }

  depends_on = [
    aws_eks_node_group.api,
    aws_eks_node_group.worker,
    aws_iam_role_policy.cluster_autoscaler,
  ]
}
```

---

### 5. `environments/dev/destroy.sh` 수정

`helm uninstall keda` 줄 바로 위에 추가:

```bash
# 추가할 줄 (helm uninstall keda 위에)
helm uninstall cluster-autoscaler -n kube-system 2>/dev/null || true
```

완성된 해당 섹션:
```bash
echo "=== Helm release 정리 (없으면 무시) ==="
helm uninstall argocd -n argocd 2>/dev/null || true
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
helm uninstall cluster-autoscaler -n kube-system 2>/dev/null || true   # 추가
helm uninstall keda -n keda 2>/dev/null || true
```

---

## apply 순서

기존 3단계 구조와 동일. CA Helm이 eks 모듈 내부에 있으므로 **별도 단계 불필요**.

```bash
# 1단계: EKS (CA Helm 포함) — 기존과 동일
terraform apply \
  -target=module.networking \
  -target=module.rds \
  -target=module.elasticache \
  -target=module.sqs \
  -target=module.s3 \
  -target=module.eks \
  -target=module.secrets

# 2단계, 3단계: 기존과 동일
```

---

## 배포 후 검증 명령어

```bash
# CA Pod 정상 기동 확인
kubectl get pods -n kube-system -l app.kubernetes.io/name=cluster-autoscaler

# CA 로그 (스케일 이벤트 확인)
kubectl logs -n kube-system -l app.kubernetes.io/name=cluster-autoscaler --tail=50

# 현재 노드 상태
kubectl get nodes

# CA가 ASG를 정상 인식하는지 확인
kubectl describe cm -n kube-system cluster-autoscaler-status
```

---

## 주의사항

### Terraform 충돌 방지
`lifecycle { ignore_changes = [scaling_config[0].desired_size] }` 없이 apply하면
CA가 바꾼 desired_size를 terraform이 원복 → CA와 Terraform이 반복 충돌.

### Celery task 강제 종료 방지
CA가 노드를 제거할 때 실행 중인 Celery task가 중단될 수 있음.
`scale-down-unneeded-time: 5m` 설정으로 완화했으나, 완전 방지를 위해 아래 추가 고려:

```yaml
# celery-deployment.yaml에 추가 (선택)
annotations:
  cluster-autoscaler.kubernetes.io/safe-to-evict: "false"
```

단, `safe-to-evict: false`는 해당 Pod가 있는 노드를 CA가 절대 제거하지 않음.
→ worker 노드 축소가 안 될 수 있으므로 상황에 맞게 판단.

### destroy 시 반드시 helm uninstall 먼저
`destroy.sh`에 추가하지 않고 terraform destroy 하면
CA가 managed하던 ASG의 desired_size가 예상치 못한 값으로 남을 수 있음.
