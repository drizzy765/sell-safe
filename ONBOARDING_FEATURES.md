# Sell-Safe — Onboarding & Seller Experience Features

> Goal: make it effortless for a Nigerian seller to put their business on Sell-Safe and add items — no typing product-by-product.
> UX principle: **skip anytime**. Instagram import is a shortcut, not a gate. Dashboard catalog is always available.
> Deadline: build by **Nov 3, 2026** (benchmark runs Nov 3–4, Meta submission due Nov 5, 02:00 WAT).
> Scope now: Features 1–3. Feature 4 (Meta Ads) is **LATER / backlog** — do not build now.

Agent instructions: log these into the project plan/TODO, keep existing architecture (Muse via Meta Model API, Instagram + WhatsApp webhooks, Supabase/DB, Jev decisions). Never commit `.env` or tokens. Update this file's checkboxes as you go.

---

## Feature 1 — Auto-filled "Confirm your shop" page (P0)

After the seller connects Instagram (already working):

- [x] Fetch from Instagram API: username, name, biography, profile_picture_url, account type/category, website, followers count, recent media (id, media_url, caption, timestamp, permalink).
- [x] Create `shops` record pre-filled with that data (shop name, handle, bio, logo, category). *(in-memory `ShopStore` for local/hackathon; Supabase migration later)*
- [x] Onboarding page `/onboarding/shop`: shows pre-filled fields; seller only edits + adds missing ones:
  - Business phone / WhatsApp number
  - Location / delivery areas (e.g. Lagos mainland/island)
  - Payment details for transfers (bank name, account name, account number) — mask account number in UI/logs
  - Languages for replies (English / Pidgin / Yoruba)
  - Opening hours, delivery fee / policy
  - **Business category dropdown** (Provisions, Fashion, Beauty, Electronics, Food, Services, Other + custom)
- [x] "Save & continue" → catalog setup (Feature 2), **or skip to dashboard** later from Feature 2/3.
- [x] Handle token expiry / disconnected account gracefully (reconnect button). Soft-fail when Graph returns `Unsupported request - method type: get` — seller can type shop name and continue.

Acceptance: connecting `@sellsafe.testshop.ng` lands on a page already showing "Mama Timi Provisions 🛒", its bio, logo and category (or blank name ready to fill if Graph profile is blocked).

---

## Feature 2 — Catalog import, multiple easy options (P0)

All options feed ONE pipeline: `source → images/text/video → Muse vision extraction (images) → draft products → seller review → publish`.  
Each shop gets **its own media + product slice** in the store (per-`shop_id` / seller namespace).

Draft product schema: `name, price_ngn, category, description, variants (size/qty), image_urls[], video_urls[], stock_status, source, source_ref, confidence`.

### Import options (build in this order)
- [x] **A. Import from Instagram posts (primary, P0).** List recent posts as a grid; seller ticks the product posts; Muse reads photo + caption → draft product (price parsed from caption like "₦9,500", "9.5k", "DM for price" → price = null, flagged). Soft-fail if Graph media is blocked — show upload / Drive / skip instead.
- [x] **B. Upload photos + videos (P0).** Multi-file upload from phone/laptop (images *and* videos). Images → Muse draft; videos stored on the shop media shelf for buyers / dashboard. All files land in **that seller’s** DB namespace.
- [x] **C. Paste a Google Drive link (P0).** Public Drive folder/file import via Drive API (`GOOGLE_DRIVE_API_KEY`); filenames like `Honey beans - NGN 6000.jpg` auto-draft + auto-approve into runtime catalog.
- [ ] **D. Send to WhatsApp (P1).** Seller sends product photos + captions to the Sell-Safe WhatsApp number with "add product" → drafts appear in dashboard.
- [ ] **E. CSV / Google Sheet upload (P2).** Template columns: name, price_ngn, category, description, image_url, stock. Provide a downloadable template.
- [x] **Skip Step 2.** Seller can skip import and manage catalog later on the dashboard (Feature 3).

### Review screen
- [x] Grid of draft cards with editable fields, confidence badge, "Approve / Edit / Delete", bulk approve.
- [x] Flag suspicious extractions (missing price, price outliers like ₦85,000 vs ₦8,500, duplicates).
- [x] Approved items become the catalog Sell-Safe uses when replying to buyers.

### Catalog MCP server (P1)
Expose catalog import so other agents (Claude/Cursor/Grok) can add products for a seller:
- Tools: `list_drive_media(folder_url)`, `import_from_drive(shop_id, file_ids)`, `import_from_instagram(shop_id, media_ids)`, `draft_products(image_urls)`, `list_drafts(shop_id)`, `approve_products(ids)`, `list_shop_media(shop_id)`.
- Drive tool pulls **images and videos** from a shared link into the shop’s media shelf, then optional draft extraction for images.
- Reuse the same pipeline; auth per shop with a scoped API key.

Acceptance: test shop imports ≥5 products from Instagram posts and ≥3 from photo upload, all approved and used in a buyer DM reply with correct prices. Sellers who skip Step 2 can still add catalog items from the dashboard.

---

## Feature 3 — Live dashboard v2 (IG Direct mirror) (P0)

Approved mockups: `sellsafe-dashboard-v2/mockups/` (inbox, catalog-home, approve-mode). Spec: `sellsafe-dashboard-v2/DASHBOARD_INBOX_PROMPT.md`.

Simplify: one `/dashboard` after connect/confirm with sidebar (Inbox · Catalog · Orders · Outreach · Settings).

- [x] Seller session via Instagram Login cookie → `/dashboard` (no separate email login for hackathon).
- [x] **Catalog home (P0):** IG-style product grid, stats, green Muse/AUTO pill, Add products menu (Instagram / upload / Drive), skip banner when Step 2 skipped.
- [x] **Live Instagram inbox (P0):** mirrors real DMs from webhook → `messages` only. Empty account → IG-style “No messages yet”. **No fake demo chats by default.**
- [x] **Reply modes (P0):** AUTO | APPROVE | SMART (Settings + thread pill). APPROVE → dashed draft bubble with Approve & send / Edit / Reject.
- [x] **Take over / hand back** per chat (pauses AI).
- [x] **Product card bubbles** + `send_image` when catalog returns an HTTP image URL.
- [~] **Receipt verdict pills** on payment screenshots (verify path exists; dashboard receipts still Settings demo-only until verdicts are queried).
- [x] **Stats strip:** chats today, orders, ₦ verified, fakes caught (real zeros when quiet — not demo filler).
- [x] **Demo mode:** Settings toggle only; labeled Demo; never replaces an empty real inbox.
- [ ] **Outreach (P1):** seller-picked one-at-a-time pitches → ig.me/m/… (after Nov 7 if needed).
- [ ] **Orders board (backlog):** after benchmark.

### UX shortcuts (must stay true)
1. Connect Instagram → Confirm shop → **optional** import → Dashboard.
2. From import page: **Skip to dashboard** always visible.
3. From dashboard Catalog: upload image/video or paste Drive link without redoing onboarding.
4. Never block on Instagram Graph media failures — offer upload / Drive / skip.

Acceptance (`@sellsafe.testshop.ng`):
1. No DMs → empty IG inbox (no fake chats).
2. DM “how much be honey beans?” → appears in seconds → AUTO replies with photo + ₦6,000 (after Drive/catalog approve).
3. Switch APPROVE → next reply is a draft; Approve sends to Instagram.
4. Fake receipt → Suspicious badge (verify path).
5. Pitch flow → P1.

---

## Feature 4 — Run Meta Ads from Sell-Safe (LATER / backlog — do NOT build now)

- Pick product → AI writes ad copy → set budget/location (e.g. ₦2,000/day, Lagos) → create "Click to Instagram Direct" ad so tappers land in DMs answered by Sell-Safe.
- Needs Marketing API `ads_management`, ad account + payment method, Meta App Review + business verification.
- Interim idea: "Boost this product" button that pre-fills copy and opens Meta Ads Manager.

---

## Build order & timeline
1. Nov 1–2: Feature 1 (+ category dropdown) + Feature 2A/2B + review + **skip to dashboard**.
2. Nov 2–3: Feature 3 dashboard (catalog section first, then demo inbox/receipts), Drive link + MCP media tools.
3. Nov 3: end-to-end test with `@sellsafe.testshop.ng`, record demo clips, freeze for benchmark.
4. After Nov 7: 2E CSV, MCP polish, Feature 4.

## Notes
- Required Instagram permissions: `instagram_business_basic`, `instagram_business_manage_messages` (already used), plus media read for post import.
- Keep secrets in `.env` only; redact bank/account numbers in logs.
- Per-seller isolation: all drafts, products, and uploaded media keyed by `shop_id` / Instagram account id.
