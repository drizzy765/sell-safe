"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) {
    return (
      <button
        type="button"
        className="rounded-lg border border-border px-3 py-1.5 text-sm text-muted-foreground"
        aria-hidden
      >
        Theme
      </button>
    );
  }
  return (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      <span className="sr-only">Theme</span>
      <select
        className="rounded-lg border border-border bg-background px-2 py-1.5 text-foreground"
        value={theme ?? "system"}
        onChange={(e) => setTheme(e.target.value)}
        aria-label="Color theme"
      >
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
