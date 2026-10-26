import json

import httpx
import pytest

from app.config import Settings
from app.llm.factory import TimeoutFallback, build_provider
from app.llm.groq.client import GroqProvider
from app.llm.meta.client import MetaProvider


def _settings(**overrides: str) -> Settings:
    values = {
        "llm_provider": "meta",
        "meta_api_key": "meta-key",
        "meta_api_base_url": "https://api.meta.ai/v1",
        "meta_text_model": "text-from-env",
        "meta_vision_model": "vision-from-env",
        "groq_api_key": "",
        "groq_text_model": "groq-text-from-env",
        "groq_vision_model": "groq-vision-from-env",
    }
    values.update(overrides)
    return Settings(**values)


def _ok(text: str = "ready") -> httpx.Response:
    return httpx.Response(
        200, json={"choices": [{"message": {"role": "assistant", "content": text}}]}
    )


def test_factory_selects_groq_or_meta() -> None:
    groq = build_provider(_settings(llm_provider="groq", groq_api_key="g"))
    meta = build_provider(_settings())
    wrapped = build_provider(_settings(groq_api_key="g"))

    assert isinstance(groq, GroqProvider)
    assert isinstance(meta, MetaProvider)
    assert isinstance(wrapped, TimeoutFallback)


@pytest.mark.asyncio
async def test_meta_chat_posts_to_configured_base_url() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _ok("ready")

    provider = MetaProvider(_settings(), transport=httpx.MockTransport(handler))
    result = await provider.chat(
        [{"role": "user", "content": "hi"}],
        tools=[{"type": "function", "function": {"name": "search_catalog"}}],
    )

    body = json.loads(seen[0].content)
    assert str(seen[0].url) == "https://api.meta.ai/v1/chat/completions"
    assert body["model"] == "text-from-env"
    assert body["tool_choice"] == "auto"
    assert result.text == "ready"
    assert seen[0].headers["authorization"] == "Bearer meta-key"


@pytest.mark.asyncio
async def test_meta_timeout_retries_once_on_groq() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "api.meta.ai" in str(request.url):
            raise httpx.TimeoutException("timed out")
        return _ok("from-groq")

    provider = build_provider(_settings(groq_api_key="g"), transport=httpx.MockTransport(handler))
    result = await provider.chat([{"role": "user", "content": "hi"}])

    assert result.text == "from-groq"
    assert [str(request.url) for request in seen] == [
        "https://api.meta.ai/v1/chat/completions",
        "https://api.groq.com/openai/v1/chat/completions",
    ]
    assert json.loads(seen[1].content)["model"] == "groq-text-from-env"
