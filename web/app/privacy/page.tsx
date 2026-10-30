import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl px-4 py-12">
      <p className="mb-2 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground">
          Sell-Safe
        </Link>{" "}
        / privacy
      </p>
      <h1 className="mb-3 text-3xl font-semibold tracking-tight">Privacy</h1>
      <div className="space-y-4 text-muted-foreground">
        <p>
          Sell-Safe is a shop assistant. When someone messages the shop on Instagram (or
          WhatsApp when available), Sell-Safe receives that message so it can answer questions
          about products and orders.
        </p>
        <p>We store:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>Message text and the platform sender id</li>
          <li>Timestamps for the conversation</li>
          <li>Catalog photos and product details you confirm</li>
          <li>Order references and payment evidence used to verify transfers</li>
          <li>Hashed fraud signals (never raw account numbers)</li>
        </ul>
        <p>Sell-Safe does not sell this information.</p>
        <p>
          To stop, stop messaging the shop. Questions go to the Instagram account used for the
          demo (sellsafe000) or the email on the submission page.
        </p>
        <p>
          The API also serves a plain HTML copy at <code className="text-foreground">/privacy</code>{" "}
          on the backend for Meta app review.
        </p>
      </div>
    </main>
  );
}
