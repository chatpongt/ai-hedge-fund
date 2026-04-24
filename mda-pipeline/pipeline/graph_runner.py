"""
Phase 3B: Extract SPO triples from MD&A text and generate a knowledge graph.

Uses Anthropic directly (no LiteLLM proxy needed) + networkx + pyvis for
HTML visualization. Output format is compatible with ai-knowledge-graph JSON.
"""

import json
import logging
import re
import textwrap
from pathlib import Path

import networkx as nx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SPO extraction via Claude
# ---------------------------------------------------------------------------

_SPO_SYSTEM = """\
You are a financial knowledge graph extractor. Extract Subject-Predicate-Object (SPO) triples
from the text. Focus on:
- Revenue and profit relationships (company, revenue, amount)
- Business drivers and their effects
- Forward guidance and targets
- Risk factors and their impacts

Return ONLY a JSON array of triples. Each triple is an object with keys:
  "subject", "predicate", "object"

Rules:
- Subjects and objects should be concise noun phrases (≤5 words)
- Predicates should be verb phrases (≤4 words)
- No duplicates
- 20–80 triples total
- Numbers are OK as objects (e.g. "650,000 ล้านบาท")

Example:
[
  {"subject": "CPALL", "predicate": "มีรายได้รวม", "object": "650,000 ล้านบาท"},
  {"subject": "7-Eleven", "predicate": "เติบโต", "object": "7.5%"}
]"""

_SPO_CHUNK_WORDS = 150
_SPO_OVERLAP_WORDS = 20


def _chunk_text(text: str, chunk_words: int = _SPO_CHUNK_WORDS, overlap: int = _SPO_OVERLAP_WORDS) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i: i + chunk_words]
        chunks.append(" ".join(chunk))
        i += chunk_words - overlap
    return chunks


def _extract_json_array(text: str) -> list[dict]:
    """Pull the first JSON array out of a Claude response."""
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def _is_valid_triple(t: dict) -> bool:
    return (
        isinstance(t, dict)
        and all(k in t for k in ("subject", "predicate", "object"))
        and all(isinstance(t[k], str) and t[k].strip() for k in ("subject", "predicate", "object"))
    )


def extract_spo_triples(
    mda_text: str,
    ticker: str,
    client,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 2048,
    chunk_words: int = _SPO_CHUNK_WORDS,
    overlap: int = _SPO_OVERLAP_WORDS,
) -> list[dict]:
    """
    Extract SPO triples from mda_text by chunking and calling Claude per chunk.
    Returns a deduplicated list of triple dicts.
    """
    chunks = _chunk_text(mda_text, chunk_words, overlap)
    logger.info("SPO extraction: %d chunks, ticker=%s, model=%s", len(chunks), ticker, model)

    all_triples: list[dict] = []
    seen: set[tuple] = set()

    for idx, chunk in enumerate(chunks):
        prompt = (
            f"Extract SPO triples from this MD&A excerpt of {ticker}:\n\n"
            f"---\n{chunk}\n---\n\n"
            "Return JSON array only."
        )
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=_SPO_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            triples = _extract_json_array(raw)

            for t in triples:
                if not _is_valid_triple(t):
                    continue
                key = (t["subject"].strip(), t["predicate"].strip(), t["object"].strip())
                if key not in seen:
                    seen.add(key)
                    all_triples.append({
                        "subject": key[0],
                        "predicate": key[1],
                        "object": key[2],
                    })

            logger.debug("Chunk %d/%d → %d triples", idx + 1, len(chunks), len(triples))

        except Exception as exc:
            logger.warning("SPO extraction failed on chunk %d: %s", idx + 1, exc)
            continue

    logger.info("Total unique SPO triples: %d", len(all_triples))
    return all_triples


# ---------------------------------------------------------------------------
# Graph visualization with pyvis
# ---------------------------------------------------------------------------

def _build_graph(triples: list[dict]) -> nx.DiGraph:
    G = nx.DiGraph()
    for t in triples:
        s, p, o = t["subject"], t["predicate"], t["object"]
        G.add_node(s)
        G.add_node(o)
        G.add_edge(s, o, label=p)
    return G


def _node_color(node: str, ticker: str) -> str:
    if node.upper() == ticker.upper():
        return "#e63946"      # red for main company
    # Heuristic: numbers → green, Thai text → blue, English → orange
    if re.search(r"\d", node):
        return "#2a9d8f"
    if any("฀" <= ch <= "๿" for ch in node):
        return "#457b9d"
    return "#f4a261"


def build_html_graph(
    triples: list[dict],
    ticker: str,
    year: int,
    output_path: str,
) -> Path:
    """Render triples as an interactive pyvis HTML graph."""
    try:
        from pyvis.network import Network
    except ImportError as exc:
        raise RuntimeError("pip install pyvis") from exc

    net = Network(
        height="800px",
        width="100%",
        bgcolor="#0d1117",
        font_color="#e6edf3",
        directed=True,
        notebook=False,
    )
    net.set_options(textwrap.dedent("""\
        {
          "nodes": {
            "font": {"size": 12, "face": "Arial"},
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "arrows": {"to": {"enabled": true}},
            "font": {"size": 10, "align": "middle"},
            "smooth": {"type": "curvedCW", "roundness": 0.2}
          },
          "physics": {
            "barnesHut": {"gravitationalConstant": -8000, "springLength": 120},
            "stabilization": {"iterations": 200}
          }
        }
    """))

    G = _build_graph(triples)
    added_nodes: set[str] = set()

    for t in triples:
        s, p, o = t["subject"], t["predicate"], t["object"]
        for node in (s, o):
            if node not in added_nodes:
                net.add_node(
                    node,
                    label=node[:40],
                    title=node,
                    color=_node_color(node, ticker),
                    size=20 if node.upper() == ticker.upper() else 12,
                )
                added_nodes.add(node)
        net.add_edge(s, o, title=p, label=p[:30], color="#8b949e")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Inject a title banner into the HTML
    net.html = (
        f"<h3 style='color:#e6edf3;font-family:Arial;padding:8px;margin:0;"
        f"background:#161b22'>{ticker} {year} — MD&A Knowledge Graph"
        f" ({len(triples)} triples)</h3>\n"
    )

    net.save_graph(str(out))
    logger.info("Graph HTML saved: %s (%d nodes, %d edges)", out, G.number_of_nodes(), G.number_of_edges())
    return out


# ---------------------------------------------------------------------------
# JSON output (ai-knowledge-graph compatible format)
# ---------------------------------------------------------------------------

def save_json(triples: list[dict], ticker: str, year: int, json_path: str) -> Path:
    payload = {
        "ticker": ticker,
        "year": year,
        "triple_count": len(triples),
        "triples": triples,
    }
    out = Path(json_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Graph JSON saved: %s", out)
    return out


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def run_knowledge_graph(
    mda_text: str,
    ticker: str,
    year: int,
    output_dir: str,
    client,
    model: str = "claude-sonnet-4-20250514",
    api_key: str = "",           # kept for signature compat; client already has key
    use_inference: bool = False,  # reserved for future use
    chunk_size: int = 150,
    overlap: int = 20,
    **_,                          # absorb any extra kwargs
) -> tuple[Path, Path]:
    """
    Extract SPO triples from mda_text and write HTML + JSON outputs.

    Parameters
    ----------
    mda_text : str
    ticker : str
    year : int
    output_dir : str
    client       anthropic.Anthropic instance
    model : str
    chunk_size : int   words per chunk
    overlap : int      word overlap between chunks

    Returns
    -------
    (html_path, json_path)
    """
    stem = f"{ticker.upper()}_{year}_mda"
    html_path = str(Path(output_dir) / f"{stem}.html")
    json_path = str(Path(output_dir) / f"{stem}.json")

    triples = extract_spo_triples(
        mda_text=mda_text,
        ticker=ticker,
        client=client,
        model=model,
        chunk_words=chunk_size,
        overlap=overlap,
    )

    if not triples:
        raise RuntimeError(f"No SPO triples extracted for {ticker} {year}")

    html_out = build_html_graph(triples, ticker, year, html_path)
    json_out = save_json(triples, ticker, year, json_path)

    return html_out, json_out
