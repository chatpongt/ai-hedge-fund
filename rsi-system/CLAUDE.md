# CLAUDE.md — RSI Hybrid System

## Project Overview

RSI (Research, Strategy, Intelligence) Hybrid System — ระบบวิเคราะห์หุ้นไทย SET อัตโนมัติ
ทำงานบน Mac Mini M4 Pro 24GB ใช้ Local AI (MLX) เป็น brain หลัก, Cloud AI เสริมข้อมูลเท่านั้น

**ไม่ใช่ระบบเทรดอัตโนมัติ** — output คือ recommendation + analysis เท่านั้น

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
│  (pipeline หลัก — รัน daily cron 18:00)                    │
├─────────┬───────────┬───────────┬───────────────────────┤
│ OBSERVE │  ORIENT   │  DECIDE   │  LEARN/WIKI           │
│ 🟢 daily │ 🔵 event  │ 🟡 valuation│ 🟣 knowledge capture  │
│ brief   │ analysis  │ prep      │                       │
└────┬────┴─────┬─────┴─────┬─────┴───────────┬───────────┘
     │          │           │                 │
┌────▼──────────▼───────────▼─────────────────▼───────────┐
│                    ADAPTERS LAYER                         │
│  mlx_adapter │ perplexity │ grok │ gemini │ bloomberg    │
└─────────────────────────────────────────────────────────┘
```

## Hardware & Models

| Model                | Size  | Purpose                              |
|----------------------|-------|--------------------------------------|
| Qwen 3 8B Q4         | ~5GB  | Main: analysis, wiki, report         |
| Qwen 3 4B Q4         | ~3GB  | Fast: parse, triage, routing         |
| DeepSeek-R1 14B Q4   | ~9GB  | Deep reasoning: nash, mta, valuation |

All local models served via MLX on localhost:8080 (OpenAI-compatible API).

**RAM Budget (24GB unified):**
- macOS + system: ~5-6GB
- Largest single model loaded: ~9GB (DeepSeek-R1 14B)
- Headroom: ~9-10GB for pipeline data and OS cache
- MLX loads one model at a time; models swap when switching tiers

## Cloud AI Roles (data enrichment only)

| Service            | Purpose                            |
|--------------------|------------------------------------|
| Perplexity Pro     | Macro data, sector data            |
| Grok (Super Grok)  | X/Twitter news, breaking news      |
| Gemini Pro         | Long document reading (200+ pages) |
| Bloomberg Anywhere | Manual CSV export only (ToS)       |

## Directory Structure

```
rsi-system/
├── CLAUDE.md              ← this file
├── orchestrator.py        ← main pipeline
├── config/
│   └── settings.py        ← centralized configuration
├── schemas/
│   ├── signal.py          ← signal output schema
│   ├── brief.py           ← flash brief schema
│   └── wiki_entry.py      ← wiki entry schema
├── adapters/
│   ├── base.py            ← base adapter interface
│   ├── mlx_adapter.py     ← MLX localhost:8080 bridge
│   ├── perplexity.py      ← Perplexity API adapter
│   ├── grok.py            ← Grok API adapter
│   └── gemini.py          ← Gemini API adapter
├── agents/
│   ├── observe.py         ← 🟢 daily brief generation
│   ├── orient.py          ← 🔵 event/strategic analysis
│   ├── decide.py          ← 🟡 valuation prep
│   └── wiki_ingest.py     ← 🟣 knowledge wiki ingestion
├── skills/prompts/        ← skill prompt templates (.md)
├── tests/                 ← golden test cases
└── logs/                  ← pipeline + quality + cost logs
```

External paths:
```
rsi-system/outputs/wiki/    ← persistent knowledge base (git-tracked)
~/Downloads/bloomberg_drop/ ← Bloomberg CSV drop folder
```

## Output Schemas

All inter-agent communication uses strict JSON schemas (defined in `schemas/`).
Agents MUST return valid JSON matching these schemas — no free-form text between agents.

## Development Commands

```bash
# Run full pipeline
python orchestrator.py

# Run individual agents
python -m agents.observe --date 2026-04-10
python -m agents.orient --event "event description"
python -m agents.decide --ticker SET:AOT

# Run tests
pytest tests/ -v

# Check MLX server status
curl http://localhost:8080/v1/models
```

## Constraints

- Bloomberg data = manual CSV export ONLY (no auto-scraping — ToS violation)
- DECIDE output = recommendation only, NEVER auto-execute trades
- Sensitive data = local only, NEVER send to cloud
- Price data = EOD sufficient, no realtime needed
- All API keys stored in macOS Keychain (production) or .env (development)

## Code Conventions

- Python 3.11+
- Type hints on all function signatures
- Pydantic models for all data schemas
- Structured logging (JSON format) to `logs/`
- Graceful degradation — if any API fails, pipeline continues with available data
- Prompt templates versioned in `skills/prompts/` with YAML frontmatter

## Daily Automation Flow

```
18:00 cron trigger
  ├─① fetch EOD data (Yahoo Finance / FMP API)
  ├─② detect Bloomberg CSV drop
  ├─③ Grok + Perplexity → news triage
  ├─④ Qwen 4B → routing signals (🔵/🟡/⚪)
  ├─⑤ Qwen 32B → Flash Brief (observe skill)
  ├─⑥ [if 🔵] orient agent → strategic analysis
  ├─⑦ wiki_ingest → /mnt/outputs/wiki/
  ├─⑧ learn agent → lesson capture
  └─⑨ macOS notification → "Brief พร้อมแล้ว"

เช้า 07:00 → user reads report
```

## Skills Reference

### Existing (prompt templates)
- 🟢 OBSERVE: `observe`, `thai-portfolio-intel`
- 🔵 ORIENT: `orient`, `world-reader`, `investment-strategy-architect`
- 🟡 DECIDE: `decide`, `thai-equity-valuation`, `nash-equilibrium-strategist`, `second-level-analyst`, `ai-disruption-valuation`
- 🟣 LEARN: `learn`, `evolve`, `knowledge-wiki`

### Planned (Sprint 2)
- `filing-diff-agent` — compare 56-1 YoY wording changes
- `earnings-call-analyst` — tone scoring from transcripts
