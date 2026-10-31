import { type ComponentPropsWithoutRef } from "react";

import { cn } from "@/lib/utils";

type AnimatedGradientTextProps = ComponentPropsWithoutRef<"span"> & {
  speed?: number;
  colorFrom?: string;
  colorTo?: string;
};

export function AnimatedGradientText({
  children,
  className,
  speed = 1,
  colorFrom = "#2876FE",
  colorTo = "#6E4AF7",
  ...props
}: AnimatedGradientTextProps) {
  return (
    <span
      style={
        {
          "--bg-size": `${speed * 300}%`,
          "--color-from": colorFrom,
          "--color-to": colorTo,
        } as React.CSSProperties
      }
      className={cn(
        "animate-gradient inline bg-[length:var(--bg-size)_100%] bg-gradient-to-r from-[var(--color-from)] via-[var(--color-to)] to-[var(--color-from)] bg-clip-text text-transparent",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
