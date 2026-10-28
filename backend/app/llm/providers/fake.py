"""Fake LLM provider strictly isolated for offline unit tests (Task T-10 / Rule 2)."""

import asyncio
import re
from collections.abc import AsyncGenerator

from app.core.config import settings
from app.llm.providers.base import BaseLLMProvider, LLMResponse

STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "of",
    "to",
    "in",
    "for",
    "on",
    "by",
    "with",
    "at",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "under",
    "which",
    "who",
    "whom",
    "whose",
    "what",
    "how",
    "why",
    "can",
    "any",
    "all",
}


def _extract_keywords(text: str) -> set[str]:
    """Extract lowercased content keywords, removing stop words and non-alphabetics."""
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {t for t in tokens if t not in STOP_WORDS}


class FakeProvider(BaseLLMProvider):
    """Deterministic fake provider used ONLY in offline unit tests.

    Per AGENTS.md Rule 2, this provider is explicitly named FakeProvider
    and cannot be used when ENVIRONMENT is 'production'.
    """

    def __init__(
        self,
        canned_response: str | None = None,
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

    def _synthesize_offline_response(self, prompt: str) -> str:
        """Deterministically extract grounded factual sentences from context passages in offline mode.

        If passages contain matching evidence for the question, constructs an answer
        where each sentence cites its exact supporting passage marker [C{i}].
        If no evidence or unrelated question, explicitly outputs [INSUFFICIENT_EVIDENCE].
        """
        if "Reply with the single word 'PONG'." in prompt:
            return "PONG"

        if "CONTEXT PASSAGES:" not in prompt or "QUESTION:" not in prompt:
            return "This is a deterministic test response."

        # 1. Extract question
        q_match = re.search(r"QUESTION:\s*\n*(.*?)(?=\n*ANSWER:|\Z)", prompt, re.DOTALL)
        question = q_match.group(1).strip() if q_match else ""
        q_words = _extract_keywords(question)
        if not q_words:
            return "[INSUFFICIENT_EVIDENCE] No legal question provided."

        # Check if question specifies a specific legal case name
        from app.qa.query_analysis import extract_target_case_name
        target_case = extract_target_case_name(question)

        # 2. Extract passage blocks
        ctx_match = re.search(r"CONTEXT PASSAGES:\s*(.*?)(?=\n*QUESTION:|\Z)", prompt, re.DOTALL)
        ctx_text = ctx_match.group(1).strip() if ctx_match else ""

        # If a specific case was requested, ensure the context actually contains that case
        if target_case:
            case_tokens = [
                t.lower()
                for t in re.findall(r"\b[a-zA-Z]{3,}\b", target_case)
                if t.lower() not in {"all", "india", "state", "union", "ltd", "pvt"}
            ]
            if case_tokens and not all(tok in ctx_text.lower() for tok in case_tokens):
                return (
                    f"[INSUFFICIENT_EVIDENCE] The retrieved context passages do not contain "
                    f"the requested judgment '{target_case}'."
                )

        # Matches [C1] ... Passage: <snippet>
        passage_blocks = re.findall(
            r"(\[C\d+\])[^\n]*\n.*?Passage:\s*(.*?)(?=\n\[C\d+\]|\n*QUESTION:|\Z)",
            ctx_text,
            re.DOTALL,
        )
        if not passage_blocks:
            return "[INSUFFICIENT_EVIDENCE] No legal passages in context."

        scored_sentences: list[tuple[int, str, str]] = []
        seen_texts: set[str] = set()

        for marker, raw_snippet in passage_blocks:
            clean_snippet = " ".join(raw_snippet.split())
            sents = re.split(r"(?<=[.!?])\s+", clean_snippet)
            for s in sents:
                s_clean = s.strip()
                if not s_clean or len(s_clean) < 15:
                    continue
                swords = _extract_keywords(s_clean)
                common = q_words.intersection(swords)
                # Require at least 2 significant overlapping keywords with the question
                if len(common) >= 2 and s_clean not in seen_texts:
                    seen_texts.add(s_clean)
                    scored_sentences.append((len(common), marker, s_clean))

        if not scored_sentences:
            return (
                "[INSUFFICIENT_EVIDENCE] The retrieved context passages do not contain "
                "sufficient evidence to answer this legal question."
            )

        # Sort candidate sentences by relevance descending
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_candidates = scored_sentences[:2]

        out_sents = []
        for _, marker, sent in top_candidates:
            s_stripped = sent.rstrip(".!?")
            out_sents.append(f"{s_stripped} {marker}.")

        return " ".join(out_sents)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        self.call_history.append({"prompt": prompt, "system_prompt": system_prompt})
        content = (
            self._canned_response
            if self._canned_response is not None
            else self._synthesize_offline_response(prompt)
        )
        prompt_words = len(prompt.split())
        comp_words = len(content.split())
        return LLMResponse(
            content=content,
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
        content = (
            self._canned_response
            if self._canned_response is not None
            else self._synthesize_offline_response(prompt)
        )
        tokens = content.split()
        for tok in tokens:
            await asyncio.sleep(0.001)
            yield tok + " "
