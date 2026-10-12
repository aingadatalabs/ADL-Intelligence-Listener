import asyncio
import logging
from typing import Any

from celery_worker.app import app
from reddit_reddrix.adapter import RedditReddrixAdapter

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    name="celery_worker.tasks.scrape_reddit",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def scrape_reddit_task(
    self: Any,
    subreddit_url: str,
    limit: int = 100,
    proxies: list[str] | None = None,
) -> dict[str, Any]:
    if not 1 <= limit <= 500:
        raise ValueError("Scrape limit must be between 1 and 500.")

    logger.info("Starting Reddit scrape | Target: %s | Limit: %d", subreddit_url, limit)
    adapter = RedditReddrixAdapter(proxies=proxies)
    signals = asyncio.run(adapter.collect_signals(subreddit_url, limit))
    logger.info("Collected %d signals from %s", len(signals), subreddit_url)

    return {
        "status": "success",
        "subreddit": subreddit_url,
        "signals_collected": len(signals),
        "signals": [signal.model_dump(mode="json") for signal in signals],
    }
