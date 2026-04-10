"""Golden tests for output schemas — ensures agents can communicate."""

import json
import pytest
from datetime import date, datetime

from schemas.signal import Signal, SignalLevel, RoutingDecision
from schemas.brief import FlashBrief, BriefSection, PortfolioSnapshot
from schemas.wiki_entry import WikiEntry, WikiCategory


class TestSignalSchema:
    """Tests for Signal output contract."""

    def test_valid_signal(self, sample_signal):
        assert sample_signal.ticker == "SET:AOT"
        assert sample_signal.signal == "bullish"
        assert 0 <= sample_signal.confidence <= 100

    def test_signal_json_roundtrip(self, sample_signal):
        json_str = sample_signal.model_dump_json()
        restored = Signal.model_validate_json(json_str)
        assert restored.ticker == sample_signal.ticker
        assert restored.confidence == sample_signal.confidence

    def test_invalid_signal_direction(self):
        with pytest.raises(Exception):
            Signal(
                ticker="SET:AOT",
                signal="very_bullish",  # invalid
                confidence=75,
                reasoning="test reasoning here for validation",
                analysis_date=date(2026, 4, 10),
            )

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            Signal(
                ticker="SET:AOT",
                signal="bullish",
                confidence=150,  # out of range
                reasoning="test reasoning here for validation",
                analysis_date=date(2026, 4, 10),
            )

    def test_signal_requires_reasoning(self):
        with pytest.raises(Exception):
            Signal(
                ticker="SET:AOT",
                signal="bullish",
                confidence=75,
                reasoning="short",  # too short (min_length=10)
                analysis_date=date(2026, 4, 10),
            )


class TestRoutingDecision:
    """Tests for triage routing contract."""

    def test_valid_routing(self, sample_routing_decision):
        assert sample_routing_decision.level == SignalLevel.BLUE
        assert sample_routing_decision.requires_orient is True

    def test_routing_json_roundtrip(self, sample_routing_decision):
        json_str = sample_routing_decision.model_dump_json()
        restored = RoutingDecision.model_validate_json(json_str)
        assert restored.event_id == sample_routing_decision.event_id
        assert restored.level == SignalLevel.BLUE

    def test_all_signal_levels(self):
        for level in SignalLevel:
            rd = RoutingDecision(
                event_id=f"test-{level.value}",
                headline="Test event",
                level=level,
                reasoning="Test",
                source="test",
            )
            assert rd.level == level


class TestFlashBrief:
    """Tests for Flash Brief output contract."""

    def test_valid_brief(self, sample_brief):
        assert len(sample_brief.sections) == 2
        assert sample_brief.sections[0].priority >= 0

    def test_brief_json_roundtrip(self, sample_brief):
        json_str = sample_brief.model_dump_json()
        data = json.loads(json_str)
        assert "market_summary" in data
        assert "sections" in data
        assert "routing_decisions" in data

    def test_brief_with_portfolio_snapshot(self, sample_date, sample_signal):
        snapshot = PortfolioSnapshot(
            total_tickers_monitored=15,
            blue_events_count=2,
            yellow_events_count=5,
            top_signals=[sample_signal],
        )
        brief = FlashBrief(
            brief_date=sample_date,
            generated_at=datetime.now(),
            market_summary="Test",
            portfolio_snapshot=snapshot,
            model_used="test",
        )
        assert brief.portfolio_snapshot.total_tickers_monitored == 15
        assert len(brief.portfolio_snapshot.top_signals) == 1

    def test_brief_with_errors(self, sample_date):
        brief = FlashBrief(
            brief_date=sample_date,
            generated_at=datetime.now(),
            market_summary="Partial brief",
            errors=["Grok unavailable", "Bloomberg data missing"],
            model_used="fallback",
        )
        assert len(brief.errors) == 2


class TestWikiEntry:
    """Tests for Wiki Entry contract."""

    def test_valid_wiki_entry(self, sample_wiki_entry):
        assert sample_wiki_entry.category == WikiCategory.MACRO
        assert len(sample_wiki_entry.tickers) == 3

    def test_wiki_json_roundtrip(self, sample_wiki_entry):
        json_str = sample_wiki_entry.model_dump_json()
        restored = WikiEntry.model_validate_json(json_str)
        assert restored.entry_id == sample_wiki_entry.entry_id
        assert restored.category == WikiCategory.MACRO

    def test_all_wiki_categories(self):
        for cat in WikiCategory:
            entry = WikiEntry(
                entry_id=f"test-{cat.value}",
                category=cat,
                title=f"Test {cat.value}",
                content="Test content",
                source="test",
                created_at=datetime.now(),
            )
            assert entry.category == cat

    def test_wiki_entry_with_supersedes(self):
        entry = WikiEntry(
            entry_id="2026-04-10-update",
            category=WikiCategory.COMPANY,
            title="Updated analysis",
            content="New analysis supersedes old",
            source="orient",
            created_at=datetime.now(),
            supersedes="2026-03-15-original",
        )
        assert entry.supersedes == "2026-03-15-original"


class TestInterAgentCommunication:
    """Integration tests: verify schemas work across agent boundaries."""

    def test_signal_in_brief(self, sample_date, sample_signal, sample_routing_decision):
        """Signals from observe should fit into brief's portfolio snapshot."""
        snapshot = PortfolioSnapshot(top_signals=[sample_signal])
        brief = FlashBrief(
            brief_date=sample_date,
            generated_at=datetime.now(),
            market_summary="Test",
            routing_decisions=[sample_routing_decision],
            portfolio_snapshot=snapshot,
            model_used="test",
        )
        data = json.loads(brief.model_dump_json())
        assert data["portfolio_snapshot"]["top_signals"][0]["ticker"] == "SET:AOT"
        assert data["routing_decisions"][0]["level"] == "blue"

    def test_full_pipeline_data_flow(self, sample_date):
        """Simulate data flowing through the full pipeline."""
        routing = RoutingDecision(
            event_id="evt-001",
            headline="Test event",
            level=SignalLevel.BLUE,
            affected_tickers=["SET:AOT"],
            reasoning="Significant",
            requires_orient=True,
            source="grok",
        )

        signal = Signal(
            ticker="SET:AOT",
            signal="bullish",
            confidence=80,
            reasoning="Orient analysis shows positive impact from event",
            data_sources=["orient_analysis"],
            analysis_date=sample_date,
        )

        brief = FlashBrief(
            brief_date=sample_date,
            generated_at=datetime.now(),
            market_summary="Pipeline test",
            routing_decisions=[routing],
            portfolio_snapshot=PortfolioSnapshot(top_signals=[signal]),
            model_used="test",
        )

        wiki = WikiEntry(
            entry_id="2026-04-10-test",
            category=WikiCategory.EVENT,
            title="Test event captured",
            content="Knowledge from the pipeline",
            tickers=["SET:AOT"],
            tags=["test"],
            source="pipeline",
            created_at=datetime.now(),
        )

        # All serializable
        assert json.loads(brief.model_dump_json())
        assert json.loads(wiki.model_dump_json())
        assert json.loads(signal.model_dump_json())
        assert json.loads(routing.model_dump_json())
