/**
 * Prices arrive as strings ("663.00") with a separate currency, and are rendered
 * without being turned into a float, so nothing can round.
 */
export function Price({
  amount,
  currency,
  className = "",
}: {
  amount: string;
  currency: string;
  className?: string;
}) {
  return (
    <span className={className}>
      <span className="text-muted">{currency} </span>
      <span className="tabular-nums">${amount}</span>
    </span>
  );
}
