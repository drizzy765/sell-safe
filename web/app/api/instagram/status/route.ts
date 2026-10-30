import { NextResponse } from "next/server";

function apiBaseUrl(): string {
  const configured = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  return configured.replace(/\/$/, "");
}

export async function GET() {
  try {
    const upstream = await fetch(`${apiBaseUrl()}/api/instagram/status`, {
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
      { detail: "Instagram status is unavailable." },
      { status: 502 },
    );
  }
}
