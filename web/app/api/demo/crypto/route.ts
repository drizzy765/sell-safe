import { NextResponse } from "next/server";

function apiBaseUrl(): string {
  const configured = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  return configured.replace(/\/$/, "");
}

export async function GET() {
  try {
    const upstream = await fetch(`${apiBaseUrl()}/api/demo/crypto`, {
      cache: "no-store",
    });
    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { ready: false, message: "Crypto demo service is unavailable.", cases: null },
      { status: 502 },
    );
  }
}
