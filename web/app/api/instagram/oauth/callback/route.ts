import { NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/apiBaseUrl";
import { IG_SESSION_COOKIE, sessionCookieOptions } from "@/lib/instagramSession";

export async function GET(request: Request) {
  const incoming = new URL(request.url);
  const code = incoming.searchParams.get("code");
  const state = incoming.searchParams.get("state");
  const error = incoming.searchParams.get("error");
  const errorDescription = incoming.searchParams.get("error_description");

  const fail = (message: string) => {
    const dest = new URL("/?platform=instagram", incoming.origin);
    dest.searchParams.set("ig_error", message);
    return NextResponse.redirect(dest);
  };

  if (error) {
    return fail(errorDescription || error || "access_denied");
  }
  if (!code || !state) {
    return fail("missing_code");
  }

  try {
    const upstream = await fetch(`${apiBaseUrl()}/api/instagram/oauth/exchange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, state }),
      cache: "no-store",
    });
    const body = (await upstream.json().catch(() => ({}))) as {
      session_id?: string;
      return_to?: string;
      username?: string;
      detail?: string;
    };
    if (!upstream.ok || !body.session_id) {
      return fail(
        typeof body.detail === "string"
          ? body.detail
          : "Could not complete Instagram Login.",
      );
    }

    const returnTo = body.return_to?.startsWith("/")
      ? body.return_to
      : "/?platform=instagram";
    const dest = new URL(returnTo, incoming.origin);
    dest.searchParams.set("ig_connected", "1");
    if (body.username) {
      dest.searchParams.set("ig_user", body.username);
    }

    const response = NextResponse.redirect(dest);
    response.cookies.set(IG_SESSION_COOKIE, body.session_id, sessionCookieOptions());
    return response;
  } catch {
    return fail("Backend is offline. Start FastAPI on :8000 (API_BASE_URL).");
  }
}
