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
              expr         = "histogram_quantile(0.50, sum(increase(homelens_sqs_consume_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(increase(homelens_sqs_consume_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p95"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(increase(homelens_sqs_consume_duration_seconds_bucket[1h])) by (le))"
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
              expr         = "histogram_quantile(0.50, sum(increase(homelens_bedrock_invoke_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(increase(homelens_bedrock_invoke_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p95"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(increase(homelens_bedrock_invoke_duration_seconds_bucket[1h])) by (le))"
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
              expr         = "histogram_quantile(0.50, sum(increase(homelens_db_save_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(increase(homelens_db_save_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p95"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(increase(homelens_db_save_duration_seconds_bucket[1h])) by (le))"
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
        # 측정: SQS 전송(sent_at) or 태스크 시작 → news/infra/price 수집 → Bedrock → DB 완료
        # yellow=30s: 이상적 목표, red=45s: 알림 기준(p90 > 35s)
        {
          id    = 4
          title = "전체 파이프라인 지연 (SQS→DB 완료) | 목표 p90: 35s 이내"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 8 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum(increase(homelens_pipeline_total_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.90, sum(increase(homelens_pipeline_total_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p90 (알림 기준)"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(increase(homelens_pipeline_total_duration_seconds_bucket[1h])) by (le))"
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
                  { color = "yellow", value = 30 },
                  { color = "red", value = 45 }
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
              expr         = "sum(increase(homelens_pipeline_total_duration_seconds_count[1h]))"
              legendFormat = "처리량 (건/s)"
              refId        = "A"
            },
            {
              expr         = "sum(increase(homelens_pipeline_errors_total[1h]))"
              legendFormat = "에러 (건/s)"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = { unit = "reqps" }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 6: Celery pod CPU 사용량 ─────────────────────────────────
        # 실제 사용량(actual) vs request(250m) / limit(1000m) 비교
        {
          id    = 6
          title = "Celery Pod CPU 사용량 | request=250m / limit=1000m"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 24 }
          targets = [
            {
              expr         = "rate(container_cpu_usage_seconds_total{namespace=\"homelens\",container=\"celery-worker\"}[2m]) * 1000"
              legendFormat = "{{pod}}"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "short"
              custom = { axisLabel = "mCPU" }
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 500 },
                  { color = "red", value = 900 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 7: Celery pod 메모리 사용량 ──────────────────────────────
        # working_set 기준 / request=512Mi / limit=1024Mi
        {
          id    = 7
          title = "Celery Pod 메모리 사용량 (Mi) | request=512Mi / limit=1024Mi"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 24 }
          targets = [
            {
              expr         = "container_memory_working_set_bytes{namespace=\"homelens\",container=\"celery-worker\"} / 1048576"
              legendFormat = "{{pod}}"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "short"
              custom = { axisLabel = "Mi" }
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 768 },
                  { color = "red", value = 950 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 8: Worker 노드 CPU 사용률 ────────────────────────────────
        # Celery pod가 실행 중인 노드만 표시 (kube_pod_info join)
        {
          id    = 8
          title = "Worker 노드 CPU 사용률 (%)"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 32 }
          targets = [
            {
              expr         = "(1 - avg by (nodename) (rate(node_cpu_seconds_total{mode=\"idle\",job=\"node-exporter\"}[2m]) * on(instance) group_left(nodename) node_uname_info)) * 100 * on(nodename) group_left() label_replace(max by (node) (kube_pod_info{namespace=\"homelens\",pod=~\"celery-worker.*\"}),\"nodename\",\"$1\",\"node\",\"(.*)\")"
              legendFormat = "CPU %"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "percent"
              min  = 0
              max  = 100
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 70 },
                  { color = "red", value = 85 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "single" } }
        },

        # ── 패널 9: Worker 노드 메모리 사용률 ─────────────────────────────
        # Celery pod가 실행 중인 노드만 표시 (kube_pod_info join)
        {
          id    = 9
          title = "Worker 노드 메모리 사용률 (%)"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 32 }
          targets = [
            {
              expr         = "(1 - avg by (nodename) (node_memory_MemAvailable_bytes{job=\"node-exporter\"} * on(instance) group_left(nodename) node_uname_info) / avg by (nodename) (node_memory_MemTotal_bytes{job=\"node-exporter\"} * on(instance) group_left(nodename) node_uname_info)) * 100 * on(nodename) group_left() label_replace(max by (node) (kube_pod_info{namespace=\"homelens\",pod=~\"celery-worker.*\"}),\"nodename\",\"$1\",\"node\",\"(.*)\")"
              legendFormat = "Memory %"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "percent"
              min  = 0
              max  = 100
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 70 },
                  { color = "red", value = 85 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "single" } }
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

# ---------------------------------------------------------------------------
# Grafana 사용자 접속 시나리오 대시보드 (HTTP 응답시간 · 에러율 · DB 쿼리 지연)
# ---------------------------------------------------------------------------
resource "kubernetes_config_map" "user_access_dashboard" {
  metadata {
    name      = "${var.project_name}-${var.env}-user-access-dashboard"
    namespace = "monitoring"
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "user-access.json" = jsonencode({
      title         = "HomeLens User Access — ${var.env}"
      uid           = "homelens-user-access-${var.env}"
      schemaVersion = 30
      refresh       = "30s"
      time          = { from = "now-1h", to = "now" }

      panels = [
        # ── 패널 1: 엔드포인트별 요청 처리량 ────────────────────────────────
        {
          id      = 1
          title   = "요청 처리량 (req/min) — 엔드포인트별"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 0 }
          targets = [
            {
              expr         = "sum by (endpoint) (increase(homelens_http_requests_total[1m]))"
              legendFormat = "{{endpoint}}"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "reqpm"
              color = { mode = "palette-classic" }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 2: 에러율 (4xx + 5xx) ───────────────────────────────────
        {
          id      = 2
          title   = "에러율 (%) | 알림 기준: 5% 초과 5분 지속"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 0 }
          targets = [
            {
              expr         = "100 * (sum(increase(homelens_http_errors_total[5m])) or vector(0)) / (sum(increase(homelens_http_requests_total[5m])) + 1)"
              legendFormat = "에러율 %"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "percent"
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 1 },
                  { color = "red", value = 5 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "single" } }
        },

        # ── 패널 3: HTTP 응답시간 분위수 ─────────────────────────────────
        {
          id      = 3
          title   = "HTTP 응답시간 분위수 | 목표: p95 2s 이내"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 8 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum(increase(homelens_http_request_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(increase(homelens_http_request_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p95"
              refId        = "B"
            },
            {
              expr         = "histogram_quantile(0.99, sum(increase(homelens_http_request_duration_seconds_bucket[5m])) by (le))"
              legendFormat = "p99"
              refId        = "C"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "s"
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

        # ── 패널 4: apt_seq DB 쿼리 지연 ─────────────────────────────────
        {
          id      = 4
          title   = "apt_seq DB 쿼리 지연 | 목표: p95 500ms 이내"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 8 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum by (le, query_type) (increase(homelens_db_query_duration_seconds_bucket[5m])))"
              legendFormat = "p50 {{query_type}}"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum by (le, query_type) (increase(homelens_db_query_duration_seconds_bucket[5m])))"
              legendFormat = "p95 {{query_type}}"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "s"
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 0.25 },
                  { color = "red", value = 0.5 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 5: 엔드포인트별 응답시간 히트맵 (현재 p95) ──────────────
        {
          id      = 5
          title   = "엔드포인트별 p95 응답시간 — 현재값"
          type    = "bargauge"
          gridPos = { h = 8, w = 24, x = 0, y = 16 }
          targets = [
            {
              expr         = "histogram_quantile(0.95, sum by (le, endpoint) (increase(homelens_http_request_duration_seconds_bucket[5m])))"
              legendFormat = "{{endpoint}}"
              refId        = "A"
              instant      = true
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "s"
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "yellow", value = 1 },
                  { color = "red", value = 2 }
                ]
              }
            }
          }
          options = {
            orientation  = "horizontal"
            reduceOptions = { calcs = ["lastNotNull"] }
          }
        },

        # ── 패널 6: 외부 API fallback 호출 횟수 ──────────────────────────
        {
          id      = 6
          title   = "외부 API fallback 호출 횟수 (5분) — 높으면 DB 데이터 부족 의미"
          type    = "timeseries"
          gridPos = { h = 8, w = 24, x = 0, y = 24 }
          targets = [
            {
              expr         = "increase(homelens_external_api_calls_total[5m])"
              legendFormat = "{{api_type}}"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "short"
              color = { fixedColor = "orange", mode = "fixed" }
              thresholds = {
                steps = [
                  { color = "green", value = null },
                  { color = "orange", value = 1 },
                  { color = "red", value = 5 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        }
      ]
    })
  }

  depends_on = [helm_release.kube_prometheus_stack]
}

# ---------------------------------------------------------------------------
# Grafana 워커 프로세스 리소스 변동률 대시보드
# homelens_worker_cpu_percent / homelens_worker_memory_rss_bytes (psutil Gauge)
# → deriv()로 분당 변동량을 시각화해 태스크 실행 중 급등 구간을 파악
# ---------------------------------------------------------------------------
resource "kubernetes_config_map" "worker_resource_dashboard" {
  metadata {
    name      = "${var.project_name}-${var.env}-worker-resource-dashboard"
    namespace = "monitoring"
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "worker-resource.json" = jsonencode({
      title         = "HomeLens Worker Resource — ${var.env}"
      uid           = "homelens-worker-resource-${var.env}"
      schemaVersion = 30
      refresh       = "15s"
      time          = { from = "now-30m", to = "now" }

      panels = [
        # ── 패널 1: CPU 사용률 현재값 ────────────────────────────────────────
        {
          id    = 1
          title = "Worker CPU 사용률 (%) | 15초 샘플"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 0 }
          targets = [
            {
              expr         = "homelens_worker_cpu_percent"
              legendFormat = "{{pod}} CPU %"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "percent"
              min  = 0
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 60 },
                  { color = "red",    value = 85 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 2: 메모리 RSS 현재값 ────────────────────────────────────────
        {
          id    = 2
          title = "Worker 메모리 RSS (MB) | 15초 샘플"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 0 }
          targets = [
            {
              expr         = "homelens_worker_memory_rss_bytes / 1048576"
              legendFormat = "{{pod}} RSS MB"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit = "short"
              custom = { axisLabel = "MB" }
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 700 },
                  { color = "red",    value = 950 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 3: CPU 변동률 (%/분) ─────────────────────────────────────────
        # deriv()는 초당 변화량 → × 60 으로 분당 변화량으로 환산
        # 양수: CPU 급증 구간(Bedrock 호출), 음수: 태스크 종료 후 하강 구간
        {
          id    = 4
          title = "CPU 변동률 (%/분) — Bedrock 호출 구간에서 급등 예상"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 8 }
          targets = [
            {
              expr         = "deriv(homelens_worker_cpu_percent[5m]) * 60"
              legendFormat = "{{pod}} Δ CPU %/min"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "short"
              custom = { axisLabel = "%/min" }
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 20 },
                  { color = "red",    value = 40 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 4: 메모리 변동률 (MB/분) ────────────────────────────────────
        # 양수 지속: 메모리 누수 의심, 음수: GC 해제 구간
        {
          id    = 5
          title = "메모리 변동률 (MB/분) — 양수 지속 시 누수 의심"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 8 }
          targets = [
            {
              expr         = "deriv(homelens_worker_memory_rss_bytes[5m]) / 1048576 * 60"
              legendFormat = "{{pod}} Δ MB/min"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "short"
              custom = { axisLabel = "MB/min" }
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 50 },
                  { color = "red",    value = 100 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        }
      ]
    })
  }

  depends_on = [helm_release.kube_prometheus_stack]
}