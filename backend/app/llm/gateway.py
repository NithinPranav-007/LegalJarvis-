"""Unified LLM Gateway managing provider routing, credentials, and ping (Task T-10 / FR-05)."""

import argparse
import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import Any

from app.core.config import settings
from app.llm.providers.base import BaseLLMProvider, LLMResponse
from app.llm.providers.fake import FakeProvider
from app.llm.providers.gemini import GeminiProvider
from app.llm.providers.openai import OpenAIProvider, mask_secret

logger = logging.getLogger(__name__)


class LLMGateway:
    """Gateway orchestrating LLM provider lifecycle, retries, and logging."""

    def __init__(
        self,
        provider_name: str | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        raw_provider = provider_name or getattr(settings, "LLM_PROVIDER", "openai") or "openai"
        self._provider_name: str = str(raw_provider).lower()
        self._model_name: str = str(
            model_name or getattr(settings, "LLM_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
        )
        self._api_key: str = str(
            api_key
            or getattr(settings, "LLM_API_KEY", "")
            or getattr(settings, "GEMINI_API_KEY", "")
            or os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or ""
        )
        self._base_url: str = str(
            base_url
            or getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
            or "https://api.openai.com/v1"
        )
        self._provider_instance: BaseLLMProvider | None = None

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def has_credentials(self) -> bool:
        if self._provider_name == "fake":
            return True
        return bool(self._api_key and len(self._api_key.strip()) > 5)

    @property
    def is_available(self) -> bool:
        """Alias for checking provider availability."""
        return self.has_credentials

    def get_provider(self) -> BaseLLMProvider:
        """Instantiate or return cached provider instance."""
        if self._provider_instance is not None:
            return self._provider_instance

        if self._provider_name == "fake":
            self._provider_instance = FakeProvider(model_name=self._model_name)
        elif self._provider_name == "openai":
            if not self.has_credentials:
                raise ValueError("OpenAI provider requires LLM_API_KEY or OPENAI_API_KEY.")
            self._provider_instance = OpenAIProvider(
                api_key=self._api_key,
                model_name=self._model_name,
                base_url=self._base_url,
            )
        elif self._provider_name == "gemini":
            if not self.has_credentials:
                raise ValueError("Gemini provider requires LLM_API_KEY or GEMINI_API_KEY.")
            self._provider_instance = GeminiProvider(
                api_key=self._api_key,
                model_name=self._model_name,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self._provider_name}")

        return self._provider_instance

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        provider = self.get_provider()
        return provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        provider = self.get_provider()
        return await provider.agenerate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def astream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        provider = self.get_provider()
        async for token in provider.astream(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield token

    def ping(self) -> dict[str, Any]:
        """Perform health-check ping to verify provider connectivity."""
        if not self.has_credentials:
            return {
                "status": "blocked: no credentials",
                "provider": self._provider_name,
                "model": self._model_name,
                "key_preview": mask_secret(self._api_key),
                "latency_ms": 0.0,
                "message": "No valid LLM_API_KEY detected in environment. System operating in retrieval-only mode.",
            }

        try:
            t0 = time.perf_counter()
            resp = self.generate(
                prompt="Reply with the single word 'PONG'.",
                max_tokens=10,
                temperature=0.0,
            )
            lat = round((time.perf_counter() - t0) * 1000.0, 2)
            return {
                "status": "ok",
                "provider": self._provider_name,
                "model": resp.model,
                "response": resp.content.strip(),
                "latency_ms": lat,
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
            }
        except Exception as exc:
            return {
                "status": "error",
                "provider": self._provider_name,
                "model": self._model_name,
                "error": str(exc),
                "latency_ms": 0.0,
            }


_DEFAULT_GATEWAY: LLMGateway | None = None


def get_llm_gateway() -> LLMGateway:
    """Return default application LLMGateway singleton."""
    global _DEFAULT_GATEWAY
    if _DEFAULT_GATEWAY is None:
        _DEFAULT_GATEWAY = LLMGateway()
    return _DEFAULT_GATEWAY


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LegalJarvis LLM Gateway Ping Tool")
    parser.add_argument("--provider", default=None, help="LLM Provider override")
    parser.add_argument("--model", default=None, help="Model ID override")
    args = parser.parse_args()

    gw = LLMGateway(provider_name=args.provider, model_name=args.model)
    res = gw.ping()
    print("\n--- LLM Gateway Connectivity Status ---")
    for k, v in res.items():
        print(f"  {k}: {v}")
