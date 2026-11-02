import { proxyOnboarding } from "@/lib/onboardingApi";

export async function GET(
  _request: Request,
  context: { params: Promise<{ buyerId: string }> },
) {
  const { buyerId } = await context.params;
  return proxyOnboarding(`/api/dashboard/inbox/${encodeURIComponent(buyerId)}`);
}
