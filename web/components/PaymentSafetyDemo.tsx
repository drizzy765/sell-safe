"use client";

import { useEffect, useState } from "react";

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

function CaseCard({ item }: { item: CryptoCase }) {
  const ok = item.verdict === "CONFIRMED";
  const pending = item.verdict === "PENDING";
  const tone = ok
    ? "border-green-200 bg-green-50 text-green-900"
    : pending
      ? "border-amber-200 bg-amber-50 text-amber-900"
      : "border-red-200 bg-red-50 text-red-900";
  return (
    <article className={`rounded-lg border p-4 ${tone}`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <h4 className="font-semibold capitalize">{item.label}</h4>
        <span className="text-sm font-bold">{item.verdict}</span>
      </div>
      <ul className="space-y-1 text-sm">
        {item.reason ? <li>Reason: {item.reason}</li> : null}
        {item.amount_usdc ? <li>Amount: {item.amount_usdc}</li> : null}
        {item.to_address ? (
          <li className="break-all">To: {item.to_address}</li>
        ) : null}
        {item.confirmations != null ? <li>Confirmations: {item.confirmations}</li> : null}
        <li className="break-all">Tx: {item.tx_hash}</li>
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

export function PaymentSafetyDemo() {
  const [activeTab, setActiveTab] = useState<DemoTab>(null);
  const [crypto, setCrypto] = useState<CryptoDemo | null>(null);
  const [cryptoError, setCryptoError] = useState("");

  useEffect(() => {
    if (activeTab !== "crypto") return;
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
  }, [activeTab]);

  return (
    <div className="rounded-xl border border-border bg-card p-8">
      <div className="mb-6 text-center">
        <h2 className="mb-2 text-2xl font-bold">How Sell-Safe Protects You</h2>
        <p className="text-muted-foreground">
          Every payment is checked against real bank or on-chain data before goods leave your shop
        </p>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <button
          type="button"
          onClick={() => setActiveTab("fake")}
          className={`rounded-lg border-2 p-4 text-left transition-colors ${
            activeTab === "fake"
              ? "border-red-500 bg-red-50"
              : "border-border hover:border-red-300"
          }`}
        >
          <div className="mb-2 flex items-center space-x-2">
            <div className="h-3 w-3 rounded-full bg-red-500" />
            <span className="font-semibold text-red-700">Fake Screenshot</span>
          </div>
          <p className="text-sm text-muted-foreground">Edited amount, no real payment</p>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("real")}
          className={`rounded-lg border-2 p-4 text-left transition-colors ${
            activeTab === "real"
              ? "border-green-500 bg-green-50"
              : "border-border hover:border-green-300"
          }`}
        >
          <div className="mb-2 flex items-center space-x-2">
            <div className="h-3 w-3 rounded-full bg-green-500" />
            <span className="font-semibold text-green-700">Real Bank Payment</span>
          </div>
          <p className="text-sm text-muted-foreground">Confirmed by Paystack webhook</p>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("crypto")}
          className={`rounded-lg border-2 p-4 text-left transition-colors ${
            activeTab === "crypto"
              ? "border-blue-500 bg-blue-50"
              : "border-border hover:border-blue-300"
          }`}
        >
          <div className="mb-2 flex items-center space-x-2">
            <div className="h-3 w-3 rounded-full bg-blue-500" />
            <span className="font-semibold text-blue-700">USDC on Base</span>
          </div>
          <p className="text-sm text-muted-foreground">Live: real, reused, and fake hashes</p>
        </button>
      </div>

      {activeTab === "fake" && (
        <div className="space-y-4 rounded-lg bg-red-50 p-6">
          <h4 className="mb-1 font-semibold text-red-900">What Sell-Safe Sees</h4>
          <ul className="space-y-1 text-sm text-red-800">
            <li>• Amount: ₦50,000 → edited to ₦20,000</li>
            <li>• No matching Paystack webhook</li>
            <li>• Visual anomalies detected</li>
          </ul>
          <div className="rounded-lg border border-red-200 bg-white p-4">
            <span className="font-bold text-red-900">VERDICT: SUSPICIOUS</span>
            <p className="mt-2 text-sm text-red-800">
              <strong>Do not release goods.</strong> No matching payment found.
            </p>
          </div>
        </div>
      )}

      {activeTab === "real" && (
        <div className="space-y-4 rounded-lg bg-green-50 p-6">
          <h4 className="mb-1 font-semibold text-green-900">What Sell-Safe Sees</h4>
          <ul className="space-y-1 text-sm text-green-800">
            <li>• Screenshot: ₦20,000</li>
            <li>• Paystack webhook: ₦20,000</li>
            <li>• Reference matches: SS-1042</li>
            <li>• Status: successful</li>
          </ul>
          <div className="rounded-lg border border-green-200 bg-white p-4">
            <span className="font-bold text-green-900">VERDICT: CONFIRMED</span>
            <p className="mt-2 text-sm text-green-800">
              <strong>Payment verified.</strong> Goods can be released.
            </p>
          </div>
        </div>
      )}

      {activeTab === "crypto" && (
        <div className="space-y-4">
          {cryptoError ? <p className="text-sm text-red-600">{cryptoError}</p> : null}
          {crypto && !crypto.ready ? (
            <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
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
        </div>
      )}

      {!activeTab && (
        <div className="text-center text-muted-foreground">
          Click a tab above to see how Sell-Safe catches fake payments
        </div>
      )}

      <p className="mt-6 text-center">
        <a
          href="#steps"
          className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Start selling
        </a>
      </p>
    </div>
  );
}
