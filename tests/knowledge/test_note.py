"""Tests for the Note model and wiki link parsing."""

from src.knowledge.note import Note, NoteType, extract_wiki_links


class TestExtractWikiLinks:
    def test_single_link(self):
        assert extract_wiki_links("See [[AAPL Analysis]] for details") == ["AAPL Analysis"]

    def test_multiple_links(self):
        result = extract_wiki_links("Compare [[AAPL]] with [[MSFT]] and [[NVDA]]")
        assert result == ["AAPL", "MSFT", "NVDA"]

    def test_no_links(self):
        assert extract_wiki_links("Plain text with no links") == []

    def test_empty_string(self):
        assert extract_wiki_links("") == []

    def test_nested_brackets_ignored(self):
        assert extract_wiki_links("[[valid link]]") == ["valid link"]

    def test_link_with_spaces(self):
        assert extract_wiki_links("[[Warren Buffett Signal]]") == ["Warren Buffett Signal"]


class TestNote:
    def test_create_note(self):
        note = Note(title="Test Note", content="Hello [[World]]")
        assert note.title == "Test Note"
        assert note.id is not None
        assert len(note.id) == 12

    def test_outgoing_links(self):
        note = Note(title="Test", content="Links to [[Alpha]] and [[Beta]]")
        assert note.outgoing_links == ["Alpha", "Beta"]

    def test_add_link(self):
        note = Note(title="Test", content="Initial content")
        note.add_link("New Target")
        assert "[[New Target]]" in note.content

    def test_matches_query_title(self):
        note = Note(title="AAPL Bullish Signal", content="Some content")
        assert note.matches_query("AAPL")
        assert note.matches_query("bullish")
        assert not note.matches_query("MSFT")

    def test_matches_query_content(self):
        note = Note(title="Signal", content="Revenue growth is strong for NVDA")
        assert note.matches_query("revenue")
        assert note.matches_query("NVDA")

    def test_matches_query_tags(self):
        note = Note(title="Signal", content="Content", tags=["AAPL", "bullish"])
        assert note.matches_query("AAPL")
        assert note.matches_query("bullish")

    def test_note_types(self):
        for nt in NoteType:
            note = Note(title="Test", content="Content", note_type=nt)
            assert note.note_type == nt

    def test_serialization_roundtrip(self):
        note = Note(
            title="Test",
            content="Content [[linked]]",
            note_type=NoteType.SIGNAL,
            tags=["AAPL"],
            source_agent="warren_buffett",
            ticker="AAPL",
            confidence=85.0,
        )
        data = note.model_dump()
        restored = Note(**data)
        assert restored.title == note.title
        assert restored.content == note.content
        assert restored.note_type == note.note_type
        assert restored.tags == note.tags
        assert restored.source_agent == note.source_agent
