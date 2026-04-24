"""Phase 1: Extract full text from PDF using the triaged strategy."""

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Strategy A — pymupdf4llm (fast, text-based)
# ---------------------------------------------------------------------------

def extract_pymupdf4llm(pdf_path: str) -> str:
    """
    Convert PDF to markdown using pymupdf4llm.
    Returns markdown string or raises RuntimeError.
    """
    try:
        import pymupdf4llm  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pymupdf4llm not installed — run: pip install pymupdf4llm") from exc

    logger.info("extract [pymupdf4llm] %s", pdf_path)
    md = pymupdf4llm.to_markdown(pdf_path)
    logger.info("extracted %d chars via pymupdf4llm", len(md))
    return md


# ---------------------------------------------------------------------------
# Strategy B — marker-pdf (OCR / bad Thai fonts)
# ---------------------------------------------------------------------------

def extract_marker(pdf_path: str, langs: str = "tha,eng", output_dir: str | None = None) -> str:
    """
    Convert PDF to markdown using marker-pdf CLI.
    Writes output to a temp dir (or output_dir) and reads it back.
    Returns markdown string or raises RuntimeError.
    """
    pdf_path = str(Path(pdf_path).expanduser().resolve())
    stem = Path(pdf_path).stem

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = output_dir or tmp
        cmd = [
            "marker_single",
            pdf_path,
            "--output_dir", out_dir,
            "--langs", langs,
        ]
        logger.info("extract [marker] %s  cmd: %s", pdf_path, " ".join(cmd))
        logger.info("marker may take several minutes for long PDFs (~0.86 s/page)")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if result.returncode != 0:
            raise RuntimeError(f"marker failed (rc={result.returncode}): {result.stderr[:500]}")

        # marker writes: {output_dir}/{stem}/{stem}.md
        md_file = Path(out_dir) / stem / f"{stem}.md"
        if not md_file.exists():
            # older marker versions write directly
            md_file = Path(out_dir) / f"{stem}.md"
        if not md_file.exists():
            raise RuntimeError(f"marker output not found at expected path: {md_file}")

        text = md_file.read_text(encoding="utf-8")
        logger.info("extracted %d chars via marker", len(text))
        return text


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def extract(pdf_path: str, strategy: str, marker_langs: str = "tha,eng") -> str:
    """
    Extract text from *pdf_path* using the given strategy string.

    Parameters
    ----------
    pdf_path : str
    strategy : str
        'strategy_A_pymupdf4llm' | 'strategy_B_marker'
    marker_langs : str
        Comma-separated lang codes for marker (default: 'tha,eng')

    Returns
    -------
    str  — full markdown/text content of the PDF
    """
    if strategy == "strategy_A_pymupdf4llm":
        try:
            return extract_pymupdf4llm(pdf_path)
        except Exception as exc:
            logger.warning("strategy_A failed (%s) — falling back to marker", exc)
            return extract_marker(pdf_path, langs=marker_langs)

    if strategy == "strategy_B_marker":
        return extract_marker(pdf_path, langs=marker_langs)

    raise ValueError(f"Unknown strategy: {strategy!r}")
