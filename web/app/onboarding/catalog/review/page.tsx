"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SellSafeLogo } from "@/components/SellSafeLogo";

type Draft = {
  id: string;
  name: string;
  price_ngn: number | null;
  category: string;
  description: string;
  image_urls: string[];
  confidence: number;
  flags: string[];
  source: string;
  stock_status: string;
};

const FLAG_LABEL: Record<string, string> = {
  missing_price: "Missing price",
  dm_for_price: "DM for price",
  price_outlier: "Price outlier",
  duplicate: "Possible duplicate",
};

export default function CatalogReviewPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [products, setProducts] = useState<Draft[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    const [draftRes, productRes] = await Promise.all([
      fetch("/api/onboarding/catalog/drafts", { cache: "no-store" }),
      fetch("/api/onboarding/catalog/products", { cache: "no-store" }),
    ]);
    const draftBody = (await draftRes.json().catch(() => ({}))) as {
      drafts?: Draft[];
      detail?: string;
    };
    const productBody = (await productRes.json().catch(() => ({}))) as {
      products?: Draft[];
    };
    if (!draftRes.ok) {
      setError(draftBody.detail || "Could not load drafts.");
      return;
    }
    setDrafts(draftBody.drafts || []);
    setProducts(productBody.products || []);
    setSelected({});
  }

  useEffect(() => {
    void reload().catch(() => setError("Could not reach the API."));
  }, []);

  function toggle(id: string) {
    setSelected((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function saveDraft(draft: Draft) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/onboarding/catalog/drafts/${draft.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: draft.name,
          price_ngn: draft.price_ngn,
          category: draft.category,
          description: draft.description,
          stock_status: draft.stock_status,
          clear_flags: !draft.flags.length,
        }),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { detail?: string };
        setError(body.detail || "Could not save draft.");
        setBusy(false);
        return;
      }
      await reload();
      setMessage("Draft saved.");
    } finally {
      setBusy(false);
    }
  }

  async function removeDraft(id: string) {
    setBusy(true);
    await fetch(`/api/onboarding/catalog/drafts/${id}`, { method: "DELETE" });
    await reload();
    setBusy(false);
  }

  async function approve(ids: string[]) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/onboarding/catalog/drafts/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids }),
      });
      const body = (await response.json().catch(() => ({}))) as {
        approved?: Draft[];
        skipped?: { id: string; detail: string }[];
        detail?: string;
      };
      if (!response.ok) {
        setError(body.detail || "Approve failed.");
        setBusy(false);
        return;
      }
      const skipped = body.skipped || [];
      setMessage(
        `Approved ${body.approved?.length || 0}` +
          (skipped.length ? ` · skipped ${skipped.length} (add prices first)` : ""),
      );
      await reload();
    } finally {
      setBusy(false);
    }
  }

  const selectedIds = Object.entries(selected)
    .filter(([, on]) => on)
    .map(([id]) => id);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
          <Link href="/" aria-label="Sell-Safe home">
            <SellSafeLogo height={26} />
          </Link>
          <Link href="/onboarding/catalog" className="text-sm text-muted-foreground hover:text-foreground">
            Import more
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-10">
        <p className="mb-2 text-sm text-muted-foreground">Step 2 · Review drafts</p>
        <h1 className="mb-2 text-3xl font-semibold tracking-tight">Approve your catalog</h1>
        <p className="mb-6 max-w-2xl text-muted-foreground">
          Edit names and prices, then approve. Approved items become the catalog Sell-Safe uses in
          buyer DMs.
        </p>

        {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
        {message ? <p className="mb-3 text-sm text-emerald-700">{message}</p> : null}

        <div className="mb-6 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={busy || selectedIds.length === 0}
            onClick={() => void approve(selectedIds)}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
          >
            Approve selected ({selectedIds.length})
          </button>
          <button
            type="button"
            disabled={busy || drafts.length === 0}
            onClick={() => void approve(drafts.map((d) => d.id))}
            className="rounded-md border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            Bulk approve all with prices
          </button>
        </div>

        {!drafts.length ? (
          <p className="rounded-xl border border-border bg-muted p-6 text-sm text-muted-foreground">
            No drafts yet.{" "}
            <Link href="/onboarding/catalog" className="underline">
              Import Instagram posts or upload photos
            </Link>
            .
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {drafts.map((draft) => (
              <article key={draft.id} className="rounded-xl border border-border p-4">
                <div className="mb-3 flex gap-3">
                  <label className="mt-1">
                    <input
                      type="checkbox"
                      checked={!!selected[draft.id]}
                      onChange={() => toggle(draft.id)}
                    />
                  </label>
                  <div className="h-20 w-20 overflow-hidden rounded-md bg-muted">
                    {draft.image_urls?.[0] ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={draft.image_urls[0]} alt="" className="h-full w-full object-cover" />
                    ) : null}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">
                      {draft.source} · confidence {(draft.confidence * 100).toFixed(0)}%
                    </p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {draft.flags.map((flag) => (
                        <span
                          key={flag}
                          className="rounded bg-amber-100 px-1.5 py-0.5 text-[11px] font-medium text-amber-900 dark:bg-amber-950 dark:text-amber-100"
                        >
                          {FLAG_LABEL[flag] || flag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <label className="mb-2 block text-sm">
                  <span className="mb-1 block font-medium">Name</span>
                  <input
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    value={draft.name}
                    onChange={(e) =>
                      setDrafts((rows) =>
                        rows.map((row) =>
                          row.id === draft.id ? { ...row, name: e.target.value } : row,
                        ),
                      )
                    }
                  />
                </label>
                <div className="mb-2 grid grid-cols-2 gap-2">
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium">Price (₦)</span>
                    <input
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                      type="number"
                      min={0}
                      value={draft.price_ngn ?? ""}
                      onChange={(e) =>
                        setDrafts((rows) =>
                          rows.map((row) =>
                            row.id === draft.id
                              ? {
                                  ...row,
                                  price_ngn: e.target.value ? Number(e.target.value) : null,
                                  flags: e.target.value
                                    ? row.flags.filter(
                                        (f) => f !== "missing_price" && f !== "dm_for_price",
                                      )
                                    : row.flags,
                                }
                              : row,
                          ),
                        )
                      }
                    />
                  </label>
                  <label className="block text-sm">
                    <span className="mb-1 block font-medium">Category</span>
                    <input
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                      value={draft.category}
                      onChange={(e) =>
                        setDrafts((rows) =>
                          rows.map((row) =>
                            row.id === draft.id ? { ...row, category: e.target.value } : row,
                          ),
                        )
                      }
                    />
                  </label>
                </div>
                <label className="mb-3 block text-sm">
                  <span className="mb-1 block font-medium">Description</span>
                  <textarea
                    className="min-h-16 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    value={draft.description}
                    onChange={(e) =>
                      setDrafts((rows) =>
                        rows.map((row) =>
                          row.id === draft.id ? { ...row, description: e.target.value } : row,
                        ),
                      )
                    }
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void saveDraft(draft)}
                    className="rounded-md border border-border px-3 py-1.5 text-sm"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    disabled={busy || draft.price_ngn == null}
                    onClick={() => void approve([draft.id])}
                    className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void removeDraft(draft.id)}
                    className="rounded-md px-3 py-1.5 text-sm text-red-600"
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}

        {products.length ? (
          <section className="mt-12">
            <h2 className="mb-3 text-xl font-semibold">Approved catalog ({products.length})</h2>
            <ul className="space-y-2">
              {products.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm"
                >
                  <span>
                    {p.name}
                    <span className="text-muted-foreground"> · {p.category || "uncategorized"}</span>
                  </span>
                  <span className="font-medium tabular-nums">
                    {p.price_ngn != null ? `₦${p.price_ngn.toLocaleString()}` : "—"}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </main>
    </div>
  );
}
