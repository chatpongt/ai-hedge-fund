"""Tests for the RetrievalEngine."""

from src.knowledge.graph import KnowledgeGraph
from src.knowledge.note import Note, NoteType
from src.knowledge.retrieval import RetrievalEngine


def _build_test_graph():
    """Build a graph with diverse notes for retrieval testing."""
    g = KnowledgeGraph()
    notes = [
        Note(title="AAPL Bullish Signal", content="Strong fundamentals indicate bullish outlook. See [[AAPL Moat Analysis]].", note_type=NoteType.SIGNAL, tags=["AAPL", "bullish"], source_agent="warren_buffett", ticker="AAPL", confidence=85.0),
        Note(title="AAPL Moat Analysis", content="Wide competitive moat with ecosystem lock-in. Related: [[AAPL Bullish Signal]].", note_type=NoteType.ANALYSIS, tags=["AAPL", "moat"], source_agent="warren_buffett", ticker="AAPL"),
        Note(title="MSFT Bearish Signal", content="Overvalued at current levels.", note_type=NoteType.SIGNAL, tags=["MSFT", "bearish"], source_agent="michael_burry", ticker="MSFT", confidence=70.0),
        Note(title="Tech Sector Overview", content="Looking at [[AAPL Bullish Signal]] and [[MSFT Bearish Signal]].", note_type=NoteType.SYNTHESIS, tags=["tech", "sector"]),
        Note(title="Orphan Note", content="Isolated with no links.", note_type=NoteType.INSIGHT, tags=["misc"]),
    ]
    for n in notes:
        g.add_note(n)
    g.rebuild_all_edges()
    return g, notes


class TestSearch:
    def test_text_search(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        results = engine.search("bullish")
        assert any(n.title == "AAPL Bullish Signal" for n in results)

    def test_search_with_ticker_filter(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        results = engine.search("signal", ticker="MSFT")
        assert len(results) == 1
        assert results[0].title == "MSFT Bearish Signal"

    def test_search_with_agent_filter(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        results = engine.search("fundamentals", agent="warren_buffett")
        assert len(results) == 1
        assert results[0].title == "AAPL Bullish Signal"

    def test_search_no_results(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        assert engine.search("nonexistent_term_xyz") == []


class TestFindRelated:
    def test_related_notes(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        aapl_signal = g.get_note_by_title("AAPL Bullish Signal")
        related = engine.find_related(aapl_signal.id)
        related_titles = {n.title for n, _ in related}
        assert "AAPL Moat Analysis" in related_titles
        assert "Tech Sector Overview" in related_titles


class TestContextRetrieval:
    def test_find_by_ticker(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        results = engine.find_by_context(tickers=["AAPL"])
        assert all(n.ticker == "AAPL" for n in results)
        assert len(results) == 2

    def test_find_by_agent(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        results = engine.find_by_context(agents=["michael_burry"])
        assert len(results) == 1
        assert results[0].source_agent == "michael_burry"


class TestEntryPoints:
    def test_entry_points_prefer_mocs(self):
        g, notes = _build_test_graph()
        # Add a MOC
        moc = Note(title="Main MOC", content="Entry point", note_type=NoteType.MOC)
        g.add_note(moc)

        engine = RetrievalEngine(g)
        entries = engine.entry_points(limit=3)
        assert entries[0].note_type == NoteType.MOC


class TestKnowledgeGaps:
    def test_missing_ticker(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        gaps = engine.knowledge_gaps(tickers=["NVDA"])
        assert any(gap["type"] == "missing_ticker" and gap["ticker"] == "NVDA" for gap in gaps)

    def test_orphan_detection(self):
        g, notes = _build_test_graph()
        engine = RetrievalEngine(g)
        gaps = engine.knowledge_gaps()
        assert any(gap["type"] == "orphan_note" and gap["title"] == "Orphan Note" for gap in gaps)
