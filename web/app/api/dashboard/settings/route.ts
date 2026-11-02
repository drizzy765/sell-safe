import { proxyOnboarding } from "@/lib/onboardingApi";

export async function PATCH(request: Request) {
  const body = await request.text();
  return proxyOnboarding("/api/dashboard/settings", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body,
  });
}
