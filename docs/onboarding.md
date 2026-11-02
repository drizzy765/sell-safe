# Onboarding & dashboard plan

Canonical feature checklist: [`ONBOARDING_FEATURES.md`](../ONBOARDING_FEATURES.md).

Dashboard v2 (approved mockups + acceptance tests): [`sellsafe-dashboard-v2/DASHBOARD_INBOX_PROMPT.md`](../sellsafe-dashboard-v2/DASHBOARD_INBOX_PROMPT.md).

## Plan changes (Dashboard v2, Nov 2)

1. **Inbox is real Instagram only.** Dashboard loads past DMs via Graph `me/conversations` (session token) and merges live webhook rows. Empty connected account shows Instagram-style “No messages yet”. Demo data is a Settings toggle and is labeled.
2. **Reply modes AUTO / APPROVE / SMART** are P0 (not backlog). APPROVE drafts appear as dashed bubbles in the thread; Approve & send uses the Messaging API.
3. **Drive folder catalog is P0.** Import uses Drive API + `GOOGLE_DRIVE_API_KEY` and the filename convention `<Name> - NGN <price>.jpg` (test folder: Sell-Safe Test Catalog - Mama Timi Provisions). Matching files auto-approve into the runtime catalog used by buyer DMs.
4. **Catalog home + IG Direct layout** match the approved mockups (sidebar, product grid, Muse/AUTO pill).
5. **Outreach / Orders** stay P1 / post-benchmark; nav placeholders only.
6. Timeline unchanged: P0 items 1–4 by Nov 3; freeze Nov 3–4.

## Env for testing

- `INSTAGRAM_ACCOUNT_ID` must match the Instagram Login account id so webhook seller_id aligns with onboarding catalog.
- `INSTAGRAM_ACCESS_TOKEN` (or Page token) for outbound sends.
- `GOOGLE_DRIVE_API_KEY` for public folder import; folder must be “Anyone with the link”.
