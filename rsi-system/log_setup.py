"""Structured logging setup for RSI Hybrid System.

Produces JSON-formatted logs for machine parsing + human-readable console output.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from config.settings import settings


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for file output."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }
        return json.dumps(log_entry, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Human-readable colored console formatter."""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        return f"{color}{timestamp} [{record.levelname:>7}]{self.RESET} {record.name}: {record.getMessage()}"


def setup_logging(debug: bool = False) -> None:
    """Configure logging with JSON file output + console output.

    Args:
        debug: If True, set log level to DEBUG (default INFO)
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Clear existing handlers
    root.handlers.clear()

    # Console handler (human-readable)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console.setFormatter(ConsoleFormatter())
    root.addHandler(console)

    # File handler (JSON structured)
    log_dir = settings.paths.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"rsi-{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.info("Logging initialized: console=%s, file=%s", "DEBUG" if debug else "INFO", log_file)
