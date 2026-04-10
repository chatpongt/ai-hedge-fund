"""Perplexity adapter — macro data, sector data, factual search."""

import logging
from typing import Any, Optional

import httpx

from config.settings import settings

from .base import AdapterError, BaseAdapter

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class PerplexityAdapter(BaseAdapter):
    """Adapter for Perplexity Pro API (search-augmented LLM)."""

    name = "perplexity"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.cloud.perplexity_api_key
        self.model = settings.cloud.perplexity_model
        if not self.api_key:
            logger.warning("Perplexity API key not set — adapter will be unavailable")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        if not self.api_key:
            raise AdapterError("perplexity", "API key not configured", retryable=False)

        model = model or self.model
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    PERPLEXITY_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("Perplexity chat ok model=%s", model)
                return content
        except httpx.HTTPStatusError as e:
            raise AdapterError("perplexity", f"HTTP {e.response.status_code}: {e.response.text}", retryable=e.response.status_code >= 500) from e
        except Exception as e:
            raise AdapterError("perplexity", str(e), retryable=True) from e

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    PERPLEXITY_API_URL,
                    json={"model": self.model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5},
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def search(self, query: str) -> str:
        """Convenience method: search for factual data via Perplexity."""
        return await self.chat(
            messages=[
                {"role": "system", "content": "You are a financial research assistant. Provide factual, data-driven answers with sources. Focus on Thai SET market when relevant."},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
        )
