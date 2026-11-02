"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { CatalogView } from "@/components/dashboard/CatalogView";
import { InboxView } from "@/components/dashboard/InboxView";
import { SettingsView } from "@/components/dashboard/SettingsView";
import {
  DashboardSettings,
  NavTab,
  Summary,
} from "@/components/dashboard/types";
import { SellSafeLogo } from "@/components/SellSafeLogo";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Could not read file"));
    reader.readAsDataURL(file);
  });
}

function DashboardInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tabParam = (searchParams.get("tab") || "catalog") as NavTab;
  const [tab, setTab] = useState<NavTab>(
    ["inbox", "catalog", "orders", "outreach", "settings"].includes(tabParam)
      ? tabParam
      : "catalog",
  );
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

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
    if (["inbox", "catalog", "orders", "outreach", "settings"].includes(tabParam)) {
      setTab(tabParam);
    }
  }, [tabParam]);

  useEffect(() => {
    if (searchParams.get("skipped") === "1") {
      void fetch("/api/dashboard/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ catalog_skipped: true }),
      }).then(() => load());
      router.replace("/dashboard?tab=catalog");
    }
  }, [searchParams, router, load]);

  function switchTab(next: NavTab) {
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
        return;
      }
      const draftCount = body.drafts?.length || 0;
      setMessage(
        draftCount
          ? `Saved ${body.media?.length || 0} file(s); ${draftCount} draft(s) ready to review.`
          : `Saved ${body.media?.length || 0} file(s) to your catalog shelf.`,
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

  async function onDrive(driveUrl: string) {
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
      const body = (await response.json().catch(() => ({}))) as {
        detail?: string;
        drafts?: unknown[];
        approved?: unknown[];
        errors?: { detail?: string; filename?: string }[];
      };
      if (!response.ok) {
        setError(body.detail || "Could not import Drive folder.");
        return;
      }
      setMessage(body.detail || "Drive import finished.");
      if (body.errors?.length) {
        setError(
          body.errors
            .map((e) => `${e.filename || "file"}: ${e.detail || "error"}`)
            .join(" · "),
        );
      }
      await load();
    } catch {
      setError("Could not import Drive folder.");
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

  async function saveSettings(patch: Partial<DashboardSettings>) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/dashboard/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) {
        setError(body.detail || "Could not save settings.");
        return;
      }
      await load();
    } finally {
      setBusy(false);
    }
  }

  if (!data && !error) {
    return (
      <main className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
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

  const settings = data!.settings;
  const unread = data!.stats.unread_inbox || 0;
  const shopHandle = data!.shop?.handle || data!.session_username || "shop";

  const nav: { id: NavTab; label: string; badge?: number }[] = [
    { id: "inbox", label: "Inbox", badge: unread || undefined },
    { id: "catalog", label: "Catalog" },
    { id: "orders", label: "Orders" },
    { id: "outreach", label: "Outreach" },
    { id: "settings", label: "Settings" },
  ];

  return (
    <div className="flex min-h-screen bg-[#fafafa] text-[#262626]">
      <aside className="flex w-[220px] shrink-0 flex-col border-r border-[#efefef] bg-[#111827] text-white">
        <div className="border-b border-white/10 px-4 py-4">
          <Link href="/" className="inline-block brightness-0 invert">
            <SellSafeLogo height={24} />
          </Link>
          <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-white/50">
            secure. smart. trusted.
          </p>
        </div>
        <nav className="flex-1 space-y-1 px-2 py-3">
          {nav.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => switchTab(item.id)}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm ${
                tab === item.id
                  ? "bg-[#2876fe] font-semibold text-white"
                  : "text-white/75 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span>{item.label}</span>
              {item.badge ? (
                <span className="rounded-full bg-[#dd2a7b] px-1.5 py-0.5 text-[10px] font-bold">
                  {item.badge}
                </span>
              ) : null}
            </button>
          ))}
        </nav>
        <div className="border-t border-white/10 px-4 py-3">
          <p className="truncate text-xs font-medium">{shopHandle}</p>
          <p className="truncate text-[11px] text-white/50">{data!.shop?.name || "Test Shop"}</p>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        {tab === "inbox" ? (
          <InboxView
            handle={shopHandle}
            replyMode={settings.reply_mode}
            conversations={data!.inbox || []}
            onRefresh={load}
            onModeChange={async (mode) => {
              await saveSettings({ reply_mode: mode });
            }}
          />
        ) : null}

        {tab === "catalog" ? (
          <CatalogView
            data={data!}
            settings={settings}
            busy={busy}
            message={message}
            error={error}
            onUpload={onUpload}
            onDrive={onDrive}
            onRemoveMedia={removeMedia}
            onDismissSkipBanner={async () => {
              await saveSettings({ catalog_skipped: false });
            }}
          />
        ) : null}

        {tab === "settings" ? (
          <SettingsView settings={settings} busy={busy} onSave={saveSettings} />
        ) : null}

        {tab === "orders" ? (
          <Placeholder
            title="Orders"
            body="Kanban (inquiry → awaiting payment → paid & verified → delivered) lands after the Nov 3–4 benchmark freeze."
          />
        ) : null}

        {tab === "outreach" ? (
          <Placeholder
            title="Outreach"
            body="Seller-picked one-at-a-time pitches (no cold mass DMs). Open after inbox + catalog are solid — paste a handle → draft → open ig.me/m/…"
          />
        ) : null}
      </main>
    </div>
  );
}

function Placeholder({ title, body }: { title: string; body: string }) {
  return (
    <div className="mx-auto max-w-lg px-6 py-16 text-center">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-2 text-sm text-[#8e8e8e]">{body}</p>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
          Loading dashboard…
        </main>
      }
    >
      <DashboardInner />
    </Suspense>
  );
}
