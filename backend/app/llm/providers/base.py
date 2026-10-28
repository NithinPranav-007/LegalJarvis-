"""Base interfaces and data models for LLM providers (Task T-10 / FR-05)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class BaseLLMProvider(ABC):
    """Abstract protocol for all LLM inference providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identification string (e.g. 'openai', 'gemini', 'fake')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Configured model identifier."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        """Synchronous completion generation."""
        pass

    @abstractmethod
    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        """Asynchronous completion generation."""
        pass

    @abstractmethod
    def astream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        """Asynchronous streaming of completion text tokens."""
        pass
