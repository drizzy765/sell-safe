import Link from "next/link";

const checks = [
  {
    name: "API health",
    detail: "GET /health should return status ok when the backend is up.",
    state: "connected" as const,
  },
  {
    name: "Instagram Login",
    detail: "Seller Connect uses Instagram Login OAuth (INSTAGRAM_APP_ID + INSTAGRAM_APP_SECRET + INSTAGRAM_OAUTH_REDIRECT_URI). Do not use META_APP_ID. Bot webhooks still use INSTAGRAM_ACCESS_TOKEN.",
    state: "connected" as const,
  },
  {
    name: "WhatsApp Cloud API",
    detail: "Blocked by Meta error 131031 for this hackathon build. Use the waitlist.",
    state: "failed" as const,
  },
  {
    name: "Paystack webhooks",
    detail: "Signature check on raw body; test-mode transfers confirm orders.",
    state: "connected" as const,
  },
  {
    name: "Base Sepolia USDC",
    detail: "CRYPTO_RPC_URL must point at chain 84532 with the USDC contract.",
    state: "connected" as const,
  },
];

export default function StatusPage() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl px-4 py-12">
      <p className="mb-2 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          Sell-Safe
        </Link>{" "}
        / status
      </p>
      <h1 className="mb-3 text-3xl font-semibold tracking-tight">System status</h1>
      <p className="mb-8 max-w-2xl text-muted-foreground">
        What is connected for the demo build, and what still fails. See the{" "}
        <Link href="/faq" className="underline underline-offset-4">
          FAQ
        </Link>{" "}
        for setup help.
      </p>
      <ul className="space-y-4">
        {checks.map((item) => (
          <li key={item.name} className="border-b border-border pb-4">
            <div className="mb-1 flex items-center gap-3">
              <span
                className={
                  item.state === "connected"
                    ? "text-sm font-medium text-emerald-700"
                    : "text-sm font-medium text-amber-700"
                }
              >
                {item.state === "connected" ? "Connected" : "Failed / blocked"}
              </span>
              <span className="font-semibold">{item.name}</span>
            </div>
            <p className="text-sm text-muted-foreground">{item.detail}</p>
          </li>
        ))}
      </ul>
    </main>
  );
}
