from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScrapeRequest(BaseModel):
    source: str
    target_url: HttpUrl
    options: dict[str, Any] = Field(default_factory=dict)


class ScrapeResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    target_url: HttpUrl
    scraped_at: datetime
    data: dict[str, Any]
