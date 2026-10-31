"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "motion/react";

import { Marquee } from "@/components/magicui/marquee";
import { cn } from "@/lib/utils";

const ITEMS = ["Paystack", "Bank alerts", "USDC on Base", "Built for Meta hackathon"];

function StaticStrip({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-center gap-x-6 gap-y-2 py-3 text-sm text-muted-foreground",
        className,
      )}
    >
      {ITEMS.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

export function TrustStrip({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className={cn("border-y border-border bg-muted/40", className)}>
      <p className="mx-auto max-w-[1120px] px-4 pt-5 text-center text-sm text-muted-foreground md:text-[15px]">
        Checks payments with real Paystack webhooks, bank alerts, and on-chain USDC — not guesswork.
      </p>
      {!mounted || reduce ? (
        <StaticStrip className="pb-5" />
      ) : (
        <div className="relative py-2 pb-4">
          <Marquee pauseOnHover className="[--duration:28s]">
            {ITEMS.map((item) => (
              <span
                key={item}
                className="mx-4 text-sm font-medium tracking-wide text-muted-foreground"
              >
                {item}
              </span>
            ))}
          </Marquee>
          <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-muted/40 to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-muted/40 to-transparent" />
        </div>
      )}
    </div>
  );
}
