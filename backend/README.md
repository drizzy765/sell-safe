# backend

FastAPI service (Python 3.11). Entry point is `app.main:app` (`GET /health`, Meta verify, WhatsApp echo).

From the repo root, with `PYTHONPATH=backend`:

```bash
uvicorn app.main:app --reload --port 8000
```

See `docs/architecture.md`.
