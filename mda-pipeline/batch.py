#!/usr/bin/env python3
"""
MD&A Extraction Pipeline — Orchestrator CLI

Usage
-----
# Single ticker (dry-run)
python batch.py --ticker CPALL --dry-run

# Single ticker (full run)
python batch.py --ticker CPALL

# All companies in companies.json
python batch.py --all

# Override strategy
python batch.py --ticker CPALL --strategy marker
"""

import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


def _load_config(path: str = "config.toml") -> dict:
    if tomllib is None:
        print("WARNING: tomllib/tomli not found — using default config values")
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(log_dir: str, run_id: str) -> tuple[logging.Logger, Path]:
    log_path = Path(log_dir) / f"run_{run_id}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path),
        ],
    )
    return logging.getLogger("batch"), log_path


# ---------------------------------------------------------------------------
# Per-company audit log
# ---------------------------------------------------------------------------

class AuditLog:
    def __init__(self, log_path: Path):
        self._path = log_path

    def record(self, entry: dict) -> None:
        entry["ts"] = datetime.utcnow().isoformat()
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Pipeline for a single company
# ---------------------------------------------------------------------------

def _run_one(company: dict, cfg: dict, dry_run: bool, strategy_override: str | None, audit: AuditLog, log: logging.Logger) -> bool:
    """
    Process one company dict. Returns True on success, False on failure.
    Logs every step; never raises — errors are caught, logged, and skipped.
    """
    ticker = company["ticker"]
    year = company["year"]
    pdf_path = company["pdf_path"]

    log.info("=" * 60)
    log.info("START  %s %d  |  pdf: %s", ticker, year, pdf_path)

    audit_entry: dict = {
        "ticker": ticker,
        "year": year,
        "pdf_path": pdf_path,
        "dry_run": dry_run,
    }

    # --- Phase 0: Triage ---
    try:
        if strategy_override:
            strategy_map = {
                "pymupdf4llm": "strategy_A_pymupdf4llm",
                "marker": "strategy_B_marker",
                "auto": None,
            }
            strategy = strategy_map.get(strategy_override)
        else:
            strategy = None

        if strategy is None:
            from pipeline.triage import triage_pdf
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            strategy = triage_pdf(pdf_path)

        audit_entry["strategy"] = strategy
        log.info("[%s/%d] triage → %s", ticker, year, strategy)

    except Exception as exc:
        log.error("[%s/%d] triage FAILED: %s", ticker, year, exc)
        audit_entry.update({"stage": "triage", "status": "failed", "error": str(exc)})
        audit.record(audit_entry)
        return False

    if dry_run:
        log.info("[%s/%d] DRY-RUN: would run extraction (%s) → MD&A detect → wiki + graph", ticker, year, strategy)
        audit_entry["status"] = "dry_run"
        audit.record(audit_entry)
        return True

    # --- Phase 1: Extract ---
    extraction_cfg = cfg.get("extraction", {})
    marker_langs = extraction_cfg.get("marker_langs", "tha,eng")

    try:
        from pipeline.extractors import extract
        full_text = extract(pdf_path, strategy, marker_langs=marker_langs)
        audit_entry["chars_extracted"] = len(full_text)
        log.info("[%s/%d] extracted %d chars", ticker, year, len(full_text))
    except Exception as exc:
        log.error("[%s/%d] extraction FAILED: %s\n%s", ticker, year, exc, traceback.format_exc())
        audit_entry.update({"stage": "extraction", "status": "failed", "error": str(exc)})
        audit.record(audit_entry)
        return False

    # --- Phase 2: Detect MD&A ---
    llm_cfg = cfg.get("llm", {})
    api_key = llm_cfg.get("api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    model = llm_cfg.get("model", "claude-sonnet-4-20250514")
    max_tokens = llm_cfg.get("max_tokens", 4096)
    use_llm_fallback = extraction_cfg.get("use_llm_for_mda_fallback", True)

    # Build Anthropic client lazily
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    except ImportError as exc:
        raise RuntimeError("anthropic package not installed — run: pip install anthropic") from exc

    try:
        from pipeline.mda_detector import detect_mda
        mda_text, method = detect_mda(
            full_text,
            use_llm_fallback=use_llm_fallback,
            llm_client=client,
            model=model,
            max_tokens=max_tokens,
        )
        audit_entry["mda_method"] = method
        if mda_text is None:
            raise ValueError("MD&A section not found by regex or LLM")
        audit_entry["mda_chars"] = len(mda_text)
        log.info("[%s/%d] MD&A detected via %s (%d chars)", ticker, year, method, len(mda_text))
    except Exception as exc:
        log.error("[%s/%d] MD&A detection FAILED: %s", ticker, year, exc)
        audit_entry.update({"stage": "mda_detection", "status": "failed", "error": str(exc)})
        audit.record(audit_entry)
        return False

    paths_cfg = cfg.get("paths", {})
    wiki_output = paths_cfg.get("wiki_output", "data/output/wiki")
    graph_output = paths_cfg.get("graph_output", "data/output/graphs")
    ai_kg_dir = paths_cfg.get("ai_knowledge_graph_dir", "../ai-knowledge-graph")

    # --- Phase 3A: Wiki node ---
    temperature = llm_cfg.get("temperature", 0.1)
    wiki_path = None
    try:
        from pipeline.wiki_writer import generate_wiki_node, save_wiki_node
        wiki_md = generate_wiki_node(mda_text, ticker, year, client, model, max_tokens, temperature)
        wiki_path = save_wiki_node(wiki_md, ticker, year, wiki_output)
        audit_entry["wiki_path"] = str(wiki_path)
        log.info("[%s/%d] wiki node → %s", ticker, year, wiki_path)
    except Exception as exc:
        log.error("[%s/%d] wiki generation FAILED: %s\n%s", ticker, year, exc, traceback.format_exc())
        audit_entry["wiki_status"] = "failed"
        audit_entry["wiki_error"] = str(exc)

    # --- Phase 3B: Knowledge graph ---
    graph_cfg = cfg.get("graph", {})
    html_path = None
    try:
        from pipeline.graph_runner import run_knowledge_graph
        html_path, json_path = run_knowledge_graph(
            mda_text=mda_text,
            ticker=ticker,
            year=year,
            output_dir=graph_output,
            ai_kg_dir=ai_kg_dir,
            model=model,
            api_key=api_key,
            use_inference=graph_cfg.get("use_inference", False),
            chunk_size=graph_cfg.get("chunk_size", 150),
            overlap=graph_cfg.get("overlap", 20),
        )
        audit_entry["graph_html"] = str(html_path)
        audit_entry["graph_json"] = str(json_path)
        log.info("[%s/%d] graph → %s", ticker, year, html_path)
    except Exception as exc:
        log.error("[%s/%d] graph generation FAILED: %s\n%s", ticker, year, exc, traceback.format_exc())
        audit_entry["graph_status"] = "failed"
        audit_entry["graph_error"] = str(exc)

    # Determine overall status
    wiki_ok = wiki_path is not None
    graph_ok = html_path is not None
    if wiki_ok and graph_ok:
        audit_entry["status"] = "success"
    elif wiki_ok or graph_ok:
        audit_entry["status"] = "partial"
    else:
        audit_entry["status"] = "failed"

    audit.record(audit_entry)
    log.info("END    %s %d  |  status=%s", ticker, year, audit_entry["status"])
    return audit_entry["status"] in ("success", "partial")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MD&A Extraction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ticker", metavar="TICKER", help="Single ticker to process (e.g. CPALL)")
    group.add_argument("--all", action="store_true", help="Process all companies in companies.json")

    parser.add_argument("--year", type=int, help="Override year (used with --ticker)")
    parser.add_argument(
        "--strategy",
        choices=["auto", "pymupdf4llm", "marker"],
        default="auto",
        help="Force extraction strategy (default: auto / triage)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show plan without running extraction or LLM calls")
    parser.add_argument("--config", default="config.toml", help="Config file (default: config.toml)")
    parser.add_argument("--companies", default="companies.json", help="Companies list (default: companies.json)")

    args = parser.parse_args()

    # Load config
    cfg = _load_config(args.config) if Path(args.config).exists() else {}

    # Run ID based on timestamp
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_dir = cfg.get("paths", {}).get("log_dir", "data/output/logs")
    log, log_path = _setup_logging(log_dir, run_id)

    audit = AuditLog(log_path.with_suffix(".audit.jsonl"))
    log.info("Run ID: %s | dry_run=%s", run_id, args.dry_run)

    # Load companies
    with open(args.companies, encoding="utf-8") as f:
        all_companies: list[dict] = json.load(f)["companies"]

    if args.ticker:
        companies = [c for c in all_companies if c["ticker"].upper() == args.ticker.upper()]
        if args.year:
            companies = [c for c in companies if c["year"] == args.year]
        if not companies:
            # Build a minimal entry so the user can still run without a companies.json entry
            log.warning("Ticker %s not in companies.json — building minimal entry", args.ticker)
            year = args.year or datetime.utcnow().year
            input_dir = cfg.get("paths", {}).get("input_dir", "data/input")
            companies = [{
                "ticker": args.ticker.upper(),
                "year": year,
                "pdf_path": f"{input_dir}/{args.ticker.lower()}_ar_{year}.pdf",
                "language": "th",
                "source": "unknown",
            }]
    else:
        companies = all_companies

    log.info("Processing %d company/year pair(s)", len(companies))

    results = {"success": 0, "failed": 0, "total": len(companies)}
    for company in companies:
        ok = _run_one(
            company=company,
            cfg=cfg,
            dry_run=args.dry_run,
            strategy_override=None if args.strategy == "auto" else args.strategy,
            audit=audit,
            log=log,
        )
        if ok:
            results["success"] += 1
        else:
            results["failed"] += 1

    log.info("")
    log.info("=" * 60)
    log.info("SUMMARY  total=%d  success=%d  failed=%d", results["total"], results["success"], results["failed"])
    log.info("Audit log: %s", audit._path)

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
