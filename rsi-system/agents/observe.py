"""🟢 Observe Agent — generates the daily Flash Brief.

Pipeline step ⑤: Takes EOD data + news triage + routing signals
and produces a comprehensive morning brief.
"""

import json
import logging
from datetime import date, datetime
from typing import Any, Optional

from adapters.mlx_adapter import MLXAdapter
from schemas.brief import BriefSection, FlashBrief, PortfolioSnapshot
from schemas.signal import RoutingDecision, Signal

logger = logging.getLogger(__name__)

OBSERVE_SYSTEM_PROMPT = """You are a senior Thai equity market analyst preparing the daily Flash Brief.

Your role:
- Summarize SET market performance (index, volume, top movers)
- Highlight significant events from the news triage
- Rank signals by importance and actionability
- Flag any portfolio-relevant developments
- Write in concise, professional Thai-English mixed style (technical terms in English)

Output format: JSON matching the FlashBrief schema.
Focus on actionable insights, not noise."""


class ObserveAgent:
    """Daily Flash Brief generator."""

    def __init__(self, mlx: Optional[MLXAdapter] = None):
        self.mlx = mlx or MLXAdapter()

    async def run(
        self,
        analysis_date: date,
        eod_data: dict[str, Any],
        news_triage: list[dict[str, Any]],
        routing_decisions: list[RoutingDecision],
        bloomberg_data: Optional[dict[str, Any]] = None,
    ) -> FlashBrief:
        """Generate the daily Flash Brief.

        Args:
            analysis_date: Date of analysis
            eod_data: End-of-day price/volume data
            news_triage: Triaged news items from Grok/Perplexity
            routing_decisions: Signal routing from triage step
            bloomberg_data: Optional Bloomberg CSV data if available

        Returns:
            Complete FlashBrief ready for user consumption
        """
        logger.info("Observe agent starting for %s", analysis_date)

        # Build context for the LLM
        context = self._build_context(analysis_date, eod_data, news_triage, routing_decisions, bloomberg_data)

        try:
            response = await self.mlx.chat_json(
                messages=[
                    {"role": "system", "content": OBSERVE_SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                max_tokens=4096,
            )
            brief = self._parse_response(response, analysis_date, routing_decisions)
            logger.info("Observe agent completed: %d sections, %d routing decisions", len(brief.sections), len(brief.routing_decisions))
            return brief
        except Exception as e:
            logger.error("Observe agent failed: %s", e)
            return self._fallback_brief(analysis_date, routing_decisions, str(e))

    def _build_context(
        self,
        analysis_date: date,
        eod_data: dict[str, Any],
        news_triage: list[dict[str, Any]],
        routing_decisions: list[RoutingDecision],
        bloomberg_data: Optional[dict[str, Any]],
    ) -> str:
        parts = [
            f"## Date: {analysis_date.isoformat()}",
            f"\n## EOD Market Data\n```json\n{json.dumps(eod_data, ensure_ascii=False, default=str)}\n```",
            f"\n## News Triage ({len(news_triage)} items)\n```json\n{json.dumps(news_triage, ensure_ascii=False, default=str)}\n```",
            f"\n## Routing Decisions ({len(routing_decisions)} items)\n```json\n{json.dumps([r.model_dump() for r in routing_decisions], ensure_ascii=False, default=str)}\n```",
        ]
        if bloomberg_data:
            parts.append(f"\n## Bloomberg Data\n```json\n{json.dumps(bloomberg_data, ensure_ascii=False, default=str)}\n```")
        parts.append("\n## Task\nGenerate a FlashBrief JSON with: market_summary, sections (sorted by priority), portfolio_snapshot.")
        return "\n".join(parts)

    def _parse_response(self, response: str, analysis_date: date, routing_decisions: list[RoutingDecision]) -> FlashBrief:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON, wrapping as single section")
            return FlashBrief(
                brief_date=analysis_date,
                generated_at=datetime.now(),
                market_summary=response[:500],
                sections=[BriefSection(title="Raw Analysis", content=response, priority=5)],
                routing_decisions=routing_decisions,
                model_used="mlx-main",
            )

        sections = [BriefSection(**s) for s in data.get("sections", [])]
        snapshot = None
        if "portfolio_snapshot" in data:
            ps = data["portfolio_snapshot"]
            top_signals = [Signal(**s) for s in ps.get("top_signals", [])]
            snapshot = PortfolioSnapshot(
                total_tickers_monitored=ps.get("total_tickers_monitored", 0),
                blue_events_count=ps.get("blue_events_count", 0),
                yellow_events_count=ps.get("yellow_events_count", 0),
                top_signals=top_signals,
            )

        return FlashBrief(
            brief_date=analysis_date,
            generated_at=datetime.now(),
            market_summary=data.get("market_summary", "No market summary available"),
            sections=sorted(sections, key=lambda s: s.priority, reverse=True),
            routing_decisions=routing_decisions,
            portfolio_snapshot=snapshot,
            model_used="mlx-main",
        )

    def _fallback_brief(self, analysis_date: date, routing_decisions: list[RoutingDecision], error: str) -> FlashBrief:
        """Graceful degradation — return a minimal brief on failure."""
        return FlashBrief(
            brief_date=analysis_date,
            generated_at=datetime.now(),
            market_summary="⚠️ Flash Brief generation failed. Routing decisions are available below.",
            sections=[BriefSection(title="System Notice", content=f"Observe agent encountered an error: {error}", priority=10)],
            routing_decisions=routing_decisions,
            model_used="fallback",
            errors=[error],
        )
