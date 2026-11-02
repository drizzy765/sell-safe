"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { SellSafeLogo } from "@/components/SellSafeLogo";

type ShopMedia = {
  id: string;
  caption?: string;
  media_url?: string;
  thumbnail_url?: string;
};

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Could not read file"));
    reader.readAsDataURL(file);
  });
}

export default function OnboardingCatalogPage() {
  const router = useRouter();
  const [media, setMedia] = useState<ShopMedia[]>([]);
  const [handle, setHandle] = useState("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [driveUrl, setDriveUrl] = useState("");
  const [driveBusy, setDriveBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch("/api/onboarding/catalog/media", { cache: "no-store" });
        const body = (await response.json().catch(() => ({}))) as {
          media?: ShopMedia[];
          handle?: string;
          detail?: string;
          warning?: string;
        };
        if (cancelled) return;
        if (!response.ok) {
          setError(body.detail || "Confirm your shop first.");
          return;
        }
        setMedia(body.media || []);
        setHandle(body.handle || "");
        if (body.warning) setError(body.warning);
      } catch {
        if (!cancelled) setError("Could not reach the API.");
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  function toggle(id: string) {
    setSelected((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  const selectedIds = Object.entries(selected)
    .filter(([, on]) => on)
    .map(([id]) => id);

  async function importSelected() {
    if (!selectedIds.length) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/onboarding/catalog/import/instagram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ media_ids: selectedIds }),
      });
      const body = (await response.json().catch(() => ({}))) as {
        detail?: string;
        errors?: { detail?: string }[];
        review?: string;
      };
      if (!response.ok) {
        setError(body.detail || "Import failed.");
        setBusy(false);
        return;
      }
      if (body.errors?.length) {
        setError(body.errors.map((e) => e.detail).filter(Boolean).join(" · "));
      }
      router.push(body.review || "/onboarding/catalog/review");
    } catch {
      setError("Import failed.");
      setBusy(false);
    }
  }

  async function onUpload(files: FileList | null) {
    if (!files?.length) return;
    setUploadBusy(true);
    setError("");
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
        review?: string;
      };
      if (!response.ok) {
        setError(body.detail || "Upload failed.");
        setUploadBusy(false);
        return;
      }
      router.push(body.review || "/dashboard?tab=catalog");
    } catch {
      setError("Upload failed.");
      setUploadBusy(false);
    }
  }

  async function saveDrive() {
    if (!driveUrl.trim()) return;
    setDriveBusy(true);
    setError("");
    try {
      const response = await fetch("/api/onboarding/catalog/import/drive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_url: driveUrl.trim() }),
      });
      const body = (await response.json().catch(() => ({}))) as {
        detail?: string;
        next?: string;
      };
      if (!response.ok) {
        setError(body.detail || "Could not import Drive folder.");
        setDriveBusy(false);
        return;
      }
      router.push(body.next || "/dashboard?tab=catalog");
    } catch {
      setError("Could not import Drive folder.");
      setDriveBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-4">
          <Link href="/" aria-label="Sell-Safe home">
            <SellSafeLogo height={26} />
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link href="/dashboard?tab=catalog&skipped=1" className="font-medium text-primary">
              Skip to dashboard
            </Link>
            <Link href="/onboarding/shop" className="text-muted-foreground hover:text-foreground">
              Back to shop
            </Link>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-10">
        <p className="mb-2 text-sm text-muted-foreground">Step 2 · Catalog import (optional)</p>
        <h1 className="mb-2 text-3xl font-semibold tracking-tight">Import products</h1>
        <p className="mb-6 max-w-2xl text-muted-foreground">
          Tick Instagram posts, upload photos/videos, or paste a Drive link. Or skip — you can manage
          catalog anytime on the dashboard.
          {handle ? (
            <>
              {" "}
              Connected as <span className="font-medium text-foreground">@{handle}</span>.
            </>
          ) : null}
        </p>

        {error ? (
          <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
            {error}
          </p>
        ) : null}

        <div className="mb-8 flex flex-wrap gap-3">
          <Link
            href="/dashboard?tab=catalog&skipped=1"
            className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground"
          >
            Skip — open dashboard catalog
          </Link>
          <Link
            href="/onboarding/catalog/review"
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-border px-5 text-sm font-medium"
          >
            Review drafts
          </Link>
        </div>

        <section className="mb-8 rounded-xl border border-border p-5">
          <h2 className="mb-2 text-lg font-semibold">Upload photos & videos</h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Multi-select images and videos. Files stay in your shop&apos;s media shelf. Images can be
            drafted into products; videos show on the dashboard catalog.
          </p>
          <input
            type="file"
            accept="image/*,video/*"
            multiple
            disabled={uploadBusy}
            onChange={(e) => void onUpload(e.target.files)}
            className="block w-full text-sm"
          />
          {uploadBusy ? <p className="mt-2 text-sm text-muted-foreground">Saving uploads…</p> : null}
        </section>

        <section className="mb-8 rounded-xl border border-border p-5">
          <h2 className="mb-2 text-lg font-semibold">Google Drive link</h2>
          <p className="mb-2 text-sm text-muted-foreground">
            Paste a folder link. Files named like{" "}
            <code>Honey beans - NGN 6000.jpg</code> import with the price attached.
          </p>
          <p className="mb-4 rounded-lg border border-border bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
            Share → General access → <strong>Anyone with the link</strong> (Viewer). Private
            folders cannot be imported with the API key.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              className="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm"
              placeholder="https://drive.google.com/drive/folders/…"
              value={driveUrl}
              onChange={(e) => setDriveUrl(e.target.value)}
            />
            <button
              type="button"
              disabled={driveBusy || !driveUrl.trim()}
              onClick={() => void saveDrive()}
              className="rounded-md border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {driveBusy ? "Importing…" : "Import folder"}
            </button>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Import from Instagram posts</h2>
          {!media.length ? (
            <p className="rounded-xl border border-border bg-muted p-6 text-sm text-muted-foreground">
              No Instagram posts available right now. Use upload, Drive, or skip to the dashboard
              catalog — you are not blocked.
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
              {media.map((item) => {
                const on = !!selected[item.id];
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => toggle(item.id)}
                    className={`overflow-hidden rounded-xl border text-left transition ${
                      on ? "border-primary ring-2 ring-primary/30" : "border-border"
                    }`}
                  >
                    <div className="aspect-square bg-muted">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={item.thumbnail_url || item.media_url || ""}
                        alt=""
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <div className="space-y-1 p-2">
                      <p className="line-clamp-2 text-xs text-muted-foreground">
                        {item.caption || "No caption"}
                      </p>
                      <p className="text-xs font-medium">{on ? "Selected" : "Tap to select"}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            type="button"
            disabled={busy || selectedIds.length === 0}
            onClick={() => void importSelected()}
            className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
          >
            {busy ? "Drafting…" : `Draft ${selectedIds.length || ""} selected`}
          </button>
          <Link href="/dashboard?tab=catalog&skipped=1" className="text-sm text-muted-foreground underline">
            Skip to dashboard
          </Link>
        </div>
      </main>
    </div>
  );
}
