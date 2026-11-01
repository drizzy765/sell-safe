import { proxyOnboarding } from "@/lib/onboardingApi";

type Params = { params: Promise<{ id: string }> };

export async function PATCH(request: Request, { params }: Params) {
  const { id } = await params;
  const body = await request.text();
  return proxyOnboarding(`/api/onboarding/catalog/drafts/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body,
  });
}

export async function DELETE(_request: Request, { params }: Params) {
  const { id } = await params;
  return proxyOnboarding(`/api/onboarding/catalog/drafts/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}
