"use client";

import { useState } from "react";

type Props = {
  onConnected?: () => void;
};

type ConnectStatus = "idle" | "connecting" | "connected" | "error";

export function InstagramConnect({ onConnected }: Props) {
  const [status, setStatus] = useState<ConnectStatus>("idle");
  const [error, setError] = useState("");

  async function handleConnect() {
    setStatus("connecting");
    setError("");

    try {
      const response = await fetch("/api/instagram/status");
      const body = (await response.json().catch(() => ({}))) as {
        ready?: boolean;
        offline?: boolean;
        detail?: string;
      };
      if (!response.ok) {
        setStatus("error");
        setError(body.detail || "Could not reach Instagram status. Try again.");
        return;
      }
      if (body.ready === true) {
        setStatus("connected");
        onConnected?.();
        return;
      }
      setStatus("error");
      setError(
        body.offline
          ? "Backend is offline. In another terminal: cd backend && uvicorn app.main:app --reload --port 8000"
          : body.detail || "Instagram Login is not configured on this server.",
      );
    } catch {
      setStatus("error");
      setError("Could not reach Instagram status. Try again.");
    }
  }

  const busy = status === "connecting";
  const connected = status === "connected";

  return (
    <div className="rounded-xl border border-border bg-card p-8 text-center">
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500">
        <svg
          className="h-8 w-8 text-white"
          fill="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
        </svg>
      </div>

      <h3 className="mb-2 text-xl font-semibold">Connect Instagram</h3>
      <p className="mb-6 text-sm text-muted-foreground">
        One click to connect your Instagram Business account. Sell-Safe will answer your DMs
        automatically.
      </p>

      <button
        type="button"
        onClick={handleConnect}
        disabled={busy || connected}
        className="inline-flex items-center justify-center rounded-md bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 px-6 py-3 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
      >
        {busy ? "Connecting..." : connected ? "Connected" : "Connect Instagram"}
      </button>

      <p className="mt-4 text-sm" role="status" aria-live="polite">
        {connected ? (
          <span className="text-foreground">
            Instagram connected. Sell-Safe can reply to your DMs.
          </span>
        ) : null}
        {status === "error" ? <span className="text-red-600">{error}</span> : null}
      </p>

      <p className="mt-4 text-xs text-muted-foreground">
        We only read messages you receive. We never post on your behalf.
      </p>
    </div>
  );
}
