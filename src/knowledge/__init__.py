"""Agent Knowledge System — Zettelkasten-inspired knowledge graph for agent cognition.

Provides external structures for agents to think with: notes, wiki links,
Maps of Content (MOCs), graph traversal, and spreading activation retrieval.
"""

from src.knowledge.note import Note, NoteType
from src.knowledge.graph import KnowledgeGraph
from src.knowledge.store import KnowledgeStore
from src.knowledge.moc import MapOfContent
from src.knowledge.retrieval import RetrievalEngine
from src.knowledge.agent_memory import AgentMemory

__all__ = [
    "Note",
    "NoteType",
    "KnowledgeGraph",
    "KnowledgeStore",
    "MapOfContent",
    "RetrievalEngine",
    "AgentMemory",
]
