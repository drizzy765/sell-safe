# GitHub Rules
Repo: `drizzy765/sell-safe` (public at submission; check no secrets in history before flipping visibility).

## Branching
- `main` always deployable; protected (PR + green CI required, even solo).
- `feat/<short-name>`, `fix/<short-name>`, `docs/…`, `chore/…`. Short-lived (≤1 day).
- Tag `v0.1-demo` at feature freeze (Nov 2), `v1.0-submission` on Nov 4.

## Commits (Conventional Commits)
`feat(verification): add duplicate reference rule` · `fix(whatsapp): verify signature on raw body` · `docs:` `test:` `chore:` `refactor:`. Imperative, ≤72 chars subject.

## PR checklist
- [ ] Scope is one feature/fix
- [ ] Tests added/updated; `pytest` passes
- [ ] `ruff check` + `ruff format --check` pass
- [ ] No secrets, `.env`, real phone numbers or real receipts in diff
- [ ] New env vars added to `.env.example`
- [ ] Docs updated if behaviour changed
- [ ] Demo clip saved if user-visible

## CI (`.github/workflows/ci.yml`)
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check . && ruff format --check .
      - run: pytest -q -m "not live"
  secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
```
Dashboard (if built): `npm ci && npm run lint && npm run build` job.

## Secrets policy
- Never commit `.env`, keys, tokens, service-role keys. Use `.env.example` (names only).
- Store secrets in Render/Railway/Vercel env settings and GitHub Actions secrets.
- Never paste keys into issues, PRs, chats or AI tools. Rotate immediately if leaked.
- Use test-mode keys only (Paystack `sk_test_…`) during the hackathon.
- Pre-commit: `gitleaks protect --staged`.

## .gitignore essentials
```
.env
.env.*
!.env.example
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
node_modules/
.next/
.vercel/
evals/data/private/
demo/raw/
*.log
.DS_Store
supabase/.temp/
```
