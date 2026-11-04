"use client";

import { Summary, formatNaira } from "./types";

function Chip({ text, tone }: { text: string; tone: "green" | "red" | "amber" | "gray" }) {
  const styles = {
    green: "bg-emerald-50 text-emerald-800",
    red: "bg-red-50 text-red-800",
    amber: "bg-amber-50 text-amber-900",
    gray: "bg-[#f1f1f6] text-[#52525b]",
  }[tone];
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ${styles}`}>{text}</span>;
}

function verdictTone(verdict: string) {
  if (verdict === "CONFIRMED") return "green" as const;
  if (verdict === "SUSPICIOUS" || verdict === "UNVERIFIED") return "red" as const;
  if (verdict === "NOT_FOUND") return "amber" as const;
  return "gray" as const;
}

const LANG_LABEL: Record<string, string> = { en: "English", pcm: "Pidgin", yo: "Yoruba" };

export function AnalyticsView({ data }: { data: Summary }) {
  const a = data.analytics;
  const stats = data.stats;
  const customers = a?.customers || [];
  const receipts = data.receipts || [];
  const langEntries = Object.entries(a?.languages || {});
  const maxLang = Math.max(1, ...langEntries.map(([, n]) => n));
  const verdictEntries = Object.entries(a?.verdicts || {});

  return (
    <div className="mx-4 mt-4 space-y-4 sm:mx-6">
      <section aria-label="Chat analysis" className="rounded-3xl border border-[#e8e8f0] bg-white p-4">
        <h2 className="text-sm font-semibold text-[#17172a]">Chat analysis</h2>
        <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">Conversations</p><p className="text-lg font-semibold tabular-nums">{a?.total_conversations ?? 0}</p></div>
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">Customers</p><p className="text-lg font-semibold tabular-nums">{a?.total_customers ?? 0}</p></div>
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">AI managed</p><p className="text-lg font-semibold tabular-nums">{a?.ai_managed ?? 0}</p></div>
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">Seller takeover</p><p className="text-lg font-semibold tabular-nums">{a?.seller_takeover ?? 0}</p></div>
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">Pending drafts</p><p className="text-lg font-semibold tabular-nums">{stats.pending_drafts ?? 0}</p></div>
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">Unread</p><p className="text-lg font-semibold tabular-nums">{stats.unread_inbox ?? 0}</p></div>
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">Buyers who ordered</p><p className="text-lg font-semibold tabular-nums">{a?.buyers_with_orders ?? 0}</p></div>
          <div><p className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">Order conversion</p><p className="text-lg font-semibold tabular-nums">{a?.order_conversion_pct ?? 0}%</p></div>
        </div>
        {langEntries.length ? (
          <div className="mt-4 space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-[#8a8aa3]">Languages buyers used</h3>
            {langEntries.map(([lang, count]) => (
              <div key={lang} className="flex items-center gap-3">
                <span className="w-16 text-xs text-[#52525b]">{LANG_LABEL[lang] || lang}</span>
                <div className="h-2 flex-1 rounded-full bg-[#f1f1f6]" role="img" aria-label={`${LANG_LABEL[lang] || lang}: ${count} chats`}>
                  <div className="h-2 rounded-full bg-[#2876fe]" style={{ width: `${Math.round((count / maxLang) * 100)}%` }} />
                </div>
                <span className="text-xs tabular-nums text-[#52525b]">{count}</span>
              </div>
            ))}
          </div>
        ) : null}
        {verdictEntries.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {verdictEntries.map(([v, n]) => <Chip key={v} text={`${v}: ${n}`} tone={verdictTone(v)} />)}
          </div>
        ) : null}
      </section>

      <section aria-label="Customer log" className="rounded-3xl border border-[#e8e8f0] bg-white p-4">
        <h2 className="text-sm font-semibold text-[#17172a]">Customer log</h2>
        {customers.length === 0 ? (
          <p className="mt-2 text-sm text-[#8a8aa3]">No customers yet. Buyer chats will appear here with orders, language and payment history.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead><tr className="text-[11px] uppercase tracking-wide text-[#8a8aa3]">
                <th className="py-2 pr-3 font-medium">Customer</th><th className="py-2 pr-3 font-medium">Language</th>
                <th className="py-2 pr-3 font-medium">Last message</th><th className="py-2 pr-3 font-medium">Orders</th>
                <th className="py-2 pr-3 font-medium">Verified paid</th><th className="py-2 pr-3 font-medium">Fakes</th>
                <th className="py-2 font-medium">Status</th>
              </tr></thead>
              <tbody>
                {customers.map((c) => (
                  <tr key={c.buyer_id} className="border-t border-[#f1f1f6]">
                    <td className="py-2 pr-3 font-medium text-[#17172a]">{c.buyer || c.buyer_id}{c.unread ? <span className="ml-2 rounded-full bg-[#dd2a7b] px-1.5 py-0.5 text-[10px] font-bold text-white">{c.unread}</span> : null}</td>
                    <td className="py-2 pr-3 text-[#52525b]">{LANG_LABEL[c.language || "en"] || c.language}</td>
                    <td className="max-w-[220px] truncate py-2 pr-3 text-[#52525b]">{c.last_message || "—"}</td>
                    <td className="py-2 pr-3 tabular-nums">{c.orders}</td>
                    <td className="py-2 pr-3 tabular-nums">{formatNaira(c.verified_ngn)}</td>
                    <td className="py-2 pr-3 tabular-nums">{c.fakes}</td>
                    <td className="py-2">{c.paused ? <Chip text="Seller handling" tone="amber" /> : c.last_verdict ? <Chip text={c.last_verdict} tone={verdictTone(c.last_verdict)} /> : <Chip text="AI active" tone="gray" />}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-label="Payment verification log" className="rounded-3xl border border-[#e8e8f0] bg-white p-4">
        <h2 className="text-sm font-semibold text-[#17172a]">Payment verification log</h2>
        {receipts.length === 0 ? (
          <p className="mt-2 text-sm text-[#8a8aa3]">No receipts checked yet. Every receipt a buyer sends gets a verdict here — the AI never confirms payment itself.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {receipts.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center gap-2 rounded-2xl bg-[#fafafa] px-3 py-2 text-sm">
                <Chip text={r.verdict} tone={verdictTone(r.verdict)} />
                <span className="font-semibold tabular-nums">{formatNaira(r.amount_ngn)}</span>
                {r.order_ref ? <span className="text-xs text-[#8a8aa3]">Order {r.order_ref}</span> : null}
                {r.reasons?.length ? <span className="text-xs text-[#52525b]">{r.reasons.join(", ")}</span> : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
