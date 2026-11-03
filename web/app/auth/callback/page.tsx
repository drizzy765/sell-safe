"use client";

import { useEffect, useState } from "react";

export default function AuthCallbackPage() {
  const [error, setError] = useState("");

  useEffect(() => {
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const access_token = hash.get("access_token") || "";
    const refresh_token = hash.get("refresh_token") || "";
    const expires_in = Number(hash.get("expires_in") || 3600);
    if (!access_token) {
      setError("This login link is missing its token. Request a new link.");
      return;
    }
    void fetch("/api/auth/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token, refresh_token, expires_in }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = (await response.json().catch(() => ({}))) as { detail?: string };
          throw new Error(body.detail || "Login failed.");
        }
        window.location.replace("/dashboard?tab=catalog");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-4">
      <div className="w-full rounded-3xl border border-border bg-card p-8 shadow-panel">
        <h1 className="text-xl font-semibold">Signing you in…</h1>
        {error ? (
          <p className="mt-3 text-sm text-danger" role="alert">
            {error}{" "}
            <a className="underline" href="/login">
              Back to login
            </a>
          </p>
        ) : (
          <p className="mt-3 text-sm text-muted-foreground">
            Restoring your shop and Instagram connection.
          </p>
        )}
      </div>
    </main>
  );
}
