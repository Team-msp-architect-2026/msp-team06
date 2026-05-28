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

echo "=== Ingress 먼저 삭제 (ALB Controller가 finalizer 처리하는 동안) ==="
kubectl delete ingress homelens-ingress -n homelens 2>/dev/null || true

echo "=== Helm release 정리 (없으면 무시) ==="
helm uninstall argocd -n argocd 2>/dev/null || true
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
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

echo "=== terraform destroy 1단계: Lambda 포함 상위 모듈 ==="
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
  -target=module.elasticache \
  -target=module.rds

echo "=== Lambda VPC ENI 정리 대기 (Lambda를 VPC에 배치했으므로 AWS가 ENI를 비동기로 삭제) ==="
echo "    networking destroy 전 60초 대기..."
sleep 60

echo "=== terraform destroy 2단계: networking ==="
terraform destroy \
  -target=module.networking
