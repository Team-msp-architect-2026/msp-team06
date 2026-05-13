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
# Deployment — Celery worker
# worker 노드그룹에만 스케줄링 (nodeSelector + toleration)
# ---------------------------------------------------------------------------
resource "kubernetes_deployment" "celery_worker" {
  metadata {
    name      = local.app_label
    namespace = kubernetes_namespace.homelens.metadata[0].name
    labels = {
      app = local.app_label
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = { app = local.app_label }
    }

    template {
      metadata {
        labels = { app = local.app_label }
      }

      spec {
        service_account_name = kubernetes_service_account.celery_worker.metadata[0].name

        # worker 노드그룹에만 배치 (terraform_instructions.md §4-4)
        node_selector = { role = "worker" }

        toleration {
          key      = "dedicated"
          value    = "worker"
          operator = "Equal"
          effect   = "NoSchedule"
        }

        container {
          name              = "celery-worker"
          image             = var.celery_image
          image_pull_policy = "Always"

          command = ["celery", "-A", "app.worker", "worker", "--loglevel=info", "--concurrency=4"]

          env {
            name  = "CELERY_BROKER_URL"
            value = "sqs://"
          }
          env {
            name  = "SQS_QUEUE_URL"
            value = var.sqs_queue_url
          }
          env {
            name  = "AWS_REGION"
            value = var.aws_region
          }
          env {
            name  = "ENVIRONMENT"
            value = var.environment
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1000m"
              memory = "1Gi"
            }
          }

          liveness_probe {
            exec {
              command = ["celery", "-A", "app.worker", "inspect", "ping", "-d", "celery@$HOSTNAME"]
            }
            initial_delay_seconds = 30
            period_seconds        = 60
            timeout_seconds       = 10
            failure_threshold     = 3
          }
        }
      }
    }
  }

  lifecycle {
    # 이미지 태그는 CI/CD에서 관리
    ignore_changes = [
      spec[0].template[0].spec[0].container[0].image,
      spec[0].replicas,
    ]
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
# KEDA ScaledObject — report-generation-queue 깊이 기준 자동 스케일
# KEDA 오퍼레이터가 클러스터에 설치된 후 적용됨
# ---------------------------------------------------------------------------
resource "kubernetes_manifest" "keda_scaled_object" {
  manifest = {
    apiVersion = "keda.sh/v1alpha1"
    kind       = "ScaledObject"

    metadata = {
      name      = "${local.app_label}-scaledobject"
      namespace = local.namespace
    }

    spec = {
      scaleTargetRef = {
        name = kubernetes_deployment.celery_worker.metadata[0].name
      }

      minReplicaCount = var.environment == "prod" ? 1 : 0
      maxReplicaCount = var.environment == "prod" ? 10 : 4
      cooldownPeriod  = 60

      triggers = [
        {
          type = "aws-sqs-queue"
          metadata = {
            queueURL                = var.sqs_queue_url
            queueLength             = "5"
            awsRegion               = var.aws_region
            identityOwner           = "operator"
          }
        }
      ]
    }
  }

  depends_on = [kubernetes_deployment.celery_worker]
}
