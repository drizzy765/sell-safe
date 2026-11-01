import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/apiBaseUrl";
import {
  IG_SESSION_COOKIE,
  IG_SESSION_HEADER,
  sessionCookieOptions,
} from "@/lib/instagramSession";

export async function POST() {
  const jar = await cookies();
  const sessionId = jar.get(IG_SESSION_COOKIE)?.value || "";

  let body = { connected: false, detail: "Instagram disconnected." };
  let status = 200;

  if (sessionId) {
    try {
      const upstream = await fetch(`${apiBaseUrl()}/api/instagram/disconnect`, {
        method: "POST",
        headers: { [IG_SESSION_HEADER]: sessionId },
        cache: "no-store",
      });
      body = (await upstream.json().catch(() => body)) as typeof body;
      status = upstream.status;
    } catch {
      // Still clear the browser cookie so the seller can reconnect.
      status = 200;
    }
  }

  const response = NextResponse.json(body, { status });
  response.cookies.set(IG_SESSION_COOKIE, "", { ...sessionCookieOptions(0), maxAge: 0 });
  return response;
}
