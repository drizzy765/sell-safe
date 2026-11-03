import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { IG_SESSION_COOKIE } from "@/lib/instagramSession";
import { backendAuth, currentUser } from "@/lib/supabaseServer";

export async function POST() {
  const user = await currentUser();
  if (!user) return NextResponse.json({ detail: "Login first." }, { status: 401 });
  const store = await cookies();
  const igSession = store.get(IG_SESSION_COOKIE)?.value || "";
  if (!igSession) {
    return NextResponse.json({ detail: "Connect Instagram first." }, { status: 400 });
  }
  const response = await backendAuth("/api/auth/link", {
    method: "POST",
    headers: { "X-IG-Session": igSession },
    body: JSON.stringify({ user_id: user.id, email: user.email || "" }),
  });
  if (!response?.ok) {
    return NextResponse.json({ detail: "Could not save this shop to your account." }, { status: 502 });
  }
  return NextResponse.json({ linked: true });
}
