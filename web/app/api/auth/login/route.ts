import { NextResponse } from "next/server";

import { supabaseAnonKey, supabaseConfigured, supabaseUrl } from "@/lib/supabaseServer";

export async function POST(request: Request) {
  if (!supabaseConfigured()) {
    return NextResponse.json(
      { detail: "Login is not configured yet. Set SUPABASE_URL and SUPABASE_ANON_KEY on the web host." },
      { status: 503 },
    );
  }
  const body = (await request.json().catch(() => ({}))) as { email?: string };
  const email = (body.email || "").trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ detail: "Enter a valid email address." }, { status: 400 });
  }
  const origin = new URL(request.url).origin;
  const response = await fetch(`${supabaseUrl()}/auth/v1/otp`, {
    method: "POST",
    headers: { apikey: supabaseAnonKey(), "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      create_user: true,
      email_redirect_to: `${origin}/auth/callback`,
    }),
  });
  if (!response.ok) {
    return NextResponse.json(
      { detail: "Could not send the login link. Check the email and try again." },
      { status: 502 },
    );
  }
  return NextResponse.json({ sent: true });
}
