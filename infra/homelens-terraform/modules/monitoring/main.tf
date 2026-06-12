resource "aws_prometheus_workspace" "main" {
    alias = "${var.project_name}-${var.env}"

    tags = { Env = var.env}
}

# ---------------------------------------------------------------------------
# kube-prometheus-stack — Prometheus + Grafana (EKS Helm)
# ---------------------------------------------------------------------------
resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = var.prometheus_stack_version
  namespace  = "monitoring"

  create_namespace = true
  timeout          = 900

  values = [
    yamlencode({
      prometheus = {
        prometheusSpec = {
          # homelens 네임스페이스 pod를 annotation 기반으로 자동 scrape
          additionalScrapeConfigs = [
            {
              job_name = "homelens-celery-metrics"
              kubernetes_sd_configs = [{
                role = "pod"
                namespaces = { names = ["homelens"] }
              }]
              relabel_configs = [
                # prometheus.io/scrape: "true" 인 pod만 수집
                {
                  source_labels = ["__meta_kubernetes_pod_annotation_prometheus_io_scrape"]
                  action        = "keep"
                  regex         = "true"
                },
                # prometheus.io/path 로 메트릭 경로 지정 (없으면 /metrics)
                {
                  source_labels = ["__meta_kubernetes_pod_annotation_prometheus_io_path"]
                  action        = "replace"
                  target_label  = "__metrics_path__"
                  regex         = "(.+)"
                },
                # prometheus.io/port 로 scrape 포트 지정
                {
                  source_labels = ["__address__", "__meta_kubernetes_pod_annotation_prometheus_io_port"]
                  action        = "replace"
                  regex         = "([^:]+)(?::\\d+)?;(\\d+)"
                  replacement   = "$1:$2"
                  target_label  = "__address__"
                },
                # pod label을 Prometheus label로 복사
                {
                  action = "labelmap"
                  regex  = "__meta_kubernetes_pod_label_(.+)"
                },
                {
                  source_labels = ["__meta_kubernetes_namespace"]
                  action        = "replace"
                  target_label  = "kubernetes_namespace"
                },
                {
                  source_labels = ["__meta_kubernetes_pod_name"]
                  action        = "replace"
                  target_label  = "kubernetes_pod_name"
                },
                # process 라벨: app=celery-worker → process=celery, app=fastapi → process=fastapi
                # PromQL에서 {process="celery"}/{process="fastapi"} 로 두 프로세스를 명확히 구분
                {
                  source_labels = ["__meta_kubernetes_pod_label_app"]
                  action        = "replace"
                  target_label  = "process"
                  regex         = "celery-.*"
                  replacement   = "celery"
                },
                {
                  source_labels = ["__meta_kubernetes_pod_label_app"]
                  action        = "replace"
                  target_label  = "process"
                  regex         = "(fastapi)"
                  replacement   = "$1"
                }
              ]
            }
          ]
          # 셀프 모니터링 — Prometheus 자체 메트릭도 수집
          podMonitorSelectorNilUsesHelmValues     = false
          serviceMonitorSelectorNilUsesHelmValues = false
        }
      }

      grafana = {
        adminPassword = var.grafana_admin_password
        sidecar = {
          dashboards = {
            enabled         = true
            label           = "grafana_dashboard"
            labelValue      = "1"
            searchNamespace = "monitoring"
          }
        }
        service = {
          type = "ClusterIP"
        }
      }

      # Alertmanager — Slack 알림 연동 (모든 환경 활성화)
      # webhook URL은 K8s Secret "homelens-slack-webhook" -n monitoring 에 저장
      # config는 infra/k8s/alertmanager-config.yaml 로 별도 관리 (Secret 직접 apply)
      alertmanager = {
        enabled = true
        alertmanagerSpec = {
          secrets = ["homelens-slack-webhook"]
        }
      }
    })
  ]
}

# ---------------------------------------------------------------------------
# CloudWatch Log Group — EKS 컨테이너 로그 (Fluent Bit → CloudWatch)
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "eks_application" {
  name              = "/aws/containerinsights/${var.eks_cluster_name}/application"
  retention_in_days = var.env == "prod" ? 90 : 30

  tags = { Env = var.env }
}

# ---------------------------------------------------------------------------
# EKS Addon — amazon-cloudwatch-observability
# Fluent Bit(로그 수집) + CloudWatch Agent(메트릭) 자동 설치
# 노드 IAM 역할에 CloudWatchAgentServerPolicy 이미 부착 → 추가 IAM 불필요
# ---------------------------------------------------------------------------
resource "aws_eks_addon" "cloudwatch_observability" {
  cluster_name = var.eks_cluster_name
  addon_name   = "amazon-cloudwatch-observability"

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = { Env = var.env }

  depends_on = [aws_cloudwatch_log_group.eks_application]
}

resource "aws_xray_group" "main" {
    group_name      = "${var.project_name}-${var.env}"
    filter_expression = "service(\"${var.project_name}-${var.env}\")"

    tags = { Env = var.env}
}


resource "aws_xray_sampling_rule" "pipeline" {
    rule_name    = "${var.project_name}-${var.env}-pipeline"
    priority     = 1000
    version      = 1
    reservoir_size = 5
    fixed_rate   = 0.05
    url_path     = "*"
    host         = "*"
    http_method  = "*"
    service_type = "*"
    service_name = "${var.project_name}-${var.env}-*"
    resource_arn = "*"

    tags = { Env = var.env }

}

resource "aws_cloudwatch_metric_alarm" "sqs_depth" {
    alarm_name        = "${var.project_name}-${var.env}-sqs-depth"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods = 2
    metric_name = "ApproximateNumberOfMessagesVisible"
    namespace   = "AWS/SQS"
    period      = 60
    statistic   = "Average"
    threshold = 100
    alarm_description = "SQS 큐 적체량 100개 초과"

    dimensions  = {
        QueueName = "${var.project_name}-${var.env}-report-generation"
    
    }
    
    tags = { Env = var.env }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
    alarm_name          = "${var.project_name}-${var.env}-lambda-errors"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods = 2
    metric_name = "Errors"
    namespace = "AWS/Lambda"
    period    = 60
    statistic = "Sum"
    threshold = 5
    alarm_description = "Lambda 에러 5회 초과"

    tags = { Env = var.env }
}
  
resource "aws_cloudwatch_metric_alarm" "rds_latency"{
  alarm_name           = "${var.project_name}-${var.env}-rds-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 2
  metric_name          = "ReadLatency"
  namespace            = "AWS/RDS"
  period               = 60
  statistic            = "Average"
  threshold            = 0.002
  alarm_description    = "RDS 읽기 지연 2ms 초과"
  
  dimensions = {
    DBInstanceIdentifier = "${var.project_name}-${var.env}-postgre"
  }


  tags = { Env = var.env }
} 

