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
  # 노드 추가 후 스케일 다운 유예 시간 (기본 10분 → 5분)
  set {
    name  = "extraArgs.scale-down-delay-after-add"
    value = "5m"
  }
  # Celery task 처리 중 노드 제거 방지 — 유휴 판정 대기 시간
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
