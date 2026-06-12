#!/bin/bash
set -e

echo "=== EKS kubeconfig 업데이트 ==="
aws eks update-kubeconfig --name homelens-dev-eks --region eu-west-3 2>/dev/null || true

# ---------------------------------------------------------------------------
# Namespace finalizer 강제 제거 함수
# Terminating 상태에서 멈춘 namespace의 finalizer를 API로 직접 제거
# ---------------------------------------------------------------------------
force_delete_namespace() {
  local ns=$1
  if kubectl get namespace "$ns" 2>/dev/null | grep -q "Terminating"; then
    echo "  → $ns namespace finalizer 강제 제거 중..."
    kubectl get namespace "$ns" -o json | \
      python3 -c "import sys,json; d=json.load(sys.stdin); d['spec']['finalizers']=[]; print(json.dumps(d))" | \
      kubectl replace --raw "/api/v1/namespaces/$ns/finalize" -f - 2>/dev/null || true
  fi
}

echo "=== ArgoCD Application finalizer 제거 (먼저 제거 안 하면 argocd namespace가 Terminating 고착) ==="
kubectl patch applicationset homelens -n argocd \
  --type=json -p='[{"op":"remove","path":"/metadata/finalizers"}]' 2>/dev/null || true
kubectl patch application homelens-dev -n argocd \
  --type=json -p='[{"op":"remove","path":"/metadata/finalizers"}]' 2>/dev/null || true

echo "=== Ingress 삭제 후 ALB 완전 제거 대기 ==="
# Ingress 삭제 → ALB Controller가 ALB를 삭제 → ENI 해제 순서로 진행
# Controller를 먼저 지우면 ALB가 고아 상태로 남아 서브넷 삭제 불가
kubectl delete ingress homelens-ingress -n homelens 2>/dev/null || true

# ALB Controller가 ALB를 삭제할 때까지 대기 (최대 5분)
echo "    ALB 삭제 완료 대기 중..."
for i in $(seq 1 30); do
  ALB_COUNT=$(aws elbv2 describe-load-balancers --region eu-west-3 \
    --query 'length(LoadBalancers[?contains(LoadBalancerName, `k8s-homelens`)])' \
    --output text 2>/dev/null || echo "0")
  if [ "$ALB_COUNT" = "0" ]; then
    echo "    ALB 삭제 완료."
    break
  fi
  echo "    ALB ${ALB_COUNT}개 아직 삭제 중... (${i}/30, 10초 대기)"
  if [ "$i" = "30" ]; then
    echo "[ERROR] ALB가 5분 내에 삭제되지 않았습니다. AWS 콘솔에서 수동 삭제 후 재실행하세요."
    exit 1
  fi
  sleep 10
done

echo "=== Helm release 정리 (없으면 무시) ==="
helm uninstall argocd -n argocd 2>/dev/null || true
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
helm uninstall cluster-autoscaler -n kube-system 2>/dev/null || true
helm uninstall keda -n keda 2>/dev/null || true

echo "=== Namespace finalizer 강제 제거 (Terminating 고착 시 자동 해제) ==="
for ns in argocd homelens keda; do
  kubectl delete namespace "$ns" --timeout=20s 2>/dev/null || true
  force_delete_namespace "$ns"
done

echo "=== Terraform state에서 Helm 항목 제거 (state에만 있고 Helm에 없는 경우) ==="
terraform state rm module.argocd.helm_release.argocd 2>/dev/null || true
terraform state rm module.alb.helm_release.alb_controller 2>/dev/null || true
terraform state rm module.celery.helm_release.keda 2>/dev/null || true
terraform state rm module.eks.helm_release.cluster_autoscaler 2>/dev/null || true

echo "=== terraform destroy 1단계: Lambda 포함 상위 모듈 (RDS/S3/networking 제외) ==="
terraform destroy \
  -target=module.argocd \
  -target=module.bedrock \
  -target=module.monitoring \
  -target=module.dns \
  -target=module.waf_cdn \
  -target=module.eventbridge \
  -target=module.step_functions \
  -target=module.lambda \
  -target=module.celery \
  -target=module.alb \
  -target=module.secrets \
  -target=module.eks \
  -target=module.sqs \
  -target=module.elasticache

echo "=== terraform destroy 2단계: NAT Gateway + EIP 먼저 삭제 ==="
# 서브넷/IGW 삭제 전에 NAT GW와 EIP를 완전히 제거해야 DependencyViolation 방지
# Terraform이 직접 관리하므로 별도 CLI 권한 불필요
terraform destroy \
  -target=module.networking.aws_nat_gateway.main \
  -target=module.networking.aws_eip.nat

echo "=== NAT Gateway 완전 삭제 대기 (AWS가 비동기로 처리) ==="
# NAT GW 삭제는 AWS 내부적으로 5~15분 소요
# describe는 read 권한만 필요 — SCP 제한 없이 동작
VPC_ID=$(aws ec2 describe-vpcs --region eu-west-3 \
  --filters "Name=tag:Name,Values=homelens-dev-vpc" \
  --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "")

if [ -n "$VPC_ID" ] && [ "$VPC_ID" != "None" ]; then
  for i in $(seq 1 40); do
    REMAINING=$(aws ec2 describe-nat-gateways --region eu-west-3 \
      --filter "Name=vpc-id,Values=$VPC_ID" \
                "Name=state,Values=available,pending,deleting" \
      --query 'length(NatGateways)' --output text 2>/dev/null || echo "0")
    if [ "$REMAINING" = "0" ]; then
      echo "    NAT Gateway 삭제 완료."
      break
    fi
    echo "    NAT Gateway ${REMAINING}개 아직 삭제 중... (${i}/40, 20초 대기)"
    sleep 20
  done
fi

echo "=== networking (VPC/서브넷/SG) 은 RDS가 사용 중이므로 제거하지 않습니다 ==="
