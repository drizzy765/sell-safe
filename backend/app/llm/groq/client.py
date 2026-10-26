"""Groq chat, vision, and transcription. https://api.groq.com/openai/v1"""

import httpx

from app.config import Settings
from app.llm.base import LLMConfigError, LLMResult
from app.llm.wire import chat_payload, parse_chat_response, parse_json_content, vision_messages

_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider:
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
        self._require(self._settings.groq_text_model, "GROQ_TEXT_MODEL")
        payload = chat_payload(self._settings.groq_text_model, messages, tools, json_schema)
        data = await self._post_json("/chat/completions", payload)
        return parse_chat_response(data)

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict:
        self._require(self._settings.groq_vision_model, "GROQ_VISION_MODEL")
        payload = chat_payload(
            self._settings.groq_vision_model,
            vision_messages(prompt, image),
            None,
            json_schema,
        )
        data = await self._post_json("/chat/completions", payload)
        return parse_json_content(parse_chat_response(data).text)

    async def transcribe(self, audio: bytes) -> str:
        self._require(self._settings.groq_transcribe_model, "GROQ_TRANSCRIBE_MODEL")
        url = f"{_BASE_URL}/audio/transcriptions"
        files = {"file": ("note.ogg", audio, "audio/ogg")}
        form = {"model": self._settings.groq_transcribe_model}
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(url, files=files, data=form, headers=self._headers())
            response.raise_for_status()
        body = response.json()
        return str(body["text"])

    def _require(self, model: str, model_env: str) -> None:
        if not self._settings.groq_api_key:
            raise LLMConfigError("GROQ_API_KEY is not set")
        if not model:
            raise LLMConfigError(f"{model_env} is not set")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._settings.groq_api_key}"}

    async def _post_json(self, path: str, payload: dict) -> dict:
        url = f"{_BASE_URL}{path}"
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()
        return response.json()
