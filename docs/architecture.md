# Architecture / System Design

## Components
```mermaid
flowchart LR
  WA[WhatsApp Cloud API] --> GW
  IG[Instagram Messaging] --> GW
  FB[Messenger] --> GW
  GW[Channel Adapters<br/>/webhooks/*] --> Q[Message Router]
  Q --> JEV[Jev: intent, language, scam]
  Q --> AG[Agent Orchestrator]
  AG --> LLM[LLMProvider<br/>Muse / Groq fallback]
  AG --> SP[Intron Sahara<br/>STT + TTS]
  AG --> TOOLS[Tools: catalog, orders, verify]
  TOOLS --> DB[(Supabase Postgres)]
  TOOLS --> ST[(Supabase Storage)]
  TOOLS --> VER[Verification Engine]
  PS[Paystack/Flutterwave webhooks] --> VER
  ALERT[Forwarded bank alerts] --> VER
  CH[RefPay / chain RPC] --> VER
  VER --> JEV
  SCH[Scheduler: reminders, daily summary] --> GW
  DASH[Next.js dashboard] --> DB
```

## Layout
```
app/
  main.py               FastAPI app, routers
  channels/             base.py (ChannelAdapter), whatsapp.py, instagram.py, messenger.py
  llm/                  base.py (LLMProvider), meta.py, groq.py
  jev/                  client.py, questions.py
  agent/                orchestrator.py, tools.py, prompts/{en,pcm,yo}.md
  verification/         extract.py, rules.py, matchers.py, verdict.py
  payments/             paystack.py, flutterwave.py, mono.py, refpay.py, alerts.py
  db/                   models.py, repo.py
  jobs/                 reminders.py, daily_summary.py
migrations/  tests/  evals/  demo/  dashboard/ (Next.js, optional)
```

## Channel adapter
```python
class ChannelAdapter(Protocol):
    name: Literal["whatsapp","instagram","messenger"]
    def verify_signature(self, raw: bytes, headers) -> bool: ...
    def parse(self, payload: dict) -> list[InboundMessage]: ...   # normalized
    async def send_text(self, to: str, text: str) -> str: ...
    async def send_image(self, to: str, url: str, caption: str) -> str: ...
    async def fetch_media(self, media_id: str) -> bytes: ...
```
`InboundMessage(channel, external_id, sender_id, seller_id, type[text|image|audio], text, media_id, ts)`. All three channels use Meta Graph webhooks with `X-Hub-Signature-256` (HMAC-SHA256 with app secret).

## LLM provider abstraction
Speech does not go through this protocol. See Speech below.
```python
class LLMProvider(Protocol):
    async def chat(self, messages, tools=None, json_schema=None) -> LLMResult: ...
    async def vision(self, image: bytes, prompt: str, json_schema) -> dict: ...
```
- `meta` (hackathon target): Meta Model API, base `https://api.meta.ai/v1` (checked 2026-10-26). Muse Spark series for text and tool calls. Muse vision for images. Muse Image and SAM 3.1 are the image-generation and segmentation models when those calls are added. Exact model ids are **TODO verify**. Env: `META_API_KEY`, `META_API_BASE_URL`, `META_TEXT_MODEL`, `META_VISION_MODEL`.
- `groq`: temporary dev fallback only, behind `LLM_PROVIDER`. OpenAI-compatible `https://api.groq.com/openai/v1`. Used when Meta credits are not available, and as the one-shot timeout fallback when both are configured. It is not the model the write-up claims. Exact fallback ids are **TODO verify**.

## Speech (Intron Sahara v2.5)
Buyer voice notes and voice replies use Intron, not the LLM provider. Key: `INTRON_API_KEY` (Bearer). Model name in this design is Sahara v2.5; **TODO verify** the id the API expects if a request takes one.

**STT.** Language codes from the [supported-languages](https://docs.voice.intron.io/docs/stt/supported-languages) page (checked 2026-10-26): Yoruba-English `yo` and Pidgin-English `pcm` are code-switched; English `en` too. Igbo-English `ig` and Hausa-English `ha` are stretch. The transcribe URL is **TODO verify** against the STT reference before wiring. Store the transcript, language code, and ASR confidence on `messages` (confidence stays null if the response has no score; field name **TODO verify**).

**TTS.** `POST https://infer.voice.intron.io/tts/v1/generate` with `Authorization: Bearer`. JSON fields: `text`, `voice_language`, `voice_accent`, `voice_gender` (`male`/`female`), optional `output_audio_format` `wav` (default) or `opus`. Max 4096 characters. 30 requests/minute. A 503 after the long poll window includes a text id; poll [TTS status](https://docs.voice.intron.io/docs/tts/tts-status) instead of sending a second generate. Spec: [TTS generate](https://docs.voice.intron.io/docs/tts/tts-generate).

The [accents page](https://docs.voice.intron.io/docs/tts/supported-languages-and-accents) lists Yoruba (`yo` / accent `yoruba`) and Pidgin (`pcm` / accent `pidgin`), plus English with a `yoruba` accent (checked 2026-10-26). A live call still has to confirm those voices (**TODO verify**). If `yo` or `pcm` is rejected, speak the same reply as English with `voice_language=en` and `voice_accent=yoruba`. Money and verdict lines are still the fixed templates; TTS only reads that text. Voice replies are on the cut list. STT is not.

## Sequence: buyer order
```mermaid
sequenceDiagram
  participant B as Buyer
  participant WA as WhatsApp
  participant API as Sell-Safe API
  participant J as Jev
  participant L as Muse Spark
  participant DB as Supabase
  B->>WA: "Abeg how much for the black bag?"
  WA->>API: POST /webhooks/whatsapp
  API->>API: verify signature, dedupe message id
  API->>J: intent + language
  J-->>API: price_question (0.95), pcm (0.92)
  API->>L: chat + tools
  L->>DB: search_catalog("black bag")
  L-->>API: reply in Pidgin with price
  API->>WA: send reply
  B->>WA: "I go take 1"
  API->>L: create_order tool
  L->>DB: insert order (awaiting_payment) + assign virtual account
  API->>WA: account details + order ref SS-1042
```

## Sequence: payment verification
```mermaid
sequenceDiagram
  participant B as Buyer
  participant API as Sell-Safe API
  participant L as Muse vision
  participant V as Verification Engine
  participant PS as Paystack
  participant J as Jev
  participant S as Seller
  B->>API: transfer screenshot
  API->>L: extract fields (JSON)
  L-->>API: amount, ref, sender, bank, time
  API->>V: verify(order, extraction)
  V->>V: rule checks + fraud_signals lookup
  V->>V: match against evidence (webhook/alert/chain)
  PS-->>API: charge.success webhook (may arrive before/after)
  V->>J: tamper? match? (probabilities)
  J-->>V: p_match, p_tamper
  V-->>API: verdict CONFIRMED / NOT FOUND / SUSPICIOUS + confidence
  API->>S: verdict card + "release / don't release goods"
  API->>B: polite status message
```

## Deployment
- API: Render or Railway (single web service + cron for jobs). Health check `/health`.
- DB/Storage: Supabase cloud. Private bucket `media/`, signed URLs only.
- Dashboard: Vercel (reads via Supabase anon key + RLS, seller-scoped).
- Local: `uvicorn` + `ngrok http 8000`.
- Secrets: platform env vars only.
