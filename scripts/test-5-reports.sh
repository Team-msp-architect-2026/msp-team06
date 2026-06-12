#!/usr/bin/env bash
# 테스트용 SQS 메시지 5개 동시 전송 스크립트
# 목적: KEDA 스케일아웃 + Celery 처리 + Grafana 패널 동시 부하 관찰
#
# 사용법:
#   bash scripts/test-5-reports.sh             # 5개 동시 전송 (기본)
#   bash scripts/test-5-reports.sh --count 3   # 개수 지정
#   bash scripts/test-5-reports.sh --no-poll   # 상태 폴링 없이 전송만

set -euo pipefail

# ── 설정 ──────────────────────────────────────────────────────────────────────
API_BASE="http://localhost:8000/api/v1"
COUNT=5
POLL=true
POLL_INTERVAL=10   # 상태 조회 주기 (초)
POLL_TIMEOUT=180   # 폴링 최대 대기 (초)
PORT_FORWARD_PID=""

# ── 인수 파싱 ─────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --count) COUNT="$2"; shift 2 ;;
    --no-poll) POLL=false; shift ;;
    *) echo "알 수 없는 인수: $1"; exit 1 ;;
  esac
done

# ── 색상 ──────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

log()  { echo -e "${CYAN}[$(date +%T)]${NC} $*"; }
ok()   { echo -e "${GREEN}[$(date +%T)] ✓${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%T)] ⚠${NC} $*"; }
err()  { echo -e "${RED}[$(date +%T)] ✗${NC} $*"; }

# ── 포트포워딩 확인 및 시작 ───────────────────────────────────────────────────
check_or_start_portforward() {
  if curl -s --max-time 2 "$API_BASE/../health" > /dev/null 2>&1 || \
     curl -s --max-time 2 "http://localhost:8000/health" > /dev/null 2>&1 || \
     curl -s --max-time 2 "http://localhost:8000/docs" > /dev/null 2>&1; then
    ok "FastAPI 포트포워딩 이미 활성 (localhost:8000)"
    return 0
  fi

  warn "포트포워딩 없음 — kubectl port-forward 시작..."
  kubectl port-forward svc/fastapi 8000:80 -n homelens > /tmp/pf-fastapi.log 2>&1 &
  PORT_FORWARD_PID=$!

  local waited=0
  while (( waited < 15 )); do
    sleep 2; waited=$((waited+2))
    if curl -s --max-time 2 "http://localhost:8000/health" > /dev/null 2>&1 || \
       curl -s --max-time 2 "http://localhost:8000/docs"   > /dev/null 2>&1; then
      ok "포트포워딩 시작됨 (PID $PORT_FORWARD_PID)"
      return 0
    fi
  done

  err "포트포워딩 실패. 수동으로 실행해주세요:"
  err "  kubectl port-forward svc/fastapi 8000:80 -n homelens"
  exit 1
}

cleanup() {
  if [[ -n "$PORT_FORWARD_PID" ]]; then
    kill "$PORT_FORWARD_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# ── 테스트 지역 목록 (서울 주요 동 — 각기 다른 regionId) ────────────────────
BASE_TS=$(date +%s)

declare -a REGIONS=(
  '{"regionId":"TEST_JONGNO_'${BASE_TS}'","regionName":"종로구 청운동","lat":37.5843,"lng":126.9714}'
  '{"regionId":"TEST_MAPO_'${BASE_TS}'","regionName":"마포구 합정동","lat":37.5496,"lng":126.9135}'
  '{"regionId":"TEST_GANGNAM_'${BASE_TS}'","regionName":"강남구 역삼동","lat":37.5012,"lng":127.0396}'
  '{"regionId":"TEST_SEODAEMUN_'${BASE_TS}'","regionName":"서대문구 홍은동","lat":37.5930,"lng":126.9378}'
  '{"regionId":"TEST_SONGPA_'${BASE_TS}'","regionName":"송파구 잠실동","lat":37.5133,"lng":127.1028}'
  '{"regionId":"TEST_NOWON_'${BASE_TS}'","regionName":"노원구 상계동","lat":37.6559,"lng":127.0618}'
  '{"regionId":"TEST_DOBONG_'${BASE_TS}'","regionName":"도봉구 방학동","lat":37.6694,"lng":127.0334}'
  '{"regionId":"TEST_EUNPYEONG_'${BASE_TS}'","regionName":"은평구 응암동","lat":37.6108,"lng":126.9186}'
  '{"regionId":"TEST_DONGJAK_'${BASE_TS}'","regionName":"동작구 사당동","lat":37.4763,"lng":126.9797}'
  '{"regionId":"TEST_GWANAK_'${BASE_TS}'","regionName":"관악구 봉천동","lat":37.4814,"lng":126.9516}'
)

# ── 메인 ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  HomeLens 부하 테스트 — SQS 메시지 ${COUNT}개 동시 전송${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""

check_or_start_portforward

echo ""
log "현재 Celery pod 현황:"
kubectl get pods -n homelens -l app=celery-worker --no-headers 2>/dev/null \
  | awk '{printf "  %-45s %s\n", $1, $2}' || echo "  (조회 실패)"
echo ""

# ── 5개 동시 전송 ─────────────────────────────────────────────────────────────
log "${BOLD}${COUNT}개 요청 동시 전송 시작...${NC}"
echo ""

START_TIME=$(date +%s%N)
declare -a PIDS=()
declare -a TMP_FILES=()

for (( i=0; i<COUNT; i++ )); do
  body="${REGIONS[$i]}"
  tmp=$(mktemp /tmp/homelens-req-XXXX.json)
  TMP_FILES+=("$tmp")

  curl -s -w '\n{"http_status":%{http_code}}' \
    -X POST "$API_BASE/reports" \
    -H "Content-Type: application/json" \
    -d "$body" > "$tmp" &
  PIDS+=($!)

  region_name=$(echo "$body" | grep -o '"regionName":"[^"]*"' | cut -d'"' -f4)
  echo -e "  ${CYAN}[$((i+1))/${COUNT}]${NC} ${region_name} → 전송됨 (PID ${PIDS[$i]})"
done

echo ""
log "모든 요청 응답 대기 중..."
for pid in "${PIDS[@]}"; do
  wait "$pid" 2>/dev/null || true
done

END_TIME=$(date +%s%N)
SEND_MS=$(( (END_TIME - START_TIME) / 1000000 ))
ok "전송 완료 (${SEND_MS}ms)"
echo ""

# ── 응답 파싱 ─────────────────────────────────────────────────────────────────
declare -a REPORT_IDS=()
declare -a LABELS=()

echo -e "${BOLD}── 요청 결과 ──────────────────────────────────────────${NC}"

for (( i=0; i<COUNT; i++ )); do
  body="${REGIONS[$i]}"
  region_name=$(echo "$body" | grep -o '"regionName":"[^"]*"' | cut -d'"' -f4)
  raw=$(cat "${TMP_FILES[$i]}" 2>/dev/null || echo "")

  http_status=$(echo "$raw" | grep -o '"http_status":[0-9]*' | cut -d: -f2 || echo "000")
  report_id=$(echo "$raw" | grep -o '"reportId":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
  status=$(echo "$raw" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
  error_code=$(echo "$raw" | grep -o '"errorCode":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

  label="${region_name}"
  LABELS+=("$label")

  if [[ "$http_status" == "200" || "$http_status" == "201" || "$http_status" == "202" ]]; then
    if [[ -n "$report_id" ]]; then
      REPORT_IDS+=("$report_id")
      ok "[$((i+1))] ${label}"
      echo "       reportId : ${report_id}"
      echo "       status   : ${status}"
    else
      warn "[$((i+1))] ${label} — HTTP ${http_status}, reportId 없음"
      echo "       응답: $(echo "$raw" | head -c 200)"
      REPORT_IDS+=("")
    fi
  elif [[ "$error_code" == "REPORT_ALREADY_EXISTS" ]]; then
    report_id=$(echo "$raw" | grep -o '"reportId":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    REPORT_IDS+=("$report_id")
    warn "[$((i+1))] ${label} — 캐시됨 (REPORT_ALREADY_EXISTS)"
    echo "       reportId : ${report_id}"
  else
    err "[$((i+1))] ${label} — HTTP ${http_status}"
    echo "       응답: $(echo "$raw" | grep -v '"http_status"' | head -c 300)"
    REPORT_IDS+=("")
  fi
done

# ── 임시 파일 정리 ────────────────────────────────────────────────────────────
for f in "${TMP_FILES[@]}"; do rm -f "$f"; done

# ── Grafana 관찰 안내 ──────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}── Grafana 관찰 포인트 ────────────────────────────────${NC}"
echo "  포트포워딩: kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring"
echo "  대시보드  : http://localhost:3000 (admin / Homelens@2026!)"
echo "  파이프라인 : HomeLens Pipeline Latency — dev"
echo "  리소스    : 시간 범위를 'Last 5 minutes'로 설정"
echo ""
echo "  확인할 패널:"
echo "    [1] SQS 큐 대기 지연  — 첫 번째 이후 메시지가 큐에서 대기하는 시간"
echo "    [4] 전체 파이프라인  — 5번째 메시지가 1번째보다 길면 큐 지연 발생"
echo "    [6] Celery Pod CPU   — 부하 시 CPU 스파이크 확인"
echo "    [7] Celery Pod Memory — OOM 위험 없는지 확인"
echo ""
echo "  KEDA 스케일아웃 확인:"
echo "    watch kubectl get pods -n homelens -l app=celery-worker"
echo ""

# ── 폴링 ──────────────────────────────────────────────────────────────────────
if [[ "$POLL" != "true" ]]; then
  log "폴링 생략 (--no-poll). 수동 상태 조회:"
  for (( i=0; i<COUNT; i++ )); do
    if [[ -n "${REPORT_IDS[$i]}" ]]; then
      echo "  curl $API_BASE/reports/${REPORT_IDS[$i]}/status"
    fi
  done
  exit 0
fi

echo -e "${BOLD}── 상태 폴링 (${POLL_INTERVAL}초 간격, 최대 ${POLL_TIMEOUT}초) ────────────────${NC}"
echo ""

declare -a COMPLETED=()
declare -A COMPLETE_TIME=()
declare -A FINAL_STATUS=()

for id in "${REPORT_IDS[@]}"; do
  COMPLETED+=("false")
done

POLL_START=$(date +%s)

while true; do
  all_done=true
  pending_count=0

  for (( i=0; i<COUNT; i++ )); do
    id="${REPORT_IDS[$i]}"
    [[ -z "$id" ]] && continue
    [[ "${COMPLETED[$i]}" == "true" ]] && continue

    resp=$(curl -s --max-time 5 "$API_BASE/reports/$id/status" 2>/dev/null || echo "")
    status=$(echo "$resp" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
    progress=$(echo "$resp" | grep -o '"progressPct":[0-9]*' | cut -d: -f2 || echo "")

    if [[ "$status" == "completed" ]]; then
      COMPLETED[$i]="true"
      COMPLETE_TIME[$i]=$(( $(date +%s) - POLL_START ))
      FINAL_STATUS[$i]="completed"
      ok "[$((i+1))] ${LABELS[$i]} — 완료 (${COMPLETE_TIME[$i]}초)"
    elif [[ "$status" == "failed" ]]; then
      COMPLETED[$i]="true"
      COMPLETE_TIME[$i]=$(( $(date +%s) - POLL_START ))
      FINAL_STATUS[$i]="failed"
      err "[$((i+1))] ${LABELS[$i]} — 실패 (${COMPLETE_TIME[$i]}초)"
    else
      all_done=false
      pending_count=$((pending_count+1))
      prog_str=""
      [[ -n "$progress" ]] && prog_str=" (${progress}%)"
      echo -e "  ${YELLOW}[$((i+1))]${NC} ${LABELS[$i]} — ${status}${prog_str}"
    fi
  done

  elapsed=$(( $(date +%s) - POLL_START ))

  if $all_done; then
    echo ""
    ok "모든 요청 처리 완료 (총 ${elapsed}초 경과)"
    break
  fi

  if (( elapsed >= POLL_TIMEOUT )); then
    echo ""
    warn "폴링 타임아웃 (${POLL_TIMEOUT}초). 미완료 요청 수: ${pending_count}"
    break
  fi

  echo -e "  ${CYAN}→ ${pending_count}개 처리 중... (${elapsed}초 경과, ${POLL_INTERVAL}초 후 재조회)${NC}"
  echo ""
  sleep $POLL_INTERVAL
done

# ── 최종 요약 ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}══════════════════ 최종 요약 ══════════════════════════${NC}"
completed_count=0
failed_count=0

for (( i=0; i<COUNT; i++ )); do
  id="${REPORT_IDS[$i]}"
  [[ -z "$id" ]] && continue
  fs="${FINAL_STATUS[$i]:-timeout}"
  ct="${COMPLETE_TIME[$i]:-?}"

  if [[ "$fs" == "completed" ]]; then
    completed_count=$((completed_count+1))
    echo -e "  ${GREEN}✓${NC} [$((i+1))] ${LABELS[$i]}  ${ct}초"
  elif [[ "$fs" == "failed" ]]; then
    failed_count=$((failed_count+1))
    echo -e "  ${RED}✗${NC} [$((i+1))] ${LABELS[$i]}  ${ct}초 (실패)"
  else
    echo -e "  ${YELLOW}?${NC} [$((i+1))] ${LABELS[$i]}  타임아웃"
  fi
done

echo ""
echo -e "  완료: ${completed_count} / 실패: ${failed_count} / 전체: ${COUNT}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""

log "Celery pod 최종 현황:"
kubectl get pods -n homelens -l app=celery-worker --no-headers 2>/dev/null \
  | awk '{printf "  %-45s %s\n", $1, $2}' || echo "  (조회 실패)"
echo ""
