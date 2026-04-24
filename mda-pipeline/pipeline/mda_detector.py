"""Phase 2: Locate the MD&A section within extracted text."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns — Thai-first, then English
# ---------------------------------------------------------------------------

MDA_START_PATTERNS: list[str] = [
    # Thai patterns (56-1 One Report format variants)
    r"การวิเคราะห์และคำอธิบายของฝ่ายจัดการ",
    r"คำอธิบายและการวิเคราะห์ของฝ่ายจัดการ",
    r"คำอธิบายของฝ่ายจัดการ",
    r"ผลการดำเนินงานและฐานะการเงิน",
    r"การวิเคราะห์ผลการดำเนินงาน",
    r"ฐานะทางการเงินและผลการดำเนินงาน",
    # 56-1 One Report section headers (ส่วนที่ 2 / ส่วนที่ 3)
    r"ส่วนที่\s*[23]\s*[:\-–]?\s*(?:การวิเคราะห์|ผลการดำเนิน)",
    # English patterns
    r"management[''`]?s?\s+discussion\s+and\s+analysis",
    r"MD\s*&\s*A\b",
    r"management[''`]?s\s+review",
    r"operating\s+and\s+financial\s+review",
    r"financial\s+review\s+and\s+analysis",
]

MDA_END_PATTERNS: list[str] = [
    # Thai
    r"รายงานของผู้สอบบัญชีรับอนุญาต",
    r"รายงานผู้สอบบัญชีรับอนุญาต",
    r"งบการเงิน(?:รวม)?",
    r"หมายเหตุประกอบงบการเงิน",
    r"การกำกับดูแลกิจการ",
    r"รายงานคณะกรรมการ",
    r"โครงสร้างผู้ถือหุ้น",
    r"ข้อมูลหลักทรัพย์",
    # English
    r"independent\s+auditor",
    r"auditor[''`]?s\s+report",
    r"financial\s+statements",
    r"notes\s+to\s+(?:the\s+)?financial\s+statements",
    r"corporate\s+governance",
    r"shareholder\s+information",
]

_START_RE = [re.compile(p, re.IGNORECASE) for p in MDA_START_PATTERNS]
_END_RE = [re.compile(p, re.IGNORECASE) for p in MDA_END_PATTERNS]

MIN_SECTION_LINES = 10   # MD&A must be at least this many lines before an end marker is accepted


def _matches_any(line: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(line) for p in patterns)


def find_mda_section(text: str) -> Optional[str]:
    """
    Locate the MD&A section in *text* using regex.

    Returns the extracted section text, or None if not found
    (caller should trigger LLM fallback).
    """
    lines = text.split("\n")
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None

    for i, line in enumerate(lines):
        if start_idx is None:
            if _matches_any(line, _START_RE):
                start_idx = i
                logger.debug("MD&A start found at line %d: %s", i, line.strip()[:80])
        else:
            # Enforce minimum section length before accepting an end boundary
            if (i - start_idx) >= MIN_SECTION_LINES and _matches_any(line, _END_RE):
                end_idx = i
                logger.debug("MD&A end found at line %d: %s", i, line.strip()[:80])
                break

    if start_idx is None:
        logger.warning("MD&A start pattern not matched — LLM fallback needed")
        return None

    section = "\n".join(lines[start_idx:end_idx])
    logger.info(
        "MD&A section extracted via regex: lines %d–%s (%d chars)",
        start_idx,
        end_idx if end_idx else "EOF",
        len(section),
    )
    return section


# ---------------------------------------------------------------------------
# LLM fallback
# ---------------------------------------------------------------------------

_LLM_SYSTEM = (
    "You are an expert at parsing Thai and English annual reports for SET-listed companies. "
    "Your task is to extract ONLY the Management Discussion and Analysis (MD&A) section. "
    "Return the raw text of that section and nothing else — no commentary, no preamble."
)

_LLM_PROMPT = """\
The following is extracted text from an annual report. It may be in Thai, English, or both.

Please locate and return the Management Discussion and Analysis (MD&A) section.
In Thai annual reports this section is often titled:
- การวิเคราะห์และคำอธิบายของฝ่ายจัดการ
- คำอธิบายและการวิเคราะห์ของฝ่ายจัดการ
- ผลการดำเนินงานและฐานะการเงิน

Return ONLY the MD&A text. If you cannot find it, return the string "NOT_FOUND".

---
{text_sample}
"""

# How many characters to send to the LLM (to stay within context limits)
_LLM_SAMPLE_CHARS = 80_000


def find_mda_section_llm(text: str, client, model: str, max_tokens: int = 4096) -> Optional[str]:
    """
    LLM-based MD&A extraction fallback (used when regex fails).

    Parameters
    ----------
    text : str        Full document text
    client            anthropic.Anthropic client instance
    model : str       Claude model string
    max_tokens : int
    """
    sample = text[:_LLM_SAMPLE_CHARS]
    prompt = _LLM_PROMPT.format(text_sample=sample)

    logger.info("Running LLM fallback for MD&A detection (model=%s, sample=%d chars)", model, len(sample))

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=_LLM_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    result = response.content[0].text.strip()

    if result == "NOT_FOUND" or len(result) < 200:
        logger.warning("LLM fallback returned no MD&A section")
        return None

    logger.info("LLM fallback extracted %d chars", len(result))
    return result


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def detect_mda(
    text: str,
    use_llm_fallback: bool = True,
    llm_client=None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> tuple[Optional[str], str]:
    """
    Detect and return the MD&A section from *text*.

    Returns
    -------
    (mda_text, method_used)
        mda_text    : extracted section or None if all methods fail
        method_used : 'regex' | 'llm' | 'failed'
    """
    section = find_mda_section(text)
    if section:
        return section, "regex"

    if use_llm_fallback and llm_client is not None:
        section = find_mda_section_llm(text, llm_client, model, max_tokens)
        if section:
            return section, "llm"

    return None, "failed"
