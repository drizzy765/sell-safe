# Messenger steps (stretch; all TODO verify against Meta's Messenger Platform docs)
**Prerequisites:** A Facebook Page where you are an admin and the Meta app.
1. **Add the Messenger product** to your Meta app.
2. **Connect your Page** and generate a Page access token.
3. **Set the webhook:** `https://<your-sell-safe-host>/webhooks/messenger`, same verify token.
4. **Subscribe the Page** to the app with the `messages` and `messaging_postbacks` fields. TODO verify.
5. **Message your Page** from a tester account (add testers under App roles while in development mode).
6. **Check connection.**
