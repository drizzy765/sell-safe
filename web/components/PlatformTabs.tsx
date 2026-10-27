"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { guides, platformIds, type PlatformId } from "@/content";

function parsePlatform(value: string | null): PlatformId {
  if (value === "instagram" || value === "messenger" || value === "whatsapp") {
    return value;
  }
  return "whatsapp";
}

export function PlatformTabs() {
  const router = useRouter();
  const params = useSearchParams();
  const current = parsePlatform(params.get("platform"));

  function select(id: PlatformId) {
    const next = new URLSearchParams(params.toString());
    if (id === "whatsapp") {
      next.delete("platform");
    } else {
      next.set("platform", id);
    }
    const query = next.toString();
    router.replace(query ? `/?${query}` : "/");
  }

  return (
    <div
      role="tablist"
      aria-label="Messaging platform"
      className="inline-flex max-w-full overflow-x-auto rounded-full border border-border bg-muted p-1"
    >
      {platformIds.map((id) => {
        const active = id === current;
        const guide = guides[id];
        return (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => select(id)}
            className={[
              "rounded-full px-4 py-2 text-sm font-medium transition",
              active
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            ].join(" ")}
            style={active ? { boxShadow: `inset 0 -2px 0 ${guide.accent}` } : undefined}
          >
            {guide.label}
          </button>
        );
      })}
    </div>
  );
}

export function useSelectedPlatform(): PlatformId {
  const params = useSearchParams();
  return parsePlatform(params.get("platform"));
}
