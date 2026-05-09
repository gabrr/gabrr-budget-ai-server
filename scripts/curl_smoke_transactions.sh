#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${LOG_FILE:-$ROOT/docs/api-smoke-log.md}"

mkdir -p "$(dirname "$LOG_FILE")"
BODY="$(mktemp)"
trap 'rm -f "$BODY"' EXIT

ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  echo ""
  echo "---"
  echo "## ${ts} — transaction smoke (curl)"
  echo ""
  echo "### GET /transactions"
  echo ""
  echo '```bash'
  echo "curl -fsS \"${BASE_URL}/transactions?limit=5&offset=0\""
  echo '```'
  echo ""
  code_get="$(curl -fsS -o "$BODY" -w '%{http_code}' "${BASE_URL}/transactions?limit=5&offset=0" || true)"
  echo "**Status:** ${code_get}"
  echo ""
  echo '```json'
  if command -v jq >/dev/null 2>&1; then
    jq . <"$BODY" || cat "$BODY"
  else
    cat "$BODY"
  fi
  echo '```'
  echo ""
  echo "### POST /transactions"
  echo ""
  echo '```bash'
  echo "curl -fsS -X POST \"${BASE_URL}/transactions\" \\"
  echo "  -H 'Content-Type: application/json' \\"
  echo "  -d '{\"posted_at\":\"2026-05-09\",\"description\":\"curl smoke\",\"amount\":\"12.34\"}'"
  echo '```'
  echo ""
  code_post="$(curl -fsS -o "$BODY" -w '%{http_code}' -X POST "${BASE_URL}/transactions" \
    -H "Content-Type: application/json" \
    -d '{"posted_at":"2026-05-09","description":"curl smoke","amount":"12.34"}' || true)"
  echo "**Status:** ${code_post}"
  echo ""
  echo '```json'
  if command -v jq >/dev/null 2>&1; then
    jq . <"$BODY" || cat "$BODY"
  else
    cat "$BODY"
  fi
  echo '```'
  echo ""
} >>"$LOG_FILE"

echo "Appended smoke run to ${LOG_FILE}"
