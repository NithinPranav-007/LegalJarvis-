"""Unit tests for LLM Gateway and providers (Task T-10 / FR-05)."""

import pytest

from app.llm.gateway import LLMGateway
from app.llm.providers.fake import FakeProvider
from app.llm.providers.openai import mask_secret


def test_fake_provider_sync_generation() -> None:
    provider = FakeProvider(
        canned_response="Under Article 21, personal liberty is guaranteed [C1].",
        model_name="test-fake-v1",
    )
    assert provider.provider_name == "fake"
    assert provider.model_name == "test-fake-v1"

    resp = provider.generate(
        prompt="What does Article 21 protect?",
        system_prompt="You are a legal assistant.",
    )
    assert resp.content == "Under Article 21, personal liberty is guaranteed [C1]."
    assert resp.model == "test-fake-v1"
    assert resp.provider == "fake"
    assert resp.prompt_tokens > 0
    assert resp.completion_tokens > 0
    assert resp.total_tokens == resp.prompt_tokens + resp.completion_tokens
    assert resp.latency_ms > 0


@pytest.mark.asyncio
async def test_fake_provider_async_and_streaming() -> None:
    provider = FakeProvider(
        canned_response="Specific performance is discretionary relief under the Act.",
    )

    # Async generate
    resp = await provider.agenerate(prompt="Explain specific performance")
    assert "discretionary relief" in resp.content

    # Async stream
    tokens = []
    async for tok in provider.astream(prompt="Explain specific performance"):
        tokens.append(tok)

    streamed_text = "".join(tokens).strip()
    assert streamed_text == "Specific performance is discretionary relief under the Act."


def test_mask_secret_utility() -> None:
    assert mask_secret(None) == "<not set>"
    assert mask_secret("") == "<not set>"
    assert mask_secret("short") == "***"
    secret = "sk-proj-1234567890abcdef1234567890"
    masked = mask_secret(secret)
    assert masked.startswith("sk-")
    assert masked.endswith("7890")
    assert "..." in masked
    assert "1234567890" not in masked


def test_gateway_with_fake_provider_in_tests() -> None:
    gw = LLMGateway(provider_name="fake", model_name="test-model")
    assert gw.provider_name == "fake"
    assert gw.has_credentials is True

    ping_result = gw.ping()
    assert ping_result["status"] == "ok"
    assert ping_result["provider"] == "fake"
    assert ping_result["model"] == "test-model"


def test_gateway_ping_blocked_when_credentials_absent() -> None:
    # Explicitly test OpenAI provider with empty API key
    gw = LLMGateway(provider_name="openai", api_key="")
    assert gw.has_credentials is False

    ping_result = gw.ping()
    assert ping_result["status"] == "blocked: no credentials"
    assert ping_result["provider"] == "openai"
    assert ping_result["latency_ms"] == 0.0
    assert "retrieval-only" in ping_result["message"].lower()


def test_gateway_unsupported_provider_raises_error() -> None:
    gw = LLMGateway(provider_name="nonexistent_llm", api_key="dummy_key_12345")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        gw.get_provider()
