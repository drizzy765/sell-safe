"use client";

import { cn } from "@/lib/utils";

type ShieldState = "idle" | "scanning" | "confirmed" | "suspicious" | "pending";

type ShieldSpinnerProps = {
  state?: ShieldState;
  size?: number;
  className?: string;
};

const strokeFor = (state: ShieldState) => {
  if (state === "confirmed") return "var(--success)";
  if (state === "suspicious") return "var(--danger)";
  if (state === "pending") return "var(--warning)";
  return "url(#shield-grad)";
};

export function ShieldSpinner({ state = "idle", size = 48, className }: ShieldSpinnerProps) {
  const stroke = strokeFor(state);

  return (
    <div
      className={cn("relative inline-flex items-center justify-center", className)}
      style={{ width: size, height: size }}
      aria-hidden
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 64 64"
        width={size}
        height={size}
        className="overflow-visible"
      >
        <defs>
          <linearGradient id="shield-grad" x1="8" y1="6" x2="56" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#2876FE" />
            <stop offset="55%" stopColor="#5A55F9" />
            <stop offset="100%" stopColor="#6E4AF7" />
          </linearGradient>
          <clipPath id="shield-clip">
            <path d="M32 6 C38 6 44 7.5 48.5 10.5 C51.5 12.5 53.5 15.5 53.5 19.5 V34.5 C53.5 44 45.5 52.5 32 58 C18.5 52.5 10.5 44 10.5 34.5 V19.5 C10.5 15.5 12.5 12.5 15.5 10.5 C20 7.5 26 6 32 6 Z" />
          </clipPath>
        </defs>
        <path
          fill="none"
          stroke={stroke}
          strokeWidth="5.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M32 6 C38 6 44 7.5 48.5 10.5 C51.5 12.5 53.5 15.5 53.5 19.5 V34.5 C53.5 44 45.5 52.5 32 58 C18.5 52.5 10.5 44 10.5 34.5 V19.5 C10.5 15.5 12.5 12.5 15.5 10.5 C20 7.5 26 6 32 6 Z"
        />
        <path
          fill="none"
          stroke={stroke}
          strokeWidth="5.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M16 30 C22 26 28 34 32 30 C36 26 42 34 48 30 M22 36 L29 43 L44 26"
        />
        {state === "scanning" ? (
          <g clipPath="url(#shield-clip)">
            <defs>
              <linearGradient id="scan-grad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="transparent" />
                <stop offset="50%" stopColor="rgba(40,118,254,0.55)" />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
            </defs>
            <rect
              x="-20"
              y="0"
              width="40"
              height="64"
              fill="url(#scan-grad)"
              className="animate-scan-band motion-reduce:animate-none"
            />
          </g>
        ) : null}
      </svg>
    </div>
  );
}
