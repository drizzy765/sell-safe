"""Canned provider for tests. CI must not call Groq or Meta."""

from app.llm.base import LLMJsonError, LLMResult


class FakeProvider:
    def __init__(
        self,
        *,
        chat_text: str = "ok",
        vision: dict | None = None,
        transcript: str = "hello",
        json_failures: int = 0,
    ) -> None:
        self.chat_text = chat_text
        self.vision_result = vision or {
            "name": "Black tote",
            "description": "Leather tote",
            "suggested_price_kobo": None,
            "category": "bags",
            "colors": ["black"],
            "confidence": 0.9,
        }
        self.transcript = transcript
        self.json_failures = json_failures
        self.vision_calls: list[str] = []
        self.chat_calls = 0

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        json_schema: dict | None = None,
    ) -> LLMResult:
        self.chat_calls += 1
        return LLMResult(text=self.chat_text)

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict:
        self.vision_calls.append(prompt)
        if self.json_failures > 0:
            self.json_failures -= 1
            raise LLMJsonError("invalid json")
        return dict(self.vision_result)

    async def transcribe(self, audio: bytes) -> str:
        return self.transcript
