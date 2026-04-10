"""Tests for adapter layer — unit tests (no real API calls)."""

import pytest
import json

from adapters.base import AdapterError, BaseAdapter
from adapters.mlx_adapter import MLXAdapter
from adapters.perplexity import PerplexityAdapter
from adapters.grok import GrokAdapter
from adapters.gemini import GeminiAdapter


class TestAdapterError:
    def test_error_message(self):
        err = AdapterError("mlx", "Connection refused", retryable=True)
        assert "mlx" in str(err)
        assert "Connection refused" in str(err)
        assert err.retryable is True

    def test_non_retryable_error(self):
        err = AdapterError("perplexity", "Invalid API key", retryable=False)
        assert err.retryable is False


class TestMLXAdapter:
    def test_init_defaults(self):
        adapter = MLXAdapter()
        assert "localhost:8080" in adapter.base_url
        assert adapter.timeout == 180

    def test_init_custom_url(self):
        adapter = MLXAdapter(base_url="http://192.168.1.100:9090/v1")
        assert adapter.base_url == "http://192.168.1.100:9090/v1"

    def test_has_all_model_refs(self):
        adapter = MLXAdapter()
        assert adapter.default_model  # main model
        assert adapter.fast_model     # 4B model
        assert adapter.reasoning_model  # DeepSeek


class TestPerplexityAdapter:
    def test_init_without_key(self):
        adapter = PerplexityAdapter(api_key="")
        assert adapter.api_key == ""

    @pytest.mark.asyncio
    async def test_chat_without_key_raises(self):
        adapter = PerplexityAdapter(api_key="")
        with pytest.raises(AdapterError, match="API key not configured"):
            await adapter.chat([{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_health_check_without_key(self):
        adapter = PerplexityAdapter(api_key="")
        result = await adapter.health_check()
        assert result is False


class TestGrokAdapter:
    def test_init_without_key(self):
        adapter = GrokAdapter(api_key="")
        assert adapter.api_key == ""

    @pytest.mark.asyncio
    async def test_chat_without_key_raises(self):
        adapter = GrokAdapter(api_key="")
        with pytest.raises(AdapterError, match="API key not configured"):
            await adapter.chat([{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_health_check_without_key(self):
        adapter = GrokAdapter(api_key="")
        result = await adapter.health_check()
        assert result is False


class TestGeminiAdapter:
    def test_init_without_key(self):
        adapter = GeminiAdapter(api_key="")
        assert adapter.api_key == ""

    @pytest.mark.asyncio
    async def test_chat_without_key_raises(self):
        adapter = GeminiAdapter(api_key="")
        with pytest.raises(AdapterError, match="API key not configured"):
            await adapter.chat([{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_health_check_without_key(self):
        adapter = GeminiAdapter(api_key="")
        result = await adapter.health_check()
        assert result is False
