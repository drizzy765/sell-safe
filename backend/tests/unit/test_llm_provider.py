import json

import httpx
import pytest

from app.config import Settings
from app.llm.base import LLMConfigError
from app.llm.fake import FakeProvider
from app.llm.groq.client import GroqProvider

_SCHEMA = {"type": "object", "properties": {"name": {"type": "string"}}}


def _settings() -> Settings:
    return Settings(
        groq_api_key="test-groq-key",
        groq_text_model="text-from-env",
        groq_vision_model="vision-from-env",
        groq_transcribe_model="whisper-from-env",
    )


def _chat_payload(text: str = '{"name":"Black tote"}', tool_calls: list | None = None) -> dict:
    message: dict = {"role": "assistant", "content": text}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}]}


@pytest.mark.asyncio
async def test_groq_chat_sends_tools_and_json_schema() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json=_chat_payload(
                "hello",
                [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "search_catalog", "arguments": '{"query":"bag"}'},
                    }
                ],
            ),
        )

    provider = GroqProvider(_settings(), transport=httpx.MockTransport(handler))
    result = await provider.chat(
        [{"role": "user", "content": "price?"}],
        tools=[{"type": "function", "function": {"name": "search_catalog"}}],
        json_schema=_SCHEMA,
    )

    body = json.loads(seen[0].content)
    assert seen[0].url.path == "/openai/v1/chat/completions"
    assert body["model"] == "text-from-env"
    assert body["tools"][0]["function"]["name"] == "search_catalog"
    assert body["response_format"]["json_schema"]["schema"] == _SCHEMA
    assert result.text == "hello"
    assert result.tool_calls[0].name == "search_catalog"
    assert seen[0].headers["authorization"] == "Bearer test-groq-key"


@pytest.mark.asyncio
async def test_groq_vision_uses_env_model_and_returns_json() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=_chat_payload('{"name":"Black tote"}'))

    provider = GroqProvider(_settings(), transport=httpx.MockTransport(handler))
    parsed = await provider.vision(b"\xff\xd8jpeg", "extract", _SCHEMA)

    body = json.loads(seen[0].content)
    assert body["model"] == "vision-from-env"
    assert parsed == {"name": "Black tote"}
    assert "jpeg" not in body["messages"][0]["content"][0]["text"]


@pytest.mark.asyncio
async def test_groq_transcribe_posts_audio() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"text": "how much"})

    provider = GroqProvider(_settings(), transport=httpx.MockTransport(handler))
    text = await provider.transcribe(b"ogg-bytes")

    assert text == "how much"
    assert seen[0].url.path == "/openai/v1/audio/transcriptions"
    assert b"whisper-from-env" in seen[0].content


@pytest.mark.asyncio
async def test_missing_key_does_not_call_the_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network was called")

    provider = GroqProvider(
        Settings(groq_api_key="", groq_text_model="text-from-env"),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(LLMConfigError):
        await provider.chat([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_missing_model_name_is_not_replaced() -> None:
    provider = GroqProvider(Settings(groq_api_key="test-groq-key", groq_text_model=""))
    with pytest.raises(LLMConfigError):
        await provider.chat([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_fake_provider_returns_canned_values() -> None:
    provider = FakeProvider(transcript="abeg")
    assert (await provider.chat([])).text == "ok"
    assert (await provider.vision(b"img", "extract", _SCHEMA))["name"] == "Black tote"
    assert await provider.transcribe(b"audio") == "abeg"
