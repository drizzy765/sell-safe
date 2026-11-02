import { proxyOnboarding } from "@/lib/onboardingApi";

export async function POST(
  request: Request,
  context: { params: Promise<{ draftId: string }> },
) {
  const { draftId } = await context.params;
  const body = await request.text();
  return proxyOnboarding(`/api/dashboard/drafts/${encodeURIComponent(draftId)}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
}
