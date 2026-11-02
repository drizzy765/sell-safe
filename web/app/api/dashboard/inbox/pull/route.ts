import { proxyOnboarding } from "@/lib/onboardingApi";

export async function POST() {
  return proxyOnboarding("/api/dashboard/inbox/pull", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
}
