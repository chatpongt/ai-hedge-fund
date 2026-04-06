"""Tests for Map of Content management."""

from src.knowledge.graph import KnowledgeGraph
from src.knowledge.moc import MapOfContent
from src.knowledge.note import Note, NoteType


class TestMapOfContent:
    def test_create_moc(self):
        graph = KnowledgeGraph()
        moc_mgr = MapOfContent(graph)

        moc = moc_mgr.create_moc(
            title="Test MOC",
            description="A test map of content.",
            sections={"Section A": ["Note 1", "Note 2"]},
            tags=["test"],
        )
        assert moc.note_type == NoteType.MOC
        assert "[[Note 1]]" in moc.content
        assert "[[Note 2]]" in moc.content
        assert "## Section A" in moc.content

    def test_add_to_moc(self):
        graph = KnowledgeGraph()
        moc_mgr = MapOfContent(graph)
        moc_mgr.create_moc(
            title="My MOC",
            description="Description",
            sections={"Signals": ["Existing Signal"]},
        )
        result = moc_mgr.add_to_moc("My MOC", "Signals", "New Signal")
        assert result is not None
        assert "[[New Signal]]" in result.content

    def test_add_new_section_to_moc(self):
        graph = KnowledgeGraph()
        moc_mgr = MapOfContent(graph)
        moc_mgr.create_moc(title="My MOC", description="Description")
        result = moc_mgr.add_to_moc("My MOC", "New Section", "A Note")
        assert result is not None
        assert "## New Section" in result.content
        assert "[[A Note]]" in result.content

    def test_auto_moc_for_ticker(self):
        graph = KnowledgeGraph()
        graph.add_note(Note(title="AAPL Signal 1", content="Bullish", note_type=NoteType.SIGNAL, ticker="AAPL"))
        graph.add_note(Note(title="AAPL Analysis", content="Deep dive", note_type=NoteType.ANALYSIS, ticker="AAPL"))
        graph.add_note(Note(title="MSFT Signal", content="Neutral", note_type=NoteType.SIGNAL, ticker="MSFT"))

        moc_mgr = MapOfContent(graph)
        moc = moc_mgr.auto_moc_for_ticker("AAPL")
        assert "AAPL" in moc.title
        assert "[[AAPL Signal 1]]" in moc.content
        assert "[[AAPL Analysis]]" in moc.content
        assert "MSFT" not in moc.content

    def test_auto_moc_for_agent(self):
        graph = KnowledgeGraph()
        graph.add_note(Note(title="WB AAPL", content="Analysis", source_agent="warren_buffett", ticker="AAPL"))
        graph.add_note(Note(title="WB MSFT", content="Analysis", source_agent="warren_buffett", ticker="MSFT"))
        graph.add_note(Note(title="MB AAPL", content="Analysis", source_agent="michael_burry", ticker="AAPL"))

        moc_mgr = MapOfContent(graph)
        moc = moc_mgr.auto_moc_for_agent("warren_buffett")
        assert "Warren Buffett" in moc.title
        assert "[[WB AAPL]]" in moc.content
        assert "[[WB MSFT]]" in moc.content
        assert "MB AAPL" not in moc.content

    def test_list_mocs(self):
        graph = KnowledgeGraph()
        moc_mgr = MapOfContent(graph)
        moc_mgr.create_moc(title="MOC 1", description="First")
        moc_mgr.create_moc(title="MOC 2", description="Second")
        graph.add_note(Note(title="Regular Note", content="Not a MOC"))

        mocs = moc_mgr.list_mocs()
        assert len(mocs) == 2
        titles = {m.title for m in mocs}
        assert "MOC 1" in titles
        assert "MOC 2" in titles
