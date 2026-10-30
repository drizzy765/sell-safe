# Meta platforms

Sell-Safe's Meta app is named **Sell-Safe**. Read `META_APP_ID` from `.env`. The app is in **Development** (`published: false`).

**Current status (Oct 30, 2026):**
- ❌ **WhatsApp:** Blocked (error 131031, business account locked)
- ✅ **Instagram:** Working via Instagram Login

**Strategy:** Instagram-first. WhatsApp waitlist captures phone numbers for notification when unblocked.

---

## WhatsApp Status: BLOCKED

**Error 131031:** Business Account locked. The WhatsApp Manager shows "Account restricted" and requires business verification documents. As a hackathon project without formal business registration, we cannot complete this verification.

**Impact:**
- Cannot send WhatsApp messages via API
- Cannot create new test sends
- The lock is on the Meta business account, not the personal handset

**Mitigation:**
- Pivoted to Instagram as primary channel
- Built WhatsApp waitlist to capture demand
- When unblocked, will notify sellers via WhatsApp with one-tap connect link

**Technical details:**
- Test number (`+1 555...`) shows `status: failed`, error **131031**
- `whatsapp_biz_verify_business` reports `is_verified: false`
- Business profile incomplete, requires document upload
- OAuthException **190** on token refresh (token expired)

**Do not attempt:**
- New WhatsApp test sends (extends the lock)
- Business verification document upload (no formal business exists)
- Creating new Pages (rate-limited, blocked)

---

## Instagram Status: WORKING

**Instagram Login** does not require a Facebook Page. This is our live path.

**Setup complete:**
- Account `sellsafe000` converted to Business professional account
- Added as Instagram Tester on Sell-Safe app
- **API setup with Instagram login** completed
- `.env` has `INSTAGRAM_ACCOUNT_ID` and `INSTAGRAM_ACCESS_TOKEN`
- Webhook subscription **On** for messages
- Webhook callback: `https://<APP_BASE_URL>/webhooks/instagram`
- `GET /webhooks/instagram` returns 200 for verify handshake
- `POST /webhooks/instagram` receives messages

**Verified:**
- `GET https://graph.instagram.com/{version}/me` returns 200 with username `sellsafe000`
- Profile check successful
- One real DM received and processed (returned 500 because Supabase empty, now using in-memory stores for local dev)

**For sellers:**
- Connect via "Connect Instagram" button (one-click OAuth)
- No technical setup required
- No Page creation needed
- Works immediately in Development mode

---

## Facebook Page Status: BLOCKED

**Error:** "Cannot create Page: You have made too many attempts to create a Page recently."

**Impact:**
- Cannot create new Pages
- Messenger requires a Page (cannot proceed)
- More attempts extend the block

**Mitigation:**
- Instagram Login does not need a Page
- Skip Messenger for this release
- Leave `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` empty in `.env`

---

## MCP Servers

Two remote MCP servers exist:

1. **Meta Social Technologies** (`https://mcp.facebook.com/devtools`)
   - Tools: `devtools_*`
   - Status: Working in Cursor

2. **WhatsApp Business Tools** (`https://mcp.facebook.com/whatsapp_business_tools`)
   - Tools: `whatsapp_biz_*`
   - Status: Working in Muse Code

The other server in each client failed OAuth with `Dynamic registration is not available for this client`. This is a Meta-side limitation. Leave the failed server alone.

**Capabilities:**
- `devtools_purge_webhook` — clear webhook subscriptions
- `devtools_get_webhooks` — list webhook subscriptions
- `whatsapp_biz_verify_business` — check verification status (returns `is_verified: false`)

**Cannot do:**
- Grant verification (requires human review)
- See Page ID or Instagram ID
- See or set tokens
- Create Pages

---

## Environment Variables

**Set and working:**
- `INSTAGRAM_ACCOUNT_ID`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_APP_SECRET` (from Instagram Login screen, different from `META_APP_SECRET`)

**Set but not working:**
- `WHATSAPP_PHONE_NUMBER_ID` (blocked)
- `WHATSAPP_BUSINESS_ACCOUNT_ID` (blocked)
- `WHATSAPP_ACCESS_TOKEN` (expired)

**Empty:**
- `FB_PAGE_ID` (cannot create Page)
- `FB_PAGE_ACCESS_TOKEN` (no Page)

**Both:**
- `META_APP_ID`
- `META_APP_SECRET`
- `META_VERIFY_TOKEN`
- `GRAPH_API_VERSION`

---

## Architecture Decision

**Instagram-first, WhatsApp waitlist.**

Given the blockers:
1. Build and ship with Instagram (working)
2. Capture WhatsApp demand via waitlist (phone numbers)
3. When Meta unblocks or business verification completes:
   - Message waitlist via WhatsApp with one-tap connect link
   - Enable WhatsApp as second channel
   - Keep Instagram as primary (it's working well)

**Simplified onboarding:**
- One "Connect Instagram" button (OAuth)
- No technical Meta setup visible to sellers
- Advanced flow hidden behind "Developer setup" link
- Technical steps moved to documentation only

---

## Original Notes (Preserved)

Two remote MCP servers exist. Use whichever one is connected in the current client. Cursor reached **Meta Social Technologies** (`https://mcp.facebook.com/devtools`, tools `devtools_*`) and Muse Code reached **WhatsApp Business Tools** (`https://mcp.facebook.com/whatsapp_business_tools`, tools `whatsapp_biz_*`). The other server in each client failed OAuth with `Dynamic registration is not available for this client`. That gate is on Meta's side. Leave the failed server alone.

Checked 2026-10-29, later the same day.

### WhatsApp is locked (detailed notes)

Sends from API setup show success, then the `messages` webhook reports `status: failed`, error **131031**, title **Business Account locked**. The recipient `wa_id` was a real WhatsApp user, so this failure is the sender account, not a missing allow-list entry and not the personal handset.

WhatsApp Manager shows **Account restricted** and sends the owner to **Security Centre**. Security Centre says it cannot find a business named sell-safe and asks for a document in that legal name. This project is a hackathon. There is no such document. Business Support Home lists no advertising issues and no support case, so that page has no **Request review** control for this lock.

`whatsapp_biz_verify_business` reports `is_verified: false` and returns a Security Centre link. The business profile is incomplete (`profile_complete: false`, `prerequisites_met: true`). One hidden test account and one hidden public test number exist. The MCP verify and publish tools only report status and links. They cannot grant verification.

Another personal WhatsApp number does not clear **131031**. The lock sits on the test sender (`+1 555…`), not on the handset.

**Human WhatsApp path, when a live send is needed again**

1. Open `https://developers.facebook.com/apps/<META_APP_ID>/use_cases/customize/api-testing-v2/` (**Step 1. Try it out**). **From** stays the `+1 555` test number. **Recipient** must be the owner's own number, Nigeria `+234`, national number with the leading `0` removed, and the verification code entered so the row is checked.
2. Send once from that page. The WhatsApp MCP send tool does not send from a test number.
3. Expand the newest `messages` webhook row. Done means `status` is `delivered` or `read`. `failed` plus `131031` means the lock is unchanged. Stop sending.
4. **Step 2. Production setup** (webhooks) waits until `APP_BASE_URL` is a public `https` origin. Callback path is `/webhooks/meta`. Verify token is `META_VERIFY_TOKEN`.
5. **Step 3. Business verification** is for a later registered business. Leave the document upload empty.

`.env` already has `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, `META_VERIFY_TOKEN`, and `GRAPH_API_VERSION`. A Graph GET with the stored `WHATSAPP_ACCESS_TOKEN` returned **401** OAuthException **190**. That token is expired. Replacing it does not clear **131031**. Leave the WhatsApp values unchanged. Send no further WhatsApp test.

The WhatsApp MCP server has no use-case manage tool. It cannot see a Page id, an Instagram id, or a token. A second pass wrote nothing to `.env`.

### Facebook Page creation is blocked

The owner and a friend both get **Cannot create Page: You have made too many attempts to create a Page recently.** Stop creating Pages. More attempts extend the block.

Messenger and **API setup with Facebook login** need that Page. Both wait. Leave `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` empty.

The three use cases are already on the Sell-Safe app: WhatsApp, **Manage messaging & content on Instagram**, and Messenger. Create no second app.

### Instagram Login is the live path (detailed notes)

The owner switched their existing Instagram to a **Business** professional account. That is the account to connect. A new Instagram is not required.

**Instagram API with Instagram Login** does not need a Facebook Page. **API setup with Facebook login** does. Use only the Instagram Login screen. Messaging is supported. In Development, only an Instagram account with a role on the app can message it.

Human path is done for credential storage. Instagram **sellsafe000** is an Instagram Tester on the Sell-Safe app. **API setup with Instagram login** lists that account. Local `.env` has `INSTAGRAM_ACCOUNT_ID` and `INSTAGRAM_ACCESS_TOKEN`. Leave `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` empty. The owner turned the **sellsafe000** webhook subscription **On** on the Generate access tokens row. The Instagram Login webhook callback is `https://<APP_BASE_URL>/webhooks/instagram` with verify token `META_VERIFY_TOKEN`. On 2026-10-29 Meta's verify handshake to that path returned 200, and the owner published the app. `GET` answers `hub.challenge` and `POST` receives events. The current `APP_BASE_URL` is a temporary tunnel and dies when that process stops. A real DM had not arrived as a `POST` before publish. After publish, `POST /webhooks/instagram` arrived and returned 500 because Supabase is empty. With Supabase unset, the webhook now uses the in-memory stores so a local reply can be sent. Those rows disappear when the app restarts. App Review stays off.

`Settings` reads `instagram_account_id`, `instagram_access_token`, and `instagram_app_secret`. `send_text` uses `POST https://graph.instagram.com/{GRAPH_API_VERSION}/me/messages` with `INSTAGRAM_ACCESS_TOKEN` when that token is set, body `{"recipient": {"id": ...}, "message": {"text": ...}}` (UTF-8, 1000 bytes max); the `graph.facebook.com` Page send stays as the fallback for when only `FB_PAGE_ACCESS_TOKEN` is set. Webhook signatures verify with `INSTAGRAM_APP_SECRET` when set, else `META_APP_SECRET`. `INSTAGRAM_APP_SECRET` comes from the Instagram Login screen and is not `META_APP_SECRET`.

Checked 2026-10-29. `GET https://graph.instagram.com/{GRAPH_API_VERSION}/me` with `INSTAGRAM_ACCESS_TOKEN` returned **200**. Username was `sellsafe000`. The `id` field on that response is the app-scoped id and must not replace `INSTAGRAM_ACCOUNT_ID`. The professional account id is the `user_id` field, which is the value already copied from **API setup with Instagram login**. The dashboard token is live. A one-hour token is only what the business-login code exchange returns before the server-side exchange. That secret is the Instagram app secret on the Instagram Login screen, not `META_APP_SECRET`.

The same check sent one `hello_world` template to the owner's WhatsApp number. Graph returned **401** / error **190**. `WHATSAPP_ACCESS_TOKEN` is expired. Do not send again. A new token does not clear **131031**.

## Phase: Instagram Login

Do this in Muse Code with `whatsapp_business_tools` if a tool can see Instagram Login. Otherwise return the human path above and stop.

1. Confirm the Sell-Safe app and that Instagram Login is available without a Page. Done when the tool says which setup screen to open, or that no Instagram tool exists.
2. `INSTAGRAM_ACCOUNT_ID` and `INSTAGRAM_ACCESS_TOKEN` are already in local `.env`. The profile check succeeded. Do not generate another Instagram token, and do not replace `INSTAGRAM_ACCOUNT_ID` with the `/me` `id` field. Done when those two names are reported as set and the values stay out of the reply.
3. Skip Page creation, Messenger, WhatsApp sends, webhooks, and business-document upload. The WhatsApp token is expired (**190**). Done when those Meta settings are unchanged.

Report `.env` names filled and names still empty. Keep secret values out of the reply.
