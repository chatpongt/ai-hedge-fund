"""Grok adapter — X/Twitter news, breaking news triage."""

import logging
from typing import Any, Optional

import httpx

from config.settings import settings

from .base import AdapterError, BaseAdapter

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"


class GrokAdapter(BaseAdapter):
    """Adapter for Grok (xAI) API — realtime news from X/Twitter."""

    name = "grok"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.cloud.grok_api_key
        self.model = settings.cloud.grok_model
        if not self.api_key:
            logger.warning("Grok API key not set — adapter will be unavailable")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        if not self.api_key:
            raise AdapterError("grok", "API key not configured", retryable=False)

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
                    GROK_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("Grok chat ok model=%s", model)
                return content
        except httpx.HTTPStatusError as e:
            raise AdapterError("grok", f"HTTP {e.response.status_code}: {e.response.text}", retryable=e.response.status_code >= 500) from e
        except Exception as e:
            raise AdapterError("grok", str(e), retryable=True) from e

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    GROK_API_URL,
                    json={"model": self.model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5},
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def scan_news(self, topics: list[str], market: str = "SET") -> str:
        """Scan X/Twitter for breaking news on given topics."""
        topics_str = ", ".join(topics)
        return await self.chat(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a financial news analyst monitoring X/Twitter for the {market} market. "
                    "Report breaking news, significant posts from key accounts, and sentiment shifts. "
                    "Return structured JSON with fields: headlines (list), sentiment (bullish/bearish/neutral), "
                    "key_accounts (list of usernames), confidence (0-100).",
                },
                {"role": "user", "content": f"Scan for breaking news on: {topics_str}"},
            ],
            temperature=0.3,
        )
