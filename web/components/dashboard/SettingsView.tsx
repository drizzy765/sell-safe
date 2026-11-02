"use client";

import { useEffect, useState } from "react";

import { DashboardSettings, ShopProfile } from "./types";

type Props = {
  settings: DashboardSettings;
  shop: ShopProfile | null;
  busy: boolean;
  onSave: (patch: Partial<DashboardSettings>) => Promise<void>;
  onSaveShop: (patch: Record<string, unknown>) => Promise<void>;
};

export function SettingsView({ settings, shop, busy, onSave, onSaveShop }: Props) {
  const [name, setName] = useState(shop?.name || "");
  const [phone, setPhone] = useState(shop?.phone || "");
  const [location, setLocation] = useState(shop?.location || "");
  const [deliveryAreas, setDeliveryAreas] = useState(shop?.delivery_areas || "");
  const [bankName, setBankName] = useState(shop?.bank_name || "");
  const [accountName, setAccountName] = useState(shop?.account_name || "");
  const [accountNumber, setAccountNumber] = useState("");
  const [sellerEmail, setSellerEmail] = useState(settings.seller_email || "");

  useEffect(() => {
    setName(shop?.name || "");
    setPhone(shop?.phone || "");
    setLocation(shop?.location || "");
    setDeliveryAreas(shop?.delivery_areas || "");
    setBankName(shop?.bank_name || "");
    setAccountName(shop?.account_name || "");
    setAccountNumber("");
    setSellerEmail(settings.seller_email || "");
  }, [shop, settings.seller_email]);

  async function saveShopInfo() {
    const patch: Record<string, unknown> = {
      name: name.trim(),
      phone: phone.trim(),
      location: location.trim(),
      delivery_areas: deliveryAreas.trim(),
      bank_name: bankName.trim(),
      account_name: accountName.trim(),
    };
    const digits = accountNumber.replace(/\D/g, "");
    if (digits) {
      patch.account_number = digits;
    }
    await onSaveShop(patch);
  }

  const accountHint = shop?.account_number_set
    ? `Saved ${shop.account_number_masked || "••••"} — enter a new number to replace`
    : "Digits only — buyers need this to pay";

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-semibold text-[#17172a]">Settings</h1>
      <p className="mb-8 text-sm text-[#6b6b80]">
        Shop profile, payout account, reply mode. Update anytime after onboarding.
      </p>

      <section className="mb-8 rounded-2xl border border-[#e8e8f0] bg-white p-5">
        <h2 className="mb-1 text-sm font-semibold text-[#17172a]">Shop info</h2>
        <p className="mb-4 text-xs text-[#6b6b80]">
          @{shop?.handle || "shop"} · edit name and contact without redoing Connect.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm sm:col-span-2">
            <span className="mb-1 block text-xs font-medium text-[#6b6b80]">Shop name</span>
            <input
              value={name}
              disabled={busy}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-[#6b6b80]">Phone</span>
            <input
              value={phone}
              disabled={busy}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+234…"
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-[#6b6b80]">Location</span>
            <input
              value={location}
              disabled={busy}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Lagos"
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2"
            />
          </label>
          <label className="block text-sm sm:col-span-2">
            <span className="mb-1 block text-xs font-medium text-[#6b6b80]">Delivery areas</span>
            <input
              value={deliveryAreas}
              disabled={busy}
              onChange={(e) => setDeliveryAreas(e.target.value)}
              placeholder="Mainland, Island…"
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2"
            />
          </label>
        </div>
      </section>

      <section className="mb-8 rounded-2xl border border-[#e8e8f0] bg-white p-5">
        <h2 className="mb-1 text-sm font-semibold text-[#17172a]">Payout account</h2>
        <p className="mb-4 text-xs text-[#6b6b80]">
          Buyers asking for account number get these details in DM. Leave blank and the bot will
          say transfer details are not set yet.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-[#6b6b80]">Bank name</span>
            <input
              value={bankName}
              disabled={busy}
              onChange={(e) => setBankName(e.target.value)}
              placeholder="Opay / GTBank…"
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-[#6b6b80]">Account name</span>
            <input
              value={accountName}
              disabled={busy}
              onChange={(e) => setAccountName(e.target.value)}
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2"
            />
          </label>
          <label className="block text-sm sm:col-span-2">
            <span className="mb-1 block text-xs font-medium text-[#6b6b80]">Account number</span>
            <input
              value={accountNumber}
              disabled={busy}
              onChange={(e) => setAccountNumber(e.target.value)}
              placeholder={accountHint}
              inputMode="numeric"
              autoComplete="off"
              className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2"
            />
          </label>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void saveShopInfo()}
          className="mt-4 rounded-full bg-[#2876fe] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        >
          Save shop &amp; payout
        </button>
      </section>

      <section className="mb-8 rounded-2xl border border-[#e8e8f0] bg-white p-5">
        <h2 className="mb-3 text-sm font-semibold text-[#17172a]">Reply mode</h2>
        <p className="mb-4 text-xs text-[#6b6b80]">
          Sell-Safe · powered by Muse. Default for new chats (per-chat override lives on the thread).
        </p>
        <div className="flex flex-wrap gap-2">
          {(["auto", "approve", "smart"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              disabled={busy}
              onClick={() => void onSave({ reply_mode: mode })}
              className={`rounded-full px-4 py-2 text-sm font-semibold uppercase ${
                settings.reply_mode === mode
                  ? "bg-[#2876fe] text-white"
                  : "border border-[#e4e4e7] text-[#6b6b80] hover:bg-[#f7f7fb]"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
        <ul className="mt-4 space-y-1 text-xs text-[#6b6b80]">
          <li>
            <strong>AUTO</strong> — replies send immediately to Instagram.
          </li>
          <li>
            <strong>APPROVE</strong> — AI drafts wait for Approve &amp; send in the inbox.
          </li>
          <li>
            <strong>SMART</strong> — simple questions auto; discounts, payments, refunds, or orders
            above the ₦ threshold need approval.
          </li>
        </ul>
        <label className="mt-4 block text-sm">
          <span className="mb-1 block text-xs font-medium text-[#6b6b80]">
            SMART threshold (₦)
          </span>
          <input
            type="number"
            min={0}
            defaultValue={settings.smart_threshold_ngn}
            disabled={busy}
            onBlur={(e) =>
              void onSave({ smart_threshold_ngn: Number(e.target.value) || 0 })
            }
            className="w-40 rounded-lg border border-[#e4e4e7] px-3 py-2"
          />
        </label>
      </section>

      <section className="mb-8 rounded-2xl border border-[#e8e8f0] bg-white p-5">
        <h2 className="mb-3 text-sm font-semibold text-[#17172a]">Approvals email</h2>
        <input
          type="email"
          value={sellerEmail}
          placeholder="you@example.com"
          disabled={busy}
          onChange={(e) => setSellerEmail(e.target.value)}
          onBlur={() => void onSave({ seller_email: sellerEmail })}
          className="w-full rounded-lg border border-[#e4e4e7] px-3 py-2 text-sm"
        />
        <p className="mt-2 text-xs text-[#6b6b80]">
          Used for &quot;Sell-Safe: approve reply…&quot; mail when APPROVE/SMART drafts are ready
          (delivery wiring next; drafts always show in Inbox).
        </p>
      </section>

      <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold text-amber-950">Demo data</h2>
            <p className="mt-1 text-xs text-amber-900/80">
              Off by default. When on, sample chats/receipts appear <em>in addition</em> to real
              Instagram DMs, clearly labeled Demo.
            </p>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void onSave({ demo_mode: !settings.demo_mode })}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
              settings.demo_mode
                ? "bg-amber-600 text-white"
                : "border border-amber-300 bg-white text-amber-900"
            }`}
          >
            {settings.demo_mode ? "On" : "Off"}
          </button>
        </div>
      </section>
    </div>
  );
}
