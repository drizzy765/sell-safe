import type { PlatformGuide } from "./types";

export const instagramGuide: PlatformGuide = {
  id: "instagram",
  label: "Instagram",
  accent: "#E1306C",
  prerequisites: [
    "Instagram Professional (Business) account",
    "A Facebook Page linked to that account",
    "The Meta app from the WhatsApp guide",
  ],
  steps: [
    {
      title: "Switch Instagram to Professional",
      blocks: [
        {
          type: "text",
          body: "In Instagram settings, switch the account to Professional (Business).",
        },
      ],
    },
    {
      title: "Link it to your Facebook Page",
      blocks: [
        {
          type: "text",
          body: "Page settings → Linked accounts → Instagram. TODO verify the menu path.",
        },
      ],
    },
    {
      title: "Allow message access",
      blocks: [
        {
          type: "text",
          body: "Instagram settings → Messages → Connected tools — allow access to messages. TODO verify.",
        },
      ],
    },
    {
      title: "Add Instagram Messaging to the Meta app",
      blocks: [
        {
          type: "text",
          body: "Connect the Page / IG account in the Meta app.",
        },
      ],
    },
    {
      title: "Set the webhook",
      blocks: [
        {
          type: "code",
          label: "Callback URL",
          value: "https://<your-sell-safe-host>/webhooks/instagram",
        },
        {
          type: "code",
          label: "Verify token",
          value: "META_VERIFY_TOKEN",
          secret: true,
        },
        {
          type: "text",
          body: "Subscribe to `messages`.",
        },
      ],
    },
    {
      title: "Add the Page access token",
      blocks: [
        {
          type: "text",
          body: "Generate a Page access token and add it to Sell-Safe (never paste it in chats).",
        },
        {
          type: "code",
          label: "Page access token (masked)",
          value: "EAAG••••••••••••••••",
          secret: true,
        },
      ],
    },
    {
      title: "DM your shop",
      blocks: [
        {
          type: "text",
          body: "DM your shop from another account, then check the connection.",
        },
      ],
    },
  ],
  note: "Going public needs Meta app review and permissions (e.g. instagram_manage_messages). TODO verify the current permission names.",
};
