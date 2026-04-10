"""Shared test fixtures for RSI system tests."""

import pytest
from datetime import date, datetime

from schemas.signal import RoutingDecision, Signal, SignalLevel
from schemas.brief import FlashBrief, BriefSection
from schemas.wiki_entry import WikiEntry, WikiCategory


@pytest.fixture
def sample_date():
    return date(2026, 4, 10)


@pytest.fixture
def sample_signal(sample_date):
    return Signal(
        ticker="SET:AOT",
        signal="bullish",
        confidence=75,
        reasoning="Strong passenger recovery post-COVID, Q3 revenue beat estimates by 12%",
        data_sources=["eod_price", "financials", "news"],
        analysis_date=sample_date,
    )


@pytest.fixture
def sample_routing_decision():
    return RoutingDecision(
        event_id="evt-2026-04-10-001",
        headline="BOT holds rate at 2.25%, signals potential cut in H2",
        level=SignalLevel.BLUE,
        affected_tickers=["SET:KBANK", "SET:BBL", "SET:SCB"],
        reasoning="Rate cut signal is significant for banking sector valuation",
        requires_orient=True,
        source="perplexity",
    )


@pytest.fixture
def sample_eod_data():
    return {
        "date": "2026-04-10",
        "set_index": {"close": 1450.32, "change_pct": 0.85, "volume": 45_000_000_000},
        "tickers": {
            "SET:AOT": {"close": 72.50, "change_pct": 2.1, "volume": 12_500_000},
            "SET:CPALL": {"close": 58.25, "change_pct": -0.5, "volume": 8_200_000},
        },
    }


@pytest.fixture
def sample_brief(sample_date, sample_routing_decision):
    return FlashBrief(
        brief_date=sample_date,
        generated_at=datetime(2026, 4, 10, 18, 30, 0),
        market_summary="SET closed at 1,450.32 (+0.85%). Banking sector led gains on BOT rate signal.",
        sections=[
            BriefSection(title="Market Overview", content="SET index rose...", priority=8),
            BriefSection(title="Key Events", content="BOT held rate...", priority=10),
        ],
        routing_decisions=[sample_routing_decision],
        model_used="mlx-main",
    )


@pytest.fixture
def sample_wiki_entry():
    return WikiEntry(
        entry_id="2026-04-10-bot-rate-hold",
        category=WikiCategory.MACRO,
        title="BOT holds rate at 2.25%, signals H2 cut",
        content="The Bank of Thailand maintained its policy rate at 2.25%...",
        tickers=["SET:KBANK", "SET:BBL", "SET:SCB"],
        tags=["bot", "interest-rate", "banking"],
        source="perplexity",
        created_at=datetime(2026, 4, 10, 18, 35, 0),
        confidence=85,
        expiry_date=date(2026, 7, 1),
    )
