import logging
from typing import Any
from uuid import UUID

from celery_worker.app import app as celery_app
from celery_worker.tasks import scrape_reddit_task
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from reddit_reddrix.validation import validate_subreddit_url

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ADL Intelligence Listener API",
    version="0.1.0",
    description="Production control plane for the ADL intelligence listener pipeline.",
)


class RedditScrapeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subreddit_url: HttpUrl = Field(description="HTTPS URL of the subreddit to collect.")
    limit: int = Field(default=100, ge=1, le=500)
    proxies: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("subreddit_url")
    @classmethod
    def subreddit_must_be_public_reddit(cls, value: HttpUrl) -> HttpUrl:
        validate_subreddit_url(str(value))
        return value

    @field_validator("proxies")
    @classmethod
    def proxies_must_be_valid_urls(cls, values: list[str]) -> list[str]:
        for proxy in values:
            if len(proxy) > 2048:
                raise ValueError("Proxy URL is too long.")
        return values


class ScrapeTaskStatus(BaseModel):
    task_id: UUID
    state: str
    ready: bool
    result: Any = None
    error: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/scrape/reddit", status_code=202)
def trigger_reddit_scrape(payload: RedditScrapeRequest) -> dict[str, str]:
    try:
        task = scrape_reddit_task.delay(
            subreddit_url=str(payload.subreddit_url),
            limit=payload.limit,
            proxies=payload.proxies or None,
        )
    except Exception as exc:
        logger.exception("Failed to dispatch Reddit scrape for %s", payload.subreddit_url)
        raise HTTPException(
            status_code=503,
            detail="The scraping service is temporarily unavailable.",
        ) from exc

    return {
        "status": "accepted",
        "task_id": task.id,
        "target": str(payload.subreddit_url),
        "message": "Reddit collection task accepted.",
    }


@app.get("/v1/tasks/{task_id}", response_model=ScrapeTaskStatus)
def get_scraping_task_status(task_id: UUID) -> ScrapeTaskStatus:
    try:
        task_result = celery_app.AsyncResult(str(task_id))
        state = task_result.state
        ready = task_result.ready()
        result = None
        error = None

        if ready:
            if state == "SUCCESS":
                try:
                    # Attempt to fetch result with a tight timeout, handling potential backend lags safely
                    result = task_result.get(timeout=1.0, propagate=False)
                except TimeoutError:
                    # If fetching payload times out, mark state as still fetching rather than failing hard
                    state = "PENDING_FETCH"
                    ready = False
            elif state == "FAILURE":
                error = "Scrape task execution failed on worker."
                # Extract failure details if available safely
                if task_result.info:
                    error = f"Scrape task failed: {str(task_result.info)}"

    except Exception as exc:
        logger.exception("Failed to read scrape task status for %s", task_id)
        raise HTTPException(
            status_code=503,
            detail="Task status tracking is temporarily unavailable.",
        ) from exc

    return ScrapeTaskStatus(
        task_id=task_id,
        state=state,
        ready=ready,
        result=result,
        error=error,
    )