import { Link } from "react-router-dom";

import { useCartListings } from "../api/queries";
import { ApiError } from "../api/client";
import { useCart } from "../cart/CartContext";
import { CardImage } from "../components/CardImage";
import { Price } from "../components/Price";
import { StateMessage } from "../components/StateMessage";
import { sumAmounts } from "../lib/money";

/**
 * The cart stores ids only, so every card is re-fetched here. A card that sold while
 * the cart sat open comes back as a 404 and is shown as unavailable rather than
 * silently disappearing or, worse, being checked out at a stale price.
 */
export function CartPage() {
  const cart = useCart();
  const results = useCartListings(cart.listingIds);

  if (cart.count === 0) {
    return (
      <StateMessage title="Your cart is empty.">
        <Link to="/cards" className="text-sm text-brass underline">
          Browse the catalogue
        </Link>
      </StateMessage>
    );
  }

  const loading = results.some((result) => result.isPending);
  const available = results.flatMap((result) => (result.data ? [result.data] : []));
  const gone = cart.listingIds.filter((_listingId, index) => {
    const result = results[index];
    return result?.error instanceof ApiError && result.error.isNotFound;
  });
  const subtotal = sumAmounts(available.map((card) => card.askingPrice));

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-lg font-medium text-ink">Your cart</h1>

      {gone.length > 0 ? (
        <div className="rounded-lg border border-brass/40 bg-brass/10 p-4 text-sm text-ink">
          {gone.length === 1 ? "A card" : `${gone.length} cards`} in your cart{" "}
          {gone.length === 1 ? "is" : "are"} no longer for sale. Remove{" "}
          {gone.length === 1 ? "it" : "them"} to continue.
          <div className="mt-2 flex flex-wrap gap-2">
            {gone.map((listingId) => (
              <button
                key={listingId}
                type="button"
                onClick={() => cart.remove(listingId)}
                className="rounded border border-seam px-2 py-1 text-xs text-muted hover:text-brass"
              >
                Remove #{listingId}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <ul className="flex flex-col gap-3">
        {available.map((card) => (
          <li
            key={card.listingId}
            className="flex gap-4 rounded-lg border border-seam bg-surface p-3"
          >
            <Link to={`/cards/${card.listingId}`} className="w-20 shrink-0">
              <CardImage src={card.imageUrl} alt={card.cardName} />
            </Link>

            <div className="flex flex-1 flex-col">
              <Link
                to={`/cards/${card.listingId}`}
                className="text-sm font-medium text-ink hover:text-brass"
              >
                {card.cardName}
              </Link>
              <p className="mt-0.5 text-xs text-muted">
                {card.setName} &middot; {card.collectorNumber} &middot;{" "}
                {card.cardCondition}
              </p>
              <button
                type="button"
                onClick={() => cart.remove(card.listingId)}
                className="mt-auto self-start text-xs text-muted underline hover:text-brass"
              >
                Remove
              </button>
            </div>

            <Price
              amount={card.askingPrice}
              currency={card.currency}
              className="text-sm font-semibold text-brass"
            />
          </li>
        ))}
      </ul>

      <div className="rounded-lg border border-seam bg-surface p-4">
        <div className="flex justify-between text-sm">
          <span className="text-muted">Subtotal</span>
          <span className="text-ink">
            {loading ? "\u2026" : `CAD $${subtotal}`}
          </span>
        </div>
        <p className="mt-2 text-xs text-muted">
          Shipping is added at checkout: CA$15 within Canada, CA$30 to the United
          States. No tax is charged.
        </p>

        <Link
          to="/checkout"
          aria-disabled={gone.length > 0}
          className={`mt-4 block rounded border px-4 py-2 text-center text-sm transition ${
            gone.length > 0
              ? "pointer-events-none border-seam text-muted opacity-50"
              : "border-brass/50 bg-brass/10 text-brass hover:bg-brass/20"
          }`}
        >
          Checkout
        </Link>
      </div>
    </div>
  );
}
