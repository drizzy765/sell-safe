import { StepCard } from "@/components/StepCard";
import type { PlatformGuide } from "@/content/types";

type Props = {
  steps: PlatformGuide["steps"];
};

export function AdvancedSetup({ steps }: Props) {
  return (
    <details className="rounded-xl border border-border bg-card">
      <summary className="cursor-pointer px-5 py-4 text-sm font-medium text-foreground">
        Advanced setup (for developers)
      </summary>
      <div className="space-y-4 border-t border-border p-4">
        {steps.map((step, index) => (
          <StepCard key={step.title} index={index + 1} step={step} />
        ))}
      </div>
    </details>
  );
}
