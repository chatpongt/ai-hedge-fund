"""Tests for the KnowledgeGraph."""

import pytest

from src.knowledge.graph import KnowledgeGraph
from src.knowledge.note import Note, NoteType


@pytest.fixture
def graph():
    return KnowledgeGraph()


@pytest.fixture
def linked_graph():
    """A graph with three linked notes: A -> B -> C, and A -> C."""
    g = KnowledgeGraph()
    a = Note(title="Alpha", content="Links to [[Beta]] and [[Charlie]]")
    b = Note(title="Beta", content="Links to [[Charlie]]")
    c = Note(title="Charlie", content="A leaf note")
    g.add_note(a)
    g.add_note(b)
    g.add_note(c)
    g.rebuild_all_edges()
    return g, a, b, c


class TestGraphBasics:
    def test_add_and_retrieve(self, graph):
        note = Note(title="Test", content="Hello")
        graph.add_note(note)
        assert graph.note_count == 1
        assert graph.get_note(note.id) == note

    def test_get_by_title(self, graph):
        note = Note(title="My Title", content="Content")
        graph.add_note(note)
        assert graph.get_note_by_title("My Title") == note
        assert graph.get_note_by_title("my title") == note  # case insensitive

    def test_remove_note(self, graph):
        note = Note(title="ToRemove", content="Content")
        graph.add_note(note)
        removed = graph.remove_note(note.id)
        assert removed == note
        assert graph.note_count == 0
        assert graph.get_note(note.id) is None

    def test_remove_nonexistent(self, graph):
        assert graph.remove_note("fake_id") is None


class TestEdges:
    def test_edge_creation(self, linked_graph):
        g, a, b, c = linked_graph
        assert g.edge_count == 3  # A->B, A->C, B->C

    def test_neighbors_outgoing(self, linked_graph):
        g, a, b, c = linked_graph
        neighbors = g.neighbors(a.id, direction="outgoing")
        neighbor_ids = {n.id for n in neighbors}
        assert b.id in neighbor_ids
        assert c.id in neighbor_ids

    def test_neighbors_incoming(self, linked_graph):
        g, a, b, c = linked_graph
        neighbors = g.neighbors(c.id, direction="incoming")
        neighbor_ids = {n.id for n in neighbors}
        assert a.id in neighbor_ids
        assert b.id in neighbor_ids

    def test_degree(self, linked_graph):
        g, a, b, c = linked_graph
        deg_a = g.degree(a.id)
        assert deg_a["out"] == 2
        assert deg_a["in"] == 0

        deg_c = g.degree(c.id)
        assert deg_c["out"] == 0
        assert deg_c["in"] == 2


class TestTraversal:
    def test_bfs_traverse(self, linked_graph):
        g, a, b, c = linked_graph
        result = g.bfs_traverse(a.id, max_depth=2)
        note_ids = {n.id for n, _ in result}
        assert a.id in note_ids
        assert b.id in note_ids
        assert c.id in note_ids

    def test_bfs_depth_limit(self, linked_graph):
        g, a, b, c = linked_graph
        result = g.bfs_traverse(a.id, max_depth=0)
        assert len(result) == 1  # Only the seed

    def test_find_path(self, linked_graph):
        g, a, b, c = linked_graph
        path = g.find_path(a.id, c.id)
        assert path is not None
        assert path[0] == a.id
        assert path[-1] == c.id

    def test_find_path_no_connection(self, graph):
        n1 = Note(title="Island1", content="No links")
        n2 = Note(title="Island2", content="No links")
        graph.add_note(n1)
        graph.add_note(n2)
        assert graph.find_path(n1.id, n2.id) is None


class TestSpreadingActivation:
    def test_basic_activation(self, linked_graph):
        g, a, b, c = linked_graph
        activations = g.spreading_activation([a.id], decay=0.5, max_depth=2)
        # Seed gets initial activation plus back-propagation from neighbors
        assert activations[a.id] >= 1.0
        assert b.id in activations
        assert c.id in activations
        # Neighbors should have lower activation than seed's initial
        assert activations[b.id] > 0
        assert activations[c.id] > 0

    def test_multiple_seeds(self, linked_graph):
        g, a, b, c = linked_graph
        activations = g.spreading_activation([a.id, b.id], decay=0.5, max_depth=1)
        assert activations[a.id] >= 1.0
        assert activations[b.id] >= 1.0

    def test_zero_decay(self, linked_graph):
        g, a, b, c = linked_graph
        activations = g.spreading_activation([a.id], decay=0.0, max_depth=2)
        # Only seed should have activation since decay kills everything
        assert activations[a.id] == 1.0
        assert b.id not in activations


class TestHubNotes:
    def test_hub_notes(self, linked_graph):
        g, a, b, c = linked_graph
        hubs = g.hub_notes(top_n=2)
        # C has highest degree (2 incoming), A has 2 outgoing
        titles = [n.title for n, _ in hubs]
        assert len(hubs) == 2
