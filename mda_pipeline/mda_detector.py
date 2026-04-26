"""
mda_detector.py — Phase 2: MD&A section boundary detection.

Given a PDF (optionally with a pre-computed TriageResult), locates the start
and end pages of the "Management Discussion & Analysis" section using a
three-strategy cascade:

  Strategy 1 — toc_jump    : parse TOC, jump directly to the listed page
  Strategy 2 — header_scan : scan every page for an MD&A section header
  Strategy 3 — fuzzy_scan  : broader keyword matching for edge cases

Thai headers supported (7 patterns):
  • คำอธิบายและการวิเคราะห์ของฝ่ายจัดการ
  • การวิเคราะห์และคำอธิบายของฝ่ายจัดการ
  • คำอธิบายของฝ่ายจัดการ
  • MD&A, Management Discussion, Management's Discussion, MDA

Usage:
    python mda_detector.py CPALL_AR2024.pdf --ticker CPALL
    python mda_detector.py report.pdf --json
    python mda_detector.py report.pdf --triage-json triage_out.json
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

# Import triage from the same package if available
try:
    from triage import TriageResult, triage_pdf
except ImportError:
    from mda_pipeline.triage import TriageResult, triage_pdf  # type: ignore[no-redef]

console = Console()

# ---------------------------------------------------------------------------
# Pydantic result model
# ---------------------------------------------------------------------------

StrategyUsed = Literal["toc_jump", "header_scan", "fuzzy_scan", "none"]


class DetectionResult(BaseModel):
    ticker: str | None = None
    pdf_path: str
    total_pages: int
    mda_start_page: int | None = None  # 1-indexed
    mda_end_page: int | None = None    # 1-indexed, inclusive
    strategy_used: StrategyUsed = "none"
    section_title: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.mda_start_page is not None

    @property
    def page_count(self) -> int | None:
        if self.mda_start_page is None or self.mda_end_page is None:
            return None
        return self.mda_end_page - self.mda_start_page + 1

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["found"] = self.found
        d["page_count"] = self.page_count
        return d


# ---------------------------------------------------------------------------
# MD&A header patterns — Thai + English
# ---------------------------------------------------------------------------

# Thai MD&A header variants (7 patterns, compiled once)
_THAI_MDA_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"คำอธิบายและการวิเคราะห์ของฝ่ายจัดการ", re.IGNORECASE),
    re.compile(r"การวิเคราะห์และคำอธิบายของฝ่ายจัดการ", re.IGNORECASE),
    re.compile(r"คำอธิบายของฝ่ายจัดการ", re.IGNORECASE),
    re.compile(r"คำอธิบายและการวิเคราะห์\s*ของ\s*ฝ่ายจัดการ", re.IGNORECASE),
    re.compile(r"การวิเคราะห์ของฝ่ายจัดการ", re.IGNORECASE),
    re.compile(r"ผลการดำเนินงานและฐานะการเงิน", re.IGNORECASE),  # alternative Thai phrasing
    re.compile(r"การวิเคราะห์ฐานะการเงินและผลการดำเนินงาน", re.IGNORECASE),
]

# English MD&A header variants
_ENG_MDA_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"management['']?s?\s+discussion\s+and\s+analysis", re.IGNORECASE),
    re.compile(r"\bmd&a\b", re.IGNORECASE),
    re.compile(r"\bmda\b", re.IGNORECASE),
    re.compile(r"management['']?s?\s+discussion", re.IGNORECASE),
    re.compile(r"discussion\s+and\s+analysis\s+of\s+financial", re.IGNORECASE),
    re.compile(r"management\s+report\s+and\s+analysis", re.IGNORECASE),
]

_ALL_MDA_PATTERNS = _THAI_MDA_PATTERNS + _ENG_MDA_PATTERNS

# Fuzzy fallback: broader patterns used only in strategy 3
_FUZZY_MDA_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"financial\s+(performance|results|review)", re.IGNORECASE),
    re.compile(r"(operating|operational)\s+results?", re.IGNORECASE),
    re.compile(r"ผลการดำเนิน", re.IGNORECASE),
    re.compile(r"ผลประกอบการ", re.IGNORECASE),
    re.compile(r"วิเคราะห์ผลการดำเนิน", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# "Next major section" patterns — used to detect MD&A end
# ---------------------------------------------------------------------------

_NEXT_SECTION_PATTERNS: list[re.Pattern[str]] = [
    # Thai section headers that follow MD&A
    re.compile(r"^(รายงาน|การกำกับดูแล|ข้อมูลหลักทรัพย์|โครงสร้างผู้ถือหุ้น|ปัจจัยความเสี่ยง)", re.MULTILINE),
    re.compile(r"^(นโยบายและภาพรวม|ลักษณะการประกอบธุรกิจ|ข้อมูลทั่วไป)", re.MULTILINE),
    re.compile(r"^(งบการเงิน|หมายเหตุประกอบงบ)", re.MULTILINE),
    # English
    re.compile(r"^(risk\s+factors?|corporate\s+governance|shareholder|financial\s+statements?)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(notes?\s+to\s+(the\s+)?financial|auditor['']?s?\s+report)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(business\s+overview|company\s+overview|general\s+information)", re.IGNORECASE | re.MULTILINE),
    # Generic numbered/lettered section start
    re.compile(r"^(chapter|section|part)\s+\d+", re.IGNORECASE | re.MULTILINE),
]

# Minimum pages an MD&A section should span (guard against false positives)
_MIN_MDA_PAGES = 3
# Maximum reasonable MD&A section length (pages) — stops run-on detection
_MAX_MDA_PAGES = 80


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_pages_text(doc: fitz.Document) -> list[str]:
    return [page.get_text("text") for page in doc]  # type: ignore[attr-defined]


def _match_mda_header(text: str, patterns: list[re.Pattern[str]] | None = None) -> tuple[bool, str | None]:
    """Return (matched, matched_text) for the first matching pattern."""
    if patterns is None:
        patterns = _ALL_MDA_PATTERNS
    for pat in patterns:
        m = pat.search(text)
        if m:
            return True, m.group(0)
    return False, None


def _is_section_start(text: str) -> bool:
    for pat in _NEXT_SECTION_PATTERNS:
        if pat.search(text):
            return True
    return False


def _find_mda_end(pages_text: list[str], start_idx: int) -> int:
    """
    From start_idx, scan forward to find the first page that looks like the
    beginning of a new major section.  Returns 1-indexed page number.
    Caps at _MAX_MDA_PAGES after the start.
    """
    cap = min(start_idx + _MAX_MDA_PAGES, len(pages_text))
    for i in range(start_idx + _MIN_MDA_PAGES, cap):
        if _is_section_start(pages_text[i]):
            # End is the page before the new section (1-indexed = i)
            return i  # i is 0-indexed next section start → 1-indexed end = i
    # Didn't find a clean boundary — return cap (1-indexed)
    return cap


# ---------------------------------------------------------------------------
# TOC parsing for toc_jump strategy
# ---------------------------------------------------------------------------

# Pattern: "MD&A / คำอธิบาย... <dots> <page_number>"
_TOC_ENTRY_RE = re.compile(
    r"(?:(?:คำอธิบาย|การวิเคราะห์|md&a|management\s+discussion).{0,60}?)"
    r"[\s\.·…\-]{2,}"
    r"(\d{1,4})\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Also try: line that matches MD&A + ends with a number (looser)
_TOC_LOOSE_RE = re.compile(
    r"(?:คำอธิบาย|การวิเคราะห์|md&a|management\s+discussion|mda).{0,80}?(\d{1,4})\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _parse_toc_for_mda(pages_text: list[str], toc_pages: list[int]) -> tuple[int | None, str | None]:
    """
    Scan TOC pages (1-indexed list) and return (page_number, matched_text).
    page_number is the document page number listed in the TOC entry.
    """
    # toc_pages is 1-indexed (from TriageResult); convert to 0-indexed for list access
    candidates: list[tuple[int, str]] = []
    search_pages = [p - 1 for p in toc_pages] if toc_pages else list(range(min(30, len(pages_text))))

    for idx in search_pages:
        if idx >= len(pages_text):
            continue
        text = pages_text[idx]
        for pattern in [_TOC_ENTRY_RE, _TOC_LOOSE_RE]:
            for m in pattern.finditer(text):
                page_ref = int(m.group(1))
                candidates.append((page_ref, m.group(0).strip()))

    if not candidates:
        return None, None

    # If multiple hits, prefer the one with lowest page number that's > 10
    # (avoid front-matter false positives)
    valid = [(p, t) for p, t in candidates if p > 10]
    if not valid:
        valid = candidates
    valid.sort(key=lambda x: x[0])
    return valid[0]


# ---------------------------------------------------------------------------
# Strategy 1: toc_jump
# ---------------------------------------------------------------------------


def _strategy_toc_jump(
    pages_text: list[str],
    triage: TriageResult,
) -> DetectionResult | None:
    """Use the TOC to get the start page, then confirm the header is there."""
    toc_page_ref, match_text = _parse_toc_for_mda(pages_text, triage.toc_pages)
    if toc_page_ref is None:
        return None

    # TOC page numbers may be PDF page numbers or document page numbers.
    # Try both: direct index and offset by number of TOC/cover pages.
    candidates_0idx = [toc_page_ref - 1]  # assume doc page = PDF page (common)
    # Also try ±3 around the referenced page to handle offset
    for delta in range(-3, 4):
        c = toc_page_ref - 1 + delta
        if 0 <= c < len(pages_text) and c not in candidates_0idx:
            candidates_0idx.append(c)

    for idx in sorted(candidates_0idx):
        if idx < 0 or idx >= len(pages_text):
            continue
        matched, title = _match_mda_header(pages_text[idx])
        if matched:
            end_page = _find_mda_end(pages_text, idx)
            return DetectionResult(
                ticker=triage.ticker,
                pdf_path=triage.pdf_path,
                total_pages=triage.total_pages,
                mda_start_page=idx + 1,
                mda_end_page=end_page,
                strategy_used="toc_jump",
                section_title=title or match_text,
                confidence=0.92,
                notes=[f"TOC entry pointed to page {toc_page_ref}; confirmed header at PDF page {idx + 1}."],
            )

    # TOC pointed to a page but header wasn't exactly there — still trust the reference
    idx = toc_page_ref - 1
    if 0 <= idx < len(pages_text):
        end_page = _find_mda_end(pages_text, idx)
        return DetectionResult(
            ticker=triage.ticker,
            pdf_path=triage.pdf_path,
            total_pages=triage.total_pages,
            mda_start_page=idx + 1,
            mda_end_page=end_page,
            strategy_used="toc_jump",
            section_title=match_text,
            confidence=0.72,
            notes=["TOC entry found but MD&A header not confirmed on target page; using TOC reference as-is."],
        )

    return None


# ---------------------------------------------------------------------------
# Strategy 2: header_scan
# ---------------------------------------------------------------------------


def _strategy_header_scan(
    pages_text: list[str],
    triage: TriageResult,
) -> DetectionResult | None:
    """Scan every page for an MD&A section header."""
    for idx, text in enumerate(pages_text):
        matched, title = _match_mda_header(text)
        if matched:
            end_page = _find_mda_end(pages_text, idx)
            return DetectionResult(
                ticker=triage.ticker,
                pdf_path=triage.pdf_path,
                total_pages=triage.total_pages,
                mda_start_page=idx + 1,
                mda_end_page=end_page,
                strategy_used="header_scan",
                section_title=title,
                confidence=0.85,
                notes=[f"MD&A header '{title}' found on page {idx + 1}."],
            )
    return None


# ---------------------------------------------------------------------------
# Strategy 3: fuzzy_scan
# ---------------------------------------------------------------------------


def _strategy_fuzzy_scan(
    pages_text: list[str],
    triage: TriageResult,
) -> DetectionResult | None:
    """
    Broader keyword matching for PDFs where the section header isn't clean.
    Scores each page by counting fuzzy signal hits; picks the best candidate.
    """
    all_patterns = _ALL_MDA_PATTERNS + _FUZZY_MDA_PATTERNS
    page_scores: list[tuple[int, int, str]] = []  # (score, idx, matched_text)

    for idx, text in enumerate(pages_text):
        score = 0
        best_match: str | None = None
        for pat in all_patterns:
            m = pat.search(text)
            if m:
                score += 1
                if best_match is None:
                    best_match = m.group(0)
        if score > 0:
            page_scores.append((score, idx, best_match or ""))

    if not page_scores:
        return None

    # Best scored page
    page_scores.sort(key=lambda x: -x[0])
    best_score, best_idx, best_text = page_scores[0]
    end_page = _find_mda_end(pages_text, best_idx)

    confidence = min(0.4 + best_score * 0.1, 0.75)
    return DetectionResult(
        ticker=triage.ticker,
        pdf_path=triage.pdf_path,
        total_pages=triage.total_pages,
        mda_start_page=best_idx + 1,
        mda_end_page=end_page,
        strategy_used="fuzzy_scan",
        section_title=best_text,
        confidence=round(confidence, 3),
        notes=[
            f"Fuzzy scan: best match on page {best_idx + 1} with score {best_score}.",
            "Low confidence — manual verification recommended.",
        ],
    )


# ---------------------------------------------------------------------------
# Main detection function (cascade)
# ---------------------------------------------------------------------------


def detect_mda(
    pdf_path: str | Path,
    ticker: str | None = None,
    triage: TriageResult | None = None,
) -> DetectionResult:
    """
    Detect MD&A section boundaries.

    Args:
        pdf_path:  Path to the annual report PDF.
        ticker:    Optional stock ticker for labelling.
        triage:    Pre-computed TriageResult (runs triage internally if None).

    Returns:
        DetectionResult with start/end pages (1-indexed).
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if triage is None:
        triage = triage_pdf(pdf_path, ticker=ticker)

    doc = fitz.open(str(pdf_path))
    pages_text = _extract_pages_text(doc)
    doc.close()

    # Cascade through strategies in order of confidence
    strategy_order = _build_strategy_order(triage.strategy)

    for strategy_fn in strategy_order:
        result = strategy_fn(pages_text, triage)
        if result is not None and result.found:
            return result

    # Nothing found
    return DetectionResult(
        ticker=ticker or triage.ticker,
        pdf_path=str(pdf_path),
        total_pages=triage.total_pages,
        strategy_used="none",
        confidence=0.0,
        notes=["MD&A section not found after exhausting all strategies."],
    )


def _build_strategy_order(preferred: str) -> list:
    """Return strategy functions in cascade order based on triage recommendation."""
    all_strategies = {
        "toc_jump": _strategy_toc_jump,
        "header_scan": _strategy_header_scan,
        "fuzzy_scan": _strategy_fuzzy_scan,
    }
    order = [preferred, "header_scan", "fuzzy_scan", "toc_jump"]
    seen: set[str] = set()
    result = []
    for name in order:
        if name not in seen and name in all_strategies:
            result.append(all_strategies[name])
            seen.add(name)
    return result


# ---------------------------------------------------------------------------
# CLI display
# ---------------------------------------------------------------------------


def _print_result(result: DetectionResult, triage: TriageResult) -> None:
    status = "[bold green]FOUND[/bold green]" if result.found else "[bold red]NOT FOUND[/bold red]"
    table = Table(
        title=f"MD&A Detection: {Path(result.pdf_path).name}  —  {status}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Field", style="dim", width=20)
    table.add_column("Value")

    rows: list[tuple[str, str]] = [
        ("ticker", result.ticker or "—"),
        ("total_pages", str(result.total_pages)),
        ("strategy_used", result.strategy_used),
        ("mda_start_page", str(result.mda_start_page) if result.mda_start_page else "—"),
        ("mda_end_page", str(result.mda_end_page) if result.mda_end_page else "—"),
        ("page_count", str(result.page_count) if result.page_count else "—"),
        ("section_title", result.section_title or "—"),
        ("confidence", f"{result.confidence:.2%}"),
    ]
    for field, value in rows:
        table.add_row(field, value)

    console.print()
    console.print(table)

    if result.notes:
        for note in result.notes:
            console.print(f"  [yellow]⚠[/yellow]  {note}")
    console.print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="MD&A section detector for annual report PDFs")
    parser.add_argument("pdf", help="Path to the annual report PDF")
    parser.add_argument("--ticker", default=None, help="Stock ticker (e.g. CPALL)")
    parser.add_argument("--triage-json", default=None, help="Path to pre-computed triage JSON (optional)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    args = parser.parse_args()

    triage: TriageResult | None = None
    if args.triage_json:
        try:
            with open(args.triage_json, encoding="utf-8") as f:
                triage = TriageResult(**json.load(f))
        except Exception as exc:
            console.print(f"[red]Failed to load triage JSON:[/red] {exc}")
            sys.exit(1)

    try:
        if triage is None:
            triage = triage_pdf(args.pdf, ticker=args.ticker)
            if not args.as_json:
                console.print("[dim]Triage complete → running detection…[/dim]")
        result = detect_mda(args.pdf, ticker=args.ticker, triage=triage)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    if args.as_json:
        output = {"triage": triage.to_dict(), "detection": result.to_dict()}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        _print_result(result, triage)


if __name__ == "__main__":
    main()
