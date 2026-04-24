"""Phase 3A: Generate a structured markdown wiki node from an MD&A section."""

import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

WIKI_SYSTEM = """\
คุณเป็น equity analyst ที่ extract structured knowledge จาก MD&A section
ของ annual report บริษัทจดทะเบียนใน SET Thailand
output เป็น markdown ที่ structured และ consistent ทุก ticker
ห้ามเพิ่ม preamble, คำอธิบาย, หรือ text นอกจาก format ที่กำหนด"""

WIKI_PROMPT_TEMPLATE = """\
จาก MD&A section ของ {ticker} ปี {year} ด้านล่างนี้:

{mda_text}

---
สร้าง knowledge wiki node ในรูปแบบนี้ **เท่านั้น** ไม่ต้องมี preamble:

```yaml
---
ticker: {ticker}
year: {year}
type: mda_summary
source: annual_report
extracted: {today}
---
```

## Key Narrative

[thesis หลัก 2-3 ประโยค ในมุมมอง management]

## Revenue Drivers

- [driver 1]
- [driver 2]

## Cost & Margin

- [สิ่งที่กระทบ gross/net margin]

## Forward Guidance

- [outlook ที่ management ระบุ]

## Watch / Red Flags

- [สิ่งผิดปกติ หรือ cautious language]

## Key Quotes

> [quote สำคัญ 1 — TH หรือ EN verbatim]
> [quote สำคัญ 2]
"""

# Truncate MD&A text sent to the API to avoid very large payloads
_MAX_MDA_CHARS = 60_000


def generate_wiki_node(
    mda_text: str,
    ticker: str,
    year: int,
    client,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    temperature: float = 0.1,
) -> str:
    """
    Call Claude to produce a structured wiki node markdown string.

    Parameters
    ----------
    mda_text : str      Extracted MD&A section
    ticker : str        Stock ticker symbol (e.g. 'CPALL')
    year : int          Report year
    client              anthropic.Anthropic client instance
    model : str
    max_tokens : int
    temperature : float

    Returns
    -------
    str  — markdown wiki node content
    """
    today = date.today().isoformat()
    truncated = mda_text[:_MAX_MDA_CHARS]
    if len(mda_text) > _MAX_MDA_CHARS:
        logger.warning(
            "MD&A text truncated from %d to %d chars for wiki generation",
            len(mda_text),
            _MAX_MDA_CHARS,
        )

    prompt = WIKI_PROMPT_TEMPLATE.format(
        ticker=ticker,
        year=year,
        today=today,
        mda_text=truncated,
    )

    logger.info("Generating wiki node for %s %d (model=%s)", ticker, year, model)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=WIKI_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    wiki_md = response.content[0].text.strip()
    logger.info("Wiki node generated: %d chars", len(wiki_md))
    return wiki_md


def save_wiki_node(wiki_md: str, ticker: str, year: int, output_dir: str) -> Path:
    """
    Write wiki markdown to `{output_dir}/{TICKER}/mda_{YEAR}.md`.

    Returns the path written.
    """
    ticker_dir = Path(output_dir) / ticker.upper()
    ticker_dir.mkdir(parents=True, exist_ok=True)
    out_path = ticker_dir / f"mda_{year}.md"
    out_path.write_text(wiki_md, encoding="utf-8")
    logger.info("Wiki node saved: %s", out_path)
    return out_path
