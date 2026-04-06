"""Tests for the AgentMemory integration layer."""

import pytest
from pathlib import Path

from src.knowledge.agent_memory import AgentMemory
from src.knowledge.note import NoteType
from src.knowledge.store import KnowledgeStore


@pytest.fixture
def memory(tmp_path):
    store = KnowledgeStore(store_path=tmp_path)
    return AgentMemory(store)


class TestRecording:
    def test_record_signal(self, memory):
        note = memory.record_signal(
            agent="warren_buffett",
            ticker="AAPL",
            signal="bullish",
            confidence=85.0,
            reasoning="Strong fundamentals and competitive moat.",
        )
        assert note.note_type == NoteType.SIGNAL
        assert note.source_agent == "warren_buffett"
        assert note.ticker == "AAPL"
        assert note.confidence == 85.0
        assert "bullish" in note.content

    def test_record_insight(self, memory):
        note = memory.record_insight(
            agent="michael_burry",
            title="Overvaluation in Tech",
            content="P/E ratios suggest overvaluation across tech sector.",
            tags=["tech", "valuation"],
        )
        assert note.note_type == NoteType.INSIGHT
        assert note.source_agent == "michael_burry"

    def test_record_analysis(self, memory):
        note = memory.record_analysis(
            agent="fundamentals_analyst",
            ticker="MSFT",
            title="MSFT Fundamentals Deep Dive",
            content="Revenue growth: 15% YoY. Margins expanding.",
        )
        assert note.note_type == NoteType.ANALYSIS
        assert "MSFT" in note.tags

    def test_record_synthesis(self, memory):
        note = memory.record_synthesis(
            title="Cross-Agent Consensus",
            content="Both [[Warren Buffett]] and [[Ben Graham]] see value in AAPL.",
            tags=["consensus"],
        )
        assert note.note_type == NoteType.SYNTHESIS
        assert note.outgoing_links == ["Warren Buffett", "Ben Graham"]


class TestRecall:
    def test_recall_by_ticker(self, memory):
        memory.record_signal(agent="wb", ticker="AAPL", signal="bullish", confidence=80, reasoning="Good")
        memory.record_signal(agent="wb", ticker="MSFT", signal="neutral", confidence=50, reasoning="OK")
        results = memory.recall(ticker="AAPL")
        assert len(results) == 1
        assert results[0].ticker == "AAPL"

    def test_recall_by_agent(self, memory):
        memory.record_signal(agent="wb", ticker="AAPL", signal="bullish", confidence=80, reasoning="Good")
        memory.record_signal(agent="mb", ticker="AAPL", signal="bearish", confidence=70, reasoning="Bad")
        results = memory.recall(agent="wb")
        assert len(results) == 1
        assert results[0].source_agent == "wb"

    def test_recall_by_query(self, memory):
        memory.record_insight(agent="wb", title="Moat Analysis", content="Wide moat detected")
        memory.record_insight(agent="wb", title="Revenue Trend", content="Revenue declining")
        results = memory.recall(query="moat")
        assert len(results) == 1
        assert "Moat" in results[0].title


class TestMOCIntegration:
    def test_ensure_ticker_moc(self, memory):
        memory.record_signal(agent="wb", ticker="AAPL", signal="bullish", confidence=80, reasoning="Good")
        moc = memory.ensure_ticker_moc("AAPL")
        assert "AAPL" in moc.title
        assert moc.note_type == NoteType.MOC

    def test_ensure_ticker_moc_idempotent(self, memory):
        memory.record_signal(agent="wb", ticker="AAPL", signal="bullish", confidence=80, reasoning="Good")
        moc1 = memory.ensure_ticker_moc("AAPL")
        moc2 = memory.ensure_ticker_moc("AAPL")
        assert moc1.id == moc2.id

    def test_ensure_agent_moc(self, memory):
        memory.record_signal(agent="warren_buffett", ticker="AAPL", signal="bullish", confidence=80, reasoning="Good")
        moc = memory.ensure_agent_moc("warren_buffett")
        assert "Warren Buffett" in moc.title


class TestStats:
    def test_stats(self, memory):
        memory.record_signal(agent="wb", ticker="AAPL", signal="bullish", confidence=80, reasoning="Good")
        memory.record_insight(agent="mb", title="Insight", content="Content", ticker="MSFT")
        stats = memory.stats()
        assert stats["total_notes"] == 2
        assert stats["by_type"]["signal"] == 1
        assert stats["by_type"]["insight"] == 1
        assert stats["by_ticker"]["AAPL"] == 1


class TestKnowledgeGaps:
    def test_gaps_for_missing_ticker(self, memory):
        gaps = memory.knowledge_gaps(tickers=["NVDA"])
        assert any(g["type"] == "missing_ticker" for g in gaps)


class TestPersistence:
    def test_save_and_reload(self, tmp_path):
        # Create and populate
        mem1 = AgentMemory.load(store_path=tmp_path)
        mem1.record_signal(agent="wb", ticker="AAPL", signal="bullish", confidence=85, reasoning="Strong")
        mem1.save()

        # Reload
        mem2 = AgentMemory.load(store_path=tmp_path)
        results = mem2.recall(ticker="AAPL")
        assert len(results) == 1
        assert results[0].confidence == 85.0
