#!/bin/sh
set -e

mkdir -p "${DATA_DIR:-/app/data}/uploads"

echo "Starting papers MCP on ${MCP_PAPERS_PORT:-8009}..."
python -m papermind.mcp.papers.server &
MCP_PID=$!

cleanup() {
  kill "$MCP_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# MCP binds asynchronously; brief wait before the web app connects.
sleep 3

PORT="${PORT:-${APP_PORT:-8000}}"
echo "Starting PaperMind on ${APP_HOST:-0.0.0.0}:${PORT}..."

exec python -m uvicorn papermind.app:app \
  --host "${APP_HOST:-0.0.0.0}" \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips='*'
