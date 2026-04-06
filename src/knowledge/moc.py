"""Map of Content (MOC) — index notes that organize knowledge by topic.

MOCs are special notes (NoteType.MOC) that serve as curated entry points
into regions of the knowledge graph. They link to related notes and
provide progressive disclosure: a summary at the top, then categorized
links for deeper exploration.
"""

from datetime import datetime
from typing import Optional

from src.knowledge.graph import KnowledgeGraph
from src.knowledge.note import Note, NoteType


class MapOfContent:
    """Builder and manager for Map of Content notes.

    MOCs organize notes into sections and auto-generate wiki-linked content.
    Example topics: per-ticker analysis, per-strategy insights, cross-agent synthesis.
    """

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def create_moc(self, title: str, description: str, sections: Optional[dict[str, list[str]]] = None, tags: Optional[list[str]] = None) -> Note:
        """Create a new MOC note.

        Args:
            title: The MOC title (e.g., "AAPL Analysis", "Value Investing Insights")
            description: Summary paragraph for the MOC
            sections: Dict of section_name -> list of note titles to link
            tags: Tags for the MOC itself
        """
        content_parts = [description, ""]
        sections = sections or {}

        for section_name, note_titles in sections.items():
            content_parts.append(f"## {section_name}")
            for note_title in note_titles:
                content_parts.append(f"- [[{note_title}]]")
            content_parts.append("")

        moc_note = Note(
            title=title,
            content="\n".join(content_parts),
            note_type=NoteType.MOC,
            tags=tags or [],
        )
        self.graph.add_note(moc_note)
        return moc_note

    def add_to_moc(self, moc_title: str, section_name: str, note_title: str) -> Optional[Note]:
        """Add a note link to a section of an existing MOC."""
        moc = self.graph.get_note_by_title(moc_title)
        if moc is None or moc.note_type != NoteType.MOC:
            return None

        section_header = f"## {section_name}"
        link_line = f"- [[{note_title}]]"

        if section_header in moc.content:
            # Insert after the section header
            lines = moc.content.split("\n")
            insert_idx = None
            for i, line in enumerate(lines):
                if line.strip() == section_header:
                    insert_idx = i + 1
                    # Skip past existing links in this section
                    while insert_idx < len(lines) and lines[insert_idx].startswith("- [["):
                        insert_idx += 1
                    break
            if insert_idx is not None:
                lines.insert(insert_idx, link_line)
                moc.content = "\n".join(lines)
        else:
            # Append new section
            moc.content += f"\n{section_header}\n{link_line}\n"

        moc.updated_at = datetime.utcnow()
        self.graph.rebuild_all_edges()
        return moc

    def auto_moc_for_ticker(self, ticker: str) -> Note:
        """Auto-generate a MOC for a specific ticker from existing notes."""
        related_notes = [n for n in self.graph.all_notes() if n.ticker == ticker and n.note_type != NoteType.MOC]

        sections: dict[str, list[str]] = {}
        for note in related_notes:
            section = note.note_type.value.title()
            sections.setdefault(section, []).append(note.title)

        return self.create_moc(
            title=f"{ticker} Knowledge Map",
            description=f"Collected knowledge and analysis for {ticker}.",
            sections=sections,
            tags=[ticker, "auto-moc"],
        )

    def auto_moc_for_agent(self, agent_name: str) -> Note:
        """Auto-generate a MOC for a specific agent's contributions."""
        related_notes = [n for n in self.graph.all_notes() if n.source_agent == agent_name and n.note_type != NoteType.MOC]

        sections: dict[str, list[str]] = {}
        for note in related_notes:
            section = note.ticker or "General"
            sections.setdefault(section, []).append(note.title)

        display_name = agent_name.replace("_", " ").title()
        return self.create_moc(
            title=f"{display_name} Knowledge Map",
            description=f"Knowledge contributed by the {display_name} agent.",
            sections=sections,
            tags=[agent_name, "auto-moc"],
        )

    def list_mocs(self) -> list[Note]:
        """Return all MOC notes in the graph."""
        return [n for n in self.graph.all_notes() if n.note_type == NoteType.MOC]
