import { proxyOnboarding } from "@/lib/onboardingApi";

export async function POST(
  _request: Request,
  context: { params: Promise<{ draftId: string }> },
) {
  const { draftId } = await context.params;
  return proxyOnboarding(`/api/dashboard/drafts/${encodeURIComponent(draftId)}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
}
