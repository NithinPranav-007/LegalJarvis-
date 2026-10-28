"""Fake LLM provider strictly isolated for offline unit tests (Task T-10 / Rule 2)."""

import asyncio
from collections.abc import AsyncGenerator

from app.core.config import settings
from app.llm.providers.base import BaseLLMProvider, LLMResponse


class FakeProvider(BaseLLMProvider):
    """Deterministic fake provider used ONLY in offline unit tests.

    Per AGENTS.md Rule 2, this provider is explicitly named FakeProvider
    and cannot be used when ENVIRONMENT is 'production'.
    """

    def __init__(
        self,
        canned_response: str = "This is a deterministic test response.",
        model_name: str = "fake-test-model",
    ):
        if getattr(settings, "ENVIRONMENT", "").lower() == "production":
            raise RuntimeError("FakeProvider is strictly prohibited in production environments.")
        self._canned_response = canned_response
        self._model_name = model_name
        self.call_history: list[dict[str, str | None]] = []

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def model_name(self) -> str:
        return self._model_name

    def set_canned_response(self, response: str) -> None:
        self._canned_response = response

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        self.call_history.append({"prompt": prompt, "system_prompt": system_prompt})
        prompt_words = len(prompt.split())
        comp_words = len(self._canned_response.split())
        return LLMResponse(
            content=self._canned_response,
            model=self._model_name,
            provider="fake",
            prompt_tokens=prompt_words,
            completion_tokens=comp_words,
            latency_ms=1.0,
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        await asyncio.sleep(0.001)
        return self.generate(prompt, system_prompt, temperature, max_tokens)

    async def astream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        self.call_history.append({"prompt": prompt, "system_prompt": system_prompt})
        tokens = self._canned_response.split()
        for tok in tokens:
            await asyncio.sleep(0.001)
            yield tok + " "
