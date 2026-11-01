import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/apiBaseUrl";
import { IG_SESSION_COOKIE, IG_SESSION_HEADER } from "@/lib/instagramSession";

export async function GET() {
  const jar = await cookies();
  const sessionId = jar.get(IG_SESSION_COOKIE)?.value || "";

  try {
    const headers: HeadersInit = {};
    if (sessionId) {
      headers[IG_SESSION_HEADER] = sessionId;
    }
    const upstream = await fetch(`${apiBaseUrl()}/api/instagram/status`, {
      cache: "no-store",
      headers,
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
      {
        connected: false,
        oauth_configured: false,
        ready: false,
        offline: true,
        detail:
          "Backend is offline. Start FastAPI on :8000 (API_BASE_URL) for Instagram status.",
      },
      { status: 200 },
    );
  }
}
