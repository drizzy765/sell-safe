export function apiBaseUrl(): string {
  const configured = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  return configured.replace(/\/$/, "");
}
