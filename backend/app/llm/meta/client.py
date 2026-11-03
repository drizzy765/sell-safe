"""Meta Model API chat and vision.

Confirmed against dev.meta.ai on 2026-10-26:
- Base URL `https://api.meta.ai/v1` and `POST /chat/completions` with a bearer token.
  https://dev.meta.ai/docs/api-reference/
- Vision is an `image_url` part on a user message (URL or base64 data URL).
  https://dev.meta.ai/docs/cookbook/vision-input
- Tool calls use OpenAI function tools. `tool_choice` only accepts `"auto"`.
  https://dev.meta.ai/docs/cookbook/tool-function-calling
- The API reference lists Responses, Chat Completions, Messages, Files, Models, and
  Status. It does not list audio transcription, so `transcribe` uses Groq when
  `GROQ_API_KEY` is set.

`META_API_BASE_URL` should be the versioned base, for example `https://api.meta.ai/v1`.
Model ids come from `META_TEXT_MODEL` and `META_VISION_MODEL` only.
"""

import httpx

from app.config import Settings
from app.llm.base import LLMConfigError, LLMResult
from app.llm.groq.client import GroqProvider
from app.llm.wire import chat_payload, parse_chat_response, parse_json_content, vision_messages


class MetaProvider:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        json_schema: dict | None = None,
    ) -> LLMResult:
        self._require(self._settings.meta_text_model, "META_TEXT_MODEL")
        payload = chat_payload(
            self._settings.meta_text_model,
            messages,
            tools,
            json_schema,
            tool_choice_auto=bool(tools),
        )
        data = await self._post_json("/chat/completions", payload)
        return parse_chat_response(data)

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict:
        self._require(self._settings.meta_vision_model, "META_VISION_MODEL")
        payload = chat_payload(
            self._settings.meta_vision_model,
            vision_messages(prompt, image),
            None,
            json_schema,
        )
        data = await self._post_json("/chat/completions", payload)
        return parse_json_content(parse_chat_response(data).text)

    async def transcribe(self, audio: bytes) -> str:
        groq = GroqProvider(self._settings, self._transport)
        return await groq.transcribe(audio)

    def _require(self, model: str, model_env: str) -> None:
        if not self._settings.meta_api_key:
            raise LLMConfigError("META_API_KEY is not set")
        if not self._settings.meta_api_base_url:
            raise LLMConfigError("META_API_BASE_URL is not set")
        if not model:
            raise LLMConfigError(f"{model_env} is not set")

    async def _post_json(self, path: str, payload: dict) -> dict:
        base = self._settings.meta_api_base_url.rstrip("/")
        url = f"{base}{path}"
        headers = {"Authorization": f"Bearer {self._settings.meta_api_key}"}
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(url, json=payload, headers=headers)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Meta request failed ({exc.response.status_code}): {exc.response.text[:500]}"
                ) from exc
        return response.json()
