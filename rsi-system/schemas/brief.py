"""Flash Brief schema — the daily morning report."""

import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field

from .signal import Signal, RoutingDecision


class BriefSection(BaseModel):
    """One section of the daily flash brief."""

    title: str = Field(..., description="Section heading")
    content: str = Field(..., description="Section body (Markdown)")
    priority: int = Field(default=0, ge=0, le=10, description="Display priority (10=highest)")


class PortfolioSnapshot(BaseModel):
    """Current portfolio state summary."""

    total_tickers_monitored: int = Field(default=0)
    blue_events_count: int = Field(default=0)
    yellow_events_count: int = Field(default=0)
    top_signals: list[Signal] = Field(default_factory=list, description="Top 5 signals by confidence")


class FlashBrief(BaseModel):
    """Complete daily Flash Brief — output of the observe agent."""

    brief_date: dt.date = Field(..., description="Brief date")
    generated_at: dt.datetime = Field(..., description="Generation timestamp")
    market_summary: str = Field(..., description="SET market overview (1-2 paragraphs)")
    sections: list[BriefSection] = Field(default_factory=list, description="Brief sections sorted by priority")
    routing_decisions: list[RoutingDecision] = Field(default_factory=list, description="All routing decisions from triage")
    portfolio_snapshot: Optional[PortfolioSnapshot] = Field(default=None, description="Portfolio state if available")
    model_used: str = Field(default="", description="Which model generated this brief")
    cost_usd: Optional[float] = Field(default=None, description="Estimated cloud API cost for this run")
    errors: list[str] = Field(default_factory=list, description="Non-fatal errors encountered during generation")
