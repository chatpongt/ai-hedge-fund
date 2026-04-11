"""Centralized configuration for RSI Hybrid System."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MLXConfig:
    """Local MLX model server configuration."""

    base_url: str = "http://localhost:8080/v1"
    main_model: str = "mlx-community/Qwen3-8B-4bit"
    fast_model: str = "mlx-community/Qwen3-4B-4bit"
    reasoning_model: str = "mlx-community/DeepSeek-R1-Distill-Qwen-14B-4bit"
    timeout: int = 180  # seconds
    max_retries: int = 2


@dataclass
class CloudConfig:
    """Cloud AI service configuration (data enrichment only)."""

    perplexity_api_key: str = field(default_factory=lambda: os.getenv("PERPLEXITY_API_KEY", ""))
    perplexity_model: str = "sonar-pro"
    grok_api_key: str = field(default_factory=lambda: os.getenv("GROK_API_KEY", ""))
    grok_model: str = "grok-3"
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = "gemini-2.5-pro"


@dataclass
class PathConfig:
    """File system paths."""

    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    wiki_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "outputs" / "wiki")
    bloomberg_drop: Path = field(default_factory=lambda: Path.home() / "Downloads" / "bloomberg_drop")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    prompts_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "skills" / "prompts")

    def ensure_dirs(self) -> None:
        """Create required directories if they don't exist."""
        for d in [self.wiki_dir, self.bloomberg_drop, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)


@dataclass
class PipelineConfig:
    """Pipeline execution settings."""

    cron_hour: int = 18
    cron_minute: int = 0
    eod_data_source: str = "yahoo"  # "yahoo" or "fmp"
    fmp_api_key: str = field(default_factory=lambda: os.getenv("FMP_API_KEY", ""))
    enable_grok: bool = True
    enable_perplexity: bool = True
    enable_gemini: bool = True
    enable_bloomberg_ingest: bool = True
    notification_enabled: bool = True


@dataclass
class Settings:
    """Top-level settings container."""

    mlx: MLXConfig = field(default_factory=MLXConfig)
    cloud: CloudConfig = field(default_factory=CloudConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)

    def __post_init__(self) -> None:
        self.paths.ensure_dirs()


# Singleton
settings = Settings()
