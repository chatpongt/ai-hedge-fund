"""Tests for the KnowledgeStore persistence layer."""

import pytest
from pathlib import Path
import tempfile

from src.knowledge.note import Note, NoteType
from src.knowledge.store import KnowledgeStore


@pytest.fixture
def tmp_store(tmp_path):
    """Create a store backed by a temp directory."""
    return KnowledgeStore(store_path=tmp_path)


class TestStoreBasics:
    def test_add_and_retrieve(self, tmp_store):
        note = Note(title="Test", content="Content")
        tmp_store.add_note(note)
        assert tmp_store.get_note(note.id) == note

    def test_remove(self, tmp_store):
        note = Note(title="Test", content="Content")
        tmp_store.add_note(note)
        removed = tmp_store.remove_note(note.id)
        assert removed.id == note.id
        assert tmp_store.get_note(note.id) is None

    def test_clear(self, tmp_store):
        tmp_store.add_note(Note(title="A", content="X"))
        tmp_store.add_note(Note(title="B", content="Y"))
        tmp_store.clear()
        assert tmp_store.graph.note_count == 0


class TestPersistence:
    def test_save_and_load(self, tmp_path):
        # Save
        store1 = KnowledgeStore(store_path=tmp_path)
        n1 = Note(title="Alpha", content="Links to [[Beta]]", note_type=NoteType.INSIGHT, tags=["AAPL"], source_agent="warren_buffett", ticker="AAPL")
        n2 = Note(title="Beta", content="Leaf note", note_type=NoteType.SIGNAL, confidence=85.0)
        store1.add_note(n1)
        store1.add_note(n2)
        store1.save()

        # Load into fresh store
        store2 = KnowledgeStore(store_path=tmp_path)
        graph = store2.load()

        assert graph.note_count == 2
        loaded_n1 = graph.get_note_by_title("Alpha")
        assert loaded_n1 is not None
        assert loaded_n1.source_agent == "warren_buffett"
        assert loaded_n1.tags == ["AAPL"]

        loaded_n2 = graph.get_note_by_title("Beta")
        assert loaded_n2 is not None
        assert loaded_n2.confidence == 85.0

    def test_edges_restored_after_load(self, tmp_path):
        store1 = KnowledgeStore(store_path=tmp_path)
        store1.add_note(Note(title="Source", content="Points to [[Target]]"))
        store1.add_note(Note(title="Target", content="A target"))
        store1.save()

        store2 = KnowledgeStore(store_path=tmp_path)
        graph = store2.load()
        source = graph.get_note_by_title("Source")
        assert graph.edge_count == 1
        neighbors = graph.neighbors(source.id, direction="outgoing")
        assert len(neighbors) == 1
        assert neighbors[0].title == "Target"

    def test_load_empty_store(self, tmp_path):
        store = KnowledgeStore(store_path=tmp_path)
        graph = store.load()
        assert graph.note_count == 0
