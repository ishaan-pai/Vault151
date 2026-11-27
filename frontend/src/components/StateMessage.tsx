import type { ReactNode } from "react";

/** One place for the loading, empty and error states, so they look the same everywhere. */
export function StateMessage({
  title,
  detail,
  children,
}: {
  title: string;
  detail?: string;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-seam bg-surface px-6 py-12 text-center">
      <p className="text-ink">{title}</p>
      {detail ? <p className="mt-2 text-sm text-muted">{detail}</p> : null}
      {children ? <div className="mt-4">{children}</div> : null}
    </div>
  );
}
