export function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  const button =
    "rounded border border-seam px-3 py-1.5 text-sm text-ink enabled:hover:border-brass/50 enabled:hover:text-brass disabled:opacity-40";

  return (
    <nav className="flex items-center justify-center gap-4" aria-label="Pagination">
      <button
        type="button"
        className={button}
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </button>
      <span className="text-sm text-muted">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        className={button}
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
      </button>
    </nav>
  );
}
