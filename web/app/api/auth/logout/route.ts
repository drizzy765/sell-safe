import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { AUTH_ACCESS_COOKIE, AUTH_REFRESH_COOKIE } from "@/lib/supabaseServer";

export async function POST() {
  const store = await cookies();
  const options = { httpOnly: true, sameSite: "lax" as const, path: "/", maxAge: 0 };
  store.set(AUTH_ACCESS_COOKIE, "", options);
  store.set(AUTH_REFRESH_COOKIE, "", options);
  return NextResponse.json({ ok: true });
}
