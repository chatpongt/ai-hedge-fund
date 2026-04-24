"""Phase 0: Detect the best extraction strategy for a given PDF."""

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STRATEGY_A = "strategy_A_pymupdf4llm"
STRATEGY_B = "strategy_B_marker"

# Characters that signal garbled / unrecoverable encoding
_GARBAGE_CHARS = set("□■▪▫◆◇●○◎◉★☆▲△▼▽►◄▶◀\x00�")
_GARBAGE_RATIO_THRESHOLD = 0.05  # >5% garbage → bad encoding
_MIN_TEXT_LENGTH = 100            # fewer chars on first 2 pages → likely scanned


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def _sample_text(pdf_path: str) -> str:
    """Extract text from first two pages with pdftotext."""
    result = _run(["pdftotext", "-f", "1", "-l", "2", pdf_path, "-"])
    return result.stdout


def _font_info(pdf_path: str) -> list[str]:
    """Return pdffonts output lines (one per embedded font)."""
    result = _run(["pdffonts", pdf_path])
    return result.stdout.splitlines()


def _has_thai_font_issue(font_lines: list[str]) -> bool:
    """
    Detect Thai fonts with encoding problems.
    pdffonts marks fonts with missing ToUnicode maps as 'no' in the 'uni' column.
    Thai custom encodings (TH*, Angsana, Cordia, CID-keyed without ToUnicode) are
    common culprits in SET annual reports.
    """
    for line in font_lines[2:]:  # skip header rows
        parts = line.split()
        if len(parts) < 6:
            continue
        # Column layout: name type encoding emb sub uni
        uni_col = parts[-1] if parts else ""
        font_name = parts[0].upper()
        has_thai_name = any(
            tok in font_name for tok in ("TH", "THAI", "ANGSANA", "CORDIA", "BROWALLIA", "SARABUN")
        )
        has_cid = "CID" in line.upper()
        uni_missing = uni_col.lower() == "no"

        if (has_thai_name or has_cid) and uni_missing:
            logger.debug("Thai font encoding issue detected: %s", line.strip())
            return True
    return False


def _garbage_ratio(text: str) -> float:
    if not text:
        return 1.0
    garbage = sum(1 for ch in text if ch in _GARBAGE_CHARS)
    return garbage / len(text)


def triage_pdf(path: str) -> str:
    """
    Inspect a PDF and return the recommended extraction strategy.

    Returns
    -------
    str
        'strategy_A_pymupdf4llm'  — fast, text-based extraction
        'strategy_B_marker'       — OCR/LLM-assisted extraction
    """
    pdf_path = str(Path(path).expanduser().resolve())

    sample = _sample_text(pdf_path)
    font_lines = _font_info(pdf_path)

    reason = None

    if len(sample.strip()) < _MIN_TEXT_LENGTH:
        reason = "insufficient text on first 2 pages (likely scanned)"
    elif _garbage_ratio(sample) > _GARBAGE_RATIO_THRESHOLD:
        reason = f"high garbage-char ratio ({_garbage_ratio(sample):.1%})"
    elif _has_thai_font_issue(font_lines):
        reason = "Thai font with missing ToUnicode map"

    if reason:
        logger.info("triage → %s | reason: %s | file: %s", STRATEGY_B, reason, path)
        return STRATEGY_B

    logger.info("triage → %s | file: %s", STRATEGY_A, path)
    return STRATEGY_A


def triage_batch(companies: list[dict]) -> dict[str, str]:
    """
    Run triage over a list of company dicts (from companies.json).

    Returns a mapping of pdf_path → strategy string.
    """
    results = {}
    for company in companies:
        pdf_path = company.get("pdf_path", "")
        ticker = company.get("ticker", "UNKNOWN")
        if not Path(pdf_path).exists():
            logger.warning("PDF not found for %s: %s — defaulting to %s", ticker, pdf_path, STRATEGY_B)
            results[pdf_path] = STRATEGY_B
        else:
            results[pdf_path] = triage_pdf(pdf_path)
    return results
