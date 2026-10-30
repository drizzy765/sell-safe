"use client";

import { useState } from "react";

export function PaymentSafetyDemo() {
  const [activeTab, setActiveTab] = useState<"fake" | "real" | null>(null);

  return (
    <div className="rounded-xl border border-border bg-card p-8">
      <div className="mb-6 text-center">
        <h2 className="mb-2 text-2xl font-bold">How Sell-Safe Protects You</h2>
        <p className="text-muted-foreground">
          Every payment is checked against real bank data before goods leave your shop
        </p>
      </div>

      {/* Demo Tabs */}
      <div className="mb-6 grid grid-cols-2 gap-4">
        <button
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
          <p className="text-sm text-muted-foreground">
            Edited amount, no real payment
          </p>
        </button>

        <button
          onClick={() => setActiveTab("real")}
          className={`rounded-lg border-2 p-4 text-left transition-colors ${
            activeTab === "real"
              ? "border-green-500 bg-green-50"
              : "border-border hover:border-green-300"
          }`}
        >
          <div className="mb-2 flex items-center space-x-2">
            <div className="h-3 w-3 rounded-full bg-green-500" />
            <span className="font-semibold text-green-700">Real Payment</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Confirmed by Paystack webhook
          </p>
        </button>
      </div>

      {/* Fake Screenshot Demo */}
      {activeTab === "fake" && (
        <div className="space-y-4 rounded-lg bg-red-50 p-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 rounded-lg bg-white p-2 shadow-sm">
              <div className="h-24 w-40 rounded bg-gray-200 flex items-center justify-center">
                <span className="text-xs text-gray-500">[Fake Screenshot]</span>
              </div>
            </div>
            <div className="flex-1">
              <h4 className="mb-1 font-semibold text-red-900">What Sell-Safe Sees</h4>
              <ul className="space-y-1 text-sm text-red-800">
                <li>• Amount: ₦50,000 → edited to ₦20,000</li>
                <li>• No matching Paystack webhook</li>
                <li>• Visual anomalies detected</li>
              </ul>
            </div>
          </div>

          <div className="rounded-lg border border-red-200 bg-white p-4">
            <div className="mb-2 flex items-center space-x-2">
              <svg className="h-5 w-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="font-bold text-red-900">VERDICT: SUSPICIOUS</span>
            </div>
            <p className="text-sm text-red-800">
              <strong>Do not release goods.</strong> No matching payment found.
            </p>
          </div>

          <div className="text-center text-sm text-red-700">
            Seller saved from losing ₦20,000 worth of goods
          </div>
        </div>
      )}

      {/* Real Payment Demo */}
      {activeTab === "real" && (
        <div className="space-y-4 rounded-lg bg-green-50 p-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 space-y-2">
              <div className="rounded-lg bg-white p-2 shadow-sm">
                <div className="h-24 w-40 rounded bg-gray-200 flex items-center justify-center">
                  <span className="text-xs text-gray-500">[Real Screenshot]</span>
                </div>
              </div>
              <div className="rounded-lg bg-blue-100 p-2 text-center">
                <span className="text-xs font-medium text-blue-800">Paystack Webhook</span>
              </div>
            </div>
            <div className="flex-1">
              <h4 className="mb-1 font-semibold text-green-900">What Sell-Safe Sees</h4>
              <ul className="space-y-1 text-sm text-green-800">
                <li>• Screenshot: ₦20,000</li>
                <li>• Paystack webhook: ₦20,000</li>
                <li>• Reference matches: SS-1042</li>
                <li>• Status: successful</li>
              </ul>
            </div>
          </div>

          <div className="rounded-lg border border-green-200 bg-white p-4">
            <div className="mb-2 flex items-center space-x-2">
              <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="font-bold text-green-900">VERDICT: CONFIRMED</span>
            </div>
            <p className="text-sm text-green-800">
              <strong>Payment verified.</strong> Goods can be released.
            </p>
          </div>

          <div className="text-center text-sm text-green-700">
            Seller safely ships goods with confirmed payment
          </div>
        </div>
      )}

      {!activeTab && (
        <div className="text-center text-muted-foreground">
          Click a tab above to see how Sell-Safe catches fake payments
        </div>
      )}

      {/* Trust Badges */}
      <div className="mt-6 grid grid-cols-3 gap-4 border-t border-border pt-6">
        <div className="text-center">
          <div className="mb-1 text-2xl font-bold">AI Vision</div>
          <div className="text-xs text-muted-foreground">Reads every screenshot</div>
        </div>
        <div className="text-center">
          <div className="mb-1 text-2xl font-bold">Bank Data</div>
          <div className="text-xs text-muted-foreground">Matches real payments</div>
        </div>
        <div className="text-center">
          <div className="mb-1 text-2xl font-bold">Instant</div>
          <div className="text-xs text-muted-foreground">Under 10 seconds</div>
        </div>
      </div>
    </div>
  );
}
