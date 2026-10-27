import type { PlatformGuide } from "./types";

export const messengerGuide: PlatformGuide = {
  id: "messenger",
  label: "Messenger",
  accent: "#0084FF",
  prerequisites: [
    "A Facebook Page where you are an admin",
    "The Meta app",
  ],
  steps: [
    {
      title: "Add the Messenger product",
      blocks: [
        {
          type: "text",
          body: "Add Messenger to your Meta app. TODO verify against Meta's Messenger Platform docs.",
        },
      ],
    },
    {
      title: "Connect your Page",
      blocks: [
        {
          type: "text",
          body: "Connect the Page and generate a Page access token.",
        },
        {
          type: "code",
          label: "Page access token (masked)",
          value: "EAAM••••••••••••••••",
          secret: true,
        },
      ],
    },
    {
      title: "Set the webhook",
      blocks: [
        {
          type: "code",
          label: "Callback URL",
          value: "https://<your-sell-safe-host>/webhooks/messenger",
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
      title: "Subscribe the Page",
      blocks: [
        {
          type: "text",
          body: "Subscribe with the `messages` and `messaging_postbacks` fields. TODO verify.",
        },
      ],
    },
    {
      title: "Message your Page",
      blocks: [
        {
          type: "text",
          body: "Message your Page from a tester account (add testers under App roles while in development mode).",
        },
      ],
    },
    {
      title: "Check connection",
      blocks: [
        {
          type: "text",
          body: "Confirm the webhook received the tester message.",
        },
      ],
    },
  ],
};
