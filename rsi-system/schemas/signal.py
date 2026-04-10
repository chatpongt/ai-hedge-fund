"""Signal schemas — output contracts between agents."""

import datetime as dt
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SignalLevel(str, Enum):
    """Priority routing level from triage."""

    BLUE = "blue"  # 🔵 significant event — needs orient analysis
    YELLOW = "yellow"  # 🟡 noteworthy — monitor
    WHITE = "white"  # ⚪ routine — log only


class Signal(BaseModel):
    """Standard signal output from any analyst agent."""

    ticker: str = Field(..., description="Stock ticker (e.g., 'SET:AOT', 'SET:CPALL')")
    signal: str = Field(..., pattern="^(bullish|bearish|neutral)$", description="Directional signal")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    reasoning: str = Field(..., min_length=10, description="Explanation of the signal")
    data_sources: list[str] = Field(default_factory=list, description="Sources used for analysis")
    analysis_date: dt.date = Field(..., description="Analysis date")

    model_config = {"json_schema_extra": {"examples": [{"ticker": "SET:AOT", "signal": "bullish", "confidence": 75, "reasoning": "Strong passenger recovery post-COVID, Q3 revenue beat estimates by 12%", "data_sources": ["eod_price", "financials", "news"], "analysis_date": "2026-04-10"}]}}


class RoutingDecision(BaseModel):
    """Triage routing decision from Qwen 4B fast model."""

    event_id: str = Field(..., description="Unique event identifier")
    headline: str = Field(..., description="Event headline")
    level: SignalLevel = Field(..., description="Priority routing level")
    affected_tickers: list[str] = Field(default_factory=list, description="Tickers impacted by this event")
    reasoning: str = Field(..., description="Why this routing level was chosen")
    requires_orient: bool = Field(default=False, description="Whether orient agent should analyze this")
    source: str = Field(..., description="Where the event came from (grok, perplexity, bloomberg)")
    raw_data: Optional[dict] = Field(default=None, description="Original source data for traceability")
