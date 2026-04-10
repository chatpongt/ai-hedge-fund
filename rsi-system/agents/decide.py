"""🟡 Decide Agent — valuation prep and recommendation output.

Takes signals from observe/orient and prepares actionable recommendations.
Output is RECOMMENDATION ONLY — never auto-executes trades.
"""

import json
import logging
import datetime as dt
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from adapters.mlx_adapter import MLXAdapter
from schemas.signal import Signal

logger = logging.getLogger(__name__)

DECIDE_SYSTEM_PROMPT = """You are a portfolio decision advisor for Thai SET equities.

Given analyst signals, prepare a recommendation for each ticker:

Rules:
1. Output is RECOMMENDATION ONLY — no automatic execution
2. Consider signal consensus across multiple analysts
3. Factor in confidence-weighted average
4. Apply position sizing guidance based on conviction
5. Flag conflicting signals explicitly

Output: JSON with fields:
- recommendations (list of {ticker, action, conviction, rationale, position_size_pct, risk_notes})
- portfolio_notes (str, overall portfolio considerations)
- conflicting_signals (list of {ticker, signals, resolution})

Actions: BUY, SELL, HOLD, WATCH, REDUCE, ACCUMULATE"""


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WATCH = "WATCH"
    REDUCE = "REDUCE"
    ACCUMULATE = "ACCUMULATE"


class Recommendation(BaseModel):
    """Single ticker recommendation."""

    ticker: str
    action: Action
    conviction: int = Field(ge=0, le=100, description="Conviction level 0-100")
    rationale: str
    position_size_pct: float = Field(ge=0, le=100, description="Suggested position size as % of portfolio")
    risk_notes: str = ""
    generated_at: dt.datetime = Field(default_factory=dt.datetime.now)


class DecideOutput(BaseModel):
    """Complete decide agent output."""

    analysis_date: dt.date
    recommendations: list[Recommendation]
    portfolio_notes: str = ""
    conflicting_signals: list[dict[str, Any]] = Field(default_factory=list)
    model_used: str = ""
    errors: list[str] = Field(default_factory=list)


class DecideAgent:
    """Valuation prep and recommendation generator."""

    def __init__(self, mlx: Optional[MLXAdapter] = None):
        self.mlx = mlx or MLXAdapter()

    async def run(
        self,
        analysis_date: dt.date,
        signals: list[Signal],
        orient_analyses: Optional[list[Any]] = None,
        portfolio_context: Optional[dict[str, Any]] = None,
    ) -> DecideOutput:
        """Generate recommendations from collected signals.

        Args:
            analysis_date: Current analysis date
            signals: All signals collected from observe/orient
            orient_analyses: Deep analyses from orient agent (if any)
            portfolio_context: Current portfolio state

        Returns:
            DecideOutput with actionable recommendations
        """
        logger.info("Decide agent starting: %d signals", len(signals))

        if not signals:
            logger.warning("No signals to process")
            return DecideOutput(analysis_date=analysis_date, recommendations=[], portfolio_notes="No signals available for decision making.")

        context = self._build_context(analysis_date, signals, orient_analyses, portfolio_context)

        try:
            response = await self.mlx.chat_json(
                messages=[
                    {"role": "system", "content": DECIDE_SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                max_tokens=4096,
            )
            output = self._parse_response(response, analysis_date)
            logger.info("Decide agent completed: %d recommendations", len(output.recommendations))
            return output
        except Exception as e:
            logger.error("Decide agent failed: %s", e)
            return DecideOutput(analysis_date=analysis_date, recommendations=[], errors=[str(e)], model_used="fallback")

    def _build_context(
        self,
        analysis_date: dt.date,
        signals: list[Signal],
        orient_analyses: Optional[list[Any]],
        portfolio_context: Optional[dict[str, Any]],
    ) -> str:
        parts = [
            f"## Date: {analysis_date.isoformat()}",
            f"\n## Analyst Signals ({len(signals)} total)",
        ]

        # Group signals by ticker
        by_ticker: dict[str, list[Signal]] = {}
        for s in signals:
            by_ticker.setdefault(s.ticker, []).append(s)

        for ticker, ticker_signals in by_ticker.items():
            parts.append(f"\n### {ticker}")
            for s in ticker_signals:
                parts.append(f"- {s.signal} (confidence={s.confidence}): {s.reasoning[:200]}")

        if orient_analyses:
            parts.append(f"\n## Deep Analyses ({len(orient_analyses)} events)")
            for oa in orient_analyses:
                parts.append(f"- **{oa.event_summary}** (confidence={oa.overall_confidence})")
                for rec in oa.strategic_recommendations[:3]:
                    parts.append(f"  - {rec}")

        if portfolio_context:
            parts.append(f"\n## Current Portfolio\n```json\n{json.dumps(portfolio_context, ensure_ascii=False, default=str)}\n```")

        parts.append("\n## Task\nGenerate recommendations. Remember: RECOMMENDATION ONLY, never auto-execute.")
        return "\n".join(parts)

    def _parse_response(self, response: str, analysis_date: dt.date) -> DecideOutput:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            return DecideOutput(
                date=analysis_date,
                recommendations=[],
                portfolio_notes=response[:500],
                model_used="mlx-main",
                errors=["Failed to parse LLM response as JSON"],
            )

        recommendations = []
        for r in data.get("recommendations", []):
            try:
                action = Action(r.get("action", "HOLD").upper())
                recommendations.append(
                    Recommendation(
                        ticker=r["ticker"],
                        action=action,
                        conviction=r.get("conviction", 50),
                        rationale=r.get("rationale", ""),
                        position_size_pct=r.get("position_size_pct", 0),
                        risk_notes=r.get("risk_notes", ""),
                    )
                )
            except (KeyError, ValueError) as e:
                logger.warning("Skipping invalid recommendation: %s", e)

        return DecideOutput(
            date=analysis_date,
            recommendations=recommendations,
            portfolio_notes=data.get("portfolio_notes", ""),
            conflicting_signals=data.get("conflicting_signals", []),
            model_used="mlx-main",
        )
