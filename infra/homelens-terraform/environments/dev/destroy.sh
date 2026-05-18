#!/bin/bash
set -e

echo "=== EKS kubeconfig 업데이트 ==="
aws eks update-kubeconfig --name homelens-dev-eks --region eu-west-3 2>/dev/null || true

echo "=== Helm release 정리 (없으면 무시) ==="
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
helm uninstall keda -n keda 2>/dev/null || true

echo "=== Terraform state에서 Helm 항목 제거 (state에만 있고 Helm에 없는 경우) ==="
terraform state rm module.alb.helm_release.alb_controller 2>/dev/null || true
terraform state rm module.celery.helm_release.keda 2>/dev/null || true

echo "=== terraform destroy ==="
terraform destroy
