import Link from "next/link";

const faqs = [
  {
    q: "Why is WhatsApp unavailable?",
    a: "Meta returned error 131031 for this app. Join the waitlist on the home page and we will message you when WhatsApp unlocks.",
  },
  {
    q: "How do I connect Instagram?",
    a: "Open the Instagram tab and use Connect Instagram. The app checks that your Login session env vars are already set — no new OAuth token is minted in this build.",
  },
  {
    q: "How does payment safety work?",
    a: "Screenshots alone never release goods. Sell-Safe waits for a bank webhook (Paystack), a forwarded bank alert, or an on-chain USDC transfer that matches the order.",
  },
  {
    q: "What data do you store?",
    a: "Message text, platform sender ids, catalog photos you send, order refs, and payment evidence needed to verify. See the privacy page for the plain-language list.",
  },
  {
    q: "Is crypto mainnet?",
    a: "The demo verifies USDC on Base Sepolia. Set CRYPTO_* and DEMO_REAL_TX_HASH for the live demo cases.",
  },
];

export default function FaqPage() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl px-4 py-12">
      <p className="mb-2 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          Sell-Safe
        </Link>{" "}
        / FAQ
      </p>
      <h1 className="mb-3 text-3xl font-semibold tracking-tight">FAQ</h1>
      <p className="mb-8 text-muted-foreground">
        Short answers for sellers setting up Sell-Safe. Status of integrations is on{" "}
        <Link href="/status" className="underline underline-offset-4">
          /status
        </Link>
        .
      </p>
      <div className="space-y-6">
        {faqs.map((item) => (
          <section key={item.q}>
            <h2 className="mb-2 text-lg font-semibold">{item.q}</h2>
            <p className="text-muted-foreground">{item.a}</p>
          </section>
        ))}
      </div>
    </main>
  );
}
