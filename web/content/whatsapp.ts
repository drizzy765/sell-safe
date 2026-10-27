import type { PlatformGuide } from "./types";

export const whatsappGuide: PlatformGuide = {
  id: "whatsapp",
  label: "WhatsApp",
  accent: "#25D366",
  prerequisites: [
    "Facebook account",
    "A phone for testing",
    "About 15 minutes",
  ],
  steps: [
    {
      title: "Create a Meta app",
      blocks: [
        {
          type: "text",
          body: 'Go to developers.facebook.com → My Apps → Create App → type "Business". TODO verify the current app-type names.',
        },
      ],
    },
    {
      title: "Add the WhatsApp product",
      blocks: [
        {
          type: "text",
          body: "Meta gives you a free test phone number and a temporary access token.",
        },
      ],
    },
    {
      title: "Add test recipients",
      blocks: [
        {
          type: "text",
          body: "Add your buyer test phones under the API setup page (the test number can only message registered recipients). TODO verify the limit.",
        },
      ],
    },
    {
      title: "Copy IDs into Sell-Safe settings",
      blocks: [
        {
          type: "text",
          body: "Phone Number ID and WhatsApp Business Account ID. The access token is never shown on this site.",
        },
        {
          type: "code",
          label: "Phone Number ID",
          value: "YOUR_WHATSAPP_PHONE_NUMBER_ID",
        },
        {
          type: "code",
          label: "Access token (masked)",
          value: "EAAB••••••••••••••••",
          secret: true,
        },
      ],
    },
    {
      title: "Set the webhook",
      blocks: [
        {
          type: "text",
          body: "Callback URL and verify token. Click Verify and save.",
        },
        {
          type: "code",
          label: "Callback URL",
          value: "https://<your-sell-safe-host>/webhooks/whatsapp",
        },
        {
          type: "code",
          label: "Verify token",
          value: "META_VERIFY_TOKEN",
          secret: true,
        },
      ],
    },
    {
      title: "Subscribe to messages",
      blocks: [
        {
          type: "text",
          body: "Subscribe to the `messages` field on the webhook.",
        },
      ],
    },
    {
      title: "Send a test message",
      blocks: [
        {
          type: "text",
          body: 'Send "hi" from a test phone, then confirm the connection in Sell-Safe.',
        },
      ],
    },
    {
      title: "Go permanent later",
      blocks: [
        {
          type: "text",
          body: "Create a permanent system-user token and add a real number. TODO verify.",
        },
      ],
    },
  ],
};
