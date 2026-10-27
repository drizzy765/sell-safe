"use client";

import { useState } from "react";

type Props = {
  label?: string;
  value: string;
  secret?: boolean;
};

function maskSecret(value: string): string {
  if (value.includes("••••")) return value;
  if (value.length <= 8) return "••••••••";
  return `${value.slice(0, 4)}••••••••`;
}

export function CodeBlock({ label, value, secret }: Props) {
  const [copied, setCopied] = useState(false);
  const display = secret ? maskSecret(value) : value;

  async function onCopy() {
    // Never copy a real secret from the page — content is already placeholder/masked.
    const toCopy = secret ? display : value;
    try {
      await navigator.clipboard.writeText(toCopy);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-muted">
      {label ? (
        <div className="border-b border-border px-3 py-1.5 text-xs text-muted-foreground">
          {label}
        </div>
      ) : null}
      <div className="flex items-start gap-2 p-3">
        <pre className="flex-1 overflow-x-auto font-mono text-sm text-foreground">
          <code>{display}</code>
        </pre>
        <button
          type="button"
          onClick={onCopy}
          className="shrink-0 rounded-lg border border-border bg-background px-2 py-1 text-xs font-medium text-foreground transition hover:border-primary"
          aria-live="polite"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}
