import { Suspense } from "react";
import { OnboardingHome } from "@/components/OnboardingHome";

export default function HomePage() {
  return (
    <Suspense fallback={<div className="p-8 text-muted-foreground">Loading…</div>}>
      <OnboardingHome />
    </Suspense>
  );
}
