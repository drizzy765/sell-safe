"""Canned provider for tests. CI must not call Groq or Meta."""

from app.llm.base import LLMJsonError, LLMResult


class FakeProvider:
    def __init__(
        self,
        *,
        chat_text: str = "ok",
        chat: list[dict] | None = None,
        vision: dict | None = None,
        transcript: str = "hello",
        json_failures: int = 0,
    ) -> None:
        self._chat_sequence = chat or []
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
        self.chat_messages: list[list[dict]] = []

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        json_schema: dict | None = None,
    ) -> LLMResult:
        self.chat_calls += 1
        self.chat_messages.append(messages)
        if self.chat_calls <= len(self._chat_sequence):
            item = self._chat_sequence[self.chat_calls - 1]
            from app.llm.base import ToolCall

            calls = [
                ToolCall(id=c.get("id"), name=c["name"], arguments=c.get("arguments", "{}"))
                for c in (item.get("tool_calls") or [])
            ]
            return LLMResult(text=item.get("text", ""), tool_calls=calls)
        return LLMResult(text=self.chat_text)

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict:
        self.vision_calls.append(prompt)
        if self.json_failures > 0:
            self.json_failures -= 1
            raise LLMJsonError("invalid json")
        return dict(self.vision_result)

    async def transcribe(self, audio: bytes) -> str:
        return self.transcript
