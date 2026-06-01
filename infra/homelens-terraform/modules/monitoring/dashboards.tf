# ---------------------------------------------------------------------------
# Grafana 파이프라인 구간 지연시간 대시보드 (ConfigMap → Grafana sidecar 자동 로드)
# ---------------------------------------------------------------------------
resource "kubernetes_config_map" "pipeline_dashboard" {
  metadata {
    name      = "${var.project_name}-${var.env}-pipeline-dashboard"
    namespace = "monitoring"
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "pipeline-latency.json" = jsonencode({
      title       = "HomeLens Pipeline Latency — ${var.env}"
      uid         = "homelens-pipeline-${var.env}"
      schemaVersion = 30
      refresh     = "30s"
      time        = { from = "now-1h", to = "now" }

      panels = [
        # ── 패널 1: SQS 대기 지연 (SQS 적재 → Celery 소비) ──────────────
        {
          id    = 1
          title = "SQS 큐 대기 지연 (SQS→Celery) | 목표: 10s 이내"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 0 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum(rate(homelens_sqs_consume_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(rate(homelens_sqs_consume_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p95"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(rate(homelens_sqs_consume_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p99"
              refId        = "C"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "s"
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 5 },
                  { color = "red", value = 10 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 2: Bedrock 호출 지연 ─────────────────────────────────────
        {
          id    = 2
          title = "Bedrock InvokeModel 지연 | 목표: 30s 이내"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 0 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum(rate(homelens_bedrock_invoke_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(rate(homelens_bedrock_invoke_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p95"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(rate(homelens_bedrock_invoke_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p99"
              refId        = "C"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "s"
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 20 },
                  { color = "red", value = 30 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 3: DB 저장 지연 ──────────────────────────────────────────
        {
          id    = 3
          title = "DB 저장 지연 (INSERT→COMMIT) | 목표: 2s 이내"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 8 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum(rate(homelens_db_save_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(rate(homelens_db_save_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p95"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(rate(homelens_db_save_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p99"
              refId        = "C"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "s"
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 1 },
                  { color = "red", value = 2 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 4: 전체 파이프라인 지연 ──────────────────────────────────
        {
          id    = 4
          title = "전체 파이프라인 지연 (SQS→DB 완료) | 목표: 30s 이내"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 8 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum(rate(homelens_pipeline_total_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.90, sum(rate(homelens_pipeline_total_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p90"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(rate(homelens_pipeline_total_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p99"
              refId        = "C"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "s"
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 25 },
                  { color = "red", value = 30 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 5: 파이프라인 처리량 (성공/실패) ─────────────────────────
        {
          id    = 5
          title = "파이프라인 처리량 (성공 / 실패)"
          type  = "timeseries"
          gridPos = { h = 8, w = 24, x = 0, y = 16 }
          targets = [
            {
              expr         = "sum(rate(homelens_pipeline_total_duration_seconds_count[5m]))"
              legendFormat = "처리량 (건/s)"
              refId        = "A"
            },
            {
              expr         = "sum(rate(homelens_pipeline_errors_total[5m]))"
              legendFormat = "에러 (건/s)"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = { unit = "reqps" }
          }
          options = { tooltip = { mode = "multi" } }
        }
      ]
    })
  }

  depends_on = [helm_release.kube_prometheus_stack]
}

# ---------------------------------------------------------------------------
# CloudWatch 성능 대시보드 (기존 — ALB/SQS/RDS/Redis/Lambda)
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.env}-performance"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title  = "검색 자동완성 응답 시간 (목표: 500ms)"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix]
          ]
          period = 60
          stat   = "p95"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        properties = {
          title  = "가격 데이터 응답 시간 (목표: 2s)"
          region = var.aws_region
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix]
          ]
          period = 60
          stat   = "p95"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        properties = {
          title  = "SQS 큐 적체량"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "${var.project_name}-${var.env}-report-generation"],
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "${var.project_name}-${var.env}-news-summary"]
          ]
          period = 60
          stat   = "Average"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        properties = {
          title  = "RDS 읽기/쓰기 지연"
          region = var.aws_region
          metrics = [
            ["AWS/RDS", "ReadLatency", "DBInstanceIdentifier", "${var.project_name}-${var.env}-postgres"],
            ["AWS/RDS", "WriteLatency", "DBInstanceIdentifier", "${var.project_name}-${var.env}-postgres"]
          ]
          period = 60
          stat   = "Average"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        properties = {
          title  = "Redis 캐시 히트율"
          region = var.aws_region
          metrics = [
            ["AWS/ElastiCache", "CacheHits", "ReplicationGroupId", "${var.project_name}-${var.env}-redis"],
            ["AWS/ElastiCache", "CacheMisses", "ReplicationGroupId", "${var.project_name}-${var.env}-redis"]
          ]
          period = 60
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        properties = {
          title  = "Lambda 에러율"
          region = var.aws_region
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project_name}-${var.env}-news-collector"],
            ["AWS/Lambda", "Errors", "FunctionName", "${var.project_name}-${var.env}-molit-price-ingest"]
          ]
          period = 60
          stat   = "Sum"
          view   = "timeSeries"
        }
      }
    ]
  })
}