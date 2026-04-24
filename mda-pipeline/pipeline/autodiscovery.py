"""
Auto-discover PDFs from data/input/ and infer ticker + year from filename.

Naming conventions supported (case-insensitive):
  cpall_ar_2024.pdf
  CPALL_2024.pdf
  cpall-annual-report-2024.pdf
  AOT_Annual_Report_2024.pdf
  56-1-one-report-KBANK-2024.pdf
  PTT_56-1_FY2024.pdf
  scb_56-1_one-report_2024.pdf

If the filename cannot be parsed automatically the file is still added to the
queue but flagged as 'needs_review' so the user can rename it.
"""

import re
import subprocess
from pathlib import Path

# Words that appear in filenames but are NOT tickers
_NON_TICKER_WORDS = {
    "AR", "FY", "ONE", "PDF", "ANN", "ANNUAL", "REPORT", "56", "56-1",
    "ONE-REPORT", "ONEREPORT", "THE", "AND", "OF", "IN", "BY",
    "TH", "EN", "SET", "SEC", "IR",
}

# Known SET tickers for disambiguation (extend as needed)
_KNOWN_TICKERS = {
    "ADVANC", "AOT", "AWC", "BAM", "BANPU", "BBL", "BCH", "BCP", "BCPG",
    "BEC", "BGRIM", "BH", "BJC", "BLA", "BPP", "BTS", "CENTEL", "CK", "CKP",
    "COM7", "CPALL", "CPF", "CPN", "DELTA", "DTAC", "EA", "EGCO", "ERW",
    "ESSO", "GFPT", "GLOBAL", "GPSC", "GULF", "HANA", "HMPRO", "INTUCH",
    "IRPC", "IVL", "JASIF", "JMT", "JMART", "KCE", "KKP", "KTB", "KBANK",
    "KTC", "LH", "LHFG", "MAKRO", "MBK", "MEGA", "MTC", "NCP", "ORI",
    "OSP", "PPB", "PR9", "PTTEP", "PTT", "PTTGC", "RATCH", "RS", "SABUY",
    "SAT", "SCB", "SCGP", "SCG", "SCC", "SGP", "SINGER", "SJWD", "SPALI",
    "SPRC", "STA", "STGT", "SUPER", "TEAMG", "THAI", "THANI", "TKN", "TMB",
    "TNITY", "TOA", "TOP", "TPBI", "TPIPP", "TQM", "TRUE", "TTA", "TTBL",
    "TTCL", "TU", "TVD", "TWPC", "U", "UAC", "UNIQ", "VGI", "VIH", "WHA",
    "WHAUP", "YUASA",
}

_YEAR_RE = re.compile(r"(?<!\d)(20[12]\d)(?!\d)")
_TOKEN_RE = re.compile(r"[A-Za-z]+")


def _extract_year(stem: str) -> int | None:
    m = _YEAR_RE.search(stem)
    return int(m.group(1)) if m else None


def _extract_ticker(stem: str) -> str | None:
    # 1. Check for known tickers first (most reliable)
    upper_stem = stem.upper()
    for ticker in sorted(_KNOWN_TICKERS, key=len, reverse=True):
        # Word-boundary-aware match
        if re.search(r"(?<![A-Z])" + re.escape(ticker) + r"(?![A-Z])", upper_stem):
            return ticker

    # 2. Fallback: pick longest uppercase-ish token that looks like a ticker
    tokens = _TOKEN_RE.findall(stem)
    candidates = [
        t.upper() for t in tokens
        if 2 <= len(t) <= 6 and t.upper() not in _NON_TICKER_WORDS and not t.isdigit()
    ]
    if candidates:
        return max(candidates, key=len)

    return None


def _detect_language(pdf_path: str) -> str:
    """Quick heuristic: if first-page text has Thai chars → 'th', else 'en'."""
    try:
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", pdf_path, "-"],
            capture_output=True, text=True, timeout=15,
        )
        thai_chars = sum(1 for ch in result.stdout if "฀" <= ch <= "๿")
        return "th" if thai_chars > 20 else "en"
    except Exception:
        return "th"  # default for SET reports


def discover_pdfs(input_dir: str) -> tuple[list[dict], list[dict]]:
    """
    Scan *input_dir* for PDF files and build company dicts.

    Returns
    -------
    (ready, needs_review)
        ready         — list of dicts with ticker + year parsed successfully
        needs_review  — list of dicts where filename was ambiguous
    """
    input_path = Path(input_dir)
    pdf_files = sorted(input_path.glob("*.pdf")) + sorted(input_path.glob("**/*.pdf"))
    # Deduplicate (glob may overlap)
    seen: set[str] = set()
    unique_pdfs = []
    for p in pdf_files:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique_pdfs.append(p)

    ready: list[dict] = []
    needs_review: list[dict] = []

    for pdf in unique_pdfs:
        stem = pdf.stem
        ticker = _extract_ticker(stem)
        year = _extract_year(stem)
        lang = _detect_language(str(pdf))

        entry = {
            "ticker": ticker or "UNKNOWN",
            "year": year or 0,
            "pdf_path": str(pdf),
            "language": lang,
            "source": "auto_discovered",
            "_filename": pdf.name,
        }

        if ticker and year:
            ready.append(entry)
        else:
            entry["_parse_issue"] = (
                "missing ticker" if not ticker else "missing year"
                if not year else "missing ticker and year"
            )
            needs_review.append(entry)

    return ready, needs_review
