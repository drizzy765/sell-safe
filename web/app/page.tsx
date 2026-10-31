"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { LandingHome } from "@/components/landing/LandingHome";
import { OnboardingHome } from "@/components/OnboardingHome";

function HomeRouter() {
  const searchParams = useSearchParams();
  const platform = searchParams.get("platform");

  if (platform === "instagram" || platform === "whatsapp" || platform === "messenger") {
    return <OnboardingHome />;
  }

  return <LandingHome />;
}

export default function HomePage() {
  return (
    <Suspense fallback={<div className="p-8 text-muted-foreground">Loading…</div>}>
      <HomeRouter />
    </Suspense>
  );
}
