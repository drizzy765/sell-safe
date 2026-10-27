import { CodeBlock } from "@/components/CodeBlock";
import type { PlatformGuide } from "@/content";

type Props = {
  index: number;
  step: PlatformGuide["steps"][number];
};

export function StepCard({ index, step }: Props) {
  return (
    <article className="rounded-xl border border-border bg-background p-5 md:p-6">
      <div className="mb-3 flex items-start gap-3">
        <span
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground"
          aria-hidden
        >
          {index}
        </span>
        <h3 className="pt-1 text-lg font-semibold leading-snug text-foreground">
          {step.title}
        </h3>
      </div>
      <div className="space-y-3 pl-11">
        {step.blocks.map((block, i) => {
          if (block.type === "text") {
            return (
              <p key={i} className="text-base leading-relaxed text-muted-foreground">
                {block.body}
              </p>
            );
          }
          return (
            <CodeBlock
              key={i}
              label={block.label}
              value={block.value}
              secret={block.secret}
            />
          );
        })}
      </div>
    </article>
  );
}
