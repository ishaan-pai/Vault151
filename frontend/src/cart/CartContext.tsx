/**
 * The cart holds listing ids and nothing else.
 *
 * Prices, availability and card details are always re-fetched, so a cart left open
 * overnight cannot show yesterday's price or offer a card that has since sold. The
 * authoritative check happens inside the checkout transaction regardless.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

const STORAGE_KEY = "vault151.cart";

function readStoredCart(): number[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((id): id is number => Number.isInteger(id));
  } catch {
    // Private browsing, cleared storage, or something else wrote nonsense here.
    // An empty cart is a safe answer; it is not worth breaking the page over.
    return [];
  }
}

interface CartValue {
  listingIds: number[];
  count: number;
  has: (listingId: number) => boolean;
  add: (listingId: number) => void;
  remove: (listingId: number) => void;
  clear: () => void;
}

const CartContext = createContext<CartValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [listingIds, setListingIds] = useState<number[]>(readStoredCart);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(listingIds));
    } catch {
      // Storage full or blocked: the cart still works for this page view.
    }
  }, [listingIds]);

  const add = useCallback((listingId: number) => {
    // Each listing is one physical card, so adding twice is meaningless.
    setListingIds((current) =>
      current.includes(listingId) ? current : [...current, listingId],
    );
  }, []);

  const remove = useCallback((listingId: number) => {
    setListingIds((current) => current.filter((id) => id !== listingId));
  }, []);

  const clear = useCallback(() => setListingIds([]), []);

  const value = useMemo<CartValue>(
    () => ({
      listingIds,
      count: listingIds.length,
      has: (listingId: number) => listingIds.includes(listingId),
      add,
      remove,
      clear,
    }),
    [listingIds, add, remove, clear],
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartValue {
  const value = useContext(CartContext);
  if (!value) throw new Error("useCart must be used inside a CartProvider");
  return value;
}
