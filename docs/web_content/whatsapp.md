# WhatsApp steps (all TODO verify against Meta's current WhatsApp Cloud API docs)
**Prerequisites:** Facebook account, a phone for testing, ~15 min.
1. **Create a Meta app** at developers.facebook.com → My Apps → Create App → type "Business". TODO verify the current app-type names.
2. **Add the WhatsApp product** to the app. Meta gives you a free **test phone number** and a temporary access token.
3. **Add test recipients:** add your buyer test phones under the API setup page (the test number can only message registered recipients). TODO verify the limit.
4. **Copy IDs** into Sell-Safe settings: Phone Number ID, WhatsApp Business Account ID. (Code block with copy button; the token is never shown on the site.)
5. **Set the webhook:** Callback URL `https://<your-sell-safe-host>/webhooks/whatsapp`, Verify token = the value you set as `META_VERIFY_TOKEN`. Click Verify and save.
6. **Subscribe to the `messages` field.**
7. **Send "hi" from a test phone** → click **Check connection** on the site.
8. Later: create a permanent system-user token and add a real number. TODO verify.
