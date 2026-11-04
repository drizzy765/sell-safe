import pytest

from app.llm.base import LLMResult
from app.llm.factory import ProviderFallback


class _FailingPrimary:
    async def chat(self, messages, tools=None, json_schema=None):
        raise RuntimeError("Meta request failed (404): model_not_found")

    async def vision(self, image, prompt, json_schema):
        raise RuntimeError("Meta request failed (404): model_not_found")

    async def transcribe(self, audio):
        return "primary transcript"


class _GroqLike:
    async def chat(self, messages, tools=None, json_schema=None):
        return LLMResult(text="fallback reply")

    async def vision(self, image, prompt, json_schema):
        return {"amount_kobo": 100}

    async def transcribe(self, audio):
        return "fallback transcript"


@pytest.mark.asyncio
async def test_any_primary_failure_falls_back_to_groq() -> None:
    """Meta model_not_found (not just timeouts) must still answer buyers."""
    wrapped = ProviderFallback(_FailingPrimary(), _GroqLike())  # type: ignore[arg-type]
    result = await wrapped.chat([{"role": "user", "content": "hi"}])
    assert result.text == "fallback reply"
    assert await wrapped.vision(b"img", "prompt", {}) == {"amount_kobo": 100}
