"use client";

import { Summary, formatNaira } from "./types";

type Props = {
  data: Summary;
  shopHandle: string;
  onOpenSettings: () => void;
};

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] font-medium uppercase tracking-wide text-[#8a8aa3]">{label}</p>
      <p className="mt-0.5 truncate text-lg font-semibold tabular-nums text-[#17172a]">{value}</p>
    </div>
  );
}

export function StatusStrip({ data, shopHandle, onOpenSettings }: Props) {
  const payoutSet = Boolean(data.shop?.account_number_set);
  const stats = data.stats;
  return (
    <section
      aria-label="Shop status"
      className="mx-4 mt-4 rounded-3xl border border-[#e8e8f0] bg-white p-4 shadow-[0_1px_2px_rgba(7,25,66,0.05),0_12px_32px_rgba(40,118,254,0.07)] sm:mx-6"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          @{shopHandle} connected
        </span>
        <span className="rounded-full bg-[#eef2ff] px-2.5 py-1 text-xs font-medium text-[#3730a3]">
          AI replies: {data.settings.reply_mode.toUpperCase()}
        </span>
        <button
          type="button"
          onClick={onOpenSettings}
          className={`rounded-full px-2.5 py-1 text-xs font-medium transition-transform active:scale-[0.96] ${
            payoutSet
              ? "bg-emerald-50 text-emerald-800"
              : "bg-amber-100 text-amber-900 underline"
          }`}
        >
          {payoutSet ? `Payout saved ${data.shop?.account_number_masked || ""}` : "Add payout details"}
        </button>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Chats today" value={String(stats.chats_today)} />
        <Stat label="Orders" value={String(stats.orders)} />
        <Stat label="Verified" value={formatNaira(stats.naira_verified)} />
        <Stat label="Fakes caught" value={String(stats.fakes_caught)} />
      </div>
      {!payoutSet ? (
        <p className="mt-3 rounded-xl bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-900">
          Buyers who ask for your account number will be told details are not set.{" "}
          <button type="button" onClick={onOpenSettings} className="font-semibold underline">
            Add them now
          </button>
        </p>
      ) : null}
    </section>
  );
}
