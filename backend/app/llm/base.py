"""Provider contract. Model names and keys come from the environment."""

from typing import Protocol

from pydantic import BaseModel, Field


class LLMConfigError(RuntimeError):
    """A required key or model name is missing. No model name is invented."""


class LLMJsonError(ValueError):
    """The model reply was not valid JSON."""


class ToolCall(BaseModel):
    id: str | None = None
    name: str
    arguments: str


class LLMResult(BaseModel):
    text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)


class LLMProvider(Protocol):
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        json_schema: dict | None = None,
    ) -> LLMResult: ...

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict: ...

    async def transcribe(self, audio: bytes) -> str: ...
