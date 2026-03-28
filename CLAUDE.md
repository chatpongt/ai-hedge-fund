# CLAUDE.md

## Project Overview

AI Hedge Fund — a multi-agent system that uses LLM-powered analyst agents (modeled after famous investors) to analyze stocks and make trading decisions. Educational project, not for real trading.

**Tech stack**: Python 3.11+, LangChain, LangGraph, FastAPI, React+Vite, Poetry

## Repository Structure

```
src/                        # CLI application
  main.py                   # Entry point — builds LangGraph StateGraph
  backtester.py             # Backtesting CLI entry point
  agents/                   # 18 analyst agents + risk_manager + portfolio_manager
  graph/state.py            # AgentState (LangGraph state definition)
  tools/api.py              # Financial data API (prices, metrics, news, insider trades)
  data/models.py            # Pydantic models for API responses
  data/cache.py             # In-memory caching layer
  llm/models.py             # LLM provider config (OpenAI, Anthropic, Groq, etc.)
  cli/input.py              # CLI argument parsing
  backtesting/              # Backtesting engine (engine.py, portfolio.py, metrics.py)
  utils/
    analysts.py             # ANALYST_CONFIG — single source of truth for agent registry
    display.py              # Pretty-print trading results
    progress.py             # Rich progress tracking
    llm.py                  # call_llm() with retry logic

app/                        # Web application
  backend/                  # FastAPI (routes/, services/, repositories/, database/)
  frontend/                 # React + Vite + TypeScript + Tailwind

tests/                      # Pytest test suite
  backtesting/              # Unit + integration tests for backtesting engine
  test_api_rate_limiting.py

docker/                     # Docker setup (Dockerfile, docker-compose.yml, run.sh)
```

## Development Commands

```bash
# Install dependencies
poetry install

# Run CLI
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --show-reasoning

# Run backtester
poetry run python src/backtester.py --ticker AAPL,MSFT --start-date 2024-01-01 --end-date 2024-06-30

# Run tests
poetry run pytest tests/

# Run web app
cd app/backend && poetry run uvicorn main:app --reload   # Backend: localhost:8000
cd app/frontend && npm run dev                            # Frontend: localhost:5173

# Formatting
poetry run black .
poetry run isort .
poetry run flake8
```

## Architecture

### Agent Workflow (LangGraph)

```
Start → [All Selected Analysts in Parallel] → Risk Manager → Portfolio Manager → End
```

- **AgentState** (`src/graph/state.py`): `messages` (accumulated), `data` (merged dicts), `metadata` (merged dicts)
- Analysts run in parallel, each returning signals into `state["data"]["analyst_signals"]`
- Risk Manager calculates position limits and risk metrics
- Portfolio Manager makes final buy/sell/short/cover/hold decisions per ticker

### Agent Pattern

Every agent follows this structure:
1. Receive `AgentState` with ticker list, date range, and model config
2. Fetch financial data via `src/tools/api.py`
3. Analyze data using LLM (via `call_llm()` from `src/utils/llm.py`)
4. Return signal: `{ "signal": "bullish|bearish|neutral", "confidence": 0-100, "reasoning": "..." }`
5. Store result in `state["data"]["analyst_signals"][agent_name]`

### Adding a New Agent

1. Create `src/agents/your_agent.py` following existing agent patterns (e.g., `warren_buffett.py`)
2. Define the agent function: `def your_agent(state: AgentState):`
3. Register in `src/utils/analysts.py` → add entry to `ANALYST_CONFIG` dict
4. The agent will automatically be available in both CLI and web app

### LLM Providers

Configured in `src/llm/models.py`. Supported providers: OpenAI, Anthropic, Groq, DeepSeek, Google Gemini, xAI, GigaChat, OpenRouter, Azure OpenAI, Ollama (local).

API keys are set via environment variables (see `.env.example`).

## Code Conventions

- **Line length**: 420 (configured in `[tool.black]`)
- **Import sorting**: isort with `profile = "black"`
- **Python version**: 3.11+
- **Type hints**: Use Pydantic models for data validation; `TypedDict` for LangGraph state
- **Agent functions**: Named `{name}_agent` (e.g., `warren_buffett_agent`)
- **Agent keys**: Snake_case in `ANALYST_CONFIG` (e.g., `"warren_buffett"`)
- **No bare excepts**: Use specific exception types
- **API calls**: Always go through `src/tools/api.py` which handles rate limiting and caching

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/main.py` | CLI entry point, builds and runs the LangGraph workflow |
| `src/utils/analysts.py` | Agent registry (`ANALYST_CONFIG`) — add new agents here |
| `src/graph/state.py` | `AgentState` TypedDict and `show_agent_reasoning()` |
| `src/tools/api.py` | All financial data API calls with rate limiting |
| `src/llm/models.py` | LLM provider setup and model registry |
| `src/agents/portfolio_manager.py` | Final trading decision maker |
| `src/agents/risk_manager.py` | Risk metrics and position limits |
| `src/backtesting/engine.py` | `BacktestEngine` — runs historical simulations |
| `app/backend/main.py` | FastAPI app entry point |
| `app/backend/routes/__init__.py` | Backend route registry |

## Testing

- Framework: pytest
- Tests located in `tests/`
- Backtesting tests include unit tests (`test_portfolio.py`, `test_metrics.py`) and integration tests (`tests/backtesting/integration/`)
- Run: `poetry run pytest tests/`

## Environment Variables

Required API keys depend on which LLM provider you use. At minimum:
- One LLM provider key (e.g., `OPENAI_API_KEY`)
- `FINANCIAL_DATASETS_API_KEY` for financial data

See `.env.example` for the full list.
