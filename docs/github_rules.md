# GitHub Rules
Repo: `drizzy765/sell-safe` (public at submission; check no secrets in history before flipping visibility).

## Branching
- `main` always deployable. No direct pushes, no force-push, no deleting the branch.
- Work lands through a pull request from `feat/<short-name>`, `fix/<short-name>`, `docs/…`, or `chore/…`. Short-lived (≤1 day).
- Phase 1 (health, schema, WhatsApp verify + echo) uses **`feat/foundation`**, cut from current `main`. Do not commit that work on `main`.
- Tag `v0.1-demo` at feature freeze (Nov 2), `v1.0-submission` on Nov 4.

## Protecting `main`
The repo is private today. On GitHub Free, branch protection applies to **public** repositories. Private repositories need GitHub Pro. Make the repo public only after the `secrets` check is green (gitleaks on full history). The hackathon submission wants a public repo anyway.

Required status checks are the workflow job names: **`test`** and **`secrets`**. GitHub only offers a check in the protection UI after it has run at least once, so turn protection on after the first green run on `feat/foundation`, before merging.

Settings → Branches → Add branch protection rule (or Rules → Rulesets, same gates):

1. Branch name pattern: `main`.
2. Require a pull request before merging. Required approvals: **0** (solo; the author cannot approve their own PR, so do not set this to 1).
3. Require status checks to pass: `test`, `secrets`. Require branches to be up to date before merging.
4. Do not allow bypassing the above settings (include administrators).
5. Block force pushes. Block deletions.
6. Leave "Allow specified actors to bypass" empty.

After that, `git push origin main` is rejected. Merge only the green PR.

Bootstrap order for this change:

1. `git switch -c feat/foundation` from `main`.
2. Commit and `git push -u origin feat/foundation`. Pushing runs CI (`on: push`). Open the PR so `on: pull_request` is recorded too.
3. Wait until `test` and `secrets` are green. If `secrets` fails, rotate the leaked value and scrub history before any public switch.
4. Make the repository public, then add the protection rule above.
5. Merge the PR on GitHub. Do not merge locally and push `main`.

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
permissions:
  contents: read
  pull-requests: read
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
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
The checked-in workflow matches this. Ruff and pytest read `pyproject.toml` (Python 3.11, `pytest -q -m "not live"`, docs left out of the formatter). Job names `test` and `secrets` are the required checks in branch protection. A web job (`npm ci && npm run lint && npm run build`) is added only when the onboarding site exists.

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
