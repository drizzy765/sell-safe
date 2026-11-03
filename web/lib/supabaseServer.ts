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
  return verifySupabaseUser(store.get(AUTH_ACCESS_COOKIE)?.value || "");
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
