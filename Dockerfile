FROM python:3.12-slim

WORKDIR /app

COPY apps/listener-api/pyproject.toml apps/listener-api/pyproject.toml
COPY apps/listener-api/src/ apps/listener-api/src/
COPY packages/core-engine/pyproject.toml packages/core-engine/pyproject.toml
COPY packages/core-engine/src/ packages/core-engine/src/
COPY packages/adapters/reddit_reddrix/pyproject.toml packages/adapters/reddit_reddrix/pyproject.toml
COPY packages/adapters/reddit_reddrix/src/ packages/adapters/reddit_reddrix/src/
COPY workers/celery_worker/pyproject.toml workers/celery_worker/pyproject.toml
COPY workers/celery_worker/src/ workers/celery_worker/src/

RUN pip install --no-cache-dir \
    ./packages/core-engine \
    ./packages/adapters/reddit_reddrix \
    ./apps/listener-api \
    ./workers/celery_worker \
    && useradd --create-home --uid 10001 app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

USER app