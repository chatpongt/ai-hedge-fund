"""Persistent JSON-based knowledge store.

Saves and loads the knowledge graph to/from disk, enabling knowledge
to persist across agent sessions. Each note is stored as a JSON object
in a single file, with the graph edges derived from wiki links on load.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.knowledge.graph import KnowledgeGraph
from src.knowledge.note import Note, NoteType


DEFAULT_STORE_PATH = Path("data/knowledge")


class KnowledgeStore:
    """File-based persistent storage for the knowledge graph.

    Notes are serialized to JSON in a directory structure:
        data/knowledge/notes.json    — all notes
        data/knowledge/metadata.json — store-level metadata
    """

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or DEFAULT_STORE_PATH
        self.graph = KnowledgeGraph()
        self._notes_file = self.store_path / "notes.json"
        self._metadata_file = self.store_path / "metadata.json"

    def _ensure_dir(self) -> None:
        self.store_path.mkdir(parents=True, exist_ok=True)

    def load(self) -> KnowledgeGraph:
        """Load all notes from disk and rebuild the graph."""
        if not self._notes_file.exists():
            return self.graph

        with open(self._notes_file, "r") as f:
            raw_notes = json.load(f)

        for raw in raw_notes:
            # Deserialize datetime strings
            raw["created_at"] = datetime.fromisoformat(raw["created_at"])
            raw["updated_at"] = datetime.fromisoformat(raw["updated_at"])
            raw["note_type"] = NoteType(raw["note_type"])
            note = Note(**raw)
            self.graph.add_note(note)

        # Rebuild edges now that all notes are loaded (resolves forward links)
        self.graph.rebuild_all_edges()
        return self.graph

    def save(self) -> None:
        """Persist all notes to disk."""
        self._ensure_dir()

        notes_data = []
        for note in self.graph.all_notes():
            data = note.model_dump()
            data["created_at"] = note.created_at.isoformat()
            data["updated_at"] = note.updated_at.isoformat()
            data["note_type"] = note.note_type.value
            notes_data.append(data)

        with open(self._notes_file, "w") as f:
            json.dump(notes_data, f, indent=2, default=str)

        # Save store metadata
        metadata = {
            "note_count": self.graph.note_count,
            "edge_count": self.graph.edge_count,
            "last_saved": datetime.utcnow().isoformat(),
        }
        with open(self._metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    def add_note(self, note: Note) -> Note:
        """Add a note to the graph and persist."""
        self.graph.add_note(note)
        self.save()
        return note

    def remove_note(self, note_id: str) -> Optional[Note]:
        """Remove a note and persist."""
        note = self.graph.remove_note(note_id)
        if note:
            self.save()
        return note

    def get_note(self, note_id: str) -> Optional[Note]:
        return self.graph.get_note(note_id)

    def get_note_by_title(self, title: str) -> Optional[Note]:
        return self.graph.get_note_by_title(title)

    def clear(self) -> None:
        """Remove all notes and delete store files."""
        self.graph = KnowledgeGraph()
        if self._notes_file.exists():
            os.remove(self._notes_file)
        if self._metadata_file.exists():
            os.remove(self._metadata_file)
