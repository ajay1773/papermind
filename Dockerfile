FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm

# fastembed / onnxruntime may need OpenMP on Linux ARM (Oracle A1).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src ./src
COPY --from=builder /app/pyproject.toml /app/uv.lock ./
COPY scripts/docker-entrypoint.sh ./scripts/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/app/data \
    UPLOAD_DIR=/app/data/uploads \
    APP_HOST=0.0.0.0 \
    APP_DEBUG=false \
    EVAL_COLLECT_ENABLED=false \
    MCP_PAPERS_URL=http://127.0.0.1:8009/mcp

RUN chmod +x ./scripts/docker-entrypoint.sh

EXPOSE 8000

CMD ["./scripts/docker-entrypoint.sh"]
