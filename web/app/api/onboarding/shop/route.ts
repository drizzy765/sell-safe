import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/apiBaseUrl";
import { IG_SESSION_COOKIE, IG_SESSION_HEADER } from "@/lib/instagramSession";

async function proxy(method: "GET" | "PATCH", request: Request) {
  const jar = await cookies();
  const sessionId = jar.get(IG_SESSION_COOKIE)?.value || "";
  if (!sessionId) {
    return NextResponse.json({ detail: "Connect Instagram first." }, { status: 401 });
  }

  const incoming = new URL(request.url);
  const upstreamUrl = new URL(`${apiBaseUrl()}/api/onboarding/shop`);
  if (method === "GET") {
    const refresh = incoming.searchParams.get("refresh");
    if (refresh) upstreamUrl.searchParams.set("refresh", refresh);
  }

  try {
    const upstream = await fetch(upstreamUrl, {
      method,
      headers: {
        [IG_SESSION_HEADER]: sessionId,
        ...(method === "PATCH" ? { "Content-Type": "application/json" } : {}),
      },
      body: method === "PATCH" ? await request.text() : undefined,
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

export async function GET(request: Request) {
  return proxy("GET", request);
}

export async function PATCH(request: Request) {
  return proxy("PATCH", request);
}
