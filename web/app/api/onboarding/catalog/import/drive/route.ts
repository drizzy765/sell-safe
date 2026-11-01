import { proxyOnboarding } from "@/lib/onboardingApi";

export async function POST(request: Request) {
  const body = await request.text();
  return proxyOnboarding("/api/onboarding/catalog/import/drive", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
}
