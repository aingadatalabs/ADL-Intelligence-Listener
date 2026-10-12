"""Compatibility exports for the installed celery_worker package."""

from celery_worker.tasks import scrape_reddit_task

__all__ = ["scrape_reddit_task"]
