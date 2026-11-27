import { Link } from "react-router-dom";

import { useCart } from "../cart/CartContext";

/**
 * Adding is not reserving. The card is only held once the order is placed, which is
 * the only moment the database can promise it, so this button makes no claim about
 * availability beyond what the catalogue already showed.
 */
export function AddToCartButton({
  listingId,
  className = "",
}: {
  listingId: number;
  className?: string;
}) {
  const cart = useCart();

  if (cart.has(listingId)) {
    return (
      <Link
        to="/cart"
        className={`block rounded border border-brass/50 bg-brass/10 px-3 py-2 text-center text-sm text-brass ${className}`}
      >
        In your cart
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={() => cart.add(listingId)}
      className={`block w-full rounded border border-seam px-3 py-2 text-center text-sm text-ink transition hover:border-brass/50 hover:text-brass ${className}`}
    >
      Add to cart
    </button>
  );
}
