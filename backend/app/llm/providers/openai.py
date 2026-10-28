"""OpenAI and OpenAI-compatible inference provider (Task T-10 / FR-05)."""

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator

import httpx

from app.llm.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


def mask_secret(secret: str | None) -> str:
    """Mask secret token for safe logging without credential leakage."""
    if not secret:
        return "<not set>"
    if len(secret) <= 8:
        return "***"
    return f"{secret[:3]}...{secret[-4:]}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API and OpenAI-compatible local server provider (e.g. Ollama, vLLM)."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ):
        if not api_key:
            raise ValueError("OpenAIProvider requires a non-empty api_key.")
        self._api_key = api_key
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries

        logger.info(
            "Initialized OpenAIProvider(model=%s, base_url=%s, key=%s)",
            self._model_name,
            self._base_url,
            mask_secret(self._api_key),
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _build_payload(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, object]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens, stream=False)

        start_time = time.perf_counter()
        last_exc: Exception | None = None

        with httpx.Client(timeout=self._timeout) as client:
            for attempt in range(self._max_retries):
                try:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code in (429, 500, 502, 503, 504):
                        sleep_time = (2**attempt) * 0.5
                        logger.warning(
                            "OpenAI HTTP %s (attempt %d/%d). Backing off %.1fs",
                            resp.status_code,
                            attempt + 1,
                            self._max_retries,
                            sleep_time,
                        )
                        time.sleep(sleep_time)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    return LLMResponse(
                        content=content,
                        model=data.get("model", self._model_name),
                        provider="openai",
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        latency_ms=round(latency_ms, 2),
                    )
                except httpx.HTTPError as exc:
                    last_exc = exc
                    if attempt == self._max_retries - 1:
                        break
                    time.sleep((2**attempt) * 0.5)

        raise RuntimeError(
            f"OpenAIProvider generation failed after {self._max_retries} attempts: {last_exc}"
        )

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens, stream=False)

        start_time = time.perf_counter()
        last_exc: Exception | None = None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(self._max_retries):
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code in (429, 500, 502, 503, 504):
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    return LLMResponse(
                        content=content,
                        model=data.get("model", self._model_name),
                        provider="openai",
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        latency_ms=round(latency_ms, 2),
                    )
                except httpx.HTTPError as exc:
                    last_exc = exc

        raise RuntimeError(f"OpenAIProvider agenerate failed: {last_exc}")

    async def astream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens, stream=True)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        raw_data = line[6:].strip()
                        if raw_data == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(raw_data)
                            delta = chunk_json["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
