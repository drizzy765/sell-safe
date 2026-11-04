"use client";

import { useState } from "react";
import Link from "next/link";
import { SellSafeLogo } from "@/components/SellSafeLogo";

const CONFUSION: Record<string, Record<string, number>> = {
  CONFIRMED: { CONFIRMED: 5, NOT_FOUND: 0, SUSPICIOUS: 0, UNVERIFIED: 0 },
  NOT_FOUND: { CONFIRMED: 0, NOT_FOUND: 4, SUSPICIOUS: 0, UNVERIFIED: 0 },
  SUSPICIOUS: { CONFIRMED: 0, NOT_FOUND: 0, SUSPICIOUS: 7, UNVERIFIED: 0 },
  UNVERIFIED: { CONFIRMED: 0, NOT_FOUND: 0, SUSPICIOUS: 0, UNVERIFIED: 4 },
};
const VERDICTS = Object.keys(CONFUSION);

const VISION = [
  { model: "Muse vision (muse-wonder-1.0)", exact: 1, abstain: 3, wrong: 0 },
  { model: "Groq vision (qwen/qwen3.8-27b)", exact: 0, abstain: 4, wrong: 0 },
];

const TRACKS = ["Payments", "Vision", "Chat & Safety", "Voice"] as const;

function Bar({ label, value, max, suffix }: { label: string; value: number; max: number; suffix?: string }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      className="flex items-center gap-3"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <span className="w-44 shrink-0 text-xs text-[#52525b]">{label}</span>
      <div className="relative h-6 flex-1 rounded-lg bg-[#f1f1f6]" role="img" aria-label={`${label}: ${value}${suffix || ""} of ${max}`}>
        <div
          className={`h-6 rounded-lg transition-all duration-500 ${hover ? "bg-[#6e4af7]" : "bg-[#2876fe]"}`}
          style={{ width: `${Math.max(4, Math.round((value / max) * 100))}%` }}
        />
        {hover ? (
          <span className="absolute -top-7 left-2 rounded-md bg-[#17172a] px-2 py-0.5 text-[11px] font-semibold text-white">
            {value}{suffix || ""} / {max}
          </span>
        ) : null}
      </div>
      <span className="w-12 text-right text-xs font-semibold tabular-nums">{value}{suffix || ""}</span>
    </div>
  );
}

export default function BenchmarkPage() {
  const [track, setTrack] = useState<(typeof TRACKS)[number]>("Payments");
  const [cell, setCell] = useState<string | null>(null);

  return (
    <main className="min-h-screen bg-[#fafafa] text-[#17172a]">
      <header className="border-b border-[#efefef] bg-white px-4 py-3">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <Link href="/"><SellSafeLogo height={24} /></Link>
          <Link href="/docs" className="text-sm font-medium text-[#2876fe] underline">Docs</Link>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="text-2xl font-semibold">Benchmark: Meta Muse in Sell-Safe</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#52525b]">
          Measured 2026-11-04 on the live system and repo eval suite. The LLM never decides
          payment verdicts — deterministic rules do. Hover any chart for exact values.
        </p>

        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ["Payments passed", "20/20"],
            ["False CONFIRMED", "0"],
            ["Injections blocked", "6/6"],
            ["Confident-wrong fields", "0"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-[#e8e8f0] bg-white p-4">
              <p className="text-[11px] font-medium uppercase tracking-wide text-[#8a8aa3]">{label}</p>
              <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap gap-2" role="tablist" aria-label="Benchmark tracks">
          {TRACKS.map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={track === t}
              onClick={() => setTrack(t)}
              className={`min-h-[40px] rounded-full px-4 py-2 text-sm font-medium transition-transform active:scale-[0.96] ${
                track === t ? "bg-gradient-brand text-white" : "border border-[#e8e8f0] bg-white text-[#52525b]"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {track === "Payments" ? (
          <section className="mt-4 rounded-3xl border border-[#e8e8f0] bg-white p-4" aria-label="Payments confusion matrix">
            <h2 className="text-sm font-semibold">Verdict confusion matrix (20 synthetic cases)</h2>
            <p className="mt-1 text-xs text-[#8a8aa3]">Rows: expected verdict. Columns: actual. Hover a cell for the count.{cell ? ` Selected: ${cell}` : ""}</p>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[480px] text-center text-sm">
                <thead>
                  <tr><th className="p-2 text-left text-xs text-[#8a8aa3]">Expected \ Actual</th>
                    {VERDICTS.map((v) => <th key={v} className="p-2 text-xs text-[#8a8aa3]">{v}</th>)}</tr>
                </thead>
                <tbody>
                  {VERDICTS.map((row) => (
                    <tr key={row}>
                      <th className="p-2 text-left text-xs font-medium">{row}</th>
                      {VERDICTS.map((col) => {
                        const n = CONFUSION[row][col];
                        const active = n > 0;
                        return (
                          <td key={col} className="p-1">
                            <button
                              type="button"
                              onMouseEnter={() => setCell(`${row} → ${col}: ${n} case(s)`)}
                              onFocus={() => setCell(`${row} → ${col}: ${n} case(s)`)}
                              className={`h-12 w-full rounded-xl text-sm font-semibold tabular-nums transition-transform active:scale-[0.96] ${
                                active ? "bg-[#2876fe] text-white" : "bg-[#f7f7fa] text-[#c6c6d4]"
                              }`}
                              aria-label={`${row} expected, ${col} actual: ${n}`}
                            >
                              {n}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs leading-5 text-[#52525b]">
              Every fake, edited, reused, or tampered receipt landed off the CONFIRMED column.
              Source: <code>evals/reports/2026-11-04-payments-c851352.md</code>
            </p>
          </section>
        ) : null}

        {track === "Vision" ? (
          <section className="mt-4 space-y-4 rounded-3xl border border-[#e8e8f0] bg-white p-4" aria-label="Vision comparison">
            <h2 className="text-sm font-semibold">Fake-transfer / catalog vision: Muse vs Groq (n=4 labeled photos)</h2>
            {VISION.map((row) => (
              <div key={row.model} className="space-y-2">
                <h3 className="text-xs font-semibold text-[#17172a]">{row.model}</h3>
                <Bar label="Exact name + price" value={row.exact} max={4} />
                <Bar label="Abstained / failed safely" value={row.abstain} max={4} />
                <Bar label="Confident-wrong fields" value={row.wrong} max={4} />
              </div>
            ))}
            <p className="text-xs leading-5 text-[#52525b]">
              Muse never invents fields it cannot read — it abstains and the seller is asked.
              Groq hit JSON-generation and rate-limit failures as fallback. Small Tier C sample;
              full comparison is in the micro1 plan.
            </p>
          </section>
        ) : null}

        {track === "Chat & Safety" ? (
          <section className="mt-4 space-y-3 rounded-3xl border border-[#e8e8f0] bg-white p-4" aria-label="Chat and safety">
            <h2 className="text-sm font-semibold">Routing + injection defence (unit bench)</h2>
            <Bar label="English browse routed" value={1} max={1} />
            <Bar label="Pidgin browse routed" value={1} max={1} />
            <Bar label="Yoruba browse routed" value={1} max={1} />
            <Bar label="Prompt injections blocked" value={6} max={6} />
            <Bar label="Pidgin order row matches goal" value={1} max={1} />
            <p className="text-xs leading-5 text-[#52525b]">
              The bench caught a real bug: bare “i wan buy” hijacked orders into the browse
              reply. Fixed and regression-tested the same day.
            </p>
          </section>
        ) : null}

        {track === "Voice" ? (
          <section className="mt-4 rounded-3xl border border-[#e8e8f0] bg-white p-4" aria-label="Voice pipeline">
            <h2 className="text-sm font-semibold">Voice-note pipeline (live, 2026-11-04)</h2>
            <ol className="mt-4 space-y-2">
              {[
                ["Buyer voice note (Pidgin)", "“How far now, how you dey, how everything dey go?”"],
                ["Intron Sahara transcript", "Recovered word-for-word in the dashboard inbox"],
                ["Muse reply in Pidgin", "“I dey fine, thank you! Wetin you wan buy today?”"],
                ["Fallback if STT fails", "Provider transcribe → safe “please type that” reply"],
              ].map(([step, detail], i) => (
                <li key={step} className="flex gap-3 rounded-2xl bg-[#fafafa] px-3 py-2 text-sm">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#2876fe] text-xs font-bold text-white">{i + 1}</span>
                  <span><strong className="font-semibold">{step}:</strong> <span className="text-[#52525b]">{detail}</span></span>
                </li>
              ))}
            </ol>
          </section>
        ) : null}

        <p className="mt-6 text-xs leading-5 text-[#8a8aa3]">
          Full write-ups: <Link className="underline" href="/docs">Docs</Link> ·{" "}
          <code>docs/benchmark_muse.md</code> · <code>docs/benchmark_micro1.md</code> ·
          Payments report <code>evals/report.md</code>. Samples are Tier C synthetic
          (payments n=20, vision n=4); limitations are stated in the docs, not hidden.
        </p>
      </div>
    </main>
  );
}
