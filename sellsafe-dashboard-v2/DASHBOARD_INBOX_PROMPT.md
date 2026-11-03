# Prompt for Sell-Safe agent — Dashboard v2 (approved designs)

Update the plan (onboarding.md / ONBOARDING_FEATURES.md) and build the following. The seller APPROVED 3 mockups (docs/mockups/: inbox.jpg, catalog-home.jpg, approve-mode.jpg) — match them closely. Keep the existing stack (Muse via Meta Model API, Instagram + WhatsApp webhooks, Google Drive catalog MCP/import, DB + realtime). Never commit .env or tokens.

## 1. Inbox that MIRRORS the seller's real Instagram DMs (P0)
- Layout like Instagram Direct: left sidebar (Inbox, Catalog, Orders, Outreach, Settings); middle chat list (header @handle, tabs Primary/General/Requests, search, avatars, usernames, last-message preview, time, unread dots); right thread with IG-style bubbles (incoming grey, outgoing purple-blue gradient), read ticks, images, product cards.
- REAL data only: sync conversations/messages from the Instagram Messaging API + webhooks. Remove the fake inbox. If the account has no messages, show exactly an empty IG-style inbox ("No messages yet").
- Demo mode stays separate, labeled "Demo data" (toggle in Settings only).
- Product card bubble: catalog photo + name + ₦ price when Sell-Safe sends an item.
- Receipt verdict pill on payment screenshots (Verified / Suspicious: reason / Fake).
- Composer like IG + "Take over" (pause AI for that chat) / "Hand back to Sell-Safe".

## 2. Reply mode switch (P0)
Pill on the thread + Settings: `Sell-Safe · powered by Muse [AUTO | APPROVE | SMART]`, default AUTO, subtitle "AI is replying automatically".
- AUTO: replies immediately.
- APPROVE: replies become Drafts (dashed bubble: Approve & send / Edit / Reject). Email the seller "Sell-Safe: approve reply to <user>?" with customer msg + AI draft + Approve button (signed one-time link that sends) + "Edit in dashboard". Optional WhatsApp ping.
- SMART: auto for simple questions; approval required for discounts, payment confirmations, refunds, or orders above a seller-set ₦ threshold.
- Respect Meta's 24-hour window (warn, don't send outside it). Per-chat override + global default. Log every AI message with mode/approver.

## 3. Catalog home (P0)
- Header: logo, shop name, @handle · category, green "Sell-Safe on AUTO · powered by Muse" pill.
- Stats: chats today, orders, ₦ verified, fake receipts caught.
- IG-style product grid with name + ₦ price; search, filter, edit, stock toggle.
- "Add products" dropdown: From Instagram posts / Upload photos / Google Drive link / Send on WhatsApp / CSV.
- If onboarding step 2 skipped: banner "Catalog skipped? Add items anytime".

## 4. Sell from the catalog in DMs (P0)
When a buyer asks about an item, pick the matching catalog product and send photo + price in the DM (image + text). Never invent prices. Out-of-stock: say so and suggest alternatives.
Test with Drive folder "Sell-Safe Test Catalog - Mama Timi Provisions" (files "<Name> - NGN <price>.jpg" + catalog sheet).

## 5. Outreach: seller-picked, one at a time (P1)
No mass/automated cold DMs (Meta API only messages users who messaged first; cold DMs risk bans).
- Seller pastes an Instagram ad/post/profile link or handle → "Pitch this".
- Sell-Safe reads public info (bio, captions if accessible), drafts a short personal pitch in the seller's voice/language with 1–3 relevant catalog items (photos + prices).
- Seller edits → "Open in Instagram": open https://ig.me/m/<handle>, copy message + download images; seller sends manually.
- Outreach tab logs target, date, status (drafted / sent by seller / replied). Replies flow into Inbox and Sell-Safe handles them per reply mode.
- Soft limit ~10 pitches/day with spam warning.
- Also allowed: auto-reply to comments on the seller's own posts ("price?" → "DM sent 📩") + private-reply DM to the commenter.

## 6. Backlog (log only, after benchmark)
Orders board (inquiry → awaiting payment → paid & verified → delivered); Paystack payment links; abandoned-chat follow-ups within 24h; low-stock alerts/auto-hide; haggling rules (min price); weekly WhatsApp summary; Pidgin/Yoruba voice-note replies (Muse voice); Meta Ads from Sell-Safe (postponed).

## Acceptance tests (@sellsafe.testshop.ng)
1. Account with no DMs → empty IG-style inbox (no fake chats).
2. DM "how much be honey beans?" from a personal account → appears in seconds → AUTO replies with photo + ₦6,000 card.
3. Switch to APPROVE → next reply is a draft, email arrives, Approve sends it to Instagram.
4. Fake receipt → "Suspicious" badge.
5. Pitch flow → draft + opens ig.me/m/<handle>.

Timeline: 1–4 by Nov 3, freeze for benchmark Nov 3–4; 5 if time, else after Nov 7.

## Plan summary (implemented Nov 2)

See `docs/onboarding.md` + updated `ONBOARDING_FEATURES.md` Feature 3.
- Inbox: Graph `me/conversations` sync (past DMs) + webhooks (live); empty = “No messages yet”; demo = Settings toggle.
- Reply modes AUTO/APPROVE/SMART + take over; drafts approve/edit/reject in-thread.
- Catalog home matches mockup; Drive folder import with `Name - NGN price.jpg` + API key.
- Sell-from-catalog: approve publishes to runtime catalog; `send_image` for HTTP product photos.
- Outreach/Orders: nav placeholders (P1 / backlog).
