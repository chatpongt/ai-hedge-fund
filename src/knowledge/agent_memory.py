"""Agent memory integration — bridges the knowledge system with the agent workflow.

Provides methods for agents to store analysis results as knowledge notes,
retrieve relevant prior knowledge before analysis, and build cross-agent
synthesis over time.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from src.knowledge.graph import KnowledgeGraph
from src.knowledge.moc import MapOfContent
from src.knowledge.note import Note, NoteType
from src.knowledge.retrieval import RetrievalEngine
from src.knowledge.store import KnowledgeStore


class AgentMemory:
    """Integration layer between the hedge fund agents and the knowledge system.

    Usage in an agent:
        memory = AgentMemory.load()
        prior = memory.recall(ticker="AAPL", agent="warren_buffett")
        # ... run analysis ...
        memory.record_signal(agent="warren_buffett", ticker="AAPL",
                             signal="bullish", confidence=85, reasoning="...")
        memory.save()
    """

    def __init__(self, store: KnowledgeStore):
        self.store = store
        self.graph = store.graph
        self.retrieval = RetrievalEngine(self.graph)
        self.moc = MapOfContent(self.graph)

    @classmethod
    def load(cls, store_path: Optional[Path] = None) -> "AgentMemory":
        """Load or create a knowledge store and return an AgentMemory instance."""
        store = KnowledgeStore(store_path=store_path)
        store.load()
        return cls(store)

    def save(self) -> None:
        """Persist current knowledge to disk."""
        self.store.save()

    def record_signal(self, agent: str, ticker: str, signal: str, confidence: float, reasoning: str, metadata: Optional[dict] = None) -> Note:
        """Record an agent's trading signal as a knowledge note."""
        note = Note(
            title=f"{agent} signal for {ticker} ({datetime.utcnow().strftime('%Y-%m-%d')})",
            content=f"Signal: {signal} (confidence: {confidence}/100)\n\n{reasoning}",
            note_type=NoteType.SIGNAL,
            tags=[ticker, agent, signal],
            source_agent=agent,
            ticker=ticker,
            confidence=confidence,
            metadata=metadata or {},
        )
        self.graph.add_note(note)
        return note

    def record_insight(self, agent: str, title: str, content: str, ticker: Optional[str] = None, tags: Optional[list[str]] = None, metadata: Optional[dict] = None) -> Note:
        """Record a general insight discovered during analysis."""
        note = Note(
            title=title,
            content=content,
            note_type=NoteType.INSIGHT,
            tags=tags or [],
            source_agent=agent,
            ticker=ticker,
            metadata=metadata or {},
        )
        self.graph.add_note(note)
        return note

    def record_analysis(self, agent: str, ticker: str, title: str, content: str, tags: Optional[list[str]] = None, metadata: Optional[dict] = None) -> Note:
        """Record a detailed analysis as a knowledge note."""
        note = Note(
            title=title,
            content=content,
            note_type=NoteType.ANALYSIS,
            tags=(tags or []) + [ticker, agent],
            source_agent=agent,
            ticker=ticker,
            metadata=metadata or {},
        )
        self.graph.add_note(note)
        return note

    def record_synthesis(self, title: str, content: str, tags: Optional[list[str]] = None) -> Note:
        """Record a cross-agent synthesis connecting multiple ideas."""
        note = Note(
            title=title,
            content=content,
            note_type=NoteType.SYNTHESIS,
            tags=tags or [],
        )
        self.graph.add_note(note)
        return note

    def recall(self, ticker: Optional[str] = None, agent: Optional[str] = None, query: Optional[str] = None, limit: int = 10) -> list[Note]:
        """Recall relevant prior knowledge for the current analysis context.

        Agents call this before analysis to retrieve relevant history,
        prior signals, and cross-agent insights.
        """
        if query:
            return self.retrieval.search(query, ticker=ticker, agent=agent, limit=limit)
        return self.retrieval.find_by_context(
            tickers=[ticker] if ticker else None,
            agents=[agent] if agent else None,
            limit=limit,
        )

    def recall_related(self, note_id: str, limit: int = 10) -> list[tuple[Note, float]]:
        """Find notes related to a specific note via graph structure."""
        return self.retrieval.find_related(note_id, limit=limit)

    def get_entry_points(self, limit: int = 10) -> list[Note]:
        """Get the best starting points for knowledge exploration."""
        return self.retrieval.entry_points(limit=limit)

    def ensure_ticker_moc(self, ticker: str) -> Note:
        """Ensure a MOC exists for the given ticker, creating one if needed."""
        existing = self.graph.get_note_by_title(f"{ticker} Knowledge Map")
        if existing:
            return existing
        return self.moc.auto_moc_for_ticker(ticker)

    def ensure_agent_moc(self, agent_name: str) -> Note:
        """Ensure a MOC exists for the given agent, creating one if needed."""
        display_name = agent_name.replace("_", " ").title()
        existing = self.graph.get_note_by_title(f"{display_name} Knowledge Map")
        if existing:
            return existing
        return self.moc.auto_moc_for_agent(agent_name)

    def knowledge_gaps(self, tickers: Optional[list[str]] = None) -> list[dict]:
        """Identify gaps in current knowledge that agents should fill."""
        return self.retrieval.knowledge_gaps(tickers=tickers)

    def stats(self) -> dict:
        """Return summary statistics about the knowledge graph."""
        all_notes = self.graph.all_notes()
        type_counts = {}
        for note in all_notes:
            type_counts[note.note_type.value] = type_counts.get(note.note_type.value, 0) + 1

        ticker_counts = {}
        for note in all_notes:
            if note.ticker:
                ticker_counts[note.ticker] = ticker_counts.get(note.ticker, 0) + 1

        agent_counts = {}
        for note in all_notes:
            if note.source_agent:
                agent_counts[note.source_agent] = agent_counts.get(note.source_agent, 0) + 1

        return {
            "total_notes": self.graph.note_count,
            "total_edges": self.graph.edge_count,
            "by_type": type_counts,
            "by_ticker": ticker_counts,
            "by_agent": agent_counts,
            "hub_notes": [(n.title, deg) for n, deg in self.graph.hub_notes(5)],
        }
