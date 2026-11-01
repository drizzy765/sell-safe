"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  onConnected?: (username?: string) => void;
  onDisconnected?: () => void;
};

type ConnectStatus = "loading" | "idle" | "connecting" | "connected" | "error";

type StatusBody = {
  connected?: boolean;
  oauth_configured?: boolean;
  username?: string | null;
  account_id?: string | null;
  detail?: string;
  offline?: boolean;
};

export function InstagramConnect({ onConnected, onDisconnected }: Props) {
  const [status, setStatus] = useState<ConnectStatus>("loading");
  const [username, setUsername] = useState("");
  const [error, setError] = useState("");
  const onConnectedRef = useRef(onConnected);
  onConnectedRef.current = onConnected;

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const params = new URLSearchParams(window.location.search);
      const igError = params.get("ig_error");
      if (igError) {
        if (!cancelled) {
          setStatus("error");
          setError(igError);
        }
      }

      try {
        const response = await fetch("/api/instagram/status", { cache: "no-store" });
        const body = (await response.json().catch(() => ({}))) as StatusBody;
        if (cancelled) return;
        if (body.connected) {
          const name = body.username || params.get("ig_user") || "";
          setStatus("connected");
          setUsername(name);
          onConnectedRef.current?.(name || undefined);
          // Already connected sellers go straight to Confirm your shop (Feature 1).
          if (params.get("platform") === "instagram" && !params.get("stay")) {
            window.location.replace("/onboarding/shop");
            return;
          }
          return;
        }
        if (!igError) {
          setStatus("idle");
        }
        if (body.detail && !body.oauth_configured) {
          setError(body.detail);
          setStatus("error");
        }
      } catch {
        if (!cancelled && !igError) {
          setStatus("error");
          setError("Could not reach Instagram status. Try again.");
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleConnect() {
    setStatus("connecting");
    setError("");
    const returnTo = "/onboarding/shop";
    window.location.href = `/api/instagram/oauth/start?return_to=${encodeURIComponent(returnTo)}&force_reauth=true`;
  }

  async function handleDisconnect() {
    setStatus("connecting");
    setError("");
    try {
      const response = await fetch("/api/instagram/disconnect", { method: "POST" });
      if (!response.ok) {
        setStatus("error");
        setError("Could not disconnect. Try again.");
        return;
      }
      setUsername("");
      setStatus("idle");
      onDisconnected?.();
    } catch {
      setStatus("error");
      setError("Could not disconnect. Try again.");
    }
  }

  const busy = status === "connecting" || status === "loading";
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

      {connected ? (
        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <button
            type="button"
            disabled
            className="inline-flex items-center justify-center rounded-md bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 px-6 py-3 text-sm font-medium text-white opacity-80"
          >
            Connected{username ? ` · @${username}` : ""}
          </button>
          <button
            type="button"
            onClick={() => void handleDisconnect()}
            disabled={busy}
            className="inline-flex items-center justify-center rounded-md border border-border px-6 py-3 text-sm font-medium hover:bg-muted disabled:opacity-50"
          >
            Disconnect
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={handleConnect}
          disabled={busy}
          className="inline-flex items-center justify-center rounded-md bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 px-6 py-3 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {status === "connecting" ? "Connecting..." : status === "loading" ? "Checking..." : "Connect Instagram"}
        </button>
      )}

      <p className="mt-4 text-sm" role="status" aria-live="polite">
        {connected ? (
          <span className="text-foreground">
            {username
              ? `@${username} connected. Sell-Safe can reply to this account's DMs.`
              : "Instagram connected. Sell-Safe can reply to your DMs."}
          </span>
        ) : null}
        {status === "error" ? <span className="text-red-600">{error}</span> : null}
      </p>

      <p className="mt-4 text-xs text-muted-foreground">
        We only read messages you receive. We never post on your behalf. Disconnect anytime to
        connect a different Instagram Business account.
      </p>
    </div>
  );
}
