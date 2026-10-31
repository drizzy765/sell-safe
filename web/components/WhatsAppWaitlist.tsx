"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

const SUCCESS_MESSAGE = "We'll message you on WhatsApp when ready";

function localDigits(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  const withoutCountry = digits.startsWith("234") ? digits.slice(3) : digits;
  return withoutCountry.slice(0, 10);
}

export function WhatsAppWaitlist({
  variant = "card",
  className,
}: {
  variant?: "card" | "band";
  className?: string;
}) {
  const [localNumber, setLocalNumber] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const phoneNumber = `+234${localNumber}`;
    if (!/^\+234[0-9]{10}$/.test(phoneNumber)) {
      setStatus("error");
      setMessage("Please enter a valid Nigerian number (+234XXXXXXXXXX)");
      return;
    }

    setStatus("submitting");

    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      if (response.ok) {
        setStatus("success");
        setMessage(SUCCESS_MESSAGE);
      } else if (response.status === 409) {
        setStatus("error");
        setMessage("This number is already on the waitlist.");
      } else {
        setStatus("error");
        setMessage("Something went wrong. Please try again.");
      }
    } catch {
      setStatus("error");
      setMessage("Something went wrong. Please try again.");
    }
  };

  const locked = status === "submitting" || status === "success";

  return (
    <div
      className={cn(
        variant === "band"
          ? "rounded-lg border border-border bg-muted/50 p-6 md:p-8"
          : "rounded-xl border border-border bg-muted p-6",
        className,
      )}
    >
      {variant === "card" ? (
        <>
          <h3 className="mb-2 text-lg font-semibold">WhatsApp Coming Soon</h3>
          <p className="mb-4 text-sm text-muted-foreground">
            WhatsApp is temporarily unavailable. Leave your number and we&apos;ll message you when
            it&apos;s ready.
          </p>
        </>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="phone" className="mb-1 block text-sm font-medium">
            WhatsApp number
          </label>
          <div className="flex overflow-hidden rounded-md border border-border bg-background focus-within:ring-2 focus-within:ring-primary/40">
            <span className="flex items-center border-r border-border px-3 text-sm text-muted-foreground">
              +234
            </span>
            <input
              type="tel"
              id="phone"
              inputMode="numeric"
              autoComplete="tel-national"
              value={localNumber}
              onChange={(e) => setLocalNumber(localDigits(e.target.value))}
              placeholder="8012345678"
              className="w-full bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-muted-foreground"
              disabled={locked}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={locked}
          className="inline-flex w-full items-center justify-center rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-transform active:scale-[0.96] hover:opacity-90 disabled:opacity-50"
        >
          {status === "submitting"
            ? "Submitting..."
            : variant === "band"
              ? "Join the waitlist"
              : "Notify Me"}
        </button>

        {status === "success" && <p className="text-sm text-success">{message}</p>}

        {status === "error" && (
          <p className="text-sm text-danger" role="alert">
            {message}
          </p>
        )}
      </form>
    </div>
  );
}
