"""Discovery and retrieval for the knowledge graph.

Combines text search, tag filtering, spreading activation, and
progressive disclosure to help agents find relevant knowledge.
"""

from datetime import datetime
from typing import Optional

from src.knowledge.graph import KnowledgeGraph
from src.knowledge.note import Note, NoteType


class RetrievalEngine:
    """Multi-strategy retrieval over the knowledge graph.

    Supports:
    - Text search across titles and content
    - Tag-based filtering
    - Type-based filtering
    - Spreading activation from seed notes
    - Recency-weighted scoring
    - Progressive disclosure (summaries first, details on demand)
    """

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def search(self, query: str, note_type: Optional[NoteType] = None, tags: Optional[list[str]] = None, ticker: Optional[str] = None, agent: Optional[str] = None, limit: int = 20) -> list[Note]:
        """Full-text search with optional filters."""
        results = []
        for note in self.graph.all_notes():
            if not note.matches_query(query):
                continue
            if note_type and note.note_type != note_type:
                continue
            if tags and not any(t in note.tags for t in tags):
                continue
            if ticker and note.ticker != ticker:
                continue
            if agent and note.source_agent != agent:
                continue
            results.append(note)

        # Sort by recency
        results.sort(key=lambda n: n.updated_at, reverse=True)
        return results[:limit]

    def find_related(self, note_id: str, max_depth: int = 2, limit: int = 10) -> list[tuple[Note, float]]:
        """Find related notes using spreading activation from a seed note.

        Returns (note, activation_score) pairs sorted by relevance.
        """
        activations = self.graph.spreading_activation(
            seed_ids=[note_id],
            decay=0.5,
            max_depth=max_depth,
        )
        # Remove the seed itself
        activations.pop(note_id, None)

        scored = []
        for nid, score in activations.items():
            note = self.graph.get_note(nid)
            if note:
                scored.append((note, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def find_by_context(self, tickers: Optional[list[str]] = None, agents: Optional[list[str]] = None, note_types: Optional[list[NoteType]] = None, since: Optional[datetime] = None, limit: int = 20) -> list[Note]:
        """Contextual retrieval — find notes matching the current analysis context."""
        results = []
        for note in self.graph.all_notes():
            if tickers and note.ticker not in tickers:
                continue
            if agents and note.source_agent not in agents:
                continue
            if note_types and note.note_type not in note_types:
                continue
            if since and note.updated_at < since:
                continue
            results.append(note)

        results.sort(key=lambda n: n.updated_at, reverse=True)
        return results[:limit]

    def get_summary(self, note_id: str, max_lines: int = 5) -> Optional[str]:
        """Progressive disclosure — return just the first few lines of a note."""
        note = self.graph.get_note(note_id)
        if note is None:
            return None
        lines = note.content.strip().split("\n")
        summary = "\n".join(lines[:max_lines])
        if len(lines) > max_lines:
            summary += "\n..."
        return summary

    def entry_points(self, limit: int = 10) -> list[Note]:
        """Return the best entry points into the knowledge graph.

        Prioritizes MOCs and highly-connected hub notes.
        """
        mocs = [n for n in self.graph.all_notes() if n.note_type == NoteType.MOC]
        mocs.sort(key=lambda n: n.updated_at, reverse=True)

        if len(mocs) >= limit:
            return mocs[:limit]

        # Fill with hub notes
        hubs = self.graph.hub_notes(top_n=limit - len(mocs))
        hub_ids = {n.id for n, _ in hubs}
        result = mocs + [n for n, _ in hubs if n.id not in {m.id for m in mocs}]
        return result[:limit]

    def knowledge_gaps(self, tickers: Optional[list[str]] = None) -> list[dict]:
        """Identify areas where knowledge is thin or missing.

        Returns a list of gap descriptions with suggestions.
        """
        gaps = []
        all_notes = self.graph.all_notes()

        if tickers:
            for ticker in tickers:
                ticker_notes = [n for n in all_notes if n.ticker == ticker]
                if not ticker_notes:
                    gaps.append({"type": "missing_ticker", "ticker": ticker, "suggestion": f"No knowledge exists for {ticker}. Run analysis agents to populate."})
                    continue

                # Check for type coverage
                types_present = {n.note_type for n in ticker_notes}
                if NoteType.SIGNAL not in types_present:
                    gaps.append({"type": "missing_signals", "ticker": ticker, "suggestion": f"No trading signals recorded for {ticker}."})
                if NoteType.MOC not in types_present:
                    gaps.append({"type": "missing_moc", "ticker": ticker, "suggestion": f"No Map of Content for {ticker}. Consider creating one."})

        # Check for orphan notes (no links in or out)
        for note in all_notes:
            degree = self.graph.degree(note.id)
            if degree["total"] == 0 and note.note_type != NoteType.EXPLORATION:
                gaps.append({"type": "orphan_note", "note_id": note.id, "title": note.title, "suggestion": f"Note '{note.title}' has no connections. Consider linking it."})

        return gaps
