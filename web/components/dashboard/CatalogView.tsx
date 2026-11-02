"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import { DashboardSettings, MediaItem, Product, Summary, formatNaira } from "./types";

type Props = {
  data: Summary;
  settings: DashboardSettings;
  busy: boolean;
  message: string;
  error: string;
  onUpload: (files: FileList | null) => Promise<void>;
  onDrive: (url: string) => Promise<void>;
  onRemoveMedia: (id: string) => Promise<void>;
  onDismissSkipBanner: () => Promise<void>;
};

export function CatalogView({
  data,
  settings,
  busy,
  message,
  error,
  onUpload,
  onDrive,
  onRemoveMedia,
  onDismissSkipBanner,
}: Props) {
  const [addOpen, setAddOpen] = useState(false);
  const [driveOpen, setDriveOpen] = useState(false);
  const [driveUrl, setDriveUrl] = useState("");
  const [query, setQuery] = useState("");
  const [skipBanner, setSkipBanner] = useState(settings.catalog_skipped);
  const fileRef = useRef<HTMLInputElement>(null);

  const products = (data.products || []).filter((p) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return p.name.toLowerCase().includes(q) || (p.category || "").toLowerCase().includes(q);
  });

  const stats = data.stats;
  const shop = data.shop;
  const mode = (settings.reply_mode || "auto").toUpperCase();

  return (
    <div className="min-h-full bg-[#f7f7fb] px-6 py-6">
      <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-3">
          <div className="h-12 w-12 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-[#e8e8f0]">
            {shop?.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={shop.logo_url} alt="" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-lg font-bold text-[#6e4af7]">
                S
              </div>
            )}
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-[#17172a]">
              {shop?.name || "Your shop"}
            </h1>
            <p className="text-sm text-[#6b6b80]">
              @{shop?.handle || "shop"}
              {shop?.category ? ` · ${shop.category}` : ""}
            </p>
            <span className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-[#e8f8ef] px-2.5 py-1 text-xs font-semibold text-[#0f9d58]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#0f9d58]" />
              Sell-Safe on {mode} · powered by Muse
            </span>
          </div>
        </div>

        <div className="relative">
          <button
            type="button"
            onClick={() => setAddOpen((v) => !v)}
            className="rounded-xl bg-gradient-to-r from-[#2876fe] to-[#6e4af7] px-4 py-2.5 text-sm font-semibold text-white shadow-sm"
          >
            + Add products
          </button>
          {addOpen ? (
            <div className="absolute right-0 z-20 mt-2 w-56 overflow-hidden rounded-xl border border-[#e8e8f0] bg-white shadow-lg">
              <Link
                href="/onboarding/catalog"
                className="block px-3 py-2.5 text-sm hover:bg-[#f7f7fb]"
                onClick={() => setAddOpen(false)}
              >
                From Instagram posts
              </Link>
              <button
                type="button"
                className="block w-full px-3 py-2.5 text-left text-sm hover:bg-[#f7f7fb]"
                onClick={() => {
                  setAddOpen(false);
                  fileRef.current?.click();
                }}
              >
                Upload photos
              </button>
              <button
                type="button"
                className="block w-full px-3 py-2.5 text-left text-sm hover:bg-[#f7f7fb]"
                onClick={() => {
                  setAddOpen(false);
                  setDriveOpen(true);
                }}
              >
                Google Drive link
              </button>
              <p className="border-t border-[#efefef] px-3 py-2 text-xs text-[#8e8e8e]">
                WhatsApp / CSV — soon
              </p>
            </div>
          ) : null}
          <input
            ref={fileRef}
            type="file"
            accept="image/*,video/*"
            multiple
            className="hidden"
            onChange={(e) => void onUpload(e.target.files)}
          />
        </div>
      </header>

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          ["Chats today", String(stats.chats_today)],
          ["Orders", String(stats.orders)],
          ["₦ verified", formatNaira(stats.naira_verified)],
          ["Fake receipts caught", String(stats.fakes_caught)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-[#ececf3]">
            <p className="text-xs text-[#6b6b80]">{label}</p>
            <p className="mt-1 text-xl font-semibold text-[#17172a]">{value}</p>
          </div>
        ))}
      </div>

      {error ? (
        <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mb-4 rounded-xl border border-[#e8e8f0] bg-white px-3 py-2 text-sm">{message}</p>
      ) : null}

      {driveOpen ? (
        <div className="mb-4 rounded-2xl border border-[#e8e8f0] bg-white p-4 shadow-sm">
          <h3 className="mb-1 text-sm font-semibold">Import Google Drive folder</h3>
          <p className="mb-2 text-xs text-[#6b6b80]">
            Use files named like <code>Honey beans - NGN 6000.jpg</code> so price is attached
            automatically.
          </p>
          <p className="mb-3 rounded-lg border border-[#e8e8f0] bg-[#f7f7fb] px-3 py-2 text-xs text-[#6b6b80]">
            Share → General access → <strong>Anyone with the link</strong> (Viewer). Private
            folders cannot be imported with the API key.
          </p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              value={driveUrl}
              onChange={(e) => setDriveUrl(e.target.value)}
              placeholder="https://drive.google.com/drive/folders/…"
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2 text-sm"
              disabled={busy}
            />
            <button
              type="button"
              disabled={busy || !driveUrl.trim()}
              onClick={() => void onDrive(driveUrl.trim()).then(() => {
                setDriveUrl("");
                setDriveOpen(false);
              })}
              className="rounded-lg bg-[#2876fe] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              Import folder
            </button>
            <button
              type="button"
              onClick={() => setDriveOpen(false)}
              className="rounded-lg border border-[#e4e4e7] px-3 py-2 text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-[#17172a]">Catalog</h2>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products…"
          className="ml-auto w-full max-w-xs rounded-lg border border-[#e4e4e7] bg-white px-3 py-2 text-sm sm:w-64"
        />
        <Link href="/onboarding/catalog/review" className="text-sm font-medium text-[#2876fe]">
          Review drafts ({data.drafts.length})
        </Link>
      </div>

      {!products.length ? (
        <div className="rounded-2xl border border-dashed border-[#d4d4de] bg-white p-10 text-center">
          <p className="text-sm font-medium text-[#17172a]">No products yet</p>
          <p className="mt-1 text-sm text-[#6b6b80]">
            Add from Instagram, upload photos, or paste a Drive folder link.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}

      {(data.media?.length || 0) > 0 ? (
        <section className="mt-8">
          <h3 className="mb-3 text-sm font-semibold text-[#17172a]">
            Media shelf ({data.media.length})
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-6">
            {data.media.map((m) => (
              <MediaCard key={m.id} item={m} busy={busy} onRemove={onRemoveMedia} />
            ))}
          </div>
        </section>
      ) : null}

      {skipBanner ? (
        <div className="fixed bottom-4 left-1/2 z-30 flex w-[min(640px,calc(100%-2rem))] -translate-x-1/2 items-start gap-3 rounded-2xl bg-gradient-to-r from-[#2876fe] to-[#6e4af7] px-4 py-3 text-white shadow-lg">
          <div className="min-w-0 flex-1 text-sm">
            <p className="font-semibold">Catalog skipped? Add items anytime.</p>
            <p className="text-white/85">
              You can add products from Instagram, upload photos, or share a Google Drive link later.
            </p>
          </div>
          <button
            type="button"
            className="text-white/90"
            onClick={() => {
              setSkipBanner(false);
              void onDismissSkipBanner();
            }}
          >
            ✕
          </button>
        </div>
      ) : null}
    </div>
  );
}

function ProductCard({ product }: { product: Product }) {
  return (
    <article className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-[#ececf3]">
      <div className="aspect-square bg-[#f0f0f5]">
        {product.image_urls?.[0] ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={product.image_urls[0]} alt="" className="h-full w-full object-cover" />
        ) : null}
      </div>
      <div className="space-y-1 p-3">
        <p className="font-semibold text-[#17172a]">{product.name}</p>
        <p className="text-sm text-[#6b6b80]">
          {formatNaira(product.price_ngn)}
          {product.stock_status === "out_of_stock" ? " · Out of stock" : ""}
        </p>
      </div>
    </article>
  );
}

function MediaCard({
  item,
  busy,
  onRemove,
}: {
  item: MediaItem;
  busy: boolean;
  onRemove: (id: string) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-xl bg-white ring-1 ring-[#ececf3]">
      <div className="aspect-square bg-[#f0f0f5]">
        {item.source === "drive" && item.content_type === "text/uri-list" ? (
          <div className="flex h-full items-center justify-center p-2 text-center text-[10px] text-[#6b6b80]">
            Drive source
          </div>
        ) : item.kind === "video" || item.content_type.startsWith("video/") ? (
          <video src={item.url} className="h-full w-full object-cover" muted controls />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={item.url} alt="" className="h-full w-full object-cover" />
        )}
      </div>
      <div className="space-y-1 p-2">
        <p className="truncate text-[11px] font-medium">{item.filename}</p>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onRemove(item.id)}
          className="text-[11px] text-red-600 underline disabled:opacity-50"
        >
          Remove
        </button>
      </div>
    </div>
  );
}
