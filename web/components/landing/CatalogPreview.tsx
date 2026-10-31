import Link from "next/link";

import { BlurFade } from "@/components/magicui/blur-fade";

const TILES = [
  { name: "Black leather bag", price: "₦15,000" },
  { name: "Ankara tote", price: "₦8,500" },
  { name: "Crossbody mini", price: "₦12,000" },
  { name: "Weekend duffel", price: "₦22,000" },
];

export function CatalogPreview() {
  return (
    <section className="py-16 md:py-20">
      <div className="mx-auto grid max-w-5xl items-center gap-10 md:grid-cols-2">
        <BlurFade>
          <h2 className="mb-3 text-2xl font-semibold tracking-tight md:text-[28px]">
            Your posts become a shop list.
          </h2>
          <p className="mb-6 text-muted-foreground">
            We read your recent posts and suggest names and prices. You approve what looks right —
            nothing goes live without you.
          </p>
          <Link
            href="/?platform=instagram"
            className="inline-flex items-center justify-center rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-transform active:scale-[0.96] hover:opacity-90"
          >
            See it in onboarding
          </Link>
        </BlurFade>
        <BlurFade delay={0.12}>
          <div className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2 md:flex-wrap md:overflow-visible">
            {TILES.map((tile) => (
              <article
                key={tile.name}
                className="min-w-[80%] snap-center rounded-md border border-border bg-muted/60 p-4 md:min-w-0 md:flex-1 md:basis-[45%]"
              >
                <div className="mb-3 h-20 rounded-sm bg-gradient-brand-soft" aria-hidden />
                <div className="mb-1 flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold">{tile.name}</h3>
                  <span className="rounded-full border border-border px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                    Draft
                  </span>
                </div>
                <p className="font-money text-sm text-foreground">{tile.price}</p>
              </article>
            ))}
          </div>
        </BlurFade>
      </div>
    </section>
  );
}
