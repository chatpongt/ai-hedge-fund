"""Phase 3B: Generate SPO knowledge graph via ai-knowledge-graph/generate-graph.py."""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def _find_generate_graph(ai_kg_dir: str) -> Path:
    candidates = [
        Path(ai_kg_dir) / "generate-graph.py",
        Path(ai_kg_dir) / "generate_graph.py",
        Path(ai_kg_dir) / "src" / "generate-graph.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"generate-graph.py not found under {ai_kg_dir}. "
        "Clone the repo: git clone https://github.com/robert-mcdermott/ai-knowledge-graph"
    )


def _write_mda_txt(mda_text: str, ticker: str, year: int, tmp_dir: str) -> Path:
    """Save MDA as .txt (generate-graph.py does not accept .md)."""
    txt_path = Path(tmp_dir) / f"{ticker}_{year}_mda.txt"
    txt_path.write_text(mda_text, encoding="utf-8")
    return txt_path


def _patch_kg_config(ai_kg_dir: str, model: str, api_key: str) -> str:
    """
    Ensure the ai-knowledge-graph config.toml points to Claude via LiteLLM
    (not Ollama). Returns path to the config file used.

    We write a temporary config file and pass it via env/flag rather than
    modifying the repo's own config.toml in place.
    """
    config_content = f"""\
[model]
name = "{model}"
api_key = "{api_key}"

[graph]
inference = false
standardize = true
chunk_size = 150
overlap = 20
"""
    cfg_path = Path(ai_kg_dir) / "_pipeline_config.toml"
    cfg_path.write_text(config_content, encoding="utf-8")
    return str(cfg_path)


def run_knowledge_graph(
    mda_text: str,
    ticker: str,
    year: int,
    output_dir: str,
    ai_kg_dir: str,
    model: str = "claude-sonnet-4-20250514",
    api_key: str = "",
    use_inference: bool = False,
    chunk_size: int = 150,
    overlap: int = 20,
) -> tuple[Path, Path]:
    """
    Generate SPO knowledge graph from *mda_text*.

    Parameters
    ----------
    mda_text : str      MD&A section text
    ticker : str
    year : int
    output_dir : str    Where to write {TICKER}_{YEAR}_mda.html / .json
    ai_kg_dir : str     Path to cloned ai-knowledge-graph repo
    model : str         Claude model for SPO extraction
    api_key : str       Anthropic API key
    use_inference : bool  Pass --inference flag (default False)
    chunk_size : int
    overlap : int

    Returns
    -------
    (html_path, json_path)
    """
    script = _find_generate_graph(ai_kg_dir)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    stem = f"{ticker.upper()}_{year}_mda"

    with tempfile.TemporaryDirectory() as tmp:
        txt_path = _write_mda_txt(mda_text, ticker, year, tmp)

        cmd = [
            "python",
            str(script),
            "--input", str(txt_path),
            "--output", str(output_dir_path / stem),
            "--model", model,
            "--chunk-size", str(chunk_size),
            "--overlap", str(overlap),
        ]
        if not use_inference:
            cmd.append("--no-inference")

        env = os.environ.copy()
        if api_key:
            env["ANTHROPIC_API_KEY"] = api_key

        logger.info("Running generate-graph.py for %s %d: %s", ticker, year, " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(
                f"generate-graph.py failed (rc={result.returncode}): {result.stderr[:500]}"
            )

    # Discover output files — the script may name them slightly differently
    html_candidates = list(output_dir_path.glob(f"{stem}*.html"))
    json_candidates = list(output_dir_path.glob(f"{stem}*.json"))

    if not html_candidates or not json_candidates:
        raise RuntimeError(
            f"generate-graph.py ran but expected output files not found in {output_dir_path}"
        )

    html_path = html_candidates[0]
    json_path = json_candidates[0]

    # Normalise names to our convention
    final_html = output_dir_path / f"{stem}.html"
    final_json = output_dir_path / f"{stem}.json"
    if html_path != final_html:
        shutil.move(str(html_path), str(final_html))
    if json_path != final_json:
        shutil.move(str(json_path), str(final_json))

    logger.info("Graph files saved: %s, %s", final_html, final_json)
    return final_html, final_json
