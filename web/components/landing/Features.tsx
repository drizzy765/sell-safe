import { Languages, Package, MessagesSquare, BadgeCheck } from "lucide-react";

import { BlurFade } from "@/components/magicui/blur-fade";

const FEATURES = [
  {
    title: "Answers in your tone",
    body: "English, Pidgin, or Yoruba samples — replies that sound like your shop.",
    icon: Languages,
  },
  {
    title: "Catalog from posts",
    body: "Drafts your catalog from Instagram posts — you approve, edit, or skip.",
    icon: Package,
  },
  {
    title: "Orders in chat",
    body: "Takes orders in chat so nothing gets lost in DMs.",
    icon: MessagesSquare,
  },
  {
    title: "Real payment checks",
    body: "Flags fake proof; confirms Paystack, bank alerts, and USDC on Base.",
    icon: BadgeCheck,
  },
];

export function Features() {
  return (
    <section id="features" className="scroll-mt-24 py-16 md:py-20">
      <BlurFade>
        <h2 className="mb-10 text-center text-2xl font-semibold tracking-tight md:text-[28px]">
          Built for how you already sell.
        </h2>
      </BlurFade>
      <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-2">
        {FEATURES.map((f, i) => {
          const Icon = f.icon;
          return (
            <BlurFade key={f.title} delay={0.06 * (i + 1)}>
              <div className="flex gap-4">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-brand-blue" strokeWidth={1.75} />
                <div>
                  <h3 className="mb-1 text-lg font-semibold">{f.title}</h3>
                  <p className="text-sm leading-6 text-muted-foreground">{f.body}</p>
                </div>
              </div>
            </BlurFade>
          );
        })}
      </div>
    </section>
  );
}
