#!/usr/bin/env bash
# AgentService integration test — exercises AgentService over HTTP only:
# create_session, run_text, run_json, stream_run_sse via POST /agents/run (see app/services/agent_service.py, app/api/agents_routes.py).
# Does not replace pytest; this is a cheap live check against agent-normalizer (make api) + this API.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(cd "$SELF_DIR/../.." && pwd)"
NORMALIZER_ROOT="${AGENT_NORMALIZER_ROOT:-$BACKEND_ROOT/../agent-normalizer}"
PORT="${PORT:-8000}"
BASE="${BASE:-http://127.0.0.1:$PORT}"
ADK="${ADK_BASE_URL:-http://127.0.0.1:8001}"
DOC="${AGENT_SERVICE_RUN_LOG:-$BACKEND_ROOT/tests/agents/agent_service_run_log.md}"
SCRATCH="${TMPDIR:-/tmp}/agent_service_test_scratch.md"
ADK_LOG="${TMPDIR:-/tmp}/agent_normalizer_make_api.log"
API_LOG="${AGENT_SERVICE_API_LOG:-${TMPDIR:-/tmp}/gabrr_agent_service_api.log}"
DIGEST_PY="$SELF_DIR/sse_digest_adk_stream.py"

MAX_INTEGRATION_RETRIES="${MAX_INTEGRATION_RETRIES:-3}"
WAIT_ADK_SECS="${WAIT_ADK_SECS:-45}"
SSE_MAX_TIME_SECS="${SSE_MAX_TIME_SECS:-5}"
SSE_HDR_LINES="${SSE_HDR_LINES:-12}"
SSE_DIGEST_MAX_BYTES="${SSE_DIGEST_MAX_BYTES:-5000}"
SSE_DIGEST_MAX_EVENTS="${SSE_DIGEST_MAX_EVENTS:-30}"

api_listening() {
  curl -sS -o /dev/null --connect-timeout 1 -w "%{http_code}" "${BASE}/docs" 2>/dev/null | grep -q '^200$'
}

adk_listening() {
  local code exit_c
  set +e
  code="$(curl -sS -o /dev/null --connect-timeout 2 -w "%{http_code}" "${ADK}/" 2>/dev/null)"
  exit_c=$?
  set -e
  [[ "$exit_c" -eq 0 && -n "$code" && "$code" != "000" ]]
}

adk_probe() {
  local code exit_c
  set +e
  code="$(curl -sS -o /dev/null --connect-timeout 2 -w "%{http_code}" "${ADK}/" 2>/dev/null)"
  exit_c=$?
  set -e
  if [[ "$exit_c" -eq 0 && -n "$code" && "$code" != "000" ]]; then
    echo "ADK: OK (GET ${ADK}/ → HTTP ${code})"
    return 0
  fi
  echo "ADK: ERROR — not reachable at ${ADK} (curl exit ${exit_c}, http_code=${code:-empty}); in agent-normalizer run \`make api\` (or fix ADK_BASE_URL)."
  return 1
}

cmd_start_api() {
  cd "$BACKEND_ROOT"
  if api_listening; then
    echo "API: already up (${BASE}/docs → 200)"
    return 0
  fi
  echo "API: starting uvicorn on port ${PORT} (log: ${API_LOG})"
  : >"$API_LOG"
  nohup uv run uvicorn app.main:app --reload --port "$PORT" --env-file .env >>"$API_LOG" 2>&1 &
  echo $! >"${API_LOG}.pid"
  local waited=0
  while ! api_listening; do
    sleep 0.4
    waited=$((waited + 1))
    if [[ "$waited" -gt 75 ]]; then
      echo "API: ERROR — still not listening after ~30s. Last log lines:"
      tail -n 25 "$API_LOG" || true
      return 1
    fi
  done
  echo "API: STARTED (${BASE} — see ${API_LOG})"
  return 0
}

cmd_status() {
  if api_listening; then
    echo "API: OK (${BASE}/docs → 200)"
  else
    echo "API: ERROR — not listening on ${BASE}"
  fi
  adk_probe || true
}

start_adk_if_down() {
  if adk_listening; then
    echo "ADK: already up (${ADK})"
    return 0
  fi
  if [[ ! -f "$NORMALIZER_ROOT/Makefile" ]]; then
    echo "ADK: ERROR — NORMALIZER_ROOT not found: $NORMALIZER_ROOT (set AGENT_NORMALIZER_ROOT)"
    return 1
  fi
  echo "ADK: starting (cd agent-normalizer && make api) → log ${ADK_LOG}"
  : >"$ADK_LOG"
  (
    cd "$NORMALIZER_ROOT"
    nohup make api >>"$ADK_LOG" 2>&1 &
    echo $! >"${ADK_LOG}.pid"
  )
  local waited=0
  while ! adk_listening; do
    sleep 1
    waited=$((waited + 1))
    if [[ "$waited" -ge "$WAIT_ADK_SECS" ]]; then
      echo "ADK: ERROR — not ready after ${WAIT_ADK_SECS}s. Last log:"
      tail -n 30 "$ADK_LOG" || true
      return 1
    fi
  done
  echo "ADK: READY"
  return 0
}

start_api_if_down() {
  cmd_start_api
}

run_checks() {
  set +e
  TEXT_HTTP="$(curl -sS -o /tmp/e2e_text.json --connect-timeout 5 --max-time 45 -w "%{http_code}" -X POST "${BASE}/agents/run" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"e2e","prompt":"Reply OK only.","mode":"text"}' 2>/dev/null || echo "000")"

  JSON_HTTP="$(curl -sS -o /tmp/e2e_json.json --connect-timeout 5 --max-time 45 -w "%{http_code}" -X POST "${BASE}/agents/run" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"e2e","prompt":"Output only this JSON and nothing else: {\"ok\":true}","mode":"json"}' 2>/dev/null || echo "000")"

  curl -sS -N --connect-timeout 5 --max-time "$SSE_MAX_TIME_SECS" -D /tmp/e2e_sse.hdr -o /tmp/e2e_sse_body.txt -X POST "${BASE}/agents/run" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"e2e","prompt":"Reply with exactly three very short lines: line1 then line2 then line3.","mode":"sse"}' 2>/dev/null || true
  SSE_HTTP="$(awk 'NR==1 { print $2 }' /tmp/e2e_sse.hdr 2>/dev/null | tr -d '\r')"
  [[ -z "$SSE_HTTP" ]] && SSE_HTTP="000"
  SSE_HDR_SNIP="$(head -n "$SSE_HDR_LINES" /tmp/e2e_sse.hdr 2>/dev/null | tr -d '\r' || true)"

  SSE_DIGEST_SNIP="$(
    cd "$BACKEND_ROOT" && uv run python "$DIGEST_PY" /tmp/e2e_sse_body.txt "$SSE_DIGEST_MAX_EVENTS" 2>/dev/null | head -c "$SSE_DIGEST_MAX_BYTES" || true
  )"
  [[ -z "${SSE_DIGEST_SNIP// }" ]] && SSE_DIGEST_SNIP="(no data: lines parsed)"

  VAL_HTTP="$(curl -sS -o /dev/null --connect-timeout 3 -w "%{http_code}" -X POST "${BASE}/agents/run" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"","prompt":"x","mode":"text"}' 2>/dev/null || echo "000")"
  set -e

  TEXT_SNIP="$(head -c 240 /tmp/e2e_text.json 2>/dev/null | tr -d '\r' || echo "(no file)")"
  JSON_SNIP="$(head -c 240 /tmp/e2e_json.json 2>/dev/null | tr -d '\r' || echo "(no file)")"
}

append_log() {
  local verdict="$1" summary="$2"
  local ts t_ok j_ok s_ok v_ok
  ts="$(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  t_ok="❌"
  [[ "${TEXT_HTTP:-}" == "200" ]] && grep -q '"text"' /tmp/e2e_text.json 2>/dev/null && t_ok="✅"
  j_ok="❌"
  [[ "${JSON_HTTP:-}" == "200" ]] && grep -q '"status"' /tmp/e2e_json.json 2>/dev/null && j_ok="✅"
  s_ok="❌"
  [[ "${SSE_HTTP:-}" == "200" ]] && s_ok="✅"
  v_ok="❌"
  [[ "${VAL_HTTP:-}" == "422" ]] && v_ok="✅"
  {
    echo ""
    echo "---"
    echo "### $ts"
    echo ""
    echo "**Verdict:** $verdict — $summary"
    echo ""
    echo "| Check | HTTP | OK? |"
    echo "| --- | --- | --- |"
    echo "| \`text\` | ${TEXT_HTTP:-} | $t_ok |"
    echo "| \`json\` | ${JSON_HTTP:-} | $j_ok |"
    echo "| \`sse\` | ${SSE_HTTP:-} | $s_ok |"
    echo "| empty \`user_id\` | ${VAL_HTTP:-} | $v_ok |"
    echo ""
    echo "**text** (truncated)"
    echo ""
    echo '```'
    echo "text: ${TEXT_SNIP:-}"
    echo '```'
    echo ""
    echo "**json** (truncated)"
    echo ""
    echo '```'
    echo "json: ${JSON_SNIP:-}"
    echo '```'
    echo ""
    echo "**sse** response headers (first lines)"
    echo ""
    echo '```'
    echo "${SSE_HDR_SNIP:-}"
    echo '```'
    echo ""
    echo "**sse** \`data:\` digest (one line per event — modelVersion, partial, finishReason, text preview)"
    echo ""
    echo '```'
    echo "${SSE_DIGEST_SNIP:-}"
    echo '```'
    echo ""
  } >>"$DOC"
}

run_agent_service_test() {
  : >"$SCRATCH"
  {
    echo "# scratch $(date -u)"
    echo "NORMALIZER_ROOT=$NORMALIZER_ROOT"
    echo "BASE=$BASE ADK=$ADK"
    echo "DOC=$DOC"
  } >"$SCRATCH"

  if ! start_adk_if_down; then
    TEXT_HTTP=""; JSON_HTTP=""; SSE_HTTP=""; VAL_HTTP=""
    TEXT_SNIP="(not run)"; JSON_SNIP="(not run)"
    SSE_HDR_SNIP="(not run)"
    SSE_DIGEST_SNIP="(not run)"
    append_log "🔴 FAIL" "ADK did not become ready (see ${ADK_LOG})"
    exit 1
  fi
  if ! start_api_if_down; then
    TEXT_HTTP=""; JSON_HTTP=""; SSE_HTTP=""; VAL_HTTP=""
    TEXT_SNIP="(not run)"; JSON_SNIP="(not run)"
    SSE_HDR_SNIP="(not run)"
    SSE_DIGEST_SNIP="(not run)"
    append_log "🔴 FAIL" "API did not start"
    exit 1
  fi

  local attempt verdict summary
  verdict="🔴 FAIL"
  summary="exhausted retries"
  for attempt in $(seq 1 "$MAX_INTEGRATION_RETRIES"); do
    echo "=== AgentService integration try $attempt / $MAX_INTEGRATION_RETRIES ==="
    run_checks
    {
      echo ""
      echo "try $attempt"
      echo "TEXT_HTTP=$TEXT_HTTP JSON_HTTP=$JSON_HTTP SSE_HTTP=$SSE_HTTP VAL_HTTP=$VAL_HTTP"
    } >>"$SCRATCH"

    if [[ "$TEXT_HTTP" == "200" && "$JSON_HTTP" == "200" && "$SSE_HTTP" == "200" && "$VAL_HTTP" == "422" ]] \
      && grep -q '"text"' /tmp/e2e_text.json 2>/dev/null \
      && grep -q '"status"' /tmp/e2e_json.json 2>/dev/null; then
      verdict="🟢 PASS"
      summary="text+json+sse+422 OK (try $attempt)"
      break
    fi
    if [[ "$attempt" -lt "$MAX_INTEGRATION_RETRIES" ]]; then
      echo "retry in 4s…"
      sleep 4
    fi
  done

  if [[ "$verdict" != "🟢 PASS" ]]; then
    verdict="🟡 PARTIAL"
    summary="see HTTP table — infra up but some checks failed after ${MAX_INTEGRATION_RETRIES} tries"
    if [[ "$TEXT_HTTP" != "200" && "$JSON_HTTP" != "200" ]]; then
      verdict="🔴 FAIL"
      summary="core modes failing (ADK or model path)"
    fi
  fi

  append_log "$verdict" "$summary"
  {
    echo ""
    echo "## learn $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- AgentService test: TEXT_HTTP=$TEXT_HTTP JSON_HTTP=$JSON_HTTP SSE_HTTP=$SSE_HTTP VAL_HTTP=$VAL_HTTP"
  } >>"$SCRATCH"
  echo "Scratch log: $SCRATCH"
  echo "Appended run to $DOC"
  [[ "$verdict" == "🟢 PASS" ]]
}

usage() {
  echo "AgentService integration test (live ADK + API)" >&2
  echo "Usage: $0 {run|status|start-api|probe-adk}" >&2
  echo "  run         default — start ADK/API if needed, hit POST /agents/run, append $DOC" >&2
  echo "  status      API + ADK reachability (OK/ERROR lines)" >&2
  echo "  start-api   start backend uvicorn if /docs not 200" >&2
  echo "  probe-adk   ADK reachability only" >&2
  exit 2
}

case "${1:-run}" in
run) run_agent_service_test ;;
status) cmd_status ;;
start-api) cmd_start_api ;;
probe-adk) adk_probe ;;
*) usage ;;
esac
