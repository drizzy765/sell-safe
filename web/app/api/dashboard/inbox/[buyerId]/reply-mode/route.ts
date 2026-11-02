import { proxyOnboarding } from "@/lib/onboardingApi";

export async function PATCH(
  request: Request,
  context: { params: Promise<{ buyerId: string }> },
) {
  const { buyerId } = await context.params;
  const body = await request.text();
  return proxyOnboarding(`/api/dashboard/inbox/${encodeURIComponent(buyerId)}/reply-mode`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body,
  });
}
