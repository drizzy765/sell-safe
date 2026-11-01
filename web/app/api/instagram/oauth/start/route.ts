import { NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/apiBaseUrl";

export async function GET(request: Request) {
  const incoming = new URL(request.url);
  const returnTo = incoming.searchParams.get("return_to") || "/?platform=instagram";
  const forceReauth = incoming.searchParams.get("force_reauth") !== "false";

  const upstreamUrl = new URL(`${apiBaseUrl()}/api/instagram/oauth/start`);
  upstreamUrl.searchParams.set("return_to", returnTo);
  upstreamUrl.searchParams.set("force_reauth", forceReauth ? "true" : "false");

  try {
    const upstream = await fetch(upstreamUrl, { cache: "no-store" });
    const body = (await upstream.json().catch(() => ({}))) as {
      authorize_url?: string;
      detail?: string;
    };
    if (!upstream.ok || !body.authorize_url) {
      const dest = new URL("/?platform=instagram", incoming.origin);
      dest.searchParams.set(
        "ig_error",
        typeof body.detail === "string"
          ? body.detail
          : "Instagram OAuth is not configured on the backend.",
      );
      return NextResponse.redirect(dest);
    }
    return NextResponse.redirect(body.authorize_url);
  } catch {
    const dest = new URL("/?platform=instagram", incoming.origin);
    dest.searchParams.set(
      "ig_error",
      "Backend is offline. Start FastAPI on :8000 (API_BASE_URL).",
    );
    return NextResponse.redirect(dest);
  }
}
