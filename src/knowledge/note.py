"""Note model with wiki link support for the agent knowledge system.

Notes are the atomic units of knowledge, inspired by Zettelkasten.
Each note has a unique ID, content with [[wiki links]], metadata,
and typed classification (insight, signal, analysis, moc, etc.).
"""

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NoteType(str, Enum):
    """Classification of knowledge notes."""

    INSIGHT = "insight"  # A distilled observation or conclusion
    SIGNAL = "signal"  # An agent's trading signal with reasoning
    ANALYSIS = "analysis"  # Detailed analysis of a topic
    MOC = "moc"  # Map of Content — index note linking related notes
    SYNTHESIS = "synthesis"  # Cross-cutting argument connecting multiple ideas
    EXPLORATION = "exploration"  # Open question or area needing investigation


# Pattern to match [[wiki links]] in note content
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def extract_wiki_links(content: str) -> list[str]:
    """Extract all [[wiki link]] targets from content."""
    return WIKI_LINK_PATTERN.findall(content)


def generate_note_id() -> str:
    """Generate a unique note ID."""
    return uuid.uuid4().hex[:12]


class Note(BaseModel):
    """A single knowledge note — the atomic unit of the knowledge graph.

    Notes contain content with [[wiki links]] that form edges in the
    knowledge graph. Each note is typed, timestamped, and tagged for
    efficient retrieval.
    """

    id: str = Field(default_factory=generate_note_id)
    title: str
    content: str
    note_type: NoteType = NoteType.INSIGHT
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source_agent: Optional[str] = None
    ticker: Optional[str] = None
    confidence: Optional[float] = None
    metadata: dict = Field(default_factory=dict)

    @property
    def outgoing_links(self) -> list[str]:
        """Extract all [[wiki link]] targets from this note's content."""
        return extract_wiki_links(self.content)

    def add_link(self, target_title: str) -> None:
        """Append a wiki link to the content."""
        self.content += f" [[{target_title}]]"
        self.updated_at = datetime.utcnow()

    def matches_query(self, query: str) -> bool:
        """Check if this note matches a text query (case-insensitive)."""
        query_lower = query.lower()
        return query_lower in self.title.lower() or query_lower in self.content.lower() or any(query_lower in tag.lower() for tag in self.tags)

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
