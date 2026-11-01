import { proxyOnboarding } from "@/lib/onboardingApi";

export async function POST(request: Request) {
  const body = await request.text();
  return proxyOnboarding("/api/onboarding/catalog/drafts/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
}
