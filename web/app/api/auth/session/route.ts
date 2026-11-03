import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { IG_SESSION_COOKIE, sessionCookieOptions } from "@/lib/instagramSession";
import {
  AUTH_ACCESS_COOKIE,
  AUTH_REFRESH_COOKIE,
  backendAuth,
  verifySupabaseUser,
} from "@/lib/supabaseServer";

const secure = process.env.NODE_ENV === "production";

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as {
    access_token?: string;
    refresh_token?: string;
    expires_in?: number;
  };
  const user = await verifySupabaseUser(body.access_token || "");
  if (!user) {
    return NextResponse.json({ detail: "Login link expired. Request a new one." }, { status: 401 });
  }
  const store = await cookies();
  store.set(AUTH_ACCESS_COOKIE, body.access_token!, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure,
    maxAge: Math.min(Number(body.expires_in) || 3600, 3600),
  });
  if (body.refresh_token) {
    store.set(AUTH_REFRESH_COOKIE, body.refresh_token, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      secure,
      maxAge: 60 * 60 * 24 * 30,
    });
  }

  // If Instagram is already connected in this browser, link it to the
  // account. Otherwise restore a previously linked shop session.
  const igSession = store.get(IG_SESSION_COOKIE)?.value || "";
  let linked = false;
  let connected = Boolean(igSession);
  if (igSession) {
    const response = await backendAuth("/api/auth/link", {
      method: "POST",
      headers: { "X-IG-Session": igSession },
      body: JSON.stringify({ user_id: user.id, email: user.email || "" }),
    });
    linked = Boolean(response?.ok);
  } else {
    const response = await backendAuth("/api/auth/restore", {
      method: "POST",
      body: JSON.stringify({ user_id: user.id }),
    });
    const data = (await response?.json().catch(() => ({}))) as {
      linked?: boolean;
      connected?: boolean;
      session_id?: string;
    };
    linked = Boolean(data?.linked);
    if (data?.connected && data.session_id) {
      store.set(IG_SESSION_COOKIE, data.session_id, sessionCookieOptions());
      connected = true;
    }
  }
  return NextResponse.json({ authenticated: true, email: user.email, linked, connected });
}
