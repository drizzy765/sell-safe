"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "motion/react";

import { cn } from "@/lib/utils";

const BUYER = "Abeg how much for the black leather bag?";

export function HeroChatMock({ className }: { className?: string }) {
  const [step, setStep] = useState(0);
  const [mounted, setMounted] = useState(false);
  const reduce = useReducedMotion();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    if (reduce) {
      setStep(3);
      return;
    }

    setStep(0);
    const t1 = setTimeout(() => setStep(1), 450);
    const t2 = setTimeout(() => setStep(2), 1400);
    const t3 = setTimeout(() => setStep(3), 2500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [mounted, reduce]);

  return (
    <div
      className={cn(
        "relative mx-auto w-full max-w-[380px] overflow-hidden rounded-[20px] border border-border bg-background shadow-panel",
        className,
      )}
      aria-label="Sample Instagram DM"
    >
      {/* Outer radius 20 ≈ inner content radius 12 + padding */}
      <div className="flex items-center gap-3 border-b border-border px-4 py-3">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-brand text-xs font-bold text-white"
          aria-hidden
        >
          T
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold tracking-tight">tolu.bags</p>
          <p className="text-xs text-muted-foreground">Instagram · Active now</p>
        </div>
        <span className="rounded-full border border-border px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
          Demo
        </span>
      </div>

      <div className="min-h-[260px] space-y-3 bg-muted/30 px-4 py-5">
        {step >= 1 ? (
          <div className="flex flex-col items-end gap-1">
            <div className="max-w-[85%] rounded-[14px] rounded-br-md bg-[#3797F0] px-3.5 py-2.5 text-sm leading-5 text-white">
              {BUYER}
            </div>
            <span className="px-1 text-[10px] text-muted-foreground">Buyer · just now</span>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="flex items-center gap-2" aria-label="Sell-Safe is typing">
            <div className="flex h-7 w-7 items-center justify-center rounded-full border border-border bg-background text-[10px] font-bold text-brand-blue">
              SS
            </div>
            <div className="flex items-center gap-1 rounded-[14px] border border-border bg-background px-3 py-2.5">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:120ms]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:240ms]" />
            </div>
          </div>
        ) : null}

        {step >= 3 ? (
          <div className="flex flex-col items-start gap-1">
            <div className="mb-0.5 flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-full border border-border bg-background text-[10px] font-bold text-brand-blue">
                SS
              </div>
              <span className="text-[11px] font-medium text-muted-foreground">Sell-Safe</span>
            </div>
            <div className="ml-9 max-w-[90%] rounded-[14px] rounded-bl-md border border-border bg-background px-3.5 py-2.5 text-sm leading-5 text-foreground shadow-[0_1px_0_rgba(7,25,66,0.04)]">
              <p>Black leather bag — ready today.</p>
              <p className="font-money mt-1.5 text-base font-semibold tracking-tight">₦15,000</p>
            </div>
            <span className="ml-9 px-1 text-[10px] text-muted-foreground">Reply · just now</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}
