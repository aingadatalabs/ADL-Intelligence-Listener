import logging
from datetime import datetime, timezone
from typing import Any
from reddrix import Reddrix
from core_engine.base import BaseScraperAdapter, UnifiedSignal
from reddit_reddrix.validation import validate_subreddit_url

logger = logging.getLogger(__name__)

class RedditReddrixAdapter(BaseScraperAdapter):
    def __init__(self, proxies: list[str] | None = None):
        self.proxies = proxies or []

    async def collect_signals(self, target_subreddit_url: str, limit: int = 100) -> list[UnifiedSignal]:
        validate_subreddit_url(target_subreddit_url)
        signals: list[UnifiedSignal] = []
        
        try:
            async with Reddrix(
                mode="standard",
                subreddit_urls=[target_subreddit_url],
                sort="new",
                include_comments=True,
                max_results=limit,
                max_posts_per_collection=limit,
                proxies=self.proxies,
                verbose=False
            ) as reddrix:
                async for item in reddrix.get_items():
                    try:
                        # Defensive extraction of required identifiers
                        sub_id = item.get("submissionId")
                        if not sub_id:
                            continue  # Skip items lacking a primary key

                        # Safe timestamp normalization (handling trailing 'Z' for UTC)
                        raw_date = item.get("submittedAt")
                        if raw_date:
                            if raw_date.endswith("Z"):
                                raw_date = raw_date[:-1] + "+00:00"
                            published_dt = datetime.fromisoformat(raw_date)
                        else:
                            published_dt = datetime.now(timezone.utc)

                        signal = UnifiedSignal(
                            event_id=f"reddit_{sub_id}",
                            platform="reddit",
                            signal_type=item.get("submissionType", "post"),
                            external_id=sub_id,
                            source_url=item.get("submissionUrl", target_subreddit_url),
                            author=item.get("author", "[deleted]"),
                            content=item.get("bodyText") or item.get("title") or "",
                            published_at=published_dt,
                            engagement_metrics={
                                "score": item.get("score", 0),
                                "upvote_ratio": item.get("upvoteRatio"),
                                "num_comments": item.get("numComments")
                            },
                            raw_metadata=item
                        )
                        signals.append(signal)

                    except Exception as item_exc:
                        # Isolate parsing errors on individual items so one bad post doesn't fail the batch
                        logger.warning("Failed to parse individual Reddit item: %s", str(item_exc))
                        continue

        except Exception as exc:
            logger.exception("Reddit collection session failed for URL: %s", target_subreddit_url)
            raise RuntimeError(f"Reddit collection failed: {str(exc)}") from exc
            
        return signals