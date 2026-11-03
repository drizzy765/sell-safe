import Link from "next/link";

import { SellSafeLogo } from "@/components/SellSafeLogo";
import { ThemeToggle } from "@/components/ThemeToggle";

const toc = [
  { id: "getting-started", label: "Getting started" },
  { id: "connect", label: "Connect Instagram" },
  { id: "shop-payout", label: "Shop & payout" },
  { id: "catalog", label: "Catalog" },
  { id: "inbox", label: "Inbox & reply modes" },
  { id: "payments", label: "Payment verification" },
  { id: "login", label: "Login & saved shop" },
  { id: "troubleshooting", label: "Troubleshooting" },
  { id: "developers", label: "For developers" },
];

function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 rounded-3xl border border-border bg-card p-6 shadow-panel sm:p-8">
      <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-6 text-muted-foreground">{children}</div>
    </section>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[12px] text-foreground">
      {children}
    </code>
  );
}

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground antialiased">
      <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1120px] items-center justify-between px-4">
          <Link href="/" aria-label="Sell-Safe home" className="flex items-center">
            <SellSafeLogo height={28} />
          </Link>
          <nav className="flex items-center gap-5 text-sm">
            <Link className="text-muted-foreground transition-colors hover:text-foreground" href="/status">
              Status
            </Link>
            <Link className="text-muted-foreground transition-colors hover:text-foreground" href="/faq">
              FAQ
            </Link>
            <Link className="text-muted-foreground transition-colors hover:text-foreground" href="/login">
              Login
            </Link>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-[1120px] px-4 py-10 md:py-14">
        <p className="text-sm text-muted-foreground">
          <Link href="/" className="hover:text-foreground">
            Sell-Safe
          </Link>{" "}
          / Docs
        </p>
        <h1 className="mt-2 text-balance text-3xl font-bold tracking-tight md:text-4xl">
          Sell-Safe documentation
        </h1>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          Everything a seller (or developer) needs: connect Instagram, build a catalog, let the AI
          answer DMs, and verify payments before goods leave the shop.
        </p>

        <div className="mt-10 grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)]">
          <aside className="hidden lg:block">
            <nav aria-label="On this page" className="sticky top-24 space-y-1 text-sm">
              {toc.map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className="block rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                  {item.label}
                </a>
              ))}
            </nav>
          </aside>

          <div className="space-y-6">
            <Section id="getting-started" title="Getting started">
              <ol className="list-decimal space-y-2 pl-5">
                <li>
                  <strong className="text-foreground">Connect Instagram</strong> — one click with
                  Meta Instagram Login. No Facebook Page is required.
                </li>
                <li>
                  <strong className="text-foreground">Confirm your shop</strong> — check the name,
                  bio, and logo pulled from Instagram, then add your payout bank details.
                </li>
                <li>
                  <strong className="text-foreground">Build your catalog</strong> — pick product
                  photos from your Instagram media, upload files, or import a public Google Drive
                  folder. Approve each product with its price.
                </li>
                <li>
                  <strong className="text-foreground">Go live</strong> — buyers who DM your shop
                  get AI replies, and every payment screenshot is verified before you ship.
                </li>
              </ol>
              <p>
                WhatsApp is currently waitlist-only (Meta business verification is pending).
                Instagram is the live channel today.
              </p>
            </Section>

            <Section id="connect" title="Connect Instagram">
              <p>You need an Instagram Professional (Business or Creator) account.</p>
              <ol className="list-decimal space-y-2 pl-5">
                <li>
                  Open{" "}
                  <Link href="/?platform=instagram" className="font-medium text-primary underline">
                    Connect Instagram
                  </Link>{" "}
                  and approve the Meta login for the shop account.
                </li>
                <li>
                  You land on <em>Confirm your shop</em>. After saving, the dashboard opens.
                </li>
                <li>
                  Use <strong className="text-foreground">Disconnect</strong> in Settings to switch
                  to a different account.
                </li>
              </ol>
              <p>
                Notes: the official Sell-Safe Instagram page only sends the connect/marketing
                reply — catalog and payment automation runs on <em>your connected shop account</em>,
                never on the official page. In Meta Development mode, buyer accounts must be added
                as Instagram Testers or their DMs will not be delivered. If Meta says{" "}
                <em>Invalid platform app</em>, the Instagram product App ID is wrong (do not use the
                main Meta App ID).
              </p>
            </Section>

            <Section id="shop-payout" title="Shop & payout">
              <p>
                In Dashboard → Settings, save your <strong className="text-foreground">bank name,
                account name, and account number</strong>. When a buyer asks “What&apos;s the business
                account number” or how to pay, Sell-Safe replies with exactly these saved details —
                deterministically, without the AI inventing numbers. If payout details are missing,
                the buyer is told they are not set yet, and the dashboard shows a warning banner
                until you add them.
              </p>
              <p>
                The dashboard status strip shows your connection, reply mode, payout state, and
                today&apos;s chats, orders, verified amount, and fakes caught.
              </p>
            </Section>

            <Section id="catalog" title="Catalog">
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong className="text-foreground">Instagram media:</strong> pick existing post
                  photos and add a name + price.
                </li>
                <li>
                  <strong className="text-foreground">Upload:</strong> add product photos directly.
                </li>
                <li>
                  <strong className="text-foreground">Google Drive:</strong> share a public folder
                  (“Anyone with the link”) and name files{" "}
                  <Code>{"<Name> - NGN <price>.jpg"}</Code>, e.g.{" "}
                  <Code>Honey Beans 1kg - NGN 6000.jpg</Code>. Matching files import with prices.
                </li>
                <li>
                  <strong className="text-foreground">Manual:</strong> add a product by hand in the
                  Catalog tab.
                </li>
              </ul>
              <p>
                Only approved products are quoted to buyers. When a buyer asks for a product, the
                reply includes the product photo and price when available.
              </p>
            </Section>

            <Section id="inbox" title="Inbox & reply modes">
              <p>
                The dashboard Inbox mirrors your real Instagram DMs. Three reply modes (switch any
                time, and per chat):
              </p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong className="text-foreground">AUTO</strong> — the AI replies immediately.
                </li>
                <li>
                  <strong className="text-foreground">APPROVE</strong> — replies appear as drafts in
                  the thread. Nothing sends until you press Approve &amp; send.
                </li>
                <li>
                  <strong className="text-foreground">SMART</strong> — routine replies send
                  automatically; payment-related replies wait for your approval.
                </li>
              </ul>
              <p>
                <strong className="text-foreground">Take over</strong> pauses the AI on one chat so
                you can talk yourself; <strong className="text-foreground">Hand back</strong>{" "}
                resumes it. If a buyer&apos;s first DM sits in Instagram Message Requests, accept it in
                the Instagram app — Meta does not deliver webhooks for unaccepted requests.
              </p>
            </Section>

            <Section id="payments" title="Payment verification">
              <p>
                A screenshot alone never releases goods. Sell-Safe extracts the receipt with AI
                vision, cross-checks it with deterministic rules, and only the verification engine
                sets the verdict — the AI never decides:
              </p>
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong className="text-foreground">CONFIRMED</strong> — matched real evidence
                  (Paystack/Flutterwave webhook, forwarded bank alert you accepted, or a USDC
                  transfer on Base). Safe to ship.
                </li>
                <li>
                  <strong className="text-foreground">SUSPICIOUS</strong> — fraud signals (edited
                  amount, reused reference, mismatched details). Do not ship.
                </li>
                <li>
                  <strong className="text-foreground">NOT_FOUND</strong> — no matching payment
                  found yet. Ask the buyer to wait or re-send.
                </li>
                <li>
                  <strong className="text-foreground">UNVERIFIED</strong> — screenshot received,
                  evidence still pending.
                </li>
              </ul>
              <p>
                If the screenshot amount differs from the order amount, release is blocked. The
                crypto demo verifies USDC on Base Sepolia (testnet).
              </p>
            </Section>

            <Section id="login" title="Login & saved shop">
              <p>
                Sellers can create a login with an email magic link at{" "}
                <Link href="/login" className="font-medium text-primary underline">
                  /login
                </Link>{" "}
                — no password. In the dashboard sidebar, choose{" "}
                <strong className="text-foreground">Save my shop</strong> once. After that, logging
                in on any browser restores your Instagram connection automatically: no reconnect
                after restarts or redeploys, unless the 60-day Instagram token has expired.
              </p>
            </Section>

            <Section id="troubleshooting" title="Troubleshooting">
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong className="text-foreground">Buyer got no reply:</strong> check the DM is
                  not waiting in Instagram Message Requests; confirm the buyer is an Instagram
                  Tester (Development mode); check the chat is not in APPROVE mode or taken over;
                  confirm payout warnings on the dashboard.
                </li>
                <li>
                  <strong className="text-foreground">“Backend is offline” once, then fine:</strong>{" "}
                  the free hosting tier sleeps when idle. The first request wakes it (up to a
                  minute). A keep-alive ping runs every 10 minutes during demo hours.
                </li>
                <li>
                  <strong className="text-foreground">OAuth redirect error:</strong> the redirect
                  URI in Meta must match the deployed API exactly:{" "}
                  <Code>https://sell-safe-api.onrender.com/api/instagram/oauth/callback</Code>.
                  Old tunnel URLs stop working when the tunnel stops.
                </li>
                <li>
                  <strong className="text-foreground">Dashboard asks to reconnect after a
                  restart:</strong> login first (above) so your saved session restores; reconnect
                  manually only if the Instagram token expired.
                </li>
                <li>
                  <strong className="text-foreground">AI replies stopped but messages
                  arrive:</strong> the language provider may be failing. Sell-Safe sends a safe
                  fallback reply instead of silence and logs the provider error; Meta Muse is the
                  primary provider, with Groq as fallback.
                </li>
              </ul>
            </Section>

            <Section id="developers" title="For developers">
              <ul className="list-disc space-y-2 pl-5">
                <li>
                  <strong className="text-foreground">Stack:</strong> FastAPI (Python 3.11) on
                  Render, Next.js on Vercel, Supabase for persistence, Meta Muse for agent/vision
                  (Groq as dev fallback), Paystack/Flutterwave webhooks, USDC on Base.
                </li>
                <li>
                  <strong className="text-foreground">Health:</strong>{" "}
                  <Code>GET https://sell-safe-api.onrender.com/health</Code> returns{" "}
                  <Code>{`{"status":"ok"}`}</Code>.
                </li>
                <li>
                  <strong className="text-foreground">Webhooks:</strong>{" "}
                  <Code>POST /webhooks/instagram</Code> and <Code>/webhooks/meta</Code> verify the
                  Meta signature on the raw body, dedupe deliveries, return 200 fast, and process
                  asynchronously.
                </li>
                <li>
                  <strong className="text-foreground">Money & verdicts:</strong> amounts are integer
                  kobo. Only the deterministic verification engine sets payment verdicts — never
                  the LLM.
                </li>
                <li>
                  <strong className="text-foreground">Source & setup:</strong> see the repository
                  README and <Code>docs/</Code> for architecture, the payment-verification spec,
                  and the full environment-variable list (<Code>.env.example</Code>).
                </li>
              </ul>
            </Section>
          </div>
        </div>
      </main>

      <footer className="border-t border-border py-8 text-center text-sm text-muted-foreground">
        Built for Nigerian sellers · Meta Global AI Hackathon
      </footer>
    </div>
  );
}
