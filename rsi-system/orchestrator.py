"""RSI Hybrid System — Main Pipeline Orchestrator.

Daily automation flow:
  ① fetch EOD data
  ② detect Bloomberg CSV drop
  ③ Grok + Perplexity → news triage
  ④ Qwen 4B → routing signals (🔵/🟡/⚪)
  ⑤ Qwen 32B → Flash Brief (observe)
  ⑥ [if 🔵] orient agent → strategic analysis
  ⑦ wiki_ingest → /mnt/outputs/wiki/
  ⑧ learn agent → lesson capture
  ⑨ notification → "Brief พร้อมแล้ว"

Usage:
    python orchestrator.py                    # Run full pipeline for today
    python orchestrator.py --date 2026-04-10  # Run for specific date
    python orchestrator.py --step observe     # Run single step
"""

import argparse
import asyncio
import csv
import json
import logging
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from adapters import GeminiAdapter, GrokAdapter, MLXAdapter, PerplexityAdapter
from adapters.base import AdapterError
from agents.decide import DecideAgent
from agents.observe import ObserveAgent
from agents.orient import OrientAgent
from agents.wiki_ingest import WikiIngestAgent
from config.settings import settings
from log_setup import setup_logging
from schemas.signal import RoutingDecision, Signal, SignalLevel

logger = logging.getLogger(__name__)


class PipelineContext:
    """Shared state across pipeline steps."""

    def __init__(self, analysis_date: date):
        self.analysis_date = analysis_date
        self.eod_data: dict[str, Any] = {}
        self.bloomberg_data: Optional[dict[str, Any]] = None
        self.news_triage: list[dict[str, Any]] = []
        self.routing_decisions: list[RoutingDecision] = []
        self.signals: list[Signal] = []
        self.brief: Optional[Any] = None
        self.orient_analyses: list[Any] = []
        self.decide_output: Optional[Any] = None
        self.wiki_entries: list[Any] = []
        self.errors: list[str] = []
        self.step_timings: dict[str, float] = {}

    def log_summary(self) -> dict[str, Any]:
        return {
            "date": self.analysis_date.isoformat(),
            "eod_tickers": len(self.eod_data),
            "news_items": len(self.news_triage),
            "routing_blue": sum(1 for r in self.routing_decisions if r.level == SignalLevel.BLUE),
            "routing_yellow": sum(1 for r in self.routing_decisions if r.level == SignalLevel.YELLOW),
            "signals": len(self.signals),
            "orient_analyses": len(self.orient_analyses),
            "wiki_entries": len(self.wiki_entries),
            "errors": self.errors,
            "step_timings": self.step_timings,
        }


class Orchestrator:
    """Main pipeline orchestrator."""

    def __init__(self):
        self.mlx = MLXAdapter()
        self.perplexity = PerplexityAdapter()
        self.grok = GrokAdapter()
        self.gemini = GeminiAdapter()

        self.observe_agent = ObserveAgent(self.mlx)
        self.orient_agent = OrientAgent(self.mlx)
        self.decide_agent = DecideAgent(self.mlx)
        self.wiki_agent = WikiIngestAgent(self.mlx)

    async def run_full_pipeline(self, analysis_date: date) -> PipelineContext:
        """Execute the complete daily pipeline."""
        ctx = PipelineContext(analysis_date)
        logger.info("=== RSI Pipeline starting for %s ===", analysis_date)

        steps = [
            ("fetch_eod", self._step_fetch_eod),
            ("detect_bloomberg", self._step_detect_bloomberg),
            ("news_triage", self._step_news_triage),
            ("routing", self._step_routing),
            ("observe", self._step_observe),
            ("orient", self._step_orient),
            ("decide", self._step_decide),
            ("wiki_ingest", self._step_wiki_ingest),
            ("notify", self._step_notify),
        ]

        for step_name, step_fn in steps:
            start = datetime.now()
            try:
                await step_fn(ctx)
                elapsed = (datetime.now() - start).total_seconds()
                ctx.step_timings[step_name] = elapsed
                logger.info("Step %s completed in %.1fs", step_name, elapsed)
            except Exception as e:
                elapsed = (datetime.now() - start).total_seconds()
                ctx.step_timings[step_name] = elapsed
                error_msg = f"Step {step_name} failed: {e}"
                ctx.errors.append(error_msg)
                logger.error(error_msg)
                # Graceful degradation — continue pipeline

        # Save pipeline log
        self._save_pipeline_log(ctx)
        logger.info("=== RSI Pipeline completed: %s ===", json.dumps(ctx.log_summary(), default=str))
        return ctx

    async def run_single_step(self, step_name: str, analysis_date: date) -> PipelineContext:
        """Run a single pipeline step (for debugging/testing)."""
        ctx = PipelineContext(analysis_date)
        step_map = {
            "fetch_eod": self._step_fetch_eod,
            "detect_bloomberg": self._step_detect_bloomberg,
            "news_triage": self._step_news_triage,
            "routing": self._step_routing,
            "observe": self._step_observe,
            "orient": self._step_orient,
            "decide": self._step_decide,
            "wiki_ingest": self._step_wiki_ingest,
            "notify": self._step_notify,
        }
        step_fn = step_map.get(step_name)
        if not step_fn:
            raise ValueError(f"Unknown step: {step_name}. Available: {list(step_map.keys())}")
        await step_fn(ctx)
        return ctx

    # ── Step implementations ──────────────────────────────────────

    async def _step_fetch_eod(self, ctx: PipelineContext) -> None:
        """① Fetch end-of-day market data."""
        logger.info("Fetching EOD data for %s", ctx.analysis_date)
        # TODO: Implement Yahoo Finance / FMP API integration
        # For now, provide a placeholder structure
        ctx.eod_data = {
            "date": ctx.analysis_date.isoformat(),
            "set_index": {"close": 0, "change_pct": 0, "volume": 0},
            "tickers": {},
            "source": "placeholder",
        }
        logger.warning("EOD fetch using placeholder — implement Yahoo/FMP integration")

    async def _step_detect_bloomberg(self, ctx: PipelineContext) -> None:
        """② Check for Bloomberg CSV files in drop folder."""
        drop_dir = settings.paths.bloomberg_drop
        if not drop_dir.exists():
            logger.info("Bloomberg drop folder does not exist, skipping")
            return

        csv_files = sorted(drop_dir.glob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not csv_files:
            logger.info("No Bloomberg CSV files found")
            return

        # Process the most recent CSV
        latest = csv_files[0]
        logger.info("Found Bloomberg CSV: %s", latest.name)
        try:
            with open(latest, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            ctx.bloomberg_data = {"file": latest.name, "rows": len(rows), "data": rows[:100]}  # cap at 100 rows for context
            logger.info("Loaded %d rows from Bloomberg CSV", len(rows))
        except Exception as e:
            logger.error("Failed to read Bloomberg CSV: %s", e)

    async def _step_news_triage(self, ctx: PipelineContext) -> None:
        """③ Gather news from Grok + Perplexity."""
        tasks = []

        if settings.pipeline.enable_grok:
            tasks.append(self._fetch_grok_news(ctx))
        if settings.pipeline.enable_perplexity:
            tasks.append(self._fetch_perplexity_data(ctx))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("News triage collected %d items", len(ctx.news_triage))

    async def _fetch_grok_news(self, ctx: PipelineContext) -> None:
        try:
            topics = ["SET index", "Thai stocks", "Bank of Thailand", "SEC Thailand"]
            result = await self.grok.scan_news(topics, market="SET")
            ctx.news_triage.append({"source": "grok", "data": result, "timestamp": datetime.now().isoformat()})
        except AdapterError as e:
            logger.warning("Grok news fetch failed (graceful skip): %s", e)
            ctx.errors.append(f"Grok unavailable: {e}")

    async def _fetch_perplexity_data(self, ctx: PipelineContext) -> None:
        try:
            result = await self.perplexity.search(f"Thai SET market news today {ctx.analysis_date.isoformat()}, key events, macro data")
            ctx.news_triage.append({"source": "perplexity", "data": result, "timestamp": datetime.now().isoformat()})
        except AdapterError as e:
            logger.warning("Perplexity fetch failed (graceful skip): %s", e)
            ctx.errors.append(f"Perplexity unavailable: {e}")

    async def _step_routing(self, ctx: PipelineContext) -> None:
        """④ Use Qwen 4B (fast model) to route news into signal levels."""
        if not ctx.news_triage:
            logger.info("No news to route")
            return

        routing_prompt = f"""Analyze these news items and assign routing levels:
- 🔵 BLUE: Significant event requiring deep analysis (orient agent)
- 🟡 YELLOW: Noteworthy, monitor closely
- ⚪ WHITE: Routine, log only

News items:
```json
{json.dumps(ctx.news_triage, ensure_ascii=False, default=str)}
```

Output: JSON list of routing decisions with fields:
event_id, headline, level (blue/yellow/white), affected_tickers, reasoning, requires_orient, source"""

        try:
            response = await self.mlx.chat_fast(
                messages=[
                    {"role": "system", "content": "You are a financial news triage system for the Thai SET market. Route events by significance."},
                    {"role": "user", "content": routing_prompt},
                ],
                max_tokens=2048,
            )
            decisions = self._parse_routing(response)
            ctx.routing_decisions = decisions
            logger.info("Routing: %d blue, %d yellow, %d white", sum(1 for d in decisions if d.level == SignalLevel.BLUE), sum(1 for d in decisions if d.level == SignalLevel.YELLOW), sum(1 for d in decisions if d.level == SignalLevel.WHITE))
        except Exception as e:
            logger.error("Routing step failed: %s", e)

    def _parse_routing(self, response: str) -> list[RoutingDecision]:
        try:
            data = json.loads(response)
            items = data if isinstance(data, list) else data.get("routing_decisions", data.get("decisions", []))
        except json.JSONDecodeError:
            logger.warning("Routing response not JSON")
            return []

        decisions = []
        for i, item in enumerate(items):
            try:
                level_str = item.get("level", "white").lower()
                level = SignalLevel(level_str)
                decisions.append(
                    RoutingDecision(
                        event_id=item.get("event_id", f"evt-{ctx_date_str()}-{i:03d}"),
                        headline=item.get("headline", "Unknown event"),
                        level=level,
                        affected_tickers=item.get("affected_tickers", []),
                        reasoning=item.get("reasoning", ""),
                        requires_orient=level == SignalLevel.BLUE,
                        source=item.get("source", "unknown"),
                        raw_data=item,
                    )
                )
            except Exception as e:
                logger.warning("Skipping invalid routing decision: %s", e)
        return decisions

    async def _step_observe(self, ctx: PipelineContext) -> None:
        """⑤ Generate Flash Brief."""
        ctx.brief = await self.observe_agent.run(
            analysis_date=ctx.analysis_date,
            eod_data=ctx.eod_data,
            news_triage=ctx.news_triage,
            routing_decisions=ctx.routing_decisions,
            bloomberg_data=ctx.bloomberg_data,
        )
        # Save brief to file
        brief_path = settings.paths.logs_dir / f"brief-{ctx.analysis_date.isoformat()}.json"
        brief_path.write_text(ctx.brief.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Flash Brief saved to %s", brief_path)

    async def _step_orient(self, ctx: PipelineContext) -> None:
        """⑥ Deep analysis for blue-level events."""
        blue_events = [r for r in ctx.routing_decisions if r.level == SignalLevel.BLUE]
        if not blue_events:
            logger.info("No blue events — skipping orient")
            return

        logger.info("Orient analyzing %d blue events", len(blue_events))
        for event in blue_events:
            # Optionally enrich with Perplexity data
            supplementary = None
            if settings.pipeline.enable_perplexity:
                try:
                    search_result = await self.perplexity.search(f"Details about: {event.headline}")
                    supplementary = {"perplexity_research": search_result}
                except AdapterError:
                    pass

            analysis = await self.orient_agent.run(event, ctx.analysis_date, supplementary)
            ctx.orient_analyses.append(analysis)
            ctx.signals.extend(analysis.signals)

    async def _step_decide(self, ctx: PipelineContext) -> None:
        """⑦ Generate recommendations from signals."""
        if not ctx.signals and not ctx.routing_decisions:
            logger.info("No signals for decide agent")
            return

        ctx.decide_output = await self.decide_agent.run(
            analysis_date=ctx.analysis_date,
            signals=ctx.signals,
            orient_analyses=ctx.orient_analyses,
        )

        # Save recommendations
        if ctx.decide_output:
            decide_path = settings.paths.logs_dir / f"decide-{ctx.analysis_date.isoformat()}.json"
            decide_path.write_text(ctx.decide_output.model_dump_json(indent=2), encoding="utf-8")

    async def _step_wiki_ingest(self, ctx: PipelineContext) -> None:
        """⑧ Capture knowledge into wiki."""
        brief_data = ctx.brief.model_dump() if ctx.brief else None
        orient_data = [a.raw_response for a in ctx.orient_analyses] if ctx.orient_analyses else None
        decide_data = ctx.decide_output.model_dump() if ctx.decide_output else None

        ctx.wiki_entries = await self.wiki_agent.run(
            analysis_date=ctx.analysis_date,
            brief_data=brief_data,
            orient_data=orient_data,
            decide_data=decide_data,
        )

    async def _step_notify(self, ctx: PipelineContext) -> None:
        """⑨ Send macOS notification."""
        if not settings.pipeline.notification_enabled:
            return

        blue_count = sum(1 for r in ctx.routing_decisions if r.level == SignalLevel.BLUE)
        msg = f"RSI Brief พร้อมแล้ว ({ctx.analysis_date})"
        if blue_count:
            msg += f" — {blue_count} blue events"
        if ctx.errors:
            msg += f" — {len(ctx.errors)} warnings"

        try:
            subprocess.run(
                ["osascript", "-e", f'display notification "{msg}" with title "RSI System"'],
                capture_output=True,
                timeout=5,
            )
            logger.info("Notification sent: %s", msg)
        except FileNotFoundError:
            logger.info("macOS notification skipped (not on macOS): %s", msg)
        except Exception as e:
            logger.warning("Notification failed: %s", e)

    def _save_pipeline_log(self, ctx: PipelineContext) -> None:
        log_path = settings.paths.logs_dir / f"pipeline-{ctx.analysis_date.isoformat()}.json"
        log_path.write_text(json.dumps(ctx.log_summary(), indent=2, default=str), encoding="utf-8")


def ctx_date_str() -> str:
    return date.today().isoformat()


async def health_check() -> dict[str, bool]:
    """Check all adapter health."""
    orch = Orchestrator()
    results = {}
    checks = [
        ("mlx", orch.mlx.health_check()),
        ("perplexity", orch.perplexity.health_check()),
        ("grok", orch.grok.health_check()),
        ("gemini", orch.gemini.health_check()),
    ]
    for name, coro in checks:
        try:
            results[name] = await coro
        except Exception:
            results[name] = False
    return results


def main():
    parser = argparse.ArgumentParser(description="RSI Hybrid System — Daily Pipeline")
    parser.add_argument("--date", type=str, default=None, help="Analysis date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--step", type=str, default=None, help="Run single step only")
    parser.add_argument("--health", action="store_true", help="Run health check and exit")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(debug=args.verbose)

    if args.health:
        results = asyncio.run(health_check())
        for name, ok in results.items():
            status = "OK" if ok else "UNAVAILABLE"
            print(f"  {name}: {status}")
        sys.exit(0 if all(results.values()) else 1)

    analysis_date = date.fromisoformat(args.date) if args.date else date.today()
    orch = Orchestrator()

    if args.step:
        ctx = asyncio.run(orch.run_single_step(args.step, analysis_date))
    else:
        ctx = asyncio.run(orch.run_full_pipeline(analysis_date))

    if ctx.errors:
        print(f"\n⚠️  Pipeline completed with {len(ctx.errors)} warnings:")
        for err in ctx.errors:
            print(f"  - {err}")
    else:
        print(f"\n✅ Pipeline completed successfully for {analysis_date}")


if __name__ == "__main__":
    main()
