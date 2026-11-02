import { proxyOnboarding } from "@/lib/onboardingApi";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const folder = url.searchParams.get("folder") || "primary";
  return proxyOnboarding(`/api/dashboard/inbox?folder=${encodeURIComponent(folder)}`);
}
