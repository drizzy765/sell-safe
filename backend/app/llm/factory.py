"""Select a provider from LLM_PROVIDER. Meta chat timeouts retry once on Groq."""

import httpx

from app.config import Settings
from app.llm.base import LLMConfigError, LLMProvider, LLMResult
from app.llm.groq.client import GroqProvider
from app.llm.meta.client import MetaProvider


class TimeoutFallback:
    """Try the primary provider once, then Groq if the call times out."""

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
        except httpx.TimeoutException:
            return await self._fallback.chat(messages, tools, json_schema)

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict:
        try:
            return await self._primary.vision(image, prompt, json_schema)
        except httpx.TimeoutException:
            return await self._fallback.vision(image, prompt, json_schema)

    async def transcribe(self, audio: bytes) -> str:
        return await self._primary.transcribe(audio)


def build_provider(
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None = None,
) -> LLMProvider:
    if settings.llm_provider == "groq":
        return GroqProvider(settings, transport)
    if settings.llm_provider == "meta":
        primary = MetaProvider(settings, transport)
        if settings.groq_api_key:
            return TimeoutFallback(primary, GroqProvider(settings, transport))
        return primary
    raise LLMConfigError("LLM_PROVIDER must be groq or meta")
