import { IG_SESSION_COOKIE, IG_SESSION_HEADER } from "@/lib/instagramSession";
import { apiBaseUrl } from "@/lib/apiBaseUrl";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function proxyOnboarding(
  path: string,
  init: RequestInit & { method?: string } = {},
): Promise<NextResponse> {
  const jar = await cookies();
  const sessionId = jar.get(IG_SESSION_COOKIE)?.value || "";
  if (!sessionId) {
    return NextResponse.json({ detail: "Connect Instagram first." }, { status: 401 });
  }

  const method = init.method || "GET";
  try {
    const upstream = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      method,
      headers: {
        [IG_SESSION_HEADER]: sessionId,
        ...(init.headers || {}),
      },
      cache: "no-store",
    });
    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Backend is offline. Start FastAPI on :8000." },
      { status: 502 },
    );
  }
}
