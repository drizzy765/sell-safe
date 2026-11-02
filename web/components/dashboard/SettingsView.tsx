"use client";

import { DashboardSettings } from "./types";

type Props = {
  settings: DashboardSettings;
  busy: boolean;
  onSave: (patch: Partial<DashboardSettings>) => Promise<void>;
};

export function SettingsView({ settings, busy, onSave }: Props) {
  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-semibold text-[#17172a]">Settings</h1>
      <p className="mb-8 text-sm text-[#6b6b80]">
        Reply mode, approvals, and demo data (demo never fills a quiet Instagram inbox by default).
      </p>

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
            <strong>APPROVE</strong> — AI drafts wait for Approve & send in the inbox.
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
          defaultValue={settings.seller_email}
          placeholder="you@example.com"
          disabled={busy}
          onBlur={(e) => void onSave({ seller_email: e.target.value })}
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
