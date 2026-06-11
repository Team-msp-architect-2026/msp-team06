# Karpenter 마이그레이션 가이드

> 작성일: 2026-06-10  
> 현재 상태: **미구현** — 기록 목적으로 작성  
> 참고 다이어그램: `docs/karpenter-eks-architecture.drawio`

---

## 개요

현재 EKS 노드는 Terraform Managed Node Group (MNG) 으로 고정 관리됨.  
Karpenter 도입 시 Pod 수요에 따라 EC2를 동적으로 프로비저닝/종료 — CA보다 노드 기동 30~60초로 빠름.

**핵심: 애플리케이션 워크플로우(FastAPI → SQS → Celery → DB)는 전혀 변경 없음.**  
Karpenter는 Layer 3(EC2 노드 레이어)만 바꿈.

### 현재 구조 vs 변경 후

```
현재
  api 노드그룹   (t3.medium, min=1, max=3)  — FastAPI + 시스템 컴포넌트
  worker 노드그룹 (t3.medium, min=0, max=2)  — Celery 전용

변경 후
  system 노드그룹 (t3.medium, min=1, max=1) — Karpenter 컨트롤러 + CoreDNS 전용 (고정 유지)
  Karpenter NodePool: api                   — FastAPI, KEDA, ALB Controller, ArgoCD, Monitoring
  Karpenter NodePool: worker                — Celery Worker 전용 (taint: dedicated=worker)
```

---

## 체크리스트 검증 결과

### ✅ 1. celery-deployment.yaml nodeSelector/toleration 유지
정확함. `infra/k8s/celery-deployment.yaml` 변경 없음.  
단, Karpenter NodePool worker에 **동일한 label/taint가 반드시 있어야** celery pod가 배치됨.

```yaml
# NodePool worker spec에 반드시 포함
labels:
  role: worker
taints:
  - key: dedicated
    value: worker
    effect: NoSchedule
```

### ✅ 2. KEDA ScaledObject 변경 없음
정확함. `modules/celery/main.tf`의 minReplicaCount:1, cooldownPeriod:300, aws-sqs-queue trigger 그대로 유지.

### ⚠️ 3. Terraform MNG 제거 + Karpenter Helm + NodePool + EC2NodeClass
절반만 맞음. 아래 누락 항목 참고.

### ✅ 4. FastAPI / Celery 코드 변경 없음
정확함. `backend/app/worker.py`, `backend/app/main.py` 건드릴 필요 없음.

### ✅ 5. KEDA minReplicaCount: 1 유지
정확함. 콜드스타트 없이 안정적으로 운영됨.

---

## 추가 필수 항목 (체크리스트에서 누락된 것들)

### 🔴 Critical 1: Karpenter 부트스트랩 문제

Karpenter 컨트롤러 자체가 실행될 노드가 필요함.  
MNG를 완전히 제거하면 Karpenter pod를 올릴 노드가 없어서 **클러스터가 아무것도 못 뜸**.

**해결**: `api` 노드그룹을 완전 제거하지 말고, `system` 노드그룹(1대 고정)으로 이름 변경 후 유지.

```hcl
# modules/eks/main.tf — api 노드그룹을 system으로 교체
resource "aws_eks_node_group" "system" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${local.name_prefix}-system"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.private_subnet_ids

  ami_type       = var.ami_type
  instance_types = ["t3.medium"]

  scaling_config {
    min_size     = 1
    desired_size = 1
    max_size     = 1   # 고정 1대 — Karpenter + CoreDNS 전용
  }

  labels = { role = "system" }

  depends_on = [aws_iam_role_policy_attachment.eks_node_policies]
  tags       = { Name = "${local.name_prefix}-system-node-group" }
}
# worker 노드그룹은 완전 제거
```

---

### 🔴 Critical 2: IAM 3개 신규 필요 (irsa.tf에 현재 없음)

| 리소스 | 용도 |
|--------|------|
| `aws_iam_role.karpenter_controller` | Karpenter 컨트롤러 IRSA (서비스어카운트 `kube-system:karpenter`용) |
| `aws_iam_role.karpenter_node` | Karpenter가 프로비저닝한 EC2에 붙이는 노드 역할 |
| `aws_iam_instance_profile.karpenter_node` | 노드 역할을 EC2에 연결하는 Instance Profile |

현재 `aws_iam_role.eks_node`는 MNG 전용이라 Karpenter가 직접 사용 불가.

```hcl
# irsa.tf 추가 — Karpenter Controller IRSA
data "aws_iam_policy_document" "karpenter_controller_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:kube-system:karpenter"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "karpenter_controller" {
  name               = "${local.name_prefix}-karpenter-controller-role"
  assume_role_policy = data.aws_iam_policy_document.karpenter_controller_assume.json
}

resource "aws_iam_role_policy" "karpenter_controller" {
  name = "karpenter-controller-policy"
  role = aws_iam_role.karpenter_controller.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:RunInstances",
          "ec2:TerminateInstances",
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeInstanceTypeOfferings",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeLaunchTemplates",
          "ec2:DescribeImages",
          "ec2:DescribeSpotPriceHistory",
          "ec2:DescribeAvailabilityZones",
          "ec2:CreateLaunchTemplate",
          "ec2:DeleteLaunchTemplate",
          "ec2:CreateFleet",
          "ec2:CreateTags",
          "ec2:DescribeTags",
          "iam:PassRole",
          "iam:GetInstanceProfile",
          "iam:CreateInstanceProfile",
          "iam:DeleteInstanceProfile",
          "iam:AddRoleToInstanceProfile",
          "iam:RemoveRoleFromInstanceProfile",
          "iam:TagInstanceProfile",
          "eks:DescribeCluster",
          "pricing:GetProducts",
          "ssm:GetParameter",
        ]
        Resource = "*"
      }
    ]
  })
}

# Karpenter Node Role (EC2에 붙는 역할)
resource "aws_iam_role" "karpenter_node" {
  name               = "${local.name_prefix}-karpenter-node-role"
  assume_role_policy = data.aws_iam_policy_document.eks_node_assume.json  # ec2.amazonaws.com
}

resource "aws_iam_role_policy_attachment" "karpenter_node_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
  ])
  role       = aws_iam_role.karpenter_node.name
  policy_arn = each.value
}

resource "aws_iam_instance_profile" "karpenter_node" {
  name = "${local.name_prefix}-karpenter-node-profile"
  role = aws_iam_role.karpenter_node.name
}
```

---

### 🔴 Critical 3: Subnet/SG Discovery 태그 누락

EC2NodeClass가 서브넷/SG를 찾는 방식이 **태그 기반**임.  
현재 `modules/networking/`에 이 태그가 없어서 Karpenter가 서브넷을 못 찾음 → 노드 프로비저닝 실패.

```hcl
# modules/networking/main.tf — private subnet 리소스에 태그 추가
resource "aws_subnet" "private" {
  # ... 기존 설정 ...
  tags = merge(local.common_tags, {
    Name                                        = "..."
    "karpenter.sh/discovery"                    = "${var.project_name}-${var.environment}-eks"
    "kubernetes.io/role/internal-elb"           = "1"
  })
}
```

```hcl
# modules/eks/main.tf — EKS 클러스터 태그에도 추가
resource "aws_eks_cluster" "main" {
  # ... 기존 설정 ...
  tags = {
    Name                     = "${local.name_prefix}-eks"
    "karpenter.sh/discovery" = "${local.name_prefix}-eks"
  }
}
```

---

### 🟡 Important 4: Karpenter Helm + NodePool + EC2NodeClass Terraform 코드

KEDA ScaledObject와 동일한 이유로 NodePool/EC2NodeClass는 `null_resource + kubectl apply` 방식 사용.

```hcl
# modules/eks/karpenter.tf (신규 파일)

resource "helm_release" "karpenter" {
  name       = "karpenter"
  repository = "oci://public.ecr.aws/karpenter"
  chart      = "karpenter"
  version    = "1.3.3"
  namespace  = "kube-system"

  set {
    name  = "settings.clusterName"
    value = aws_eks_cluster.main.name
  }
  set {
    name  = "settings.interruptionQueue"
    value = ""   # Spot 미사용 시 비워둠
  }
  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.karpenter_controller.arn
  }

  depends_on = [aws_eks_node_group.system]
}

resource "null_resource" "karpenter_ec2nodeclass" {
  triggers = {
    cluster_name      = aws_eks_cluster.main.name
    node_role_name    = aws_iam_role.karpenter_node.name
    instance_profile  = aws_iam_instance_profile.karpenter_node.name
  }

  provisioner "local-exec" {
    command = <<-EOF
      aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}
      kubectl apply -f - <<YAML
      apiVersion: karpenter.k8s.aws/v1
      kind: EC2NodeClass
      metadata:
        name: default
      spec:
        amiFamily: AL2023
        role: ${aws_iam_role.karpenter_node.name}
        subnetSelectorTerms:
          - tags:
              karpenter.sh/discovery: ${aws_eks_cluster.main.name}
        securityGroupSelectorTerms:
          - tags:
              karpenter.sh/discovery: ${aws_eks_cluster.main.name}
        tags:
          karpenter.sh/discovery: ${aws_eks_cluster.main.name}
      YAML
    EOF
  }

  depends_on = [helm_release.karpenter]
}

resource "null_resource" "karpenter_nodepool_api" {
  triggers = {
    cluster_name = aws_eks_cluster.main.name
  }

  provisioner "local-exec" {
    command = <<-EOF
      aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}
      kubectl apply -f - <<YAML
      apiVersion: karpenter.sh/v1
      kind: NodePool
      metadata:
        name: api
      spec:
        template:
          metadata:
            labels:
              role: api
          spec:
            nodeClassRef:
              group: karpenter.k8s.aws
              kind: EC2NodeClass
              name: default
            requirements:
              - key: kubernetes.io/arch
                operator: In
                values: ["amd64"]
              - key: karpenter.sh/capacity-type
                operator: In
                values: ["on-demand"]
              - key: node.kubernetes.io/instance-type
                operator: In
                values: ["t3.medium", "t3.large"]
        limits:
          cpu: "16"
          memory: "32Gi"
        disruption:
          consolidationPolicy: WhenUnderutilized
          consolidateAfter: 1m
      YAML
    EOF
  }

  depends_on = [null_resource.karpenter_ec2nodeclass]
}

resource "null_resource" "karpenter_nodepool_worker" {
  triggers = {
    cluster_name = aws_eks_cluster.main.name
  }

  provisioner "local-exec" {
    command = <<-EOF
      aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}
      kubectl apply -f - <<YAML
      apiVersion: karpenter.sh/v1
      kind: NodePool
      metadata:
        name: worker
      spec:
        template:
          metadata:
            labels:
              role: worker
          spec:
            nodeClassRef:
              group: karpenter.k8s.aws
              kind: EC2NodeClass
              name: default
            requirements:
              - key: kubernetes.io/arch
                operator: In
                values: ["amd64"]
              - key: karpenter.sh/capacity-type
                operator: In
                values: ["on-demand"]
              - key: node.kubernetes.io/instance-type
                operator: In
                values: ["t3.medium", "t3.large"]
            taints:
              - key: dedicated
                value: worker
                effect: NoSchedule
        limits:
          cpu: "16"
          memory: "32Gi"
        disruption:
          consolidationPolicy: WhenEmpty
          consolidateAfter: 30s
      YAML
    EOF
  }

  depends_on = [null_resource.karpenter_ec2nodeclass]
}
```

---

### 🟡 Important 5: destroy.sh 업데이트 필요

현재 destroy.sh에서 Karpenter를 그냥 삭제하면 Karpenter가 프로비저닝한 EC2 노드가 고아 상태로 남음.  
`helm uninstall keda` 위쪽에 아래 내용 추가:

```bash
echo "=== Karpenter NodePool 삭제 (Karpenter가 프로비저닝한 노드 자동 종료) ==="
kubectl delete nodepools --all 2>/dev/null || true
kubectl delete ec2nodeclasses --all 2>/dev/null || true

echo "    Karpenter 노드 종료 대기 중 (최대 2분)..."
for i in $(seq 1 12); do
  NODE_COUNT=$(kubectl get nodes -l karpenter.sh/nodepool --no-headers 2>/dev/null | wc -l || echo "0")
  if [ "$NODE_COUNT" = "0" ]; then
    echo "    Karpenter 노드 모두 종료됨."
    break
  fi
  echo "    노드 ${NODE_COUNT}개 종료 중... (${i}/12, 10초 대기)"
  sleep 10
done

helm uninstall karpenter -n kube-system 2>/dev/null || true

# state 정리
terraform state rm module.eks.null_resource.karpenter_nodepool_api 2>/dev/null || true
terraform state rm module.eks.null_resource.karpenter_nodepool_worker 2>/dev/null || true
terraform state rm module.eks.null_resource.karpenter_ec2nodeclass 2>/dev/null || true
terraform state rm module.eks.helm_release.karpenter 2>/dev/null || true
```

---

### 🟡 Important 6: aws-auth ConfigMap 업데이트

매일 apply 후 aws-auth에 **Karpenter Node Role도 추가** 필요.

```yaml
# ~/aws-auth.yaml 의 mapRoles 섹션에 추가
mapRoles: |
  - rolearn: arn:aws:iam::611058323802:role/homelens-dev-karpenter-node-role
    username: system:node:{{EC2PrivateDNSName}}
    groups:
      - system:bootstrappers
      - system:nodes
```

---

### 🟡 Important 7: variables.tf / tfvars 정리

Karpenter 전환 후 더 이상 필요 없는 변수들:

```
제거 대상 (modules/eks/variables.tf):
  - api_node_instance_type
  - api_node_min_size / desired_size / max_size
  - worker_node_instance_type
  - worker_node_min_size / desired_size / max_size

제거 대상 (environments/dev/terraform.tfvars):
  - api_node_instance_type = "t3.medium"
  - api_node_min_size = 1 / desired_size = 2 / max_size = 3
  - worker_node_instance_type = "t3.medium"
  - worker_node_min_size = 0 / desired_size = 1 / max_size = 2

제거 대상 (environments/dev/main.tf — module "eks" 호출부):
  - api_node_instance_type, api_node_min/desired/max_size
  - worker_node_instance_type, worker_node_min/desired/max_size
```

---

## 수정/신규 파일 전체 목록

| 파일 | 작업 | 내용 |
|------|------|------|
| `modules/eks/main.tf` | 수정 | worker MNG 제거, api MNG → system MNG(1대 고정)으로 교체, 클러스터 태그 추가 |
| `modules/eks/irsa.tf` | 수정 | Karpenter Controller IRSA + Node Role + Instance Profile 추가 |
| `modules/eks/karpenter.tf` | **신규** | Karpenter Helm + EC2NodeClass + NodePool api/worker |
| `modules/eks/variables.tf` | 수정 | MNG 관련 변수 전부 제거 |
| `modules/eks/outputs.tf` | 수정 | `karpenter_node_role_name` output 추가 |
| `modules/networking/main.tf` | 수정 | private subnet에 `karpenter.sh/discovery` 태그 추가 |
| `environments/dev/main.tf` | 수정 | module "eks" 호출에서 MNG 변수 제거 |
| `environments/dev/terraform.tfvars` | 수정 | MNG 변수 6개 제거 |
| `environments/dev/versions.tf` | 확인 | null provider 포함 여부 확인 (karpenter.tf에서 null_resource 사용) |
| `environments/dev/destroy.sh` | 수정 | Karpenter 해체 순서 추가 (NodePool 삭제 → 노드 종료 대기 → helm uninstall) |

---

## apply 순서 (Karpenter 도입 후)

1단계, 2단계, 3단계 구조는 동일. EKS 모듈 내부에서 Karpenter가 `system` 노드그룹에 의존하므로 별도 단계 불필요.

```bash
# 1단계: EKS까지 (system 노드그룹 + Karpenter IRSA 포함)
terraform apply \
  -target=module.networking \
  -target=module.rds \
  -target=module.elasticache \
  -target=module.sqs \
  -target=module.s3 \
  -target=module.eks \   # 내부적으로 system 노드그룹 + Karpenter Helm + NodePool 순서로 실행됨
  -target=module.secrets

# 2단계: Helm 사용 모듈 (EKS endpoint 확보 후)
terraform apply \
  -target=module.alb \
  -target=module.celery \
  -target=module.argocd

# 3단계: 나머지 (동일)
terraform apply \
  -target=module.lambda \
  -target=module.step_functions \
  -target=module.eventbridge \
  -target=module.waf_cdn \
  -target=module.dns \
  -target=module.monitoring \
  -target=module.bedrock

# aws-auth 업데이트 (기존 팀원 + Karpenter Node Role 추가)
aws eks update-kubeconfig --name homelens-dev-eks --region eu-west-3
kubectl get configmap aws-auth -n kube-system -o yaml > ~/aws-auth.yaml
# → mapRoles에 karpenter-node-role ARN 추가
kubectl apply -f ~/aws-auth.yaml

# Karpenter 노드 프로비저닝 확인
kubectl get nodeclaim   # Karpenter가 생성한 노드 요청 확인
kubectl get nodes       # 실제 EC2 노드 확인
```

---

## 참고

- Karpenter 공식 문서: https://karpenter.sh/docs/
- EKS용 Karpenter 설치 가이드: https://karpenter.sh/docs/getting-started/getting-started-with-karpenter/
- Karpenter Helm chart 최신 버전 확인: `helm search repo karpenter --versions`
- 현재 EKS 버전: 1.35 (Karpenter v1.3.x 호환)
