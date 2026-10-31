"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import { BorderBeam } from "@/components/magicui/border-beam";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { ShieldSpinner } from "@/components/ShieldSpinner";
import { cn } from "@/lib/utils";

type DemoTab = "fake" | "real" | "crypto" | null;

type CryptoCase = {
  label: string;
  verdict: string;
  reason: string | null;
  tx_hash: string;
  amount_usdc: string | null;
  to_address: string | null;
  confirmations: number | null;
  explorer_url: string | null;
  network: string;
};

type CryptoDemo = {
  ready: boolean;
  message: string | null;
  cases: CryptoCase[] | null;
};

type Phase = "idle" | "scanning" | "done";

const SCAN_STEPS = ["Reading receipt…", "Matching Paystack…", "Writing verdict…"] as const;

function CaseCard({ item }: { item: CryptoCase }) {
  const ok = item.verdict === "CONFIRMED";
  const pending = item.verdict === "PENDING";
  const tone = ok
    ? "border-success/40 bg-success/10 text-foreground"
    : pending
      ? "border-warning/40 bg-warning/10 text-foreground"
      : "border-danger/40 bg-danger/10 text-foreground";
  return (
    <article className={cn("rounded-[10px] border p-4", tone)}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <h4 className="font-semibold capitalize">{item.label}</h4>
        <span className="text-sm font-bold">{item.verdict}</span>
      </div>
      <ul className="space-y-1 text-sm text-muted-foreground">
        {item.reason ? <li>Reason: {item.reason}</li> : null}
        {item.amount_usdc ? <li>Amount: {item.amount_usdc}</li> : null}
        {item.to_address ? <li className="break-all">To: {item.to_address}</li> : null}
        {item.confirmations != null ? <li>Confirmations: {item.confirmations}</li> : null}
        <li className="break-all font-mono text-xs">Tx: {item.tx_hash}</li>
        {item.explorer_url ? (
          <li>
            <a
              className="underline underline-offset-2"
              href={item.explorer_url}
              target="_blank"
              rel="noreferrer"
            >
              View on Basescan
            </a>
          </li>
        ) : null}
      </ul>
    </article>
  );
}

function ScanChecklist({ active }: { active: boolean }) {
  const [visible, setVisible] = useState(0);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (!active) {
      setVisible(0);
      return;
    }
    if (reduce) {
      setVisible(SCAN_STEPS.length);
      return;
    }
    setVisible(1);
    const timers = [
      window.setTimeout(() => setVisible(2), 380),
      window.setTimeout(() => setVisible(3), 760),
    ];
    return () => timers.forEach(clearTimeout);
  }, [active, reduce]);

  if (!active) return null;

  return (
    <ul className="mx-auto mb-6 flex w-full max-w-sm flex-col gap-2" aria-live="polite">
      <AnimatePresence initial={false}>
        {SCAN_STEPS.slice(0, visible).map((label) => (
          <motion.li
            key={label}
            initial={reduce ? false : { opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", duration: 0.3, bounce: 0 }}
            className="flex items-center gap-2 rounded-[10px] border border-border bg-muted/50 px-3 py-2 text-sm text-foreground"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-brand-blue" aria-hidden />
            {label}
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}

function VerdictBadge({
  tone,
  label,
  detail,
}: {
  tone: "danger" | "success";
  label: string;
  detail: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-2 rounded-[10px] border bg-background px-4 py-3 motion-safe:animate-badge-pop",
        tone === "danger" ? "border-danger/40" : "border-success/40",
      )}
    >
      <span
        className={cn(
          "inline-flex items-center gap-1.5 text-sm font-bold",
          tone === "danger" ? "text-danger" : "text-success",
        )}
      >
        <span aria-hidden>{tone === "danger" ? "⚠" : "✓"}</span>
        {label}
      </span>
      <p className="text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}

const TABS: { id: Exclude<DemoTab, null>; label: string; hint: string; accent: string }[] = [
  { id: "fake", label: "Fake screenshot", hint: "Edited amount, no real payment", accent: "danger" },
  { id: "real", label: "Real bank payment", hint: "Confirmed by Paystack webhook", accent: "success" },
  { id: "crypto", label: "USDC on Base", hint: "Live: real, reused, and fake hashes", accent: "primary" },
];

export function PaymentSafetyDemo({
  className,
  showCta = true,
}: {
  className?: string;
  showCta?: boolean;
}) {
  const reduce = useReducedMotion();
  const [activeTab, setActiveTab] = useState<DemoTab>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [crypto, setCrypto] = useState<CryptoDemo | null>(null);
  const [cryptoError, setCryptoError] = useState("");

  const selectTab = (tab: Exclude<DemoTab, null>) => {
    setActiveTab(tab);
    setCrypto(null);
    setCryptoError("");
    if (reduce) {
      setPhase("done");
      return;
    }
    setPhase("scanning");
    window.setTimeout(() => setPhase("done"), 1400);
  };

  useEffect(() => {
    if (activeTab !== "crypto" || phase !== "done") return;
    let cancelled = false;
    setCryptoError("");
    fetch("/api/demo/crypto")
      .then(async (response) => {
        const body = (await response.json()) as CryptoDemo;
        if (!cancelled) setCrypto(body);
      })
      .catch(() => {
        if (!cancelled) setCryptoError("Could not load the live crypto demo.");
      });
    return () => {
      cancelled = true;
    };
  }, [activeTab, phase]);

  const shieldState =
    phase === "scanning"
      ? "scanning"
      : phase === "done" && activeTab === "fake"
        ? "suspicious"
        : phase === "done" && activeTab === "real"
          ? "confirmed"
          : phase === "done" && activeTab === "crypto"
            ? "pending"
            : "idle";

  return (
    <div className={cn("relative", className)}>
      <div className="mb-10 text-center">
        <h2 className="mb-3 text-2xl font-semibold tracking-tight md:text-[28px]">
          See a fake payment get caught.
        </h2>
        <p className="mx-auto max-w-2xl text-muted-foreground">
          Tap a proof type. Sell-Safe checks real payment rails — not the picture alone.
        </p>
      </div>

      {/* Outer 24 = inner 12 + padding 12 */}
      <div className="rounded-xl bg-gradient-brand-soft p-3 md:p-4">
        <div className="relative mx-auto max-w-3xl overflow-hidden rounded-lg border border-border bg-background p-5 shadow-panel md:p-8">
          {phase === "scanning" ? <BorderBeam duration={4} size={100} /> : null}

          <div className="mb-5 flex flex-col items-center gap-3">
            <ShieldSpinner state={shieldState} size={56} />
            <p className="text-sm text-muted-foreground" aria-live="polite">
              {phase === "scanning"
                ? "Checking payment proof…"
                : phase === "done"
                  ? "Verdict ready"
                  : "Pick a proof type to try"}
            </p>
          </div>

          <ScanChecklist active={phase === "scanning"} />

          <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {TABS.map((tab) => {
              const selected = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => selectTab(tab.id)}
                  className={cn(
                    "min-h-[72px] rounded-[10px] border p-4 text-left transition-colors duration-150 active:scale-[0.98]",
                    selected
                      ? tab.accent === "danger"
                        ? "border-danger bg-danger/5"
                        : tab.accent === "success"
                          ? "border-success bg-success/5"
                          : "border-primary bg-primary/5"
                      : "border-border hover:border-brand-mid/40",
                  )}
                >
                  <span className="block text-sm font-semibold">{tab.label}</span>
                  <span className="mt-1 block text-xs text-muted-foreground">{tab.hint}</span>
                </button>
              );
            })}
          </div>

          {phase === "done" && activeTab === "fake" ? (
            <div className="space-y-4 rounded-[10px] border border-danger/30 bg-danger/5 p-5">
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>
                  Amount: ₦
                  <NumberTicker value={50000} className="font-money" /> → edited to ₦
                  <NumberTicker value={20000} delay={0.2} className="font-money" />
                </li>
                <li>No matching Paystack webhook</li>
                <li>Visual anomalies detected</li>
              </ul>
              <VerdictBadge
                tone="danger"
                label="SUSPICIOUS"
                detail="This looks edited. Don't send the goods yet."
              />
            </div>
          ) : null}

          {phase === "done" && activeTab === "real" ? (
            <div className="space-y-4 rounded-[10px] border border-success/30 bg-success/5 p-5">
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>
                  Screenshot: ₦
                  <NumberTicker value={20000} className="font-money" />
                </li>
                <li>
                  Paystack webhook: ₦
                  <NumberTicker value={20000} delay={0.15} className="font-money" />
                </li>
                <li>Reference matches: SS-1042</li>
                <li>Status: successful</li>
              </ul>
              <VerdictBadge
                tone="success"
                label="CONFIRMED"
                detail="Paystack matches. Safe to pack."
              />
            </div>
          ) : null}

          {phase === "done" && activeTab === "crypto" ? (
            <div className="space-y-4">
              {cryptoError ? <p className="text-sm text-danger">{cryptoError}</p> : null}
              {crypto && !crypto.ready ? (
                <p className="rounded-[10px] border border-warning/40 bg-warning/10 p-4 text-sm">
                  {crypto.message || "Crypto demo is not ready."}
                </p>
              ) : null}
              {crypto?.ready && crypto.cases ? (
                <div className="grid gap-4 md:grid-cols-3">
                  {crypto.cases.map((item) => (
                    <CaseCard key={`${item.label}-${item.tx_hash}`} item={item} />
                  ))}
                </div>
              ) : null}
              {!crypto && !cryptoError ? (
                <p className="text-sm text-muted-foreground">Loading live Base Sepolia checks…</p>
              ) : null}
              {crypto?.ready ? (
                <p className="text-sm text-muted-foreground">
                  CONFIRMED when USDC lands on Base for your order — reused hashes stay SUSPICIOUS.
                </p>
              ) : null}
            </div>
          ) : null}

          {showCta ? (
            <p className="mt-8 text-center">
              <Link
                href="/?platform=instagram"
                className="inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-6 text-sm font-semibold text-primary-foreground transition-transform duration-150 active:scale-[0.96] hover:opacity-90"
              >
                Start selling
              </Link>
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
