import { NextResponse } from "next/server";

import { backendAuth, currentUser } from "@/lib/supabaseServer";

export async function GET() {
  const user = await currentUser();
  if (!user) return NextResponse.json({ authenticated: false });
  let linked = false;
  const response = await backendAuth("/api/auth/restore", {
    method: "POST",
    body: JSON.stringify({ user_id: user.id }),
  });
  if (response?.ok) {
    const data = (await response.json().catch(() => ({}))) as { linked?: boolean };
    linked = Boolean(data.linked);
  }
  return NextResponse.json({ authenticated: true, email: user.email, linked });
}
