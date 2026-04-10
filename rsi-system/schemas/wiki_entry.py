"""Wiki Entry schema — persistent knowledge base entries."""

import datetime as dt
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WikiCategory(str, Enum):
    """Knowledge wiki categories."""

    COMPANY = "company"  # Company-specific knowledge
    SECTOR = "sector"  # Sector/industry analysis
    MACRO = "macro"  # Macroeconomic data
    STRATEGY = "strategy"  # Investment strategy insights
    LESSON = "lesson"  # Lessons learned from past decisions
    EVENT = "event"  # Significant market events


class WikiEntry(BaseModel):
    """A single knowledge wiki entry."""

    entry_id: str = Field(..., description="Unique entry ID (YYYY-MM-DD-slug)")
    category: WikiCategory = Field(..., description="Knowledge category")
    title: str = Field(..., description="Entry title")
    content: str = Field(..., description="Entry body (Markdown)")
    tickers: list[str] = Field(default_factory=list, description="Related tickers")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    source: str = Field(..., description="Data source")
    created_at: dt.datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[dt.datetime] = Field(default=None, description="Last update timestamp")
    supersedes: Optional[str] = Field(default=None, description="Entry ID this supersedes (for updates)")
    confidence: int = Field(default=50, ge=0, le=100, description="Confidence in this knowledge")
    expiry_date: Optional[dt.date] = Field(default=None, description="When this knowledge may become stale")
