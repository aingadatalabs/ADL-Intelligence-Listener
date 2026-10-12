from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class UnifiedSignal(BaseModel):
    event_id: str
    platform: str = "reddit"
    signal_type: str  # post, comment
    external_id: str
    source_url: str
    author: str
    content: str
    published_at: datetime
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseScraperAdapter(ABC):
    @abstractmethod
    async def collect_signals(self, target: str, limit: int = 100) -> list[UnifiedSignal]:
        """Collects raw data and normalizes it into UnifiedSignal instances."""
        pass