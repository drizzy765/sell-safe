"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { SellSafeLogo } from "@/components/SellSafeLogo";

type Product = {
  id: string;
  name: string;
  price_ngn: number | null;
  category: string;
  description: string;
  image_urls: string[];
  stock_status: string;
  status: string;
  flags?: string[];
  confidence?: number;
};

type MediaItem = {
  id: string;
  kind: string;
  filename: string;
  url: string;
  caption: string;
  source: string;
  content_type: string;
};

type Chat = {
  id: string;
  channel: string;
  buyer: string;
  language: string;
  preview: string;
  reply: string;
  at: string;
  demo?: boolean;
};

type Receipt = {
  id: string;
  verdict: string;
  amount_ngn: number;
  reasons: string[];
  demo?: boolean;
};

type Summary = {
  shop: { id: string; name: string; handle: string; category?: string } | null;
  stats: {
    chats_today: number;
    orders: number;
    naira_verified: number;
    fakes_caught: number;
    avg_reply_seconds: number;
    demo?: boolean;
  };
  products: Product[];
  drafts: Product[];
  media: MediaItem[];
  inbox: Chat[];
  receipts: Receipt[];
  demo_mode: boolean;
};

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Could not read file"));
    reader.readAsDataURL(file);
  });
}

function formatNaira(amount: number | null | undefined) {
  if (amount == null) return "—";
  return `₦${amount.toLocaleString("en-NG")}`;
}

function DashboardInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab") || "catalog";
  const [tab, setTab] = useState(tabParam === "inbox" || tabParam === "receipts" ? tabParam : "catalog");
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [driveUrl, setDriveUrl] = useState("");

  const load = useCallback(async () => {
    const response = await fetch("/api/dashboard/summary", { cache: "no-store" });
    const body = (await response.json().catch(() => ({}))) as Summary & { detail?: string };
    if (!response.ok) {
      setError(body.detail || "Connect Instagram and confirm your shop first.");
      setData(null);
      return;
    }
    setData(body);
    setError("");
  }, []);

  useEffect(() => {
    void load().catch(() => setError("Could not reach the API."));
  }, [load]);

  useEffect(() => {
    if (tabParam === "inbox" || tabParam === "receipts" || tabParam === "catalog") {
      setTab(tabParam);
    }
  }, [tabParam]);

  function switchTab(next: "catalog" | "inbox" | "receipts") {
    setTab(next);
    router.replace(`/dashboard?tab=${next}`);
  }

  async function onUpload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const items = [];
      for (const file of Array.from(files).slice(0, 12)) {
        const content_base64 = await fileToBase64(file);
        items.push({ filename: file.name, content_base64, caption: "" });
      }
      const response = await fetch("/api/onboarding/catalog/import/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items }),
      });
      const body = (await response.json().catch(() => ({}))) as {
        detail?: string;
        drafts?: unknown[];
        media?: unknown[];
        errors?: { detail?: string }[];
      };
      if (!response.ok) {
        setError(body.detail || "Upload failed.");
        setBusy(false);
        return;
      }
      const draftCount = body.drafts?.length || 0;
      const mediaCount = body.media?.length || 0;
      setMessage(
        draftCount
          ? `Saved ${mediaCount} file(s); ${draftCount} draft(s) ready to review.`
          : `Saved ${mediaCount} file(s) to your catalog shelf.`,
      );
      if (body.errors?.length) {
        setError(body.errors.map((e) => e.detail).filter(Boolean).join(" · "));
      }
      await load();
    } catch {
      setError("Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function saveDrive() {
    if (!driveUrl.trim()) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/onboarding/catalog/import/drive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_url: driveUrl.trim() }),
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) {
        setError(body.detail || "Could not save Drive link.");
        setBusy(false);
        return;
      }
      setMessage(body.detail || "Drive link saved.");
      setDriveUrl("");
      await load();
    } catch {
      setError("Could not save Drive link.");
    } finally {
      setBusy(false);
    }
  }

  async function removeMedia(id: string) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/onboarding/catalog/shelf/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { detail?: string };
        setError(body.detail || "Could not delete media.");
        setBusy(false);
        return;
      }
      setMessage("Removed from shelf.");
      await load();
    } catch {
      setError("Could not delete media.");
    } finally {
      setBusy(false);
    }
  }

  if (!data && !error) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-16 text-sm text-muted-foreground">
        Loading dashboard…
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="mx-auto max-w-lg px-4 py-16">
        <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          {error}
        </p>
        <div className="flex flex-wrap gap-3 text-sm">
          <Link href="/?platform=instagram" className="font-medium text-primary underline">
            Connect Instagram
          </Link>
          <Link href="/onboarding/shop" className="underline">
            Confirm shop
          </Link>
        </div>
      </main>
    );
  }

  const shop = data?.shop;
  const stats = data?.stats;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
          <Link href="/" aria-label="Sell-Safe home">
            <SellSafeLogo height={26} />
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link href="/onboarding/catalog" className="text-muted-foreground hover:text-foreground">
              Import tools
            </Link>
            <Link href="/onboarding/shop" className="text-muted-foreground hover:text-foreground">
              Edit shop
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Seller dashboard</p>
            <h1 className="text-3xl font-semibold tracking-tight">
              {shop?.name || "Your shop"}
              {shop?.handle ? (
                <span className="ml-2 text-lg font-normal text-muted-foreground">@{shop.handle}</span>
              ) : null}
            </h1>
            {shop?.category ? (
              <p className="mt-1 text-sm text-muted-foreground">{shop.category}</p>
            ) : null}
          </div>
          {data?.demo_mode ? (
            <span className="rounded-md border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">
              Demo data — inbox & stats until real traffic
            </span>
          ) : null}
        </div>

        {stats ? (
          <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[
              ["Chats today", String(stats.chats_today)],
              ["Orders", String(stats.orders)],
              ["₦ verified", formatNaira(stats.naira_verified)],
              ["Fakes caught", String(stats.fakes_caught)],
              ["Avg reply", `${stats.avg_reply_seconds}s`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-border px-3 py-3">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="mt-1 text-lg font-semibold">{value}</p>
              </div>
            ))}
          </div>
        ) : null}

        <div className="mb-6 flex gap-1 border-b border-border">
          {(
            [
              ["catalog", "Catalog"],
              ["inbox", "Inbox"],
              ["receipts", "Receipts"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => switchTab(id)}
              className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-medium ${
                tab === id
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {error ? (
          <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
            {error}
          </p>
        ) : null}
        {message ? (
          <p className="mb-4 rounded-lg border border-border bg-muted px-3 py-2 text-sm">{message}</p>
        ) : null}

        {tab === "catalog" ? (
          <div className="space-y-8">
            <section className="rounded-xl border border-border p-5">
              <h2 className="mb-1 text-lg font-semibold">Add to catalog</h2>
              <p className="mb-4 text-sm text-muted-foreground">
                Upload images and videos for this shop, or paste a Drive link. Skipped Step 2? Start
                here.
              </p>
              <div className="mb-4">
                <label className="mb-2 block text-sm font-medium">Photos & videos</label>
                <input
                  type="file"
                  accept="image/*,video/*"
                  multiple
                  disabled={busy}
                  onChange={(e) => void onUpload(e.target.files)}
                  className="block w-full text-sm"
                />
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm"
                  placeholder="https://drive.google.com/drive/folders/…"
                  value={driveUrl}
                  onChange={(e) => setDriveUrl(e.target.value)}
                  disabled={busy}
                />
                <button
                  type="button"
                  disabled={busy || !driveUrl.trim()}
                  onClick={() => void saveDrive()}
                  className="rounded-md border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
                >
                  Save Drive link
                </button>
              </div>
              <div className="mt-4 flex flex-wrap gap-3 text-sm">
                <Link href="/onboarding/catalog" className="text-primary underline">
                  Instagram post import
                </Link>
                <Link href="/onboarding/catalog/review" className="underline">
                  Review drafts ({data?.drafts.length || 0})
                </Link>
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-lg font-semibold">
                Products ({data?.products.length || 0})
              </h2>
              {!data?.products.length ? (
                <p className="rounded-xl border border-dashed border-border p-6 text-sm text-muted-foreground">
                  No approved products yet. Upload photos above or{" "}
                  <Link href="/onboarding/catalog/review" className="underline">
                    approve drafts
                  </Link>
                  .
                </p>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {data.products.map((p) => (
                    <article key={p.id} className="overflow-hidden rounded-xl border border-border">
                      <div className="aspect-square bg-muted">
                        {p.image_urls?.[0] ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={p.image_urls[0]}
                            alt=""
                            className="h-full w-full object-cover"
                          />
                        ) : null}
                      </div>
                      <div className="space-y-1 p-3">
                        <p className="font-medium">{p.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatNaira(p.price_ngn)}
                          {p.category ? ` · ${p.category}` : ""}
                        </p>
                        <p className="line-clamp-2 text-xs text-muted-foreground">{p.description}</p>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>

            {(data?.drafts.length || 0) > 0 ? (
              <section>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-lg font-semibold">Drafts ({data?.drafts.length})</h2>
                  <Link
                    href="/onboarding/catalog/review"
                    className="text-sm font-medium text-primary underline"
                  >
                    Review & approve
                  </Link>
                </div>
                <ul className="space-y-2 text-sm">
                  {data?.drafts.map((d) => (
                    <li
                      key={d.id}
                      className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
                    >
                      <span>
                        {d.name || "Untitled"} · {formatNaira(d.price_ngn)}
                      </span>
                      <span className="text-xs text-muted-foreground">{d.stock_status}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            <section>
              <h2 className="mb-3 text-lg font-semibold">
                Media shelf ({data?.media.length || 0})
              </h2>
              {!data?.media.length ? (
                <p className="text-sm text-muted-foreground">
                  Uploaded images, videos, and Drive links for this shop appear here.
                </p>
              ) : (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                  {data.media.map((m) => (
                    <div key={m.id} className="overflow-hidden rounded-xl border border-border">
                      <div className="aspect-square bg-muted">
                        {m.source === "drive" ? (
                          <div className="flex h-full items-center justify-center p-3 text-center text-xs text-muted-foreground">
                            Drive link saved
                          </div>
                        ) : m.kind === "video" || m.content_type.startsWith("video/") ? (
                          <video src={m.url} className="h-full w-full object-cover" controls muted />
                        ) : (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={m.url} alt="" className="h-full w-full object-cover" />
                        )}
                      </div>
                      <div className="space-y-1 p-2">
                        <p className="truncate text-xs font-medium">{m.filename}</p>
                        <p className="text-[11px] text-muted-foreground">
                          {m.kind} · {m.source}
                        </p>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => void removeMedia(m.id)}
                          className="text-[11px] text-red-600 underline disabled:opacity-50"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        ) : null}

        {tab === "inbox" ? (
          <section className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Live Instagram/WhatsApp threads will land here. Sample chats shown while your shop is
              quiet.
            </p>
            {(data?.inbox || []).map((chat) => (
              <article key={chat.id} className="rounded-xl border border-border p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">{chat.buyer}</span>
                  <span>{chat.channel}</span>
                  <span>{chat.language}</span>
                  <span>{chat.at}</span>
                  {chat.demo ? (
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-900">Demo</span>
                  ) : null}
                </div>
                <p className="text-sm">
                  <span className="text-muted-foreground">Buyer: </span>
                  {chat.preview}
                </p>
                <p className="mt-1 text-sm">
                  <span className="text-muted-foreground">Sell-Safe: </span>
                  {chat.reply}
                </p>
              </article>
            ))}
          </section>
        ) : null}

        {tab === "receipts" ? (
          <section className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Receipt checks and bank alerts. Demo verdicts until live payments flow.
            </p>
            {(data?.receipts || []).map((r) => (
              <article key={r.id} className="rounded-xl border border-border p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-semibold ${
                      r.verdict === "CONFIRMED"
                        ? "bg-emerald-100 text-emerald-900"
                        : "bg-amber-100 text-amber-900"
                    }`}
                  >
                    {r.verdict}
                  </span>
                  <span className="text-sm font-medium">{formatNaira(r.amount_ngn)}</span>
                  {r.demo ? (
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
                      Demo
                    </span>
                  ) : null}
                </div>
                <ul className="list-inside list-disc text-sm text-muted-foreground">
                  {r.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </article>
            ))}
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto max-w-5xl px-4 py-16 text-sm text-muted-foreground">
          Loading dashboard…
        </main>
      }
    >
      <DashboardInner />
    </Suspense>
  );
}
