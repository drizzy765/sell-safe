export const IG_SESSION_COOKIE = "sellsafe_ig_session";

export const IG_SESSION_HEADER = "X-IG-Session";

export function sessionCookieOptions(maxAgeSeconds = 60 * 60 * 24 * 55) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: maxAgeSeconds,
  };
}
