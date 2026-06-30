#!/bin/bash
# Start both MCP servers in the background.
# Run from the project root: ./scripts/start_mcp_servers.sh

echo "Starting papers MCP server on :8009..."
python -m papermind.mcp.papers.server &
PAPERS_PID=$!

echo "Starting paper-store MCP server on :8008..."
python -m papermind.mcp.store.server &
STORE_PID=$!

echo "MCP servers started (papers=$PAPERS_PID, store=$STORE_PID)"
echo "Press Ctrl+C to stop both."

trap "kill $PAPERS_PID $STORE_PID 2>/dev/null" EXIT
wait
