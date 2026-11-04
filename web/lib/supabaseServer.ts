import { cookies } from "next/headers";

import { apiBaseUrl } from "./apiBaseUrl";

export const AUTH_ACCESS_COOKIE = "sellsafe_auth_access";
export const AUTH_REFRESH_COOKIE = "sellsafe_auth_refresh";

export function supabaseUrl(): string {
  return (process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || "").replace(/\/$/, "");
}

export function supabaseAnonKey(): string {
  return process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
}

export function supabaseConfigured(): boolean {
  return Boolean(supabaseUrl() && supabaseAnonKey());
}

export type SupabaseUser = { id: string; email?: string };

export async function verifySupabaseUser(accessToken: string): Promise<SupabaseUser | null> {
  if (!accessToken || !supabaseConfigured()) return null;
  try {
    const response = await fetch(`${supabaseUrl()}/auth/v1/user`, {
      headers: { apikey: supabaseAnonKey(), Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.ok) return null;
    const body = (await response.json()) as { id?: string; email?: string };
    return body.id ? { id: body.id, email: body.email } : null;
  } catch {
    return null;
  }
}

export async function currentUser(): Promise<SupabaseUser | null> {
  const store = await cookies();
  const user = await verifySupabaseUser(store.get(AUTH_ACCESS_COOKIE)?.value || "");
  if (user) return user;
  // Access cookie lives 1h; refresh silently so sellers stay logged in.
  const refreshToken = store.get(AUTH_REFRESH_COOKIE)?.value || "";
  if (!refreshToken || !supabaseConfigured()) return null;
  try {
    const response = await fetch(`${supabaseUrl()}/auth/v1/token?grant_type=refresh_token`, {
      method: "POST",
      headers: { apikey: supabaseAnonKey(), "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!response.ok) return null;
    const body = (await response.json()) as {
      access_token?: string;
      refresh_token?: string;
      expires_in?: number;
      user?: { id?: string; email?: string };
    };
    if (!body.access_token || !body.user?.id) return null;
    const secure = process.env.NODE_ENV === "production";
    store.set(AUTH_ACCESS_COOKIE, body.access_token, {
      httpOnly: true, sameSite: "lax", path: "/", secure,
      maxAge: Math.min(Number(body.expires_in) || 3600, 3600),
    });
    if (body.refresh_token) {
      store.set(AUTH_REFRESH_COOKIE, body.refresh_token, {
        httpOnly: true, sameSite: "lax", path: "/", secure, maxAge: 60 * 60 * 24 * 30,
      });
    }
    return { id: body.user.id, email: body.user.email };
  } catch {
    return null;
  }
}

export async function backendAuth(path: string, init: RequestInit): Promise<Response | null> {
  const token = process.env.INTERNAL_API_TOKEN || "";
  if (!token) return null;
  try {
    return await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Token": token,
        ...(init.headers || {}),
      },
      cache: "no-store",
    });
  } catch {
    return null;
  }
}
