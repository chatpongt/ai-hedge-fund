"""
triage.py — Phase 1: Document triage for MD&A detection pipeline.

Classifies PDF annual reports by:
  - Document type  (annual_report / 56-1 / form_f / unknown)
  - Language       (thai / english / bilingual)
  - TOC presence   and page numbers
  - Best detection strategy to use downstream

Usage:
    python triage.py CPALL_AR2024.pdf --ticker CPALL
    python triage.py report.pdf --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal

import fitz  # PyMuPDF
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------------
# Pydantic result model
# ---------------------------------------------------------------------------

DocType = Literal["annual_report", "56-1", "form_f", "unknown"]
Language = Literal["thai", "english", "bilingual"]
Strategy = Literal["toc_jump", "header_scan", "fuzzy_scan"]


class TriageResult(BaseModel):
    ticker: str | None = None
    pdf_path: str
    total_pages: int
    doc_type: DocType
    language: Language
    has_toc: bool
    toc_pages: list[int] = Field(default_factory=list)
    strategy: Strategy
    confidence: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()


# ---------------------------------------------------------------------------
# Language detection helpers
# ---------------------------------------------------------------------------

# Unicode range for Thai script: U+0E00–U+0E7F
_THAI_RE = re.compile(r"[฀-๿]")
_ENG_WORD_RE = re.compile(r"[A-Za-z]{3,}")


def _detect_language(sample_text: str) -> Language:
    thai_chars = len(_THAI_RE.findall(sample_text))
    eng_words = len(_ENG_WORD_RE.findall(sample_text))
    total = thai_chars + eng_words
    if total == 0:
        return "english"
    thai_ratio = thai_chars / total
    if thai_ratio > 0.70:
        return "thai"
    if thai_ratio < 0.25:
        return "english"
    return "bilingual"


# ---------------------------------------------------------------------------
# Document type detection
# ---------------------------------------------------------------------------

# Signals for each document type (search first 20 pages)
_DOC_TYPE_SIGNALS: dict[DocType, list[str]] = {
    "annual_report": [
        "annual report",
        "รายงานประจำปี",
        "annual report 20",
        "รายงานประจำปี 25",  # BE year
    ],
    "56-1": [
        "แบบ 56-1",
        "แบบแสดงรายการข้อมูลประจำปี",
        "form 56-1",
        "one report",
        "56-1 one report",
    ],
    "form_f": [
        "form 20-f",
        "form 40-f",
        "form 6-k",
        "annual report on form",
        "securities and exchange commission",
    ],
}


def _detect_doc_type(pages_text: list[str]) -> tuple[DocType, float]:
    """Score each doc type against first 20 pages; return best match."""
    early_text = " ".join(pages_text[:20]).lower()
    scores: dict[DocType, int] = {k: 0 for k in _DOC_TYPE_SIGNALS}
    for doc_type, signals in _DOC_TYPE_SIGNALS.items():
        for sig in signals:
            if sig.lower() in early_text:
                scores[doc_type] += 1

    best_type: DocType = max(scores, key=lambda k: scores[k])  # type: ignore[arg-type]
    best_score = scores[best_type]
    if best_score == 0:
        return "unknown", 0.3
    confidence = min(0.5 + best_score * 0.1, 0.95)
    return best_type, confidence


# ---------------------------------------------------------------------------
# TOC detection
# ---------------------------------------------------------------------------

# Thai and English TOC header patterns
_TOC_HEADER_PATTERNS = [
    re.compile(r"สารบ[ัั]ญ", re.IGNORECASE),
    re.compile(r"table\s+of\s+contents?", re.IGNORECASE),
    re.compile(r"contents?\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"รายการ\s*เนื้อหา", re.IGNORECASE),
]

# A TOC page typically has many lines that end with a page number
_TOC_LINE_PATTERN = re.compile(r".{5,}\s+\.{2,}\s*\d+\s*$|.{5,}\s+\d{1,3}\s*$", re.MULTILINE)


def _is_toc_page(text: str) -> bool:
    """Heuristic: page is a TOC if it has a TOC header OR many dot-leader lines."""
    for pat in _TOC_HEADER_PATTERNS:
        if pat.search(text):
            return True
    dot_lines = _TOC_LINE_PATTERN.findall(text)
    # At least 5 entries with page numbers suggests a TOC
    return len(dot_lines) >= 5


def _find_toc_pages(pages_text: list[str], max_search: int = 30) -> list[int]:
    toc_pages: list[int] = []
    search_limit = min(max_search, len(pages_text))
    for i, text in enumerate(pages_text[:search_limit]):
        if _is_toc_page(text):
            toc_pages.append(i)  # 0-indexed; caller can +1 for display
    return toc_pages


# ---------------------------------------------------------------------------
# Strategy selection
# ---------------------------------------------------------------------------


def _choose_strategy(has_toc: bool, language: Language, total_pages: int) -> Strategy:
    """
    toc_jump   — use TOC to locate MD&A page directly (fastest, most reliable)
    header_scan — scan every page for MD&A section header
    fuzzy_scan  — broader fuzzy match for poorly-formatted PDFs
    """
    if has_toc:
        return "toc_jump"
    # Large bilingual/Thai docs without TOC → header_scan usually works
    if total_pages <= 300:
        return "header_scan"
    # Very large docs with no TOC → fall back to fuzzy
    return "fuzzy_scan"


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------


def _extract_pages_text(doc: fitz.Document) -> list[str]:
    """Extract plain text for every page. Returns list indexed by page number."""
    texts: list[str] = []
    for page in doc:
        texts.append(page.get_text("text"))  # type: ignore[attr-defined]
    return texts


# ---------------------------------------------------------------------------
# Main triage function
# ---------------------------------------------------------------------------


def triage_pdf(pdf_path: str | Path, ticker: str | None = None) -> TriageResult:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    total_pages = doc.page_count
    pages_text = _extract_pages_text(doc)
    doc.close()

    # --- language (sample first 10 pages) ---
    sample = " ".join(pages_text[:10])
    language = _detect_language(sample)

    # --- doc type ---
    doc_type, type_confidence = _detect_doc_type(pages_text)

    # --- TOC ---
    toc_pages = _find_toc_pages(pages_text)
    has_toc = len(toc_pages) > 0

    # --- strategy ---
    strategy = _choose_strategy(has_toc, language, total_pages)

    # --- overall confidence ---
    # Combine type confidence with presence of TOC as supporting signal
    confidence = round(type_confidence * (1.1 if has_toc else 0.9), 3)
    confidence = min(confidence, 0.99)

    notes: list[str] = []
    if doc_type == "unknown":
        notes.append("Could not classify document type — MD&A detection may be less accurate.")
    if not has_toc and total_pages > 100:
        notes.append("No TOC found in first 30 pages; falling back to header scan.")

    return TriageResult(
        ticker=ticker,
        pdf_path=str(pdf_path),
        total_pages=total_pages,
        doc_type=doc_type,
        language=language,
        has_toc=has_toc,
        toc_pages=[p + 1 for p in toc_pages],  # convert to 1-indexed for display
        strategy=strategy,
        confidence=confidence,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# CLI display
# ---------------------------------------------------------------------------


def _print_result(result: TriageResult) -> None:
    table = Table(title=f"Triage: {Path(result.pdf_path).name}", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="dim", width=20)
    table.add_column("Value")

    rows = [
        ("ticker", result.ticker or "—"),
        ("total_pages", str(result.total_pages)),
        ("doc_type", result.doc_type),
        ("language", result.language),
        ("has_toc", "✓" if result.has_toc else "✗"),
        ("toc_pages", str(result.toc_pages) if result.toc_pages else "—"),
        ("strategy", f"[bold green]{result.strategy}[/bold green]"),
        ("confidence", f"{result.confidence:.2%}"),
    ]
    for field, value in rows:
        table.add_row(field, value)

    console.print(table)

    if result.notes:
        for note in result.notes:
            console.print(f"  [yellow]⚠[/yellow]  {note}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF triage for MD&A detection pipeline")
    parser.add_argument("pdf", help="Path to the annual report PDF")
    parser.add_argument("--ticker", default=None, help="Stock ticker (e.g. CPALL)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    args = parser.parse_args()

    try:
        result = triage_pdf(args.pdf, ticker=args.ticker)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    if args.as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_result(result)


if __name__ == "__main__":
    main()
