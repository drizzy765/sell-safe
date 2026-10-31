import Link from "next/link";

import { cn } from "@/lib/utils";

type ShimmerButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  shimmerColor?: string;
  background?: string;
  href?: string;
};

export function ShimmerButton({
  children,
  className,
  shimmerColor = "#ffffff",
  background = "var(--gradient-brand)",
  href,
  ...props
}: ShimmerButtonProps) {
  const classes = cn(
    "group relative z-0 inline-flex cursor-pointer items-center justify-center overflow-hidden whitespace-nowrap rounded-md px-6 py-3 text-sm font-semibold text-white transition-transform duration-150 active:scale-[0.96]",
    "shadow-panel",
    className,
  );

  const style = {
    "--spread": "90deg",
    "--shimmer-color": shimmerColor,
    "--speed": "2.2s",
    "--bg": background,
    backgroundImage: background,
  } as React.CSSProperties;

  const inner = (
    <>
      <div className="-z-30 absolute inset-0 overflow-visible blur-[2px] [container-type:size]">
        <div className="absolute inset-0 h-[100cqh] animate-shimmer-slide [aspect-ratio:1] [border-radius:0] [mask:none]">
          <div className="absolute -inset-full w-auto rotate-0 animate-spin-around [background:conic-gradient(from_calc(270deg-(var(--spread)*0.5)),transparent_0,var(--shimmer-color)_var(--spread),transparent_var(--spread))] [translate:0_0]" />
        </div>
      </div>
      {children}
      <div className="absolute inset-0 rounded-md shadow-[inset_0_-8px_10px_#ffffff1f]" />
    </>
  );

  if (href) {
    return (
      <Link href={href} className={classes} style={style}>
        {inner}
      </Link>
    );
  }

  return (
    <button type="button" className={classes} style={style} {...props}>
      {inner}
    </button>
  );
}
