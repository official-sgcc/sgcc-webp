FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --locked --no-dev --no-install-project

COPY src ./src

RUN uv sync --locked --no-dev --no-editable


FROM python:3.13-slim

ENV PORT=8080 \
    HOST=0.0.0.0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH=/opt/venv/bin:$PATH
ENV UVICORN_PORT=$PORT \
    UVICORN_HOST=$HOST

RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /data

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
USER appuser

EXPOSE $PORT
VOLUME ["/data"]

CMD ["uvicorn", "sgcc_webp:app"]
