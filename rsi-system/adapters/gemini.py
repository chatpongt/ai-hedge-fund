"""Gemini adapter — long document reading (Annual Reports 200+ pages)."""

import logging
from typing import Any, Optional

import httpx

from config.settings import settings

from .base import AdapterError, BaseAdapter

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini Pro — long-context document analysis."""

    name = "gemini"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.cloud.gemini_api_key
        self.model = settings.cloud.gemini_model
        if not self.api_key:
            logger.warning("Gemini API key not set — adapter will be unavailable")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 8192,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        if not self.api_key:
            raise AdapterError("gemini", "API key not configured", retryable=False)

        model = model or self.model
        # Convert OpenAI message format to Gemini format
        contents = []
        system_instruction = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if response_format and response_format.get("type") == "json_object":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        url = f"{GEMINI_API_URL}/{model}:generateContent?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("Gemini chat ok model=%s", model)
                return content
        except httpx.HTTPStatusError as e:
            raise AdapterError("gemini", f"HTTP {e.response.status_code}: {e.response.text}", retryable=e.response.status_code >= 500) from e
        except (KeyError, IndexError) as e:
            raise AdapterError("gemini", f"Unexpected response format: {e}", retryable=False) from e
        except Exception as e:
            raise AdapterError("gemini", str(e), retryable=True) from e

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            url = f"{GEMINI_API_URL}?key={self.api_key}"
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False

    async def analyze_document(self, document_text: str, instruction: str) -> str:
        """Analyze a long document (e.g., Annual Report) with Gemini's large context window."""
        return await self.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert financial analyst specializing in Thai SET-listed companies. "
                    "Analyze documents thoroughly, extracting key financial data, risks, and strategic insights.",
                },
                {"role": "user", "content": f"## Instruction\n{instruction}\n\n## Document\n{document_text}"},
            ],
            temperature=0.3,
            max_tokens=8192,
        )
