#!/usr/bin/env python3
"""
MD&A Extraction Pipeline — Drop-and-Go Orchestrator

USAGE
-----
  # Drop PDFs into data/input/ then just run:
  python batch.py

  # Single ticker (auto-found in data/input/)
  python batch.py --ticker CPALL

  # Dry-run: show plan without calling LLM
  python batch.py --dry-run

  # Force extraction strategy
  python batch.py --ticker CPALL --strategy marker

FILENAME CONVENTION (auto-detected)
-------------------------------------
  cpall_ar_2024.pdf
  CPALL_2024.pdf
  cpall-annual-report-2024.pdf
  AOT_Annual_Report_2024.pdf
"""

import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ── optional Rich for pretty output ─────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    _RICH = True
    console = Console()
except ImportError:
    _RICH = False
    console = None  # type: ignore

# ── config loader ────────────────────────────────────────────────────────────
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


def _load_config(path: str = "config.toml") -> dict:
    if tomllib is None or not Path(path).exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


# ── logging ──────────────────────────────────────────────────────────────────

def _setup_logging(log_dir: str, run_id: str) -> tuple[logging.Logger, Path]:
    log_path = Path(log_dir) / f"run_{run_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        handlers=[
            logging.FileHandler(log_path),
        ],
    )
    return logging.getLogger("batch"), log_path


# ── audit log ────────────────────────────────────────────────────────────────

class AuditLog:
    def __init__(self, path: Path):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, entry: dict) -> None:
        entry["ts"] = datetime.utcnow().isoformat()
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── console helpers ───────────────────────────────────────────────────────────

def _print(msg: str, style: str = "") -> None:
    if _RICH:
        console.print(msg, style=style)
    else:
        print(msg)


def _step(label: str, msg: str) -> None:
    _print(f"  [bold cyan]{label:12s}[/bold cyan]  {msg}" if _RICH else f"  {label:12s}  {msg}")


def _ok(label: str, msg: str) -> None:
    _print(f"  [bold green]✓ {label:10s}[/bold green]  {msg}" if _RICH else f"  ✓ {label:10s}  {msg}")


def _fail(label: str, msg: str) -> None:
    _print(f"  [bold red]✗ {label:10s}[/bold red]  {msg}" if _RICH else f"  ✗ {label:10s}  {msg}")


def _warn(msg: str) -> None:
    _print(f"  [yellow]⚠  {msg}[/yellow]" if _RICH else f"  ⚠  {msg}")


def _header(ticker: str, year: int, pdf: str, n: int, total: int) -> None:
    border = "─" * 56
    if _RICH:
        console.rule(f"[bold]{ticker} {year}[/bold]  ({n}/{total})")
    else:
        print(f"\n{'─'*56}")
        print(f"  {ticker} {year}  ({n}/{total})  {Path(pdf).name}")
        print(f"{'─'*56}")


# ── scan + preview ───────────────────────────────────────────────────────────

def _show_scan_table(ready: list[dict], needs_review: list[dict]) -> None:
    if not _RICH:
        print(f"\nFound {len(ready)+len(needs_review)} PDF(s)  →  {len(ready)} ready, {len(needs_review)} need review\n")
        for c in ready:
            print(f"  ✓  {c['ticker']:8s} {c['year']}  {Path(c['pdf_path']).name}")
        for c in needs_review:
            print(f"  ⚠  {'?':8s} ?     {Path(c['pdf_path']).name}  [{c.get('_parse_issue','')}]")
        return

    table = Table(title="PDFs discovered", show_lines=True)
    table.add_column("Ticker", style="bold cyan", width=10)
    table.add_column("Year", width=6)
    table.add_column("Filename", style="dim")
    table.add_column("Status")

    for c in ready:
        table.add_row(c["ticker"], str(c["year"]), Path(c["pdf_path"]).name, "[green]ready[/green]")
    for c in needs_review:
        issue = c.get("_parse_issue", "?")
        table.add_row("?", "?", Path(c["pdf_path"]).name, f"[yellow]review ({issue})[/yellow]")

    console.print(table)


# ── per-company pipeline ─────────────────────────────────────────────────────

def _run_one(
    company: dict,
    cfg: dict,
    dry_run: bool,
    strategy_override: str | None,
    audit: AuditLog,
    log: logging.Logger,
    n: int,
    total: int,
) -> bool:
    ticker = company["ticker"]
    year = company["year"]
    pdf_path = company["pdf_path"]

    _header(ticker, year, pdf_path, n, total)
    audit_entry: dict = {"ticker": ticker, "year": year, "pdf_path": pdf_path, "dry_run": dry_run}

    # Phase 0 — Triage
    try:
        if strategy_override:
            strategy = {"pymupdf4llm": "strategy_A_pymupdf4llm", "marker": "strategy_B_marker"}[strategy_override]
        else:
            from pipeline.triage import triage_pdf
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            strategy = triage_pdf(pdf_path)
        audit_entry["strategy"] = strategy
        label = "pymupdf4llm" if "A" in strategy else "marker-pdf"
        _step("triage", f"→ {label}")
        log.info("[%s/%d] triage → %s", ticker, year, strategy)
    except Exception as exc:
        _fail("triage", str(exc))
        log.error("[%s/%d] triage FAILED: %s", ticker, year, exc)
        audit_entry.update({"stage": "triage", "status": "failed", "error": str(exc)})
        audit.record(audit_entry)
        return False

    if dry_run:
        _print(f"  [dim]dry-run: would extract → detect MD&A → wiki + graph[/dim]" if _RICH else "  dry-run: would extract → detect MD&A → wiki + graph")
        audit_entry["status"] = "dry_run"
        audit.record(audit_entry)
        return True

    # Phase 1 — Extract
    extraction_cfg = cfg.get("extraction", {})
    marker_langs = extraction_cfg.get("marker_langs", "tha,eng")
    try:
        from pipeline.extractors import extract
        _step("extract", f"reading PDF…")
        full_text = extract(pdf_path, strategy, marker_langs=marker_langs)
        audit_entry["chars_extracted"] = len(full_text)
        _ok("extract", f"{len(full_text):,} chars")
        log.info("[%s/%d] extracted %d chars", ticker, year, len(full_text))
    except Exception as exc:
        _fail("extract", str(exc))
        log.error("[%s/%d] extract FAILED: %s\n%s", ticker, year, exc, traceback.format_exc())
        audit_entry.update({"stage": "extraction", "status": "failed", "error": str(exc)})
        audit.record(audit_entry)
        return False

    # Phase 2 — Detect MD&A
    llm_cfg = cfg.get("llm", {})
    api_key = llm_cfg.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    model = llm_cfg.get("model", "claude-sonnet-4-20250514")
    max_tokens = llm_cfg.get("max_tokens", 4096)
    use_llm_fallback = extraction_cfg.get("use_llm_for_mda_fallback", True)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    except ImportError as exc:
        raise RuntimeError("pip install anthropic") from exc

    try:
        from pipeline.mda_detector import detect_mda
        _step("MD&A detect", "scanning…")
        mda_text, method = detect_mda(full_text, use_llm_fallback=use_llm_fallback, llm_client=client, model=model, max_tokens=max_tokens)
        if mda_text is None:
            raise ValueError("MD&A section not found")
        audit_entry.update({"mda_method": method, "mda_chars": len(mda_text)})
        _ok("MD&A detect", f"{len(mda_text):,} chars  [{method}]")
        log.info("[%s/%d] MD&A via %s (%d chars)", ticker, year, method, len(mda_text))
    except Exception as exc:
        _fail("MD&A detect", str(exc))
        log.error("[%s/%d] MD&A FAILED: %s", ticker, year, exc)
        audit_entry.update({"stage": "mda", "status": "failed", "error": str(exc)})
        audit.record(audit_entry)
        return False

    paths_cfg = cfg.get("paths", {})
    wiki_output = paths_cfg.get("wiki_output", "data/output/wiki")
    graph_output = paths_cfg.get("graph_output", "data/output/graphs")

    # Phase 3A — Wiki node
    temperature = llm_cfg.get("temperature", 0.1)
    wiki_path = None
    try:
        from pipeline.wiki_writer import generate_wiki_node, save_wiki_node
        _step("wiki", "calling Claude…")
        wiki_md = generate_wiki_node(mda_text, ticker, year, client, model, max_tokens, temperature)
        wiki_path = save_wiki_node(wiki_md, ticker, year, wiki_output)
        audit_entry["wiki_path"] = str(wiki_path)
        _ok("wiki", str(wiki_path))
        log.info("[%s/%d] wiki → %s", ticker, year, wiki_path)
    except Exception as exc:
        _fail("wiki", str(exc))
        log.error("[%s/%d] wiki FAILED: %s\n%s", ticker, year, exc, traceback.format_exc())
        audit_entry.update({"wiki_status": "failed", "wiki_error": str(exc)})

    # Phase 3B — Knowledge graph
    graph_cfg = cfg.get("graph", {})
    html_path = None
    try:
        from pipeline.graph_runner import run_knowledge_graph
        _step("graph", "generating SPO graph…")
        html_path, json_path = run_knowledge_graph(
            mda_text=mda_text, ticker=ticker, year=year,
            output_dir=graph_output, client=client, model=model,
            use_inference=graph_cfg.get("use_inference", False),
            chunk_size=graph_cfg.get("chunk_size", 150),
            overlap=graph_cfg.get("overlap", 20),
        )
        audit_entry.update({"graph_html": str(html_path), "graph_json": str(json_path)})
        _ok("graph", str(html_path))
        log.info("[%s/%d] graph → %s", ticker, year, html_path)
    except Exception as exc:
        _fail("graph", str(exc))
        log.error("[%s/%d] graph FAILED: %s\n%s", ticker, year, exc, traceback.format_exc())
        audit_entry.update({"graph_status": "failed", "graph_error": str(exc)})

    audit_entry["status"] = "success" if (wiki_path and html_path) else "partial" if (wiki_path or html_path) else "failed"
    audit.record(audit_entry)
    return audit_entry["status"] in ("success", "partial")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MD&A Extraction Pipeline — drop PDFs in data/input/ and run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--ticker", metavar="TICKER", help="Process only this ticker (scanned from data/input/)")
    parser.add_argument("--year", type=int, help="Filter by year (used with --ticker)")
    parser.add_argument("--strategy", choices=["auto", "pymupdf4llm", "marker"], default="auto")
    parser.add_argument("--dry-run", action="store_true", help="Show plan, no LLM calls")
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--input-dir", default=None, help="Override input dir (default: config.toml paths.input_dir)")
    parser.add_argument("--companies", default=None, help="Use a companies.json instead of auto-scanning")
    args = parser.parse_args()

    cfg = _load_config(args.config) if Path(args.config).exists() else {}
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_dir = cfg.get("paths", {}).get("log_dir", "data/output/logs")
    log, log_path = _setup_logging(log_dir, run_id)

    audit = AuditLog(log_path.with_suffix(".audit.jsonl"))

    if _RICH:
        console.print(Panel.fit(
            "[bold]MD&A Extraction Pipeline[/bold]\n"
            f"run_id: [dim]{run_id}[/dim]  dry_run: [cyan]{args.dry_run}[/cyan]",
            border_style="blue",
        ))
    else:
        print(f"\n{'='*56}\nMD&A Extraction Pipeline  |  run_id: {run_id}\n{'='*56}\n")

    # ── build company list ────────────────────────────────────────────────────
    companies: list[dict] = []
    needs_review: list[dict] = []

    if args.companies and Path(args.companies).exists():
        with open(args.companies, encoding="utf-8") as f:
            companies = json.load(f)["companies"]
    else:
        from pipeline.autodiscovery import discover_pdfs
        input_dir = args.input_dir or cfg.get("paths", {}).get("input_dir", "data/input")
        Path(input_dir).mkdir(parents=True, exist_ok=True)
        companies, needs_review = discover_pdfs(input_dir)

    # Filter by --ticker / --year
    if args.ticker:
        companies = [c for c in companies if c["ticker"].upper() == args.ticker.upper()]
        if args.year:
            companies = [c for c in companies if c["year"] == args.year]

    _show_scan_table(companies, needs_review)

    if needs_review:
        _warn(f"{len(needs_review)} file(s) skipped — rename to TICKER_YEAR.pdf or add to companies.json")
        for nr in needs_review:
            _warn(f"  {Path(nr['pdf_path']).name}  ({nr.get('_parse_issue','')})")

    if not companies:
        _print("\n[yellow]No PDFs to process. Drop PDF files into data/input/ and re-run.[/yellow]" if _RICH
               else "\nNo PDFs to process. Drop PDF files into data/input/ and re-run.")
        sys.exit(0)

    _print(f"\n[bold]Processing {len(companies)} file(s)…[/bold]\n" if _RICH else f"\nProcessing {len(companies)} file(s)…\n")

    results = {"success": 0, "partial": 0, "failed": 0}
    for i, company in enumerate(companies, 1):
        ok = _run_one(
            company=company, cfg=cfg, dry_run=args.dry_run,
            strategy_override=None if args.strategy == "auto" else args.strategy,
            audit=audit, log=log, n=i, total=len(companies),
        )
        results["success" if ok else "failed"] += 1

    # ── summary ───────────────────────────────────────────────────────────────
    if _RICH:
        console.rule("[bold]Summary[/bold]")
        console.print(
            f"  Total: {len(companies)}  "
            f"[green]✓ {results['success']}[/green]  "
            f"[red]✗ {results['failed']}[/red]"
        )
        console.print(f"  Audit log: [dim]{audit._path}[/dim]")
        console.print(f"  Full log:  [dim]{log_path}[/dim]")
    else:
        print(f"\n{'='*56}")
        print(f"  Total: {len(companies)}  ✓ {results['success']}  ✗ {results['failed']}")
        print(f"  Audit: {audit._path}")

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
