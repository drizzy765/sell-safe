"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type ShopMedia = {
  id: string;
  caption?: string;
  media_url?: string;
  thumbnail_url?: string;
  permalink?: string;
};

type Shop = {
  id: string;
  handle: string;
  name: string;
  bio: string;
  logo_url: string;
  category: string;
  website: string;
  followers_count?: number | null;
  account_type?: string;
  phone: string;
  location: string;
  delivery_areas: string;
  bank_name: string;
  account_name: string;
  account_number_masked?: string;
  account_number_set?: boolean;
  languages: string[];
  opening_hours: string;
  delivery_policy: string;
  recent_media: ShopMedia[];
  confirmed: boolean;
};

const LANGS = [
  { id: "en", label: "English" },
  { id: "pcm", label: "Pidgin" },
  { id: "yo", label: "Yoruba" },
] as const;

const BUSINESS_CATEGORIES = [
  "Provisions",
  "Fashion",
  "Beauty",
  "Electronics",
  "Food & drinks",
  "Home & living",
  "Services",
  "Other",
] as const;

const inputClass =
  "w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary/30";

export function ConfirmShopForm() {
  const router = useRouter();
  const [shop, setShop] = useState<Shop | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "saving" | "error">("loading");
  const [error, setError] = useState("");
  const [accountNumber, setAccountNumber] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // Don't force refresh=1 on every visit — that re-hits Meta and can 401 the page.
        const response = await fetch("/api/onboarding/shop", { cache: "no-store" });
        const body = (await response.json().catch(() => ({}))) as {
          shop?: Shop;
          detail?: string;
          warning?: string;
        };
        if (cancelled) return;
        if (!response.ok || !body.shop) {
          setStatus("error");
          setError(body.detail || "Could not load shop from Instagram.");
          return;
        }
        setShop(body.shop);
        if (body.warning) {
          setError(body.warning);
        }
        setStatus("ready");
      } catch {
        if (!cancelled) {
          setStatus("error");
          setError("Could not reach the API.");
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  function update<K extends keyof Shop>(key: K, value: Shop[K]) {
    setShop((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function toggleLang(id: string) {
    if (!shop) return;
    const has = shop.languages.includes(id);
    const next = has ? shop.languages.filter((x) => x !== id) : [...shop.languages, id];
    update("languages", next.length ? next : ["en"]);
  }

  async function save(confirm: boolean, goTo?: string) {
    if (!shop) return;
    setStatus("saving");
    setError("");
    try {
      const response = await fetch("/api/onboarding/shop", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: shop.name,
          bio: shop.bio,
          category: shop.category,
          website: shop.website,
          phone: shop.phone,
          location: shop.location,
          delivery_areas: shop.delivery_areas,
          bank_name: shop.bank_name,
          account_name: shop.account_name,
          account_number: accountNumber || undefined,
          languages: shop.languages,
          opening_hours: shop.opening_hours,
          delivery_policy: shop.delivery_policy,
          confirm,
        }),
      });
      const body = (await response.json().catch(() => ({}))) as {
        shop?: Shop;
        next?: string | null;
        skip_to?: string | null;
        detail?: string;
      };
      if (!response.ok || !body.shop) {
        setStatus("error");
        setError(body.detail || "Could not save shop.");
        return;
      }
      setShop(body.shop);
      setAccountNumber("");
      setStatus("ready");
      if (confirm) {
        router.push(goTo || body.next || body.skip_to || "/dashboard?tab=catalog");
      }
    } catch {
      setStatus("error");
      setError("Could not save shop.");
    }
  }

  if (status === "loading") {
    return <p className="text-muted-foreground">Loading your Instagram shop…</p>;
  }

  if (status === "error" && !shop) {
    return (
      <div className="space-y-4 rounded-xl border border-border bg-card p-6">
        <p className="text-red-600">{error}</p>
        <p className="text-sm text-muted-foreground">
          Backend restarts clear the login session. Connect again, and make sure this Instagram
          account is an <strong>Instagram Tester</strong> on the Meta app (Roles → Instagram Testers)
          and has accepted the invite in Instagram → Settings → Apps and websites.
        </p>
        <Link
          className="text-sm font-medium text-primary underline"
          href="/?platform=instagram&stay=1"
        >
          Reconnect Instagram
        </Link>
      </div>
    );
  }

  if (!shop) return null;

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center">
        {shop.logo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={shop.logo_url}
            alt=""
            className="h-20 w-20 rounded-full object-cover ring-1 ring-border"
          />
        ) : (
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted text-xl font-semibold">
            {(shop.name || shop.handle || "?").slice(0, 1).toUpperCase()}
          </div>
        )}
        <div>
          <p className="text-sm text-muted-foreground">Connected Instagram</p>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {shop.name || "Confirm your shop"}
          </h1>
          {shop.handle ? (
            <p className="text-muted-foreground">@{shop.handle}</p>
          ) : (
            <p className="text-muted-foreground">Enter your shop name below to continue</p>
          )}
          {typeof shop.followers_count === "number" ? (
            <p className="text-sm text-muted-foreground">
              {shop.followers_count.toLocaleString()} followers
              {shop.account_type ? ` · ${shop.account_type}` : ""}
            </p>
          ) : null}
        </div>
      </header>

      {error ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
          {error}
        </p>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2">
        <Field label="Shop name">
          <input
            className={inputClass}
            value={shop.name}
            onChange={(e) => update("name", e.target.value)}
          />
        </Field>
        <Field label="Business category">
          <select
            className={inputClass}
            value={
              (BUSINESS_CATEGORIES as readonly string[]).includes(shop.category)
                ? shop.category
                : shop.category
                  ? "Other"
                  : ""
            }
            onChange={(e) => update("category", e.target.value === "Other" ? "Other" : e.target.value)}
          >
            <option value="">Select category</option>
            {BUSINESS_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
          {shop.category === "Other" ||
          (shop.category !== "" &&
            !(BUSINESS_CATEGORIES as readonly string[]).includes(shop.category)) ? (
            <input
              className={`${inputClass} mt-2`}
              value={shop.category === "Other" ? "" : shop.category}
              onChange={(e) => update("category", e.target.value || "Other")}
              placeholder="Type your category"
            />
          ) : null}
        </Field>
        <Field label="Bio" className="md:col-span-2">
          <textarea
            className={`${inputClass} min-h-24`}
            value={shop.bio}
            onChange={(e) => update("bio", e.target.value)}
          />
        </Field>
        <Field label="Website">
          <input
            className={inputClass}
            value={shop.website}
            onChange={(e) => update("website", e.target.value)}
          />
        </Field>
        <Field label="Business WhatsApp / phone">
          <input
            className={inputClass}
            value={shop.phone}
            onChange={(e) => update("phone", e.target.value)}
            placeholder="+234…"
          />
        </Field>
        <Field label="Location">
          <input
            className={inputClass}
            value={shop.location}
            onChange={(e) => update("location", e.target.value)}
            placeholder="Lagos"
          />
        </Field>
        <Field label="Delivery areas">
          <input
            className={inputClass}
            value={shop.delivery_areas}
            onChange={(e) => update("delivery_areas", e.target.value)}
            placeholder="Mainland, Island…"
          />
        </Field>
        <Field label="Bank name">
          <input
            className={inputClass}
            value={shop.bank_name}
            onChange={(e) => update("bank_name", e.target.value)}
          />
        </Field>
        <Field label="Account name">
          <input
            className={inputClass}
            value={shop.account_name}
            onChange={(e) => update("account_name", e.target.value)}
          />
        </Field>
        <Field label="Account number">
          <input
            className={inputClass}
            value={accountNumber}
            onChange={(e) => setAccountNumber(e.target.value)}
            placeholder={
              shop.account_number_set
                ? `Saved ${shop.account_number_masked}`
                : "Digits only — masked after save"
            }
            inputMode="numeric"
            autoComplete="off"
          />
        </Field>
        <Field label="Opening hours" className="md:col-span-2">
          <input
            className={inputClass}
            value={shop.opening_hours}
            onChange={(e) => update("opening_hours", e.target.value)}
            placeholder="Mon–Sat 9am–7pm"
          />
        </Field>
        <Field label="Delivery fee / policy" className="md:col-span-2">
          <textarea
            className={`${inputClass} min-h-20`}
            value={shop.delivery_policy}
            onChange={(e) => update("delivery_policy", e.target.value)}
          />
        </Field>
      </section>

      <section>
        <p className="mb-2 text-sm font-medium">Reply languages</p>
        <div className="flex flex-wrap gap-3">
          {LANGS.map((lang) => (
            <label key={lang.id} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={shop.languages.includes(lang.id)}
                onChange={() => toggleLang(lang.id)}
              />
              {lang.label}
            </label>
          ))}
        </div>
      </section>

      {shop.recent_media?.length ? (
        <section>
          <p className="mb-3 text-sm font-medium">
            Recent Instagram posts ({shop.recent_media.length}) — used next for catalog import
          </p>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6">
            {shop.recent_media.slice(0, 12).map((item) => (
              <a
                key={item.id}
                href={item.permalink || item.media_url || "#"}
                target="_blank"
                rel="noreferrer"
                className="aspect-square overflow-hidden rounded-md border border-border bg-muted"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={item.thumbnail_url || item.media_url || ""}
                  alt=""
                  className="h-full w-full object-cover"
                />
              </a>
            ))}
          </div>
        </section>
      ) : null}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:flex-wrap">
        <button
          type="button"
          disabled={status === "saving"}
          onClick={() => void save(true)}
          className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
        >
          {status === "saving" ? "Saving…" : "Save & continue"}
        </button>
        <button
          type="button"
          disabled={status === "saving"}
          onClick={() => void save(true, "/dashboard?tab=catalog")}
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-border px-5 text-sm font-medium disabled:opacity-50"
        >
          Save & skip to dashboard
        </button>
        <button
          type="button"
          disabled={status === "saving"}
          onClick={() => void save(false)}
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-border px-5 text-sm font-medium disabled:opacity-50"
        >
          Save draft
        </button>
        <Link href="/?platform=instagram&stay=1" className="text-sm text-muted-foreground underline">
          Disconnect / use another account
        </Link>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={`block space-y-1.5 text-sm ${className}`}>
      <span className="font-medium">{label}</span>
      {children}
    </label>
  );
}
