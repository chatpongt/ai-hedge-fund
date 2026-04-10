"""🟣 Wiki Ingest Agent — captures knowledge into persistent wiki.

Takes analysis outputs and distills them into reusable knowledge entries
stored in /mnt/outputs/wiki/ (git-tracked).
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from adapters.mlx_adapter import MLXAdapter
from config.settings import settings
from schemas.wiki_entry import WikiCategory, WikiEntry

logger = logging.getLogger(__name__)

WIKI_SYSTEM_PROMPT = """You are a knowledge curator for a Thai equity research system.

Your role: distill analysis outputs into reusable knowledge entries.

For each piece of analysis, determine:
1. Is this knowledge worth preserving? (not all daily noise is worth keeping)
2. What category does it belong to? (company, sector, macro, strategy, lesson, event)
3. Does it update/supersede an existing entry?
4. When might this knowledge expire or become stale?

Output: JSON list of WikiEntry objects with fields:
- entry_id (format: YYYY-MM-DD-slug)
- category (company|sector|macro|strategy|lesson|event)
- title
- content (Markdown)
- tickers (list)
- tags (list)
- source
- confidence (0-100)
- expiry_date (optional, YYYY-MM-DD)
- supersedes (optional, entry_id of old entry)

Only create entries for genuinely useful knowledge. Quality over quantity."""


class WikiIngestAgent:
    """Knowledge wiki ingestion and management."""

    def __init__(self, mlx: Optional[MLXAdapter] = None, wiki_dir: Optional[Path] = None):
        self.mlx = mlx or MLXAdapter()
        self.wiki_dir = wiki_dir or settings.paths.wiki_dir
        self.wiki_dir.mkdir(parents=True, exist_ok=True)

    async def run(
        self,
        analysis_date: date,
        brief_data: Optional[dict[str, Any]] = None,
        orient_data: Optional[list[dict[str, Any]]] = None,
        decide_data: Optional[dict[str, Any]] = None,
    ) -> list[WikiEntry]:
        """Ingest analysis outputs into the knowledge wiki.

        Args:
            analysis_date: Current date
            brief_data: Flash brief data
            orient_data: Orient analysis data
            decide_data: Decide recommendations data

        Returns:
            List of created WikiEntry objects
        """
        logger.info("Wiki ingest starting for %s", analysis_date)

        context = self._build_context(analysis_date, brief_data, orient_data, decide_data)

        try:
            response = await self.mlx.chat_json(
                messages=[
                    {"role": "system", "content": WIKI_SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                max_tokens=4096,
            )
            entries = self._parse_response(response, analysis_date)
            saved = self._save_entries(entries)
            logger.info("Wiki ingest completed: %d entries created", len(saved))
            return saved
        except Exception as e:
            logger.error("Wiki ingest failed: %s", e)
            return []

    def _build_context(
        self,
        analysis_date: date,
        brief_data: Optional[dict[str, Any]],
        orient_data: Optional[list[dict[str, Any]]],
        decide_data: Optional[dict[str, Any]],
    ) -> str:
        parts = [f"## Date: {analysis_date.isoformat()}"]
        if brief_data:
            parts.append(f"\n## Flash Brief\n```json\n{json.dumps(brief_data, ensure_ascii=False, default=str)}\n```")
        if orient_data:
            parts.append(f"\n## Orient Analyses ({len(orient_data)} events)\n```json\n{json.dumps(orient_data, ensure_ascii=False, default=str)}\n```")
        if decide_data:
            parts.append(f"\n## Decide Recommendations\n```json\n{json.dumps(decide_data, ensure_ascii=False, default=str)}\n```")

        # Show existing wiki entries for deduplication
        existing = self._list_recent_entries(30)
        if existing:
            parts.append(f"\n## Existing Wiki Entries (last 30 days)\n{json.dumps(existing, ensure_ascii=False)}")

        parts.append("\n## Task\nDistill the above into wiki entries. Only create entries for genuinely useful, lasting knowledge.")
        return "\n".join(parts)

    def _parse_response(self, response: str, analysis_date: date) -> list[WikiEntry]:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Wiki ingest got non-JSON response")
            return []

        entries_data = data if isinstance(data, list) else data.get("entries", [])
        entries = []
        for item in entries_data:
            try:
                if "created_at" not in item:
                    item["created_at"] = datetime.now().isoformat()
                entries.append(WikiEntry(**item))
            except Exception as e:
                logger.warning("Skipping invalid wiki entry: %s", e)
        return entries

    def _save_entries(self, entries: list[WikiEntry]) -> list[WikiEntry]:
        saved = []
        for entry in entries:
            category_dir = self.wiki_dir / entry.category.value
            category_dir.mkdir(parents=True, exist_ok=True)

            file_path = category_dir / f"{entry.entry_id}.json"
            file_path.write_text(entry.model_dump_json(indent=2), encoding="utf-8")

            # Also save a human-readable markdown version
            md_path = category_dir / f"{entry.entry_id}.md"
            md_content = f"# {entry.title}\n\n"
            md_content += f"**Category**: {entry.category.value}  \n"
            md_content += f"**Tickers**: {', '.join(entry.tickers)}  \n"
            md_content += f"**Tags**: {', '.join(entry.tags)}  \n"
            md_content += f"**Confidence**: {entry.confidence}/100  \n"
            md_content += f"**Source**: {entry.source}  \n"
            md_content += f"**Created**: {entry.created_at.isoformat()}  \n"
            if entry.expiry_date:
                md_content += f"**Expires**: {entry.expiry_date.isoformat()}  \n"
            if entry.supersedes:
                md_content += f"**Supersedes**: {entry.supersedes}  \n"
            md_content += f"\n---\n\n{entry.content}\n"
            md_path.write_text(md_content, encoding="utf-8")

            saved.append(entry)
            logger.info("Saved wiki entry: %s → %s", entry.entry_id, file_path)

        return saved

    def _list_recent_entries(self, days: int = 30) -> list[dict[str, str]]:
        """List recent wiki entry IDs and titles for deduplication."""
        recent = []
        if not self.wiki_dir.exists():
            return recent
        for json_file in sorted(self.wiki_dir.rglob("*.json"), reverse=True):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                recent.append({"entry_id": data.get("entry_id", ""), "title": data.get("title", ""), "category": data.get("category", "")})
                if len(recent) >= 50:
                    break
            except Exception:
                continue
        return recent
