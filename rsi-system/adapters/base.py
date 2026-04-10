"""Base adapter interface for all AI providers."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Raised when an adapter call fails."""

    def __init__(self, adapter_name: str, message: str, retryable: bool = False):
        self.adapter_name = adapter_name
        self.retryable = retryable
        super().__init__(f"[{adapter_name}] {message}")


class BaseAdapter(ABC):
    """Abstract base for all AI adapters (local and cloud)."""

    name: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        """Send a chat completion request and return the response text.

        Args:
            messages: OpenAI-format message list [{"role": ..., "content": ...}]
            model: Model override (uses adapter default if None)
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            response_format: Optional JSON schema for structured output

        Returns:
            Response text content

        Raises:
            AdapterError: On failure after retries
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the adapter's backing service is available."""
        ...

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Chat with JSON response format hint."""
        return await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
