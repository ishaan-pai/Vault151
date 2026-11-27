import type { ReactNode } from "react";

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "brass";
}) {
  const tones = {
    neutral: "border-seam bg-canvas text-muted",
    brass: "border-brass/40 bg-brass/10 text-brass",
  };
  return (
    <span
      className={`inline-flex items-center rounded border px-1.5 py-0.5 text-xs ${tones[tone]}`}
    >
      {children}
    </span>
  );
}
