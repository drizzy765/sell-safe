"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { CatalogView } from "@/components/dashboard/CatalogView";
import { AnalyticsView } from "@/components/dashboard/AnalyticsView";
import { InboxView } from "@/components/dashboard/InboxView";
import { SettingsView } from "@/components/dashboard/SettingsView";
import {
  DashboardSettings,
  NavTab,
  Summary,
} from "@/components/dashboard/types";
import { SellSafeLogo } from "@/components/SellSafeLogo";
import { StatusStrip } from "@/components/dashboard/StatusStrip";
import { Inbox, LayoutGrid, LogIn, LogOut, Megaphone, Settings, ShoppingBag } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Could not read file"));
    reader.readAsDataURL(file);
  });
}


const DEMO_SUMMARY: Summary = {
  shop: {
    id: "demo-shop", name: "Mama Timi Provisions", handle: "sellsafe.testshop.ng",
    account_number_set: true, account_number_masked: "••••2792", bank_name: "OPay",
    account_name: "Oluwatimilehin Agoro", reply_mode: "auto",
  },
  stats: { chats_today: 3, orders: 2, naira_verified: 11000, fakes_caught: 1, avg_reply_seconds: 4, unread_inbox: 1, pending_drafts: 1 },
  products: [
    { id: "p1", name: "Palm Oil 5L", price_ngn: 11000, category: "Oils", description: "", image_urls: [], stock_status: "in_stock", status: "live" },
    { id: "p2", name: "Tomato Paste Carton", price_ngn: 16000, category: "Provisions", description: "", image_urls: [], stock_status: "in_stock", status: "live" },
    { id: "p3", name: "Long Grain Rice 5kg", price_ngn: 9500, category: "Grains", description: "", image_urls: [], stock_status: "in_stock", status: "live" },
  ],
  drafts: [], media: [],
  inbox: [
    { id: "c1", buyer_id: "b1", channel: "instagram", buyer: "testicles22", language: "pcm", preview: "I don send am (receipt)", reply: "Thanks, we go check am quick and confirm soon.", at: "today 12:45", unread: 1, paused: false, reply_mode: "auto", demo: true },
    { id: "c2", buyer_id: "b2", channel: "instagram", buyer: "adaeze_styles", language: "pcm", preview: "Abeg how much be the honey beans?", reply: "Na ₦6,000 per paint bucket.", at: "today 10:14", unread: 0, paused: false, reply_mode: "auto", demo: true },
  ],
  receipts: [
    { id: "r1", verdict: "SUSPICIOUS", amount_ngn: 11000, reasons: ["receipt looks generated", "no matching bank evidence"], order_ref: "SS-1001", buyer_id: "b1" },
  ],
  reply_drafts: [],
  settings: { reply_mode: "auto", smart_threshold_ngn: 50000, demo_mode: true, seller_email: "", catalog_skipped: false },
  demo_mode: true,
  analytics: {
    total_conversations: 2, total_customers: 2, languages: { pcm: 2 }, ai_managed: 2, seller_takeover: 0,
    verdicts: { SUSPICIOUS: 1 }, buyers_with_orders: 1, order_conversion_pct: 50,
    customers: [
      { buyer_id: "b1", buyer: "testicles22", language: "pcm", last_message: "I don send am (receipt)", orders: 1, verified_ngn: 0, fakes: 1, last_verdict: "SUSPICIOUS", unread: 1, paused: false },
      { buyer_id: "b2", buyer: "adaeze_styles", language: "pcm", last_message: "Abeg how much be the honey beans?", orders: 0, verified_ngn: 0, fakes: 0, last_verdict: "", unread: 0, paused: false },
    ],
  },
};

function DashboardInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const demoMode = searchParams.get("demo") === "1";
  const tabParam = (searchParams.get("tab") || (demoMode ? "inbox" : "catalog")) as NavTab;
  const [tab, setTab] = useState<NavTab>(
    ["inbox", "catalog", "orders", "outreach", "settings"].includes(tabParam)
      ? tabParam
      : "catalog",
  );
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [auth, setAuth] = useState<{ authenticated: boolean; email?: string; linked?: boolean }>({
    authenticated: false,
  });
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    void fetch("/api/auth/me", { cache: "no-store" })
      .then((r) => r.json())
      .then(setAuth)
      .catch(() => undefined);
  }, []);

  async function linkAccount() {
    const response = await fetch("/api/auth/link", { method: "POST" });
    if (response.ok) setAuth((a) => ({ ...a, linked: true }));
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => undefined);
    setAuth({ authenticated: false });
  }

  const load = useCallback(async () => {
    if (demoMode) {
      setData(DEMO_SUMMARY);
      setError("");
      return;
    }
    const response = await fetch("/api/dashboard/summary", { cache: "no-store" });
    const body = (await response.json().catch(() => ({}))) as Summary & { detail?: string };
    if (!response.ok) {
      setError(body.detail || "Connect Instagram and confirm your shop first.");
      setData(null);
      return;
    }
    setData(body);
    setError("");
  }, [demoMode]);

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
    router.replace(demoMode ? `/dashboard?demo=1&tab=${next}` : `/dashboard?tab=${next}`);
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
    setMessage("");
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
      setMessage("Settings saved.");
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function saveShop(patch: Record<string, unknown>) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/onboarding/shop", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) {
        setError(body.detail || "Could not save shop info.");
        return;
      }
      setMessage("Shop & payout details saved.");
      await load();
    } catch {
      setError("Could not save shop info.");
    } finally {
      setBusy(false);
    }
  }

  if (!data && !error) {
    return (
      <main className="mx-auto min-h-screen max-w-5xl px-4 py-10" aria-busy="true" aria-label="Loading dashboard">
        <div className="h-8 w-44 animate-pulse rounded-lg bg-[#ececf4]" />
        <div className="mt-6 h-36 animate-pulse rounded-3xl bg-[#f1f1f8]" />
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-2xl bg-[#f1f1f8]" />
          ))}
        </div>
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

  const nav: { id: NavTab; label: string; badge?: number; Icon: typeof Inbox }[] = [
    { id: "inbox", label: "Inbox", badge: unread || undefined, Icon: Inbox },
    { id: "catalog", label: "Catalog", Icon: LayoutGrid },
    { id: "orders", label: "Analysis", Icon: ShoppingBag },
    { id: "outreach", label: "Outreach", Icon: Megaphone },
    { id: "settings", label: "Settings", Icon: Settings },
  ];

  return (
    <div className="flex min-h-screen bg-[#fafafa] text-[#262626]">
      <aside className="hidden w-[228px] shrink-0 flex-col border-r border-[#efefef] bg-[#0b1226] text-white lg:flex">
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
              className={`flex min-h-[44px] w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm transition-[background-color,color,transform] active:scale-[0.96] ${
                tab === item.id
                  ? "bg-gradient-brand font-semibold text-white"
                  : "text-white/75 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span className="inline-flex items-center gap-2.5">
                <item.Icon size={17} strokeWidth={tab === item.id ? 2 : 1.5} aria-hidden />
                {item.label}
              </span>
              {item.badge ? (
                <span className="rounded-full bg-[#dd2a7b] px-1.5 py-0.5 text-[10px] font-bold">
                  {item.badge}
                </span>
              ) : null}
            </button>
          ))}
        </nav>
        <div className="border-t border-white/10 px-4 py-3 text-xs">
          {auth.authenticated ? (
            <>
              <p className="truncate text-white/85">{auth.email}</p>
              <p className="mt-0.5 text-white/50">{auth.linked ? "Shop saved to your account" : "Shop not saved yet"}</p>
              <div className="mt-2 flex gap-3">
                {!auth.linked ? (
                  <button type="button" onClick={() => void linkAccount()} className="font-semibold text-[#7db3ff] underline">
                    Save my shop
                  </button>
                ) : null}
                <button type="button" onClick={() => void logout()} className="inline-flex items-center gap-1 text-white/60 underline">
                  <LogOut size={12} aria-hidden /> Logout
                </button>
              </div>
            </>
          ) : (
            <Link href="/login" className="inline-flex min-h-[40px] items-center gap-2 font-semibold text-[#7db3ff]">
              <LogIn size={14} aria-hidden /> Login to save your shop
            </Link>
          )}
        </div>
        <button
          type="button"
          onClick={() => switchTab("settings")}
          className="border-t border-white/10 px-4 py-3 text-left transition-colors hover:bg-white/5"
          title="Edit shop & payout info"
        >
          <p className="truncate text-xs font-medium">{shopHandle}</p>
          <p className="truncate text-[11px] text-white/50">{data!.shop?.name || "Test Shop"}</p>
          <p className="mt-1 text-[10px] text-[#2876fe]">Edit shop info →</p>
        </button>
      </aside>

      <main className="min-w-0 flex-1 pb-20 lg:pb-0">
        <header className="flex items-center justify-between border-b border-[#efefef] bg-white px-4 py-3 lg:hidden">
          <SellSafeLogo height={22} />
          <span className="max-w-[45%] truncate text-xs font-medium text-[#52525b]">@{shopHandle}</span>
        </header>
        <StatusStrip data={data!} shopHandle={shopHandle} onOpenSettings={() => switchTab("settings")} />
        {message && tab === "settings" ? (
          <p className="mx-6 mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-950">
            {message}
          </p>
        ) : null}
        {error && data ? (
          <p className="mx-6 mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
            {error}
          </p>
        ) : null}
        <motion.div
          key={tab}
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: [0.2, 0, 0, 1] }}
        >
        {tab === "inbox" ? (
          <InboxView
            handle={shopHandle}
            replyMode={settings.reply_mode}
            conversations={data!.inbox || []}
            inboxSync={data!.inbox_sync}
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
          <SettingsView
            settings={settings}
            shop={data!.shop}
            busy={busy}
            onSave={saveSettings}
            onSaveShop={saveShop}
          />
        ) : null}

        {tab === "orders" ? <AnalyticsView data={data!} /> : null}

        {tab === "outreach" ? (
          <Placeholder
            title="Outreach"
            body="Seller-picked one-at-a-time pitches (no cold mass DMs). Open after inbox + catalog are solid — paste a handle → draft → open ig.me/m/…"
          />
        ) : null}
        </motion.div>
        <nav aria-label="Dashboard" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-[#e8e8f0] bg-white/95 backdrop-blur lg:hidden">
          {nav.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => switchTab(item.id)}
              aria-current={tab === item.id ? "page" : undefined}
              className={`flex min-h-[56px] flex-col items-center justify-center gap-1 text-[10px] transition-[color,transform] active:scale-[0.96] ${
                tab === item.id ? "font-semibold text-[#2876fe]" : "text-[#6b6b80]"
              }`}
            >
              <span className="relative">
                <item.Icon size={20} strokeWidth={tab === item.id ? 2 : 1.5} aria-hidden />
                {item.badge ? (
                  <span className="absolute -right-2 -top-1 rounded-full bg-[#dd2a7b] px-1 text-[9px] font-bold text-white">{item.badge}</span>
                ) : null}
              </span>
              {item.label}
            </button>
          ))}
        </nav>
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
