import { proxyOnboarding } from "@/lib/onboardingApi";

type Params = { params: Promise<{ id: string }> };

export async function DELETE(_request: Request, { params }: Params) {
  const { id } = await params;
  return proxyOnboarding(`/api/onboarding/catalog/shelf/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}
