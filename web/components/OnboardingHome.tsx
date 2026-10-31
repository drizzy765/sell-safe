"use client";

import Link from "next/link";
import { useState } from "react";

import { AdvancedSetup } from "@/components/AdvancedSetup";
import { InstagramConnect } from "@/components/InstagramConnect";
import { PaymentSafetyDemo } from "@/components/PaymentSafetyDemo";
import { PlatformTabs, useSelectedPlatform } from "@/components/PlatformTabs";
import { SampleReplyDemo } from "@/components/SampleReplyDemo";
import { SellSafeLogo } from "@/components/SellSafeLogo";
import { StepCard } from "@/components/StepCard";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WhatsAppWaitlist } from "@/components/WhatsAppWaitlist";
import { guides } from "@/content";

export function OnboardingHome() {
  const platform = useSelectedPlatform();
  const guide = guides[platform];
  const [instagramConnected, setInstagramConnected] = useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1080px] items-center justify-between px-4">
          <Link href="/" className="flex items-center" aria-label="Sell-Safe home">
            <SellSafeLogo height={28} />
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link className="text-muted-foreground hover:text-foreground" href="/">
              Home
            </Link>
            <a className="text-muted-foreground hover:text-foreground" href="#steps">
              Docs
            </a>
            <a className="text-muted-foreground hover:text-foreground" href="/status">
              Status
            </a>
            <a className="text-muted-foreground hover:text-foreground" href="/faq">
              FAQ
            </a>
            <a className="text-muted-foreground hover:text-foreground" href="/privacy">
              Privacy
            </a>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1080px] px-4 py-10 md:py-14">
        <section className="mb-10 space-y-4">
          <h1 className="text-3xl font-semibold tracking-tight md:text-[40px] md:leading-[48px]">
            Connect Sell-Safe to your shop
          </h1>
          <p className="max-w-2xl text-base text-muted-foreground md:text-lg">
            Pick where your buyers message you. Follow the steps for that platform only.
          </p>
          <PlatformTabs />
        </section>

        <div className="grid gap-8 md:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="h-fit rounded-xl border border-border bg-muted p-5 md:sticky md:top-24">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Prerequisites
            </h2>
            <ul className="space-y-2 text-sm text-foreground">
              {guide.prerequisites.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-primary" aria-hidden>
                    •
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </aside>

          <section id="steps" className="space-y-4">
            {platform === "whatsapp" ? (
              <WhatsAppWaitlist />
            ) : platform === "instagram" ? (
              <>
                <InstagramConnect onConnected={() => setInstagramConnected(true)} />
                {instagramConnected ? (
                  <>
                    <SampleReplyDemo />
                    <PaymentSafetyDemo />
                  </>
                ) : null}
                <AdvancedSetup steps={guide.steps} />
              </>
            ) : (
              guide.steps.map((step, index) => (
                <StepCard key={step.title} index={index + 1} step={step} />
              ))
            )}
            {guide.note ? (
              <p className="rounded-xl border border-border bg-muted p-4 text-sm text-muted-foreground">
                {guide.note}
              </p>
            ) : null}
          </section>
        </div>
      </main>

      <footer className="border-t border-border py-8 text-center text-sm text-muted-foreground">
        Built for the Meta Global AI Hackathon
      </footer>
    </div>
  );
}
