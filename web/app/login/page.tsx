"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { SellSafeLogo } from "@/components/SellSafeLogo";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) throw new Error(body.detail || "Could not send the login link.");
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the login link.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-4 py-10">
      <div className="w-full rounded-3xl border border-border bg-card p-8 shadow-panel">
        <SellSafeLogo height={28} />
        <h1 className="mt-6 text-2xl font-semibold tracking-tight">Save your shop</h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Login once and your Instagram connection, payout details, and dashboard are restored on
          any device. No password to remember.
        </p>
        {sent ? (
          <div className="mt-6 rounded-2xl bg-gradient-brand-soft p-4 text-sm" role="status">
            Login link sent to <strong>{email}</strong>. Open it on this device to finish.
          </div>
        ) : (
          <form className="mt-6 space-y-3" onSubmit={submit}>
            <label className="block text-sm">
              <span className="mb-1 block text-xs font-medium text-muted-foreground">Email</span>
              <input
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@yourshop.ng"
                className="w-full rounded-xl border border-border bg-background px-3 py-2.5 outline-none transition-shadow focus:ring-2 focus:ring-primary/40"
              />
            </label>
            {error ? (
              <p className="text-sm text-danger" role="alert">
                {error}
              </p>
            ) : null}
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-xl bg-gradient-brand px-4 py-3 text-sm font-semibold text-white transition-transform active:scale-[0.96] disabled:opacity-50"
            >
              {busy ? "Sending…" : "Email me a login link"}
            </button>
          </form>
        )}
        <p className="mt-6 text-xs leading-5 text-muted-foreground">
          New here?{" "}
          <Link className="font-medium text-primary underline" href="/?platform=instagram">
            Connect Instagram first
          </Link>
          , then login from the dashboard to save that shop to your account.
        </p>
      </div>
    </main>
  );
}
