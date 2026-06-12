locals {
  name_prefix = "${var.project_name}-${var.environment}"
  namespace   = "homelens"
  app_label   = "celery-worker"
}

# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------
resource "kubernetes_namespace" "homelens" {
  metadata {
    name = local.namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

# ---------------------------------------------------------------------------
# ServiceAccount — IRSA 어노테이션으로 celery-worker-role 바인딩
# ---------------------------------------------------------------------------
resource "kubernetes_service_account" "celery_worker" {
  metadata {
    name      = "celery-worker"
    namespace = kubernetes_namespace.homelens.metadata[0].name

    annotations = {
      "eks.amazonaws.com/role-arn" = var.celery_worker_role_arn
    }
  }
}

# ---------------------------------------------------------------------------
# KEDA Operator — Helm (kedacore/charts)
# ScaledObject CRD 설치 전에 반드시 먼저 배포
# ---------------------------------------------------------------------------
resource "helm_release" "keda" {
  name       = "keda"
  repository = "https://kedacore.github.io/charts"
  chart      = "keda"
  version    = "2.14.2"
  namespace  = "keda"

  create_namespace = true

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = var.keda_operator_role_arn
  }
  set {
    name  = "podIdentity.provider"
    value = "aws"
  }

  depends_on = [kubernetes_namespace.homelens]
}

# ---------------------------------------------------------------------------
# KEDA ScaledObject — null_resource + kubectl
# kubernetes_manifest은 plan 단계에서 CRD 검증 → KEDA 설치 전 실패하므로 kubectl 사용
# ---------------------------------------------------------------------------
resource "null_resource" "keda_scaled_object" {
  triggers = {
    queue_url      = var.sqs_queue_url
    aws_region     = var.aws_region
    environment    = var.environment
    max_replicas   = var.environment == "prod" ? 10 : 25
    min_replicas   = 1
    cooldown_period = 300
  }

  provisioner "local-exec" {
    command = <<-EOF
      aws eks update-kubeconfig --name ${var.eks_cluster_name} --region ${var.aws_region}
      kubectl apply -f - <<YAML
      apiVersion: keda.sh/v1alpha1
      kind: ScaledObject
      metadata:
        name: ${local.app_label}-scaledobject
        namespace: ${local.namespace}
      spec:
        scaleTargetRef:
          name: celery-worker
        minReplicaCount: 1
        maxReplicaCount: ${var.environment == "prod" ? 10 : 25}
        cooldownPeriod: 300
        triggers:
        - type: aws-sqs-queue
          metadata:
            queueURL: ${var.sqs_queue_url}
            queueLength: "5"
            awsRegion: ${var.aws_region}
            identityOwner: operator
      YAML
    EOF
  }

  depends_on = [helm_release.keda]
}
