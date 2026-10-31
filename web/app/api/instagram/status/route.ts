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
    // Backend not running — return structured offline so the UI can explain,
    // instead of a bare gateway failure during local `npm run dev`.
    return NextResponse.json(
      {
        ready: false,
        offline: true,
        detail:
          "Backend is offline. Start FastAPI on :8000 (API_BASE_URL) for Instagram status.",
      },
      { status: 200 },
    );
  }
}
