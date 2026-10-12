from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl, ValidationError

from listener_api.main import RedditScrapeRequest, app

client = TestClient(app)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.reddit.com/r/python",
        "https://127.0.0.1/r/python",
        "https://www.reddit.com.evil.test/r/python",
        "https://www.reddit.com/r/python/comments/123",
        "https://www.reddit.com/r/python?redirect=https://127.0.0.1",
    ],
)
def test_scrape_request_rejects_unsafe_targets(url: str) -> None:
    with pytest.raises(ValidationError):
        # Cast to HttpUrl to satisfy strict static type checkers during test initialization
        RedditScrapeRequest(subreddit_url=cast(HttpUrl, url))


def test_scrape_request_bounds_limit_and_proxy_count() -> None:
    with pytest.raises(ValidationError):
        RedditScrapeRequest(
            subreddit_url=cast(HttpUrl, "https://www.reddit.com/r/python"), 
            limit=501
        )
    with pytest.raises(ValidationError):
        RedditScrapeRequest(
            subreddit_url=cast(HttpUrl, "https://www.reddit.com/r/python"),
            proxies=["https://proxy.example"] * 11,
        )


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scrape_endpoint_dispatches_valid_request(monkeypatch: pytest.MonkeyPatch) -> None:
    dispatch = Mock(return_value=SimpleNamespace(id="00000000-0000-0000-0000-000000000001"))
    monkeypatch.setattr("listener_api.main.scrape_reddit_task.delay", dispatch)

    response = client.post(
        "/v1/scrape/reddit",
        json={"subreddit_url": "https://www.reddit.com/r/python", "limit": 25},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    dispatch.assert_called_once_with(
        subreddit_url="https://www.reddit.com/r/python",
        limit=25,
        proxies=None,
    )


def test_scrape_endpoint_does_not_return_internal_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatch = Mock(side_effect=RuntimeError("broker password leaked"))
    monkeypatch.setattr("listener_api.main.scrape_reddit_task.delay", dispatch)

    response = client.post(
        "/v1/scrape/reddit",
        json={"subreddit_url": "https://www.reddit.com/r/python"},
    )

    assert response.status_code == 503
    assert "broker password leaked" not in response.text