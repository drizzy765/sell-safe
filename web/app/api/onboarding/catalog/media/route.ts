import { proxyOnboarding } from "@/lib/onboardingApi";

export async function GET() {
  return proxyOnboarding("/api/onboarding/catalog/media");
}
