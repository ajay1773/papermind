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

# Wait until MCP is actually accepting connections before starting the web app.
MCP_PORT="${MCP_PAPERS_PORT:-8009}"
echo "Waiting for MCP to be ready on port ${MCP_PORT}..."
for i in $(seq 1 20); do
  if python -c "import socket; s=socket.create_connection(('127.0.0.1', ${MCP_PORT}), timeout=1); s.close()" 2>/dev/null; then
    echo "MCP ready after ${i}s."
    break
  fi
  sleep 1
done

PORT="${PORT:-${APP_PORT:-8000}}"
echo "Starting PaperMind on ${APP_HOST:-0.0.0.0}:${PORT}..."

exec python -m uvicorn papermind.app:app \
  --host "${APP_HOST:-0.0.0.0}" \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips='*'
