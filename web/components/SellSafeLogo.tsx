"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

type LogoVariant = "wordmark" | "icon" | "mono";

type SellSafeLogoProps = {
  variant?: LogoVariant;
  className?: string;
  height?: number;
};

export function SellSafeLogo({
  variant = "wordmark",
  className,
  height = 32,
}: SellSafeLogoProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (variant === "mono" || variant === "icon") {
    const src = variant === "mono" ? "/brand/mark-mono.svg" : "/brand/mark-icon.svg";
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt="Sell-Safe"
        width={height}
        height={height}
        className={cn(variant === "mono" && "text-foreground", className)}
      />
    );
  }

  const dark = mounted && resolvedTheme === "dark";
  const src = dark ? "/brand/mark-dark.svg" : "/brand/mark-wordmark.svg";
  const width = Math.round(height * (280 / 64));

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt="Sell-Safe" width={width} height={height} className={className} />
  );
}
