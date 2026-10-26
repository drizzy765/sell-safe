"""Turn a product photo into catalog fields. The seller still confirms the price."""

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMJsonError, LLMProvider

CATALOG_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "suggested_price_kobo": {"type": ["integer", "null"]},
        "category": {"type": "string"},
        "colors": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
    "required": [
        "name",
        "description",
        "suggested_price_kobo",
        "category",
        "colors",
        "confidence",
    ],
}

_PROMPT = (
    "Extract the product in this photo. Return JSON with name, description, "
    "suggested_price_kobo (integer kobo or null), category, colors, and confidence. "
    "Do not invent a price if you cannot see one."
)


class CatalogExtraction(BaseModel):
    name: str
    description: str
    suggested_price_kobo: int | None
    category: str
    colors: list[str]
    confidence: float


class AskSeller:
    """Vision did not return usable JSON. Ask the seller to type the listing."""


async def extract_catalog(provider: LLMProvider, image: bytes) -> CatalogExtraction | AskSeller:
    try:
        return await _once(provider, image, _PROMPT)
    except (LLMJsonError, ValidationError) as exc:
        retry_prompt = f"{_PROMPT}\n\nThe previous output was invalid: {exc}"
        try:
            return await _once(provider, image, retry_prompt)
        except (LLMJsonError, ValidationError):
            return AskSeller()


async def _once(provider: LLMProvider, image: bytes, prompt: str) -> CatalogExtraction:
    payload = await provider.vision(image, prompt, CATALOG_SCHEMA)
    return CatalogExtraction.model_validate(payload)
