"""MLX adapter — bridge to local MLX-LM server on localhost:8080.

The MLX server exposes an OpenAI-compatible API, so we use httpx
to call it directly (no SDK dependency needed).
"""

import json
import logging
from typing import Any, Optional

import httpx

from config.settings import settings

from .base import AdapterError, BaseAdapter

logger = logging.getLogger(__name__)


class MLXAdapter(BaseAdapter):
    """Adapter for local MLX-LM model server."""

    name = "mlx"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.mlx.base_url
        self.default_model = settings.mlx.main_model
        self.fast_model = settings.mlx.fast_model
        self.reasoning_model = settings.mlx.reasoning_model
        self.timeout = settings.mlx.timeout
        self.max_retries = settings.mlx.max_retries

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        model = model or self.default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(f"{self.base_url}/chat/completions", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info("MLX chat ok model=%s tokens=%s attempt=%d", model, data.get("usage", {}), attempt)
                    return content
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning("MLX timeout attempt=%d/%d model=%s", attempt, self.max_retries, model)
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error("MLX HTTP error %s attempt=%d/%d", e.response.status_code, attempt, self.max_retries)
            except (httpx.ConnectError, httpx.ReadError) as e:
                last_error = e
                logger.warning("MLX connection error attempt=%d/%d: %s", attempt, self.max_retries, e)

        raise AdapterError("mlx", f"Failed after {self.max_retries} attempts: {last_error}", retryable=True)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/models")
                return resp.status_code == 200
        except Exception:
            return False

    async def chat_fast(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Use the small/fast model (Qwen 4B) for triage and parsing."""
        return await self.chat(messages, model=self.fast_model, temperature=temperature, max_tokens=max_tokens)

    async def chat_reasoning(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.5,
        max_tokens: int = 8192,
    ) -> str:
        """Use the deep reasoning model (DeepSeek-R1) for complex analysis."""
        return await self.chat(messages, model=self.reasoning_model, temperature=temperature, max_tokens=max_tokens)

    async def list_models(self) -> list[str]:
        """List available models on the MLX server."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/models")
                resp.raise_for_status()
                data = resp.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.error("Failed to list MLX models: %s", e)
            return []
