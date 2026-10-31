"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

import { BlurFade } from "@/components/magicui/blur-fade";
import { cn } from "@/lib/utils";

const FAQS = [
  {
    q: "Do I need a developer?",
    a: "No for Instagram Login. Advanced webhook setup is optional under Docs.",
  },
  {
    q: "Will it reply without me?",
    a: "Yes, after you connect and approve your catalog and tone.",
  },
  {
    q: "What is SUSPICIOUS?",
    a: "The receipt didn’t match a real Paystack, bank, or on-chain payment. Pause and check before sending goods.",
  },
  {
    q: "What is CONFIRMED?",
    a: "We saw a matching real payment signal. Safe to fulfil.",
  },
  {
    q: "Is WhatsApp ready?",
    a: "Not yet — join the waitlist. Instagram is ready today.",
  },
];

export function LandingFaq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="scroll-mt-24 py-16 md:py-24">
      <div className="mx-auto grid max-w-5xl gap-10 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <BlurFade>
          <h2 className="mb-3 text-2xl font-semibold tracking-tight md:text-[28px]">
            Questions sellers ask
          </h2>
          <p className="mb-4 text-muted-foreground">
            Short answers. More detail lives in FAQ and Privacy.
          </p>
          <div className="flex flex-wrap gap-4 text-sm">
            <a className="text-brand-blue underline-offset-4 hover:underline" href="/faq">
              Full FAQ
            </a>
            <a className="text-brand-blue underline-offset-4 hover:underline" href="/privacy">
              Privacy
            </a>
          </div>
        </BlurFade>
        <BlurFade delay={0.08}>
          <ul className="divide-y divide-border border-y border-border">
            {FAQS.map((item, i) => {
              const isOpen = open === i;
              return (
                <li key={item.q}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between gap-4 py-4 text-left text-sm font-semibold"
                    aria-expanded={isOpen}
                    onClick={() => setOpen(isOpen ? null : i)}
                  >
                    {item.q}
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200",
                        isOpen && "rotate-180",
                      )}
                    />
                  </button>
                  {isOpen ? (
                    <p className="pb-4 text-sm leading-6 text-muted-foreground">{item.a}</p>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </BlurFade>
      </div>
    </section>
  );
}
