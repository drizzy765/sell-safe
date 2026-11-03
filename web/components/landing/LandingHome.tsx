"use client";

import Link from "next/link";

import { CatalogPreview } from "@/components/landing/CatalogPreview";
import { Features } from "@/components/landing/Features";
import { HeroChatMock } from "@/components/landing/HeroChatMock";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { LandingFaq } from "@/components/landing/LandingFaq";
import { TrustStrip } from "@/components/landing/TrustStrip";
import { BlurFade } from "@/components/magicui/blur-fade";
import { DotPattern } from "@/components/magicui/dot-pattern";
import { PaymentSafetyDemo } from "@/components/PaymentSafetyDemo";
import { SellSafeLogo } from "@/components/SellSafeLogo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WhatsAppWaitlist } from "@/components/WhatsAppWaitlist";

export function LandingHome() {
  return (
    <div className="min-h-screen bg-background text-foreground antialiased">
      <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1120px] items-center justify-between px-4">
          <Link href="/" className="flex items-center" aria-label="Sell-Safe home">
            <SellSafeLogo height={28} />
          </Link>
          <nav className="hidden items-center gap-6 text-sm md:flex">
            <a className="text-muted-foreground transition-colors duration-150 hover:text-foreground" href="#features">
              Features
            </a>
            <a className="text-muted-foreground transition-colors duration-150 hover:text-foreground" href="#how-it-works">
              How it works
            </a>
            <a className="text-muted-foreground transition-colors duration-150 hover:text-foreground" href="#demo">
              Try it
            </a>
            <a className="text-muted-foreground transition-colors duration-150 hover:text-foreground" href="#faq">
              FAQ
            </a>
          </nav>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              href="/?platform=instagram"
              className="hidden min-h-10 items-center rounded-md bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground transition-transform duration-150 active:scale-[0.96] hover:opacity-90 sm:inline-flex"
            >
              Connect Instagram
            </Link>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-gradient-flow opacity-40" aria-hidden />
        <DotPattern className="fill-brand-blue/[0.10] [mask-image:radial-gradient(ellipse_at_center,white,transparent_72%)]" />
        <div className="relative mx-auto grid max-w-[1120px] items-center gap-12 px-4 py-16 md:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] md:gap-14 md:py-28">
          <div>
            <BlurFade>
              <h1 className="mb-5 text-balance text-[32px] font-bold leading-10 tracking-tight md:text-5xl md:leading-[1.12]">
                Sell on Instagram. Catch fake payments before you ship.
              </h1>
            </BlurFade>
            <BlurFade delay={0.1}>
              <p className="mb-8 max-w-xl text-base leading-7 text-muted-foreground md:text-lg">
                Sell-Safe replies to your DMs, builds a catalog from your posts, and flags fake
                transfer screenshots before you send goods.
              </p>
            </BlurFade>
            <BlurFade delay={0.18}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link
                  href="/?platform=instagram"
                  className="inline-flex min-h-11 w-full items-center justify-center rounded-md bg-primary px-6 text-sm font-semibold text-primary-foreground shadow-panel transition-transform duration-150 active:scale-[0.96] hover:opacity-95 sm:w-auto"
                >
                  Connect Instagram
                </Link>
                <a
                  href="#waitlist"
                  className="inline-flex min-h-11 w-full items-center justify-center rounded-md border border-border px-6 text-sm font-semibold transition-colors duration-150 hover:bg-muted sm:w-auto"
                >
                  Join WhatsApp waitlist
                </a>
              </div>
            </BlurFade>
          </div>
          <BlurFade delay={0.16}>
            <HeroChatMock />
          </BlurFade>
        </div>
      </section>

      <TrustStrip />

      <main className="mx-auto max-w-[1120px] px-4">
        <HowItWorks />

        <section id="demo" className="scroll-mt-24 py-20 md:py-28">
          <PaymentSafetyDemo showCta />
        </section>

        <Features />
        <CatalogPreview />

        <section id="waitlist" className="scroll-mt-24 py-16 md:py-24">
          <div className="mx-auto max-w-xl">
            <h2 className="mb-2 text-center text-2xl font-semibold tracking-tight md:text-[28px]">
              Coming soon to WhatsApp.
            </h2>
            <p className="mb-8 text-center text-muted-foreground">
              Leave your number. We&apos;ll text you when Sell-Safe can run your WhatsApp shop the
              same way. Instagram is ready today — connect above.
            </p>
            <WhatsAppWaitlist variant="band" />
          </div>
        </section>

        <LandingFaq />
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-[1120px] flex-col gap-6 px-4 py-10 md:flex-row md:items-center md:justify-between">
          <SellSafeLogo height={24} />
          <nav className="flex flex-wrap gap-4 text-sm text-muted-foreground">
            <a className="transition-colors duration-150 hover:text-foreground" href="/status">
              Status
            </a>
            <a className="transition-colors duration-150 hover:text-foreground" href="/faq">
              FAQ
            </a>
            <a className="transition-colors duration-150 hover:text-foreground" href="/privacy">
              Privacy
            </a>
            <Link className="transition-colors duration-150 hover:text-foreground" href="/?platform=instagram">
              Connect
            </Link>
          </nav>
          <p className="text-xs text-muted-foreground">
            Built for Nigerian sellers · Meta Global AI Hackathon
          </p>
        </div>
      </footer>
    </div>
  );
}
