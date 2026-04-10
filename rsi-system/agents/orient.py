"""🔵 Orient Agent — deep strategic analysis for significant events.

Triggered only when routing assigns 🔵 (blue) level to an event.
Uses the reasoning model (DeepSeek-R1) for complex analysis.
"""

import json
import logging
from datetime import date, datetime
from typing import Any, Optional

from adapters.mlx_adapter import MLXAdapter
from schemas.signal import RoutingDecision, Signal

logger = logging.getLogger(__name__)

ORIENT_SYSTEM_PROMPT = """You are an expert investment strategist analyzing a significant market event
affecting the Thai SET market.

Your analysis framework:
1. **Event Assessment**: What happened and why it matters
2. **Impact Chain**: First-order → second-order → third-order effects
3. **Affected Entities**: Which companies/sectors are impacted (positive and negative)
4. **Historical Analogues**: Similar past events and their outcomes
5. **Strategic Implications**: What actions should be considered
6. **Risk Factors**: What could invalidate this analysis

Output: JSON with fields:
- event_summary (str)
- impact_analysis (str, detailed markdown)
- affected_tickers (list of {ticker, direction, confidence, reasoning})
- historical_analogues (list of {event, date, outcome})
- strategic_recommendations (list of str)
- risk_factors (list of str)
- overall_confidence (int 0-100)"""


class OrientAnalysis:
    """Result of orient agent analysis."""

    def __init__(
        self,
        event_id: str,
        event_summary: str,
        impact_analysis: str,
        signals: list[Signal],
        strategic_recommendations: list[str],
        risk_factors: list[str],
        overall_confidence: int,
        model_used: str,
        raw_response: dict[str, Any],
    ):
        self.event_id = event_id
        self.event_summary = event_summary
        self.impact_analysis = impact_analysis
        self.signals = signals
        self.strategic_recommendations = strategic_recommendations
        self.risk_factors = risk_factors
        self.overall_confidence = overall_confidence
        self.model_used = model_used
        self.raw_response = raw_response
        self.created_at = datetime.now()


class OrientAgent:
    """Deep strategic analysis for blue-level events."""

    def __init__(self, mlx: Optional[MLXAdapter] = None):
        self.mlx = mlx or MLXAdapter()

    async def run(
        self,
        routing_decision: RoutingDecision,
        analysis_date: date,
        supplementary_data: Optional[dict[str, Any]] = None,
    ) -> OrientAnalysis:
        """Analyze a blue-level event with deep reasoning.

        Args:
            routing_decision: The blue-level routing decision to analyze
            analysis_date: Current analysis date
            supplementary_data: Additional context data (e.g., from Perplexity)

        Returns:
            OrientAnalysis with detailed strategic analysis
        """
        logger.info("Orient agent starting for event=%s", routing_decision.event_id)

        context = self._build_context(routing_decision, analysis_date, supplementary_data)

        try:
            # Use deep reasoning model for complex analysis
            response = await self.mlx.chat_reasoning(
                messages=[
                    {"role": "system", "content": ORIENT_SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                max_tokens=8192,
            )
            analysis = self._parse_response(response, routing_decision, analysis_date)
            logger.info("Orient agent completed: confidence=%d, %d signals", analysis.overall_confidence, len(analysis.signals))
            return analysis
        except Exception as e:
            logger.error("Orient agent failed for event=%s: %s", routing_decision.event_id, e)
            return self._fallback_analysis(routing_decision, str(e))

    def _build_context(
        self,
        routing: RoutingDecision,
        analysis_date: date,
        supplementary_data: Optional[dict[str, Any]],
    ) -> str:
        parts = [
            f"## Analysis Date: {analysis_date.isoformat()}",
            f"\n## Event Details",
            f"- **Event ID**: {routing.event_id}",
            f"- **Headline**: {routing.headline}",
            f"- **Source**: {routing.source}",
            f"- **Triage Reasoning**: {routing.reasoning}",
            f"- **Affected Tickers**: {', '.join(routing.affected_tickers)}",
        ]
        if routing.raw_data:
            parts.append(f"\n## Raw Source Data\n```json\n{json.dumps(routing.raw_data, ensure_ascii=False, default=str)}\n```")
        if supplementary_data:
            parts.append(f"\n## Supplementary Research\n```json\n{json.dumps(supplementary_data, ensure_ascii=False, default=str)}\n```")
        parts.append("\n## Task\nProvide deep strategic analysis of this event. Use the framework in your system prompt.")
        return "\n".join(parts)

    def _parse_response(self, response: str, routing: RoutingDecision, analysis_date: date) -> OrientAnalysis:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            return OrientAnalysis(
                event_id=routing.event_id,
                event_summary=routing.headline,
                impact_analysis=response,
                signals=[],
                strategic_recommendations=[],
                risk_factors=[],
                overall_confidence=30,
                model_used="mlx-reasoning",
                raw_response={"raw_text": response},
            )

        signals = []
        for t in data.get("affected_tickers", []):
            if isinstance(t, dict) and "ticker" in t:
                direction = t.get("direction", "neutral")
                signal_map = {"positive": "bullish", "negative": "bearish", "bullish": "bullish", "bearish": "bearish"}
                signals.append(
                    Signal(
                        ticker=t["ticker"],
                        signal=signal_map.get(direction, "neutral"),
                        confidence=t.get("confidence", 50),
                        reasoning=t.get("reasoning", ""),
                        data_sources=["orient_analysis"],
                        analysis_date=analysis_date,
                    )
                )

        return OrientAnalysis(
            event_id=routing.event_id,
            event_summary=data.get("event_summary", routing.headline),
            impact_analysis=data.get("impact_analysis", ""),
            signals=signals,
            strategic_recommendations=data.get("strategic_recommendations", []),
            risk_factors=data.get("risk_factors", []),
            overall_confidence=data.get("overall_confidence", 50),
            model_used="mlx-reasoning",
            raw_response=data,
        )

    def _fallback_analysis(self, routing: RoutingDecision, error: str) -> OrientAnalysis:
        return OrientAnalysis(
            event_id=routing.event_id,
            event_summary=f"[Analysis failed] {routing.headline}",
            impact_analysis=f"Orient agent failed: {error}",
            signals=[],
            strategic_recommendations=["Manual analysis recommended"],
            risk_factors=["Automated analysis unavailable"],
            overall_confidence=0,
            model_used="fallback",
            raw_response={"error": error},
        )
