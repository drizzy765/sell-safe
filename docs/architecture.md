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
  AG --> LLM[LLMProvider<br/>Meta Llama / Groq]
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
```python
class LLMProvider(Protocol):
    async def chat(self, messages, tools=None, json_schema=None) -> LLMResult: ...
    async def vision(self, image: bytes, prompt: str, json_schema) -> dict: ...
    async def transcribe(self, audio: bytes) -> str: ...
```
- `groq`: OpenAI-compatible `https://api.groq.com/openai/v1`, Llama models (+ Whisper for transcription).
- `meta`: Meta Model API (dev.meta.ai). **TODO verify** base URL, model names, vision + tool-calling support from official docs before switching; config via `META_API_BASE_URL`, `META_TEXT_MODEL`, `META_VISION_MODEL`.
- If Meta lacks transcription, keep Groq Whisper for audio only and note it in the write-up.

## Sequence: buyer order
```mermaid
sequenceDiagram
  participant B as Buyer
  participant WA as WhatsApp
  participant API as Sell-Safe API
  participant J as Jev
  participant L as Llama
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
  participant L as Llama Vision
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
