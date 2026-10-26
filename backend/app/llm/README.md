# backend/app/llm

`LLMProvider` is `chat` and `vision` only. Speech is Intron Sahara (`docs/architecture.md`), not this package.

- `meta`: Meta Model API, `POST {META_API_BASE_URL}/chat/completions`. Official base `https://api.meta.ai/v1` as of 2026-10-26. Muse Spark for text and tools, Muse vision for images. Exact ids are **TODO verify**.
- `groq`: temporary dev fallback at `https://api.groq.com/openai/v1`. Not the model the hackathon claim uses.

Model names come from env only.
