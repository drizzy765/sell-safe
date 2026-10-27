# Rule: CLI-Anything, skills, and MCPs

Use these when they clearly help a sell-safe task. Do not install Hub CLIs prophylactically.

## CLI-Anything

- **Generator** (wrap a GUI app into an agent CLI): Cursor plugin at `~/.cursor/plugins/local/cli-anything`. Prefer `/cli-anything`, `/cli-anything-refine`, `/cli-anything-test`, `/cli-anything-validate`, `/cli-anything-list`. Methodology: `{PLUGIN_ROOT}/references/HARNESS.md`.
- **Consumer** (use published CLIs): `cli-hub search|list|info|install`, then `cli-anything-<name> --json …`. Meta-skill: `cli-hub-meta-skill`. Scope installs (`--capability` / `--dry-run`); never bulk-install a matrix for one need.
- Likely later needs: `drawio`/`mermaid` (architecture), `shotcut`/`openscreen`/`videocaptioner` (demo video), `gimp`/`inkscape` (assets). Core FastAPI/WhatsApp work stays in-repo — do not invent a harness for that.

## Prefer these skills (when the task matches)

- Engineering: `tdd` / `test-driven-development`, `pr`, `code-review`, `diagnosing-bugs`, `security-and-hardening`, `shipping-and-launch`, `research`, `domain-modeling`
- Product/ops: `shipping-and-launch`, `observability-and-instrumentation`
- Media/fraud adjacent: `resemble-detect` only if explicitly checking synthetic media
- UI (onboarding/dashboard): `frontend-ui-engineering`, `make-interfaces-feel-better`, shadcn skill/MCP

## MCPs in this workspace

| MCP | Status | Use for |
| --- | --- | --- |
| `github` | ready | PRs, issues, checks |
| `websearch` | ready | Live docs / Meta / Paystack / Intron |
| `plugin-gmail-gmail` | ready | Bank-alert email flows (no secrets in logs) |
| `plugin-shadcn-shadcn` | ready | Onboarding/dashboard components |
| `memory` | ready | Persist durable project prefs |
| `sequential-thinking` | ready | Hard multi-step design only |
| `supabase` | needsAuth | Schema/migrations/RLS — authenticate before use |
| Notion / Drive / X / Mobbin / Refero / Outlook | needsAuth | Only after user authenticates |

Authenticate an MCP with its `mcp_auth` tool when a task actually needs it; do not auth everything up front.
