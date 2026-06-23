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
          title = "Bedrock InvokeModel 지연 | 목표: 45s 이내"
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
                  { color = "yellow", value = 30 },
                  { color = "red", value = 45 }
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
        # yellow=45s: Bedrock 단독 목표, red=60s: 전체 파이프라인 알림 기준(p90 > 60s)
        {
          id    = 4
          title = "전체 파이프라인 지연 (SQS→DB 완료) | 목표 p90: 60s 이내"
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
                  { color = "yellow", value = 45 },
                  { color = "red", value = 60 }
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
              expr         = "100 * (sum(increase(homelens_http_errors_total[5m])) or vector(0)) / ((sum(increase(homelens_http_requests_total[5m])) or vector(0)) + 1)"
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
# Grafana 병목 격리 대시보드
# 행 1: 비동기 AI 처리 구간 (Celery & Bedrock) — process="celery" 라벨로 격리
# 행 2: 동기 데이터 조회 구간 (FastAPI & Redis & RDS) — process="fastapi" 라벨로 격리
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
      title         = "HomeLens 병목 격리 — ${var.env}"
      uid           = "homelens-worker-resource-${var.env}"
      schemaVersion = 30
      refresh       = "15s"
      time          = { from = "now-30m", to = "now" }

      panels = [

        # ════════════════════════════════════════════════════════════════════
        # 행 1 — 비동기 AI 처리 구간 (Celery & Bedrock)
        # 이 구간이 느리면: SQS 대기열 증가 + Bedrock 지연 동시 확인
        # 스케일링 대응: KEDA가 SQS 큐 기준으로 Celery 워커 자동 증설
        # ════════════════════════════════════════════════════════════════════
        {
          id         = 1
          type       = "row"
          title      = "비동기 AI 처리 구간 — Celery & Bedrock  (병목 시: SQS 대기 ↑ + Bedrock 지연 ↑)"
          collapsed  = false
          gridPos    = { h = 1, w = 24, x = 0, y = 0 }
        },

        # ── 패널 1-1: Celery Worker CPU % (psutil 15초 샘플) ─────────────
        {
          id    = 2
          title = "Celery Worker CPU % | process=celery | 15초 샘플"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 1 }
          targets = [
            {
              expr         = "homelens_worker_cpu_percent{process=\"celery\"}"
              legendFormat = "{{kubernetes_pod_name}} CPU %"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "percent"
              min   = 0
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

        # ── 패널 1-2: Celery Worker 메모리 RSS ───────────────────────────
        {
          id    = 3
          title = "Celery Worker 메모리 RSS (MB) | process=celery | 15초 샘플"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 1 }
          targets = [
            {
              expr         = "homelens_worker_memory_rss_bytes{process=\"celery\"} / 1048576"
              legendFormat = "{{kubernetes_pod_name}} RSS MB"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit   = "short"
              custom = { axisLabel = "MB" }
              color  = { mode = "palette-classic" }
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

        # ── 패널 1-3: Bedrock 호출 대기시간 ─────────────────────────────
        # p95 > 45s 이면 Bedrock 자체 병목 — Celery 증설보다 요청 조절 필요
        {
          id    = 4
          title = "Bedrock 호출 대기시간 (p50 / p95) | 목표: p95 45s 이내"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 9 }
          targets = [
            {
              expr         = "histogram_quantile(0.50, sum(increase(homelens_bedrock_invoke_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p50"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.95, sum(increase(homelens_bedrock_invoke_duration_seconds_bucket[1h])) by (le))"
              legendFormat = "p95 (알림 기준)"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "s"
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 30 },
                  { color = "red",    value = 45 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 1-4: SQS 큐 대기열 ─────────────────────────────────────
        # 큐가 쌓이면 KEDA가 Celery 워커를 자동 스케일아웃 (최대 4개)
        # 큐 > 5 이상 지속 → 워커 증설 또는 Bedrock 지연 확인
        {
          id    = 5
          title = "SQS 큐 대기 메시지 수 | KEDA 스케일아웃 기준: 5건/워커"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 9 }
          targets = [
            {
              expr         = "homelens_sqs_queue_depth"
              legendFormat = "대기 메시지"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { fixedColor = "orange", mode = "fixed" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 5 },
                  { color = "red",    value = 20 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "single" } }
        },

        # ════════════════════════════════════════════════════════════════════
        # 행 2 — 동기 데이터 조회 구간 (FastAPI & Redis & RDS)
        # 이 구간이 느리면: Redis 미스 급증 → RDS 쿼리 지연 동시 확인
        # 스케일링 대응: FastAPI 레플리카 증설 또는 Redis TTL/캐싱 전략 조정
        # ════════════════════════════════════════════════════════════════════
        {
          id         = 10
          type       = "row"
          title      = "동기 데이터 조회 구간 — FastAPI & Redis & RDS  (병목 시: 캐시 미스 ↑ + DB 지연 ↑)"
          collapsed  = false
          gridPos    = { h = 1, w = 24, x = 0, y = 17 }
        },

        # ── 패널 2-1: FastAPI CPU % (cAdvisor 컨테이너 메트릭) ──────────
        # psutil 대신 cAdvisor 사용 — FastAPI는 싱글 프로세스 비동기 루프
        {
          id    = 11
          title = "FastAPI CPU % | process=fastapi | cAdvisor"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 18 }
          targets = [
            {
              expr         = "rate(container_cpu_usage_seconds_total{namespace=\"homelens\",container=\"fastapi\"}[2m]) * 100"
              legendFormat = "{{pod}} CPU %"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "percent"
              min   = 0
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

        # ── 패널 2-2: FastAPI 메모리 (cAdvisor) ─────────────────────────
        {
          id    = 12
          title = "FastAPI 메모리 (MB) | process=fastapi | cAdvisor"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 18 }
          targets = [
            {
              expr         = "container_memory_working_set_bytes{namespace=\"homelens\",container=\"fastapi\"} / 1048576"
              legendFormat = "{{pod}} Working Set MB"
              refId        = "A"
            }
          ]
          fieldConfig = {
            defaults = {
              unit   = "short"
              custom = { axisLabel = "MB" }
              color  = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 400 },
                  { color = "red",    value = 700 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 2-3: Redis 캐시 히트율 (%) ─────────────────────────────
        # 히트율 하락 = DB 부하 증가 예고 신호
        # cache_type 별(price/news/kapt) 분리 → 어떤 데이터가 캐시 효율 낮은지 파악
        {
          id    = 13
          title = "Redis 캐시 히트율 (%) — 하락 시 RDS 부하 증가 예고"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 26 }
          targets = [
            {
              expr         = "sum(rate(homelens_cache_hits_total[5m])) by (cache_type) / (sum(rate(homelens_cache_hits_total[5m])) by (cache_type) + sum(rate(homelens_cache_misses_total[5m])) by (cache_type) + 0.001) * 100"
              legendFormat = "{{cache_type}} 히트율 %"
              refId        = "A"
            },
            {
              expr         = "sum(rate(homelens_cache_misses_total[5m])) by (cache_type) * 60"
              legendFormat = "{{cache_type}} 미스 건/분"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "red",    value = null },
                  { color = "yellow", value = 70 },
                  { color = "green",  value = 90 }
                ]
              }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ── 패널 2-4: RDS 쿼리 응답시간 p95 ─────────────────────────────
        # Redis 캐시 미스 → RDS 쿼리 → 이 지연이 올라오면 DB 스케일 필요
        {
          id    = 14
          title = "RDS 쿼리 응답시간 p95 (ms) | query_type별 | 목표: 500ms 이내"
          type  = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 26 }
          targets = [
            {
              expr         = "histogram_quantile(0.95, sum(rate(homelens_db_query_duration_seconds_bucket[5m])) by (le, query_type)) * 1000"
              legendFormat = "{{query_type}} p95 ms"
              refId        = "A"
            },
            {
              expr         = "histogram_quantile(0.50, sum(rate(homelens_db_query_duration_seconds_bucket[5m])) by (le, query_type)) * 1000"
              legendFormat = "{{query_type}} p50 ms"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "short"
              custom = { axisLabel = "ms" }
              color = { mode = "palette-classic" }
              thresholds = {
                steps = [
                  { color = "green",  value = null },
                  { color = "yellow", value = 200 },
                  { color = "red",    value = 500 }
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
# Grafana 오토스케일링 통합 대시보드
# HPA (FastAPI) + KEDA (Celery Worker) + Cluster Autoscaler (Node) 한 화면
# ---------------------------------------------------------------------------
resource "kubernetes_config_map" "autoscaling_dashboard" {
  metadata {
    name      = "${var.project_name}-${var.env}-autoscaling-dashboard"
    namespace = "monitoring"
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "autoscaling.json" = jsonencode({
      title         = "HomeLens 오토스케일링 — ${var.env}"
      uid           = "homelens-autoscaling-${var.env}"
      schemaVersion = 30
      refresh       = "15s"
      time          = { from = "now-1h", to = "now" }

      panels = [

        # ════════════════════════════════════════════════════════════
        # 행 0 — 개요 Stat 패널 (현재 상태 한눈에)
        # ════════════════════════════════════════════════════════════
        {
          id      = 1
          title   = "FastAPI 현재 Pod 수"
          type    = "stat"
          gridPos = { h = 4, w = 4, x = 0, y = 0 }
          targets = [{
            expr    = "kube_horizontalpodautoscaler_status_current_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
            refId   = "A"
            instant = true
          }]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "thresholds" }
              thresholds = { steps = [
                { color = "green", value = null },
                { color = "yellow", value = 2 },
                { color = "red", value = 4 }
              ]}
            }
          }
          options = { reduceOptions = { calcs = ["lastNotNull"] }, colorMode = "background" }
        },

        {
          id      = 2
          title   = "FastAPI 목표 Pod 수 (HPA 계산)"
          type    = "stat"
          gridPos = { h = 4, w = 4, x = 4, y = 0 }
          targets = [{
            expr    = "kube_horizontalpodautoscaler_status_desired_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
            refId   = "A"
            instant = true
          }]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "thresholds" }
              thresholds = { steps = [
                { color = "green", value = null },
                { color = "yellow", value = 2 },
                { color = "red", value = 4 }
              ]}
            }
          }
          options = { reduceOptions = { calcs = ["lastNotNull"] }, colorMode = "background" }
        },

        {
          id      = 3
          title   = "FastAPI HPA 최대 Pod"
          type    = "stat"
          gridPos = { h = 4, w = 4, x = 8, y = 0 }
          targets = [{
            expr    = "kube_horizontalpodautoscaler_spec_max_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
            refId   = "A"
            instant = true
          }]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { fixedColor = "blue", mode = "fixed" }
            }
          }
          options = { reduceOptions = { calcs = ["lastNotNull"] }, colorMode = "value" }
        },

        {
          id      = 4
          title   = "Celery Worker 현재 Pod 수 (KEDA)"
          type    = "stat"
          gridPos = { h = 4, w = 4, x = 12, y = 0 }
          targets = [{
            expr    = "kube_deployment_status_replicas{deployment=\"celery-worker\", namespace=\"homelens\"}"
            refId   = "A"
            instant = true
          }]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "thresholds" }
              thresholds = { steps = [
                { color = "green", value = null },
                { color = "yellow", value = 5 },
                { color = "red", value = 15 }
              ]}
            }
          }
          options = { reduceOptions = { calcs = ["lastNotNull"] }, colorMode = "background" }
        },

        {
          id      = 5
          title   = "SQS 큐 깊이 (KEDA 트리거)"
          type    = "stat"
          gridPos = { h = 4, w = 4, x = 16, y = 0 }
          targets = [{
            expr    = "homelens_sqs_queue_depth"
            refId   = "A"
            instant = true
          }]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "thresholds" }
              thresholds = { steps = [
                { color = "green", value = null },
                { color = "yellow", value = 5 },
                { color = "red", value = 20 }
              ]}
            }
          }
          options = { reduceOptions = { calcs = ["lastNotNull"] }, colorMode = "background" }
        },

        {
          id      = 6
          title   = "전체 EKS 노드 수"
          type    = "stat"
          gridPos = { h = 4, w = 4, x = 20, y = 0 }
          targets = [{
            expr    = "count(kube_node_status_condition{condition=\"Ready\",status=\"true\"})"
            refId   = "A"
            instant = true
          }]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "thresholds" }
              thresholds = { steps = [
                { color = "green", value = null },
                { color = "yellow", value = 3 },
                { color = "red", value = 4 }
              ]}
            }
          }
          options = { reduceOptions = { calcs = ["lastNotNull"] }, colorMode = "background" }
        },

        # ════════════════════════════════════════════════════════════
        # 행 1 — HPA: FastAPI CPU 70% 초과 시 스케일아웃
        # ════════════════════════════════════════════════════════════
        {
          id        = 10
          type      = "row"
          title     = "HPA — FastAPI 수평 자동 스케일  (CPU 70% 기준 / scaleDown cooldown 300s)"
          collapsed = false
          gridPos   = { h = 1, w = 24, x = 0, y = 4 }
        },

        {
          id      = 11
          title   = "FastAPI HPA Replicas 추이 (현재 / 목표 / min / max)"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 5 }
          targets = [
            {
              expr         = "kube_horizontalpodautoscaler_status_current_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
              legendFormat = "현재 replicas"
              refId        = "A"
            },
            {
              expr         = "kube_horizontalpodautoscaler_status_desired_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
              legendFormat = "HPA 목표 replicas"
              refId        = "B"
            },
            {
              expr         = "kube_horizontalpodautoscaler_spec_min_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
              legendFormat = "min (설정)"
              refId        = "C"
            },
            {
              expr         = "kube_horizontalpodautoscaler_spec_max_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
              legendFormat = "max (설정)"
              refId        = "D"
            }
          ]
          fieldConfig = {
            defaults = {
              unit   = "short"
              color  = { mode = "palette-classic" }
              custom = { fillOpacity = 5, lineWidth = 2 }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        {
          id      = 12
          title   = "FastAPI CPU 사용률 (%) vs HPA 임계값 70%"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 5 }
          targets = [
            {
              expr         = "100 * sum(rate(container_cpu_usage_seconds_total{namespace=\"homelens\", container=\"fastapi\"}[2m])) / sum(kube_pod_container_resource_requests{namespace=\"homelens\", container=\"fastapi\", resource=\"cpu\"})"
              legendFormat = "FastAPI CPU 사용률 %"
              refId        = "A"
            },
            {
              expr         = "vector(70)"
              legendFormat = "스케일아웃 임계값 (70%)"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "percent"
              min   = 0
              color = { mode = "palette-classic" }
              thresholds = { steps = [
                { color = "green",  value = null },
                { color = "yellow", value = 60 },
                { color = "red",    value = 70 }
              ]}
            }
            overrides = [{
              matcher    = { id = "byName", options = "스케일아웃 임계값 (70%)" }
              properties = [
                { id = "color", value = { fixedColor = "red", mode = "fixed" } },
                { id = "custom.lineStyle", value = { dash = [8, 4], fill = "dash" } }
              ]
            }]
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ════════════════════════════════════════════════════════════
        # 행 2 — KEDA: SQS 큐÷queueLength(4) 기준 스케일
        # ════════════════════════════════════════════════════════════
        {
          id        = 20
          type      = "row"
          title     = "KEDA — Celery Worker 자동 스케일  (SQS 큐÷4 / min=1 / max=25 / cooldown=300s)"
          collapsed = false
          gridPos   = { h = 1, w = 24, x = 0, y = 13 }
        },

        {
          id      = 21
          title   = "Celery Worker Replicas 추이 (현재 / 가용 / KEDA 계산값)"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 14 }
          targets = [
            {
              expr         = "kube_deployment_status_replicas{deployment=\"celery-worker\", namespace=\"homelens\"}"
              legendFormat = "전체 replicas"
              refId        = "A"
            },
            {
              expr         = "kube_deployment_status_replicas_available{deployment=\"celery-worker\", namespace=\"homelens\"}"
              legendFormat = "가용(Ready) replicas"
              refId        = "B"
            },
            {
              expr         = "kube_deployment_spec_replicas{deployment=\"celery-worker\", namespace=\"homelens\"}"
              legendFormat = "목표(spec) replicas"
              refId        = "C"
            },
            {
              expr         = "ceil(homelens_sqs_queue_depth / 4)"
              legendFormat = "KEDA 계산값 ceil(큐÷4)"
              refId        = "D"
            }
          ]
          fieldConfig = {
            defaults = {
              unit   = "short"
              color  = { mode = "palette-classic" }
              custom = { fillOpacity = 5, lineWidth = 2 }
            }
            overrides = [{
              matcher    = { id = "byName", options = "KEDA 계산값 ceil(큐÷4)" }
              properties = [
                { id = "color", value = { fixedColor = "orange", mode = "fixed" } },
                { id = "custom.lineStyle", value = { dash = [8, 4], fill = "dash" } }
              ]
            }]
          }
          options = { tooltip = { mode = "multi" } }
        },

        {
          id      = 22
          title   = "SQS 큐 깊이 vs 현재 Pod 처리 용량 — 큐 > 용량이면 KEDA 스케일아웃"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 14 }
          targets = [
            {
              expr         = "homelens_sqs_queue_depth"
              legendFormat = "SQS 대기 메시지 수"
              refId        = "A"
            },
            {
              expr         = "kube_deployment_status_replicas_available{deployment=\"celery-worker\", namespace=\"homelens\"} * 4"
              legendFormat = "현재 처리 용량 (Pod수×4)"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "palette-classic" }
              thresholds = { steps = [
                { color = "green",  value = null },
                { color = "yellow", value = 4 },
                { color = "red",    value = 20 }
              ]}
            }
            overrides = [{
              matcher    = { id = "byName", options = "현재 처리 용량 (Pod수×4)" }
              properties = [
                { id = "color", value = { fixedColor = "green", mode = "fixed" } },
                { id = "custom.lineStyle", value = { dash = [8, 4], fill = "dash" } }
              ]
            }]
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ════════════════════════════════════════════════════════════
        # 행 3 — Cluster Autoscaler: Pending Pod → 노드 추가
        # ════════════════════════════════════════════════════════════
        {
          id        = 30
          type      = "row"
          title     = "Cluster Autoscaler — 노드 Scale Out/In  (Pending Pod → 노드추가 2~5분 / 유휴 5분 → 제거 / worker min=2/max=4)"
          collapsed = false
          gridPos   = { h = 1, w = 24, x = 0, y = 22 }
        },

        {
          id      = 31
          title   = "EKS 노드 수 변화 — CA Scale Out/In 추이"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 23 }
          targets = [
            {
              expr         = "count(kube_node_status_condition{condition=\"Ready\",status=\"true\"})"
              legendFormat = "전체 노드"
              refId        = "A"
            },
            {
              expr         = "count(kube_node_labels{label_eks_amazonaws_com_nodegroup=\"homelens-${var.env}-worker\"})"
              legendFormat = "Worker 노드 (CA 대상, min=2/max=4)"
              refId        = "B"
            },
            {
              expr         = "count(kube_node_labels{label_eks_amazonaws_com_nodegroup=\"homelens-${var.env}-api\"})"
              legendFormat = "API 노드"
              refId        = "C"
            }
          ]
          fieldConfig = {
            defaults = {
              unit   = "short"
              color  = { mode = "palette-classic" }
              custom = { fillOpacity = 10, lineWidth = 2 }
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        {
          id      = 32
          title   = "Pending / Unschedulable Pod 수 — CA 스케일아웃 트리거 (0이 정상)"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 23 }
          targets = [
            {
              expr         = "count(kube_pod_status_scheduled{namespace=\"homelens\", condition=\"false\"}) or vector(0)"
              legendFormat = "homelens Unschedulable Pods (CA 트리거)"
              refId        = "A"
            },
            {
              expr         = "sum(kube_pod_status_scheduled{condition=\"false\"}) or vector(0)"
              legendFormat = "전체 Unschedulable Pods"
              refId        = "B"
            }
          ]
          fieldConfig = {
            defaults = {
              unit  = "short"
              color = { mode = "palette-classic" }
              thresholds = { steps = [
                { color = "green",  value = null },
                { color = "yellow", value = 1 },
                { color = "red",    value = 3 }
              ]}
            }
            overrides = [{
              matcher    = { id = "byName", options = "homelens Pending Pods" }
              properties = [{ id = "color", value = { fixedColor = "red", mode = "fixed" } }]
            }]
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ════════════════════════════════════════════════════════════
        # 행 4 — 노드 리소스 할당률 (CA 스케일 판단 근거)
        # ════════════════════════════════════════════════════════════
        {
          id        = 40
          type      = "row"
          title     = "노드 리소스 할당률 — CA 스케일 판단 근거  (request 예약량 기준)"
          collapsed = false
          gridPos   = { h = 1, w = 24, x = 0, y = 31 }
        },

        {
          id      = 41
          title   = "노드별 CPU 할당률 (%) — 90% 초과 시 CA 스케일아웃 임박"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 0, y = 32 }
          targets = [{
            expr         = "100 * sum by (node) (kube_pod_container_resource_requests{resource=\"cpu\"}) / on(node) kube_node_status_allocatable{resource=\"cpu\"}"
            legendFormat = "{{node}}"
            refId        = "A"
          }]
          fieldConfig = {
            defaults = {
              unit  = "percent"
              min   = 0
              max   = 100
              color = { mode = "palette-classic" }
              thresholds = { steps = [
                { color = "green",  value = null },
                { color = "yellow", value = 70 },
                { color = "red",    value = 90 }
              ]}
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        {
          id      = 42
          title   = "노드별 메모리 할당률 (%) — 90% 초과 시 CA 스케일아웃 임박"
          type    = "timeseries"
          gridPos = { h = 8, w = 12, x = 12, y = 32 }
          targets = [{
            expr         = "100 * sum by (node) (kube_pod_container_resource_requests{resource=\"memory\"}) / on(node) kube_node_status_allocatable{resource=\"memory\"}"
            legendFormat = "{{node}}"
            refId        = "A"
          }]
          fieldConfig = {
            defaults = {
              unit  = "percent"
              min   = 0
              max   = 100
              color = { mode = "palette-classic" }
              thresholds = { steps = [
                { color = "green",  value = null },
                { color = "yellow", value = 70 },
                { color = "red",    value = 90 }
              ]}
            }
          }
          options = { tooltip = { mode = "multi" } }
        },

        # ════════════════════════════════════════════════════════════
        # 행 5 — 스케일링 연쇄 흐름 오버레이
        # ════════════════════════════════════════════════════════════
        {
          id        = 50
          type      = "row"
          title     = "스케일링 연쇄 흐름  ① SQS 큐 ↑  →  ② KEDA Pod ↑  →  ③ Pending  →  ④ CA 노드 ↑"
          collapsed = false
          gridPos   = { h = 1, w = 24, x = 0, y = 40 }
        },

        {
          id      = 51
          title   = "스케일링 연쇄 오버레이 — SQS 큐 / Celery Pod / Worker 노드 / FastAPI Pod"
          type    = "timeseries"
          gridPos = { h = 10, w = 24, x = 0, y = 41 }
          targets = [
            {
              expr         = "homelens_sqs_queue_depth"
              legendFormat = "① SQS 큐 깊이"
              refId        = "A"
            },
            {
              expr         = "kube_deployment_status_replicas{deployment=\"celery-worker\", namespace=\"homelens\"}"
              legendFormat = "② Celery Worker Pod 수 (KEDA)"
              refId        = "B"
            },
            {
              expr         = "count(kube_node_labels{label_eks_amazonaws_com_nodegroup=\"homelens-${var.env}-worker\"})"
              legendFormat = "③ Worker 노드 수 (CA)"
              refId        = "C"
            },
            {
              expr         = "kube_horizontalpodautoscaler_status_current_replicas{horizontalpodautoscaler=\"fastapi-hpa\", namespace=\"homelens\"}"
              legendFormat = "④ FastAPI Pod 수 (HPA)"
              refId        = "D"
            }
          ]
          fieldConfig = {
            defaults = {
              unit   = "short"
              color  = { mode = "palette-classic" }
              custom = { fillOpacity = 8, lineWidth = 2 }
            }
          }
          options = {
            tooltip = { mode = "multi" }
            legend  = { displayMode = "table", placement = "bottom", calcs = ["lastNotNull", "min", "max"] }
          }
        }

      ]
    })
  }

  depends_on = [helm_release.kube_prometheus_stack]
}
