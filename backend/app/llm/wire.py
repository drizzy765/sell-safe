"""OpenAI-compatible chat request and response mapping. Shared by Groq and Meta."""

import base64
import json

from app.llm.base import LLMJsonError, LLMResult, ToolCall


def chat_payload(
    model: str,
    messages: list[dict],
    tools: list[dict] | None,
    json_schema: dict | None,
    *,
    tool_choice_auto: bool = False,
) -> dict:
    body: dict = {"model": model, "messages": messages}
    if tools:
        body["tools"] = tools
        if tool_choice_auto:
            body["tool_choice"] = "auto"
    if json_schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "response", "strict": True, "schema": json_schema},
        }
    return body


def vision_messages(prompt: str, image: bytes) -> list[dict]:
    encoded = base64.b64encode(image).decode("ascii")
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
            ],
        }
    ]


def parse_chat_response(payload: dict) -> LLMResult:
    message = payload["choices"][0]["message"]
    calls: list[ToolCall] = []
    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        calls.append(
            ToolCall(
                id=call.get("id"),
                name=str(function.get("name") or ""),
                arguments=str(function.get("arguments") or ""),
            )
        )
    content = message.get("content") or ""
    return LLMResult(text=str(content), tool_calls=calls)


def parse_json_content(text: str) -> dict:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMJsonError(str(exc)) from exc
    if not isinstance(value, dict):
        raise LLMJsonError("vision JSON must be an object")
    return value
