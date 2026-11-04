"""Select a provider from LLM_PROVIDER. Meta failures fall back to Groq."""

import logging

import httpx

from app.config import Settings
from app.llm.base import LLMConfigError, LLMProvider, LLMResult
from app.llm.groq.client import GroqProvider
from app.llm.meta.client import MetaProvider

logger = logging.getLogger(__name__)


class ProviderFallback:
    """Try the primary provider once, then Groq on any failure.

    Covers timeouts, model_not_found, and provider outages: buyers should
    get a real reply from the fallback instead of the static template.
    If Groq also fails, its error propagates to the caller's fallback.
    """

    def __init__(self, primary: MetaProvider, fallback: GroqProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        json_schema: dict | None = None,
    ) -> LLMResult:
        try:
            return await self._primary.chat(messages, tools, json_schema)
        except Exception:
            logger.exception("Primary LLM provider failed; falling back to Groq")
            return await self._fallback.chat(messages, tools, json_schema)

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict:
        try:
            return await self._primary.vision(image, prompt, json_schema)
        except Exception:
            logger.exception("Primary LLM vision failed; falling back to Groq")
            return await self._fallback.vision(image, prompt, json_schema)

    async def transcribe(self, audio: bytes) -> str:
        return await self._primary.transcribe(audio)


# Backwards-compatible alias (older imports/tests).
TimeoutFallback = ProviderFallback


def build_provider(
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None = None,
) -> LLMProvider:
    if settings.llm_provider == "groq":
        return GroqProvider(settings, transport)
    if settings.llm_provider == "meta":
        primary = MetaProvider(settings, transport)
        if settings.groq_api_key:
            return ProviderFallback(primary, GroqProvider(settings, transport))
        return primary
    raise LLMConfigError("LLM_PROVIDER must be groq or meta")
