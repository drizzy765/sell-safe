import { NextResponse } from "next/server";

import { IG_SESSION_COOKIE, sessionCookieOptions } from "@/lib/instagramSession";

/**
 * Claim an opaque Instagram session id (from the FastAPI HTTPS OAuth callback)
 * into an httpOnly cookie on the web origin, then redirect into onboarding.
 */
export async function GET(request: Request) {
  const incoming = new URL(request.url);
  const sessionId = incoming.searchParams.get("session_id") || "";
  const username = incoming.searchParams.get("ig_user") || "";
  const returnToRaw = incoming.searchParams.get("return_to") || "/?platform=instagram";
  const igError = incoming.searchParams.get("ig_error");

  const returnTo = returnToRaw.startsWith("/") ? returnToRaw : "/?platform=instagram";
  const dest = new URL(returnTo, incoming.origin);

  if (igError) {
    dest.searchParams.set("ig_error", igError);
    return NextResponse.redirect(dest);
  }

  if (!sessionId) {
    dest.searchParams.set("ig_error", "missing_session");
    return NextResponse.redirect(dest);
  }

  dest.searchParams.set("ig_connected", "1");
  if (username) {
    dest.searchParams.set("ig_user", username);
  }

  const response = NextResponse.redirect(dest);
  response.cookies.set(IG_SESSION_COOKIE, sessionId, sessionCookieOptions());
  return response;
}
