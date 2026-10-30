import { NextResponse } from "next/server";

function apiBaseUrl(): string {
  const configured = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  return configured.replace(/\/$/, "");
}

export async function POST(request: Request) {
  const body = await request.text();
  try {
    const upstream = await fetch(`${apiBaseUrl()}/api/waitlist`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return NextResponse.json({ detail: "Waitlist service is unavailable." }, { status: 502 });
  }
}
