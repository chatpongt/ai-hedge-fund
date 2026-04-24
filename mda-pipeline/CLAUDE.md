# MD&A Extraction Pipeline

Batch pipeline that extracts MD&A sections from SET-listed company annual reports (PDF)
and produces two outputs per company: a structured markdown wiki node and an SPO
knowledge-graph (HTML + JSON).

## Quick Start

```bash
cd mda-pipeline

# install deps
pip install pymupdf4llm pdfplumber pypdf tomli anthropic

# install marker separately (heavy)
pip install marker-pdf

# single ticker dry-run
python batch.py --ticker CPALL --dry-run

# full run
python batch.py --ticker CPALL

# all companies in companies.json
python batch.py --all
```

Set `ANTHROPIC_API_KEY` in your environment (or fill `config.toml`).

## Structure

```
pipeline/
  triage.py        Phase 0 — detect extraction strategy per PDF
  extractors.py    Phase 1 — pymupdf4llm (fast) / marker (fallback)
  mda_detector.py  Phase 2 — regex + LLM fallback to locate MD&A section
  wiki_writer.py   Phase 3A — Claude API → structured wiki markdown
  graph_runner.py  Phase 3B — calls ai-knowledge-graph/generate-graph.py
batch.py           Orchestrator CLI
config.toml        LLM + path config
companies.json     Ticker list + PDF paths
data/
  input/           Put PDFs here
  output/
    wiki/          {TICKER}/mda_{YEAR}.md
    graphs/        {TICKER}_{YEAR}_mda.{html,json}
    logs/          Per-run JSONL logs
tests/
  test_mda_detector.py
```

## Triage Strategies

| Strategy | When |
|---|---|
| `strategy_A_pymupdf4llm` | Text PDF, fonts OK, no Thai encoding issues |
| `strategy_B_marker` | Scanned PDF, Thai font issues, or garbled pdftotext output |

## Key Gotchas

- Thai font encoding: if pdftotext output has `???` or `□` → force strategy_B
- `generate-graph.py` accepts `.txt` not `.md` → pipeline saves mda as `.txt` first
- marker is slow (~0.86 s/page); 200-page AR ≈ 3 min — expected
- SET 56-1 One Report format: MD&A may live in "ส่วนที่ 2" instead of a standalone chapter
