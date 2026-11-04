"use client";

import { Suspense, useEffect } from "react";
import { useSearchParams } from "next/navigation";

import { LandingHome } from "@/components/landing/LandingHome";
import { OnboardingHome } from "@/components/OnboardingHome";

function HomeRouter() {
  const searchParams = useSearchParams();
  const platform = searchParams.get("platform");

  // Magic links fall back to the site root when the Supabase allowlist
  // misses /auth/callback — rescue the token hash and finish login.
  useEffect(() => {
    const hash = window.location.hash || "";
    if (hash.includes("access_token=")) {
      window.location.replace(`/auth/callback${hash}`);
    }
  }, []);

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
