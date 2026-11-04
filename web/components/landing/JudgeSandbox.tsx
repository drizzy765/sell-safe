"use client";

import { FormEvent, useState } from "react";

type Msg = { from: "buyer" | "agent" | "system"; text: string };

const CATALOG: Record<string, number> = {
  "Tomato Paste Carton": 16000,
  "Spaghetti Carton (20 Packs)": 19000,
  "Seasoning Cubes Pack (100)": 1800,
  "Palm Oil 5L": 11000,
  "Long Grain Rice 5kg": 9500,
};

const STARTERS: Msg[] = [
  { from: "agent", text: "Hello! Welcome to Mama Timi Provisions. How can I help you today?" },
];

function agentReply(input: string, paid: boolean): { text: string; system?: string } {
  const t = input.toLowerCase();
  if (t.includes("wetin") || t.includes("what do you have") || t.includes("catalog") || t.includes("what do you sell")) {
    const lines = Object.entries(CATALOG).map(([n, p]) => `• ${n} — ₦${p.toLocaleString("en-NG")}`);
    return { text: `Na wetin we get be this:\n${lines.join("\n")}\nTell me which one you want.` };
  }
  if (t.includes("account") || t.includes("how do i pay") || t.includes("how i go pay")) {
    return { text: "Transfer to Oluwatimilehin Agoro / OPay / 9161842792. After paying, send the receipt photo." };
  }
  for (const [name, price] of Object.entries(CATALOG)) {
    const key = name.toLowerCase().split(" ").slice(0, 2).join(" ");
    if (t.includes(key) || t.includes(name.toLowerCase())) {
      if (t.includes("buy") || t.includes("wan") || t.includes("want") || t.includes("order")) {
        return {
          text: `${name} is ₦${price.toLocaleString("en-NG")}. Transfer to Oluwatimilehin Agoro / OPay / 9161842792, then send the receipt photo make we confirm am.`,
        };
      }
      return { text: `${name} is ₦${price.toLocaleString("en-NG")}. You wan buy am?` };
    }
  }
  if (t.includes("receipt") || t.includes("sent") || t.includes("send am") || t.includes("paid")) {
    return paid
      ? { text: "We don receive am. The seller go confirm from the dashboard — the agent no fit confirm payment by itself." }
      : { text: "Abeg send the receipt photo here make we check am." };
  }
  if (t.includes("hi") || t.includes("hello") || t.includes("how far") || t.includes("good")) {
    return { text: "I dey fine, thank you! Wetin you wan buy today?" };
  }
  return { text: "I fit help you with prices, ordering, and payment. Try: “wetin you get?” or pick a shortcut below." };
}

const CHIPS = [
  "wetin you get?",
  "I wan buy Palm Oil 5L",
  "send account number",
  "I don send am (receipt)",
];

export function JudgeSandbox() {
  const [messages, setMessages] = useState<Msg[]>(STARTERS);
  const [input, setInput] = useState("");
  const [receiptSent, setReceiptSent] = useState(false);
  const [verdict, setVerdict] = useState<null | { ok: boolean }>(null);

  function send(text: string) {
    const clean = text.trim();
    if (!clean) return;
    const reply = agentReply(clean, receiptSent);
    setMessages((m) => [...m, { from: "buyer", text: clean }, { from: "agent", text: reply.text }]);
    setInput("");
  }

  function sendReceipt(fake: boolean) {
    if (receiptSent) return;
    setReceiptSent(true);
    setMessages((m) => [
      ...m,
      { from: "buyer", text: fake ? "📎 transfer-receipt.png (₦11,000 — generated image)" : "📎 transfer-receipt.png (₦11,000)" },
      { from: "agent", text: "Thanks, we go check am quick and confirm soon. Stay tuned." },
    ]);
    window.setTimeout(() => {
      setVerdict({ ok: !fake });
      setMessages((m) => [
        ...m,
        fake
          ? { from: "system", text: "Verdict: SUSPICIOUS — receipt looks generated/tampered, no matching bank evidence. Seller alerted. Goods NOT released. (Deterministic verdict — the LLM never confirms payment.)" }
          : { from: "system", text: "Verdict: needs seller review — screenshot alone never auto-releases. The seller approves in the dashboard, then the buyer is confirmed." },
      ]);
    }, 900);
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="overflow-hidden rounded-3xl border border-[#e8e8f0] bg-white shadow-[0_12px_32px_rgba(40,118,254,0.07)]">
        <div className="flex items-center justify-between bg-[#0b1226] px-4 py-3 text-white">
          <div>
            <p className="text-sm font-semibold">@sellsafe.testshop.ng</p>
            <p className="text-[11px] text-white/60">Sell-Safe agent · auto</p>
          </div>
          <span className="rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-medium">Judge sandbox — no login</span>
        </div>
        <div className="max-h-[380px] space-y-2 overflow-y-auto px-4 py-4" aria-live="polite">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.from === "buyer" ? "justify-end" : "justify-start"}`}>
              <p
                className={`max-w-[85%] whitespace-pre-line rounded-2xl px-3 py-2 text-sm leading-6 ${
                  m.from === "buyer"
                    ? "bg-[#2876fe] text-white"
                    : m.from === "system"
                      ? "border border-amber-200 bg-amber-50 text-amber-950"
                      : "bg-[#f1f1f6] text-[#17172a]"
                }`}
              >
                {m.text}
              </p>
            </div>
          ))}
          {verdict && !verdict.ok ? (
            <p className="rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-center text-xs font-semibold text-red-800">
              Fake caught. This is the whole product: sellers ship only after a real verdict.
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2 px-4 pb-2">
          {CHIPS.map((chip) => (
            <button key={chip} type="button" onClick={() => send(chip)}
              className="min-h-[36px] rounded-full border border-[#e8e8f0] px-3 py-1.5 text-xs font-medium text-[#2876fe] transition-transform active:scale-[0.96]">
              {chip}
            </button>
          ))}
          <button type="button" onClick={() => sendReceipt(true)} disabled={receiptSent}
            className="min-h-[36px] rounded-full bg-[#17172a] px-3 py-1.5 text-xs font-semibold text-white transition-transform active:scale-[0.96] disabled:opacity-40">
            Send fake receipt
          </button>
          <button type="button" onClick={() => sendReceipt(false)} disabled={receiptSent}
            className="min-h-[36px] rounded-full border border-[#e8e8f0] px-3 py-1.5 text-xs font-medium text-[#52525b] transition-transform active:scale-[0.96] disabled:opacity-40">
            Send receipt photo
          </button>
        </div>
        <form onSubmit={submit} className="flex gap-2 border-t border-[#f1f1f6] px-4 py-3">
          <label className="sr-only" htmlFor="sandbox-input">Message the shop</label>
          <input id="sandbox-input" value={input} onChange={(e) => setInput(e.target.value)}
            placeholder="Message as a buyer… try pidgin"
            className="min-h-[44px] flex-1 rounded-full border border-[#e8e8f0] px-4 text-sm outline-none focus:ring-2 focus:ring-[#2876fe]/40" />
          <button type="submit" className="min-h-[44px] rounded-full bg-gradient-brand px-4 text-sm font-semibold text-white transition-transform active:scale-[0.96]">
            Send
          </button>
        </form>
      </div>
      <p className="mt-3 text-center text-xs leading-5 text-[#8a8aa3]">
        Same deterministic flows as the live agent (catalog, payout, verdict). Real shops reply
        on Instagram via Meta Muse — connect yours to try it on your own account.
      </p>
    </div>
  );
}
