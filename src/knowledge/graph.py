"""Knowledge graph with wiki link topology and traversal.

Implements a directed graph where notes are nodes and [[wiki links]] are edges.
Supports spreading activation, small-world topology analysis, and
agent-oriented traversal patterns.
"""

from collections import defaultdict, deque
from typing import Optional

from src.knowledge.note import Note


class KnowledgeGraph:
    """A directed graph of knowledge notes connected by wiki links.

    The graph builds its topology from [[wiki links]] in note content.
    It supports BFS/DFS traversal, spreading activation for relevance
    scoring, and topology metrics (degree, clustering, path length).
    """

    def __init__(self):
        self._notes: dict[str, Note] = {}  # id -> Note
        self._title_index: dict[str, str] = {}  # normalized_title -> id
        self._outgoing: dict[str, set[str]] = defaultdict(set)  # id -> set of target ids
        self._incoming: dict[str, set[str]] = defaultdict(set)  # id -> set of source ids

    @property
    def note_count(self) -> int:
        return len(self._notes)

    @property
    def edge_count(self) -> int:
        return sum(len(targets) for targets in self._outgoing.values())

    def _normalize_title(self, title: str) -> str:
        return title.strip().lower()

    def add_note(self, note: Note) -> None:
        """Add a note and index its outgoing wiki links."""
        self._notes[note.id] = note
        self._title_index[self._normalize_title(note.title)] = note.id
        self._rebuild_edges_for(note)

    def _rebuild_edges_for(self, note: Note) -> None:
        """Rebuild outgoing edges for a note based on its wiki links."""
        # Clear old outgoing edges
        for old_target in self._outgoing.get(note.id, set()):
            self._incoming[old_target].discard(note.id)
        self._outgoing[note.id] = set()

        # Build new edges from wiki links
        for link_title in note.outgoing_links:
            target_id = self._title_index.get(self._normalize_title(link_title))
            if target_id and target_id != note.id:
                self._outgoing[note.id].add(target_id)
                self._incoming[target_id].add(note.id)

    def rebuild_all_edges(self) -> None:
        """Rebuild the entire edge index from all notes' wiki links."""
        self._outgoing.clear()
        self._incoming.clear()
        for note in self._notes.values():
            self._rebuild_edges_for(note)

    def get_note(self, note_id: str) -> Optional[Note]:
        return self._notes.get(note_id)

    def get_note_by_title(self, title: str) -> Optional[Note]:
        note_id = self._title_index.get(self._normalize_title(title))
        return self._notes.get(note_id) if note_id else None

    def remove_note(self, note_id: str) -> Optional[Note]:
        """Remove a note and clean up all edges."""
        note = self._notes.pop(note_id, None)
        if note is None:
            return None
        self._title_index.pop(self._normalize_title(note.title), None)
        # Clean outgoing
        for target_id in self._outgoing.pop(note_id, set()):
            self._incoming[target_id].discard(note_id)
        # Clean incoming
        for source_id in self._incoming.pop(note_id, set()):
            self._outgoing[source_id].discard(note_id)
        return note

    def neighbors(self, note_id: str, direction: str = "both") -> list[Note]:
        """Get neighboring notes. direction: 'outgoing', 'incoming', or 'both'."""
        ids = set()
        if direction in ("outgoing", "both"):
            ids |= self._outgoing.get(note_id, set())
        if direction in ("incoming", "both"):
            ids |= self._incoming.get(note_id, set())
        return [self._notes[nid] for nid in ids if nid in self._notes]

    def bfs_traverse(self, start_id: str, max_depth: int = 3) -> list[tuple[Note, int]]:
        """Breadth-first traversal returning (note, depth) pairs."""
        if start_id not in self._notes:
            return []
        visited = {start_id}
        queue = deque([(start_id, 0)])
        result = [(self._notes[start_id], 0)]

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor_id in self._outgoing.get(current_id, set()) | self._incoming.get(current_id, set()):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))
                    result.append((self._notes[neighbor_id], depth + 1))

        return result

    def spreading_activation(self, seed_ids: list[str], decay: float = 0.5, max_depth: int = 3, initial_activation: float = 1.0) -> dict[str, float]:
        """Spreading activation from seed notes through the graph.

        Each seed starts with initial_activation. Activation spreads to
        neighbors, decaying by the decay factor at each hop. Activations
        accumulate when a node is reached via multiple paths.

        Returns a dict of note_id -> activation score.
        """
        activations: dict[str, float] = defaultdict(float)
        queue: deque[tuple[str, float, int]] = deque()

        for seed_id in seed_ids:
            if seed_id in self._notes:
                activations[seed_id] += initial_activation
                queue.append((seed_id, initial_activation, 0))

        visited_at_depth: dict[str, int] = {sid: 0 for sid in seed_ids}

        while queue:
            current_id, current_activation, depth = queue.popleft()
            if depth >= max_depth:
                continue

            spread_value = current_activation * decay
            if spread_value < 0.01:
                continue

            neighbor_ids = self._outgoing.get(current_id, set()) | self._incoming.get(current_id, set())
            for neighbor_id in neighbor_ids:
                if neighbor_id not in self._notes:
                    continue
                activations[neighbor_id] += spread_value
                prev_depth = visited_at_depth.get(neighbor_id)
                if prev_depth is None or depth + 1 < prev_depth:
                    visited_at_depth[neighbor_id] = depth + 1
                    queue.append((neighbor_id, spread_value, depth + 1))

        return dict(activations)

    def degree(self, note_id: str) -> dict[str, int]:
        """Return in-degree, out-degree, and total degree for a note."""
        in_deg = len(self._incoming.get(note_id, set()))
        out_deg = len(self._outgoing.get(note_id, set()))
        return {"in": in_deg, "out": out_deg, "total": in_deg + out_deg}

    def hub_notes(self, top_n: int = 10) -> list[tuple[Note, int]]:
        """Return the most-connected notes (by total degree), descending."""
        scored = []
        for note_id, note in self._notes.items():
            total = len(self._outgoing.get(note_id, set())) + len(self._incoming.get(note_id, set()))
            scored.append((note, total))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def find_path(self, from_id: str, to_id: str, max_depth: int = 10) -> Optional[list[str]]:
        """Find shortest path between two notes using BFS. Returns list of note IDs."""
        if from_id not in self._notes or to_id not in self._notes:
            return None
        if from_id == to_id:
            return [from_id]

        visited = {from_id}
        queue = deque([(from_id, [from_id])])

        while queue:
            current_id, path = queue.popleft()
            if len(path) > max_depth:
                continue
            for neighbor_id in self._outgoing.get(current_id, set()) | self._incoming.get(current_id, set()):
                if neighbor_id == to_id:
                    return path + [neighbor_id]
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def all_notes(self) -> list[Note]:
        return list(self._notes.values())
