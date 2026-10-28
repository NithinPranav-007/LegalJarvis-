"""Google Gemini inference provider (Task T-10 / FR-05)."""

import json
import logging
import time
from collections.abc import AsyncGenerator

import httpx

from app.llm.providers.base import BaseLLMProvider, LLMResponse
from app.llm.providers.openai import mask_secret

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseLLMProvider):
    """Google Gemini model provider using official v1beta REST endpoints."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-flash",
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ):
        if not api_key:
            raise ValueError("GeminiProvider requires a non-empty api_key.")
        self._api_key = api_key
        self._model_name = model_name
        self._timeout = timeout_seconds
        self._max_retries = max_retries

        logger.info(
            "Initialized GeminiProvider(model=%s, key=%s)",
            self._model_name,
            mask_secret(self._api_key),
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _build_payload(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        return payload

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        url = f"{GEMINI_BASE_URL}/{self._model_name}:generateContent?key={self._api_key}"
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens)
        start_time = time.perf_counter()
        last_exc: Exception | None = None

        with httpx.Client(timeout=self._timeout) as client:
            for attempt in range(self._max_retries):
                try:
                    resp = client.post(url, json=payload)
                    if resp.status_code in (429, 500, 502, 503, 504):
                        sleep_time = (2**attempt) * 0.5
                        time.sleep(sleep_time)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    candidates = data.get("candidates", [])
                    content = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        content = "".join(p.get("text", "") for p in parts)

                    usage = data.get("usageMetadata", {})
                    return LLMResponse(
                        content=content,
                        model=self._model_name,
                        provider="gemini",
                        prompt_tokens=usage.get("promptTokenCount", 0),
                        completion_tokens=usage.get("candidatesTokenCount", 0),
                        latency_ms=round(latency_ms, 2),
                    )
                except httpx.HTTPError as exc:
                    last_exc = exc
                    time.sleep((2**attempt) * 0.5)

        raise RuntimeError(f"GeminiProvider generation failed: {last_exc}")

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        url = f"{GEMINI_BASE_URL}/{self._model_name}:generateContent?key={self._api_key}"
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens)
        start_time = time.perf_counter()
        last_exc: Exception | None = None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for _attempt in range(self._max_retries):
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (429, 500, 502, 503, 504):
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    candidates = data.get("candidates", [])
                    content = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        content = "".join(p.get("text", "") for p in parts)

                    usage = data.get("usageMetadata", {})
                    return LLMResponse(
                        content=content,
                        model=self._model_name,
                        provider="gemini",
                        prompt_tokens=usage.get("promptTokenCount", 0),
                        completion_tokens=usage.get("candidatesTokenCount", 0),
                        latency_ms=round(latency_ms, 2),
                    )
                except httpx.HTTPError as exc:
                    last_exc = exc

        raise RuntimeError(f"GeminiProvider agenerate failed: {last_exc}")

    async def astream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        url = f"{GEMINI_BASE_URL}/{self._model_name}:streamGenerateContent?alt=sse&key={self._api_key}"
        payload = self._build_payload(prompt, system_prompt, temperature, max_tokens)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    raw_data = line[6:].strip()
                    try:
                        chunk_json = json.loads(raw_data)
                        candidates = chunk_json.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                text_piece = p.get("text", "")
                                if text_piece:
                                    yield text_piece
                    except json.JSONDecodeError:
                        continue
