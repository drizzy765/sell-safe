import { Link2, ShieldCheck, Sparkles } from "lucide-react";

import { BlurFade } from "@/components/magicui/blur-fade";

const STEPS = [
  {
    n: "01",
    title: "Connect",
    body: "Link Instagram in one tap. No developer setup for the happy path.",
    icon: Link2,
  },
  {
    n: "02",
    title: "Teach",
    body: "Approve the catalog we draft from your posts. Tell us your prices and policies in chat.",
    icon: Sparkles,
  },
  {
    n: "03",
    title: "Protect",
    body: "When a buyer sends payment proof, Sell-Safe checks it. Fake screenshots get SUSPICIOUS. Real money gets CONFIRMED.",
    icon: ShieldCheck,
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="scroll-mt-24 py-16 md:py-24">
      <BlurFade>
        <h2 className="mb-3 text-center text-2xl font-semibold tracking-tight md:text-[28px] md:leading-9">
          Up and selling in three steps.
        </h2>
        <p className="mx-auto mb-12 max-w-xl text-center text-muted-foreground">
          Connect, approve your catalog, then let Sell-Safe check every payment.
        </p>
      </BlurFade>
      <ol className="mx-auto grid max-w-5xl gap-10 md:grid-cols-3">
        {STEPS.map((step, i) => {
          const Icon = step.icon;
          return (
            <BlurFade key={step.n} delay={0.08 * (i + 1)}>
              <li className="flex flex-col items-start gap-3">
                <div className="flex items-center gap-3">
                  <span className="font-money text-sm font-semibold text-brand-blue">{step.n}</span>
                  <Icon className="h-5 w-5 text-foreground" strokeWidth={1.75} aria-hidden />
                </div>
                <h3 className="text-xl font-semibold">{step.title}</h3>
                <p className="text-sm leading-6 text-muted-foreground">{step.body}</p>
              </li>
            </BlurFade>
          );
        })}
      </ol>
    </section>
  );
}
