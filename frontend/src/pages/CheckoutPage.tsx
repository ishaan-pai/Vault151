import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useCartListings, useCreateOrder } from "../api/queries";
import { COUNTRY_LABELS, SHIPPING_COUNTRIES, type ShippingCountry } from "../api/types";
import { useCart } from "../cart/CartContext";
import { StateMessage } from "../components/StateMessage";
import { rememberOrderEmail } from "../lib/orderMemory";
import { sumAmounts } from "../lib/money";

const fieldClass =
  "w-full rounded border border-seam bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted/70";
const labelClass = "block text-xs text-muted";

export function CheckoutPage() {
  const cart = useCart();
  const navigate = useNavigate();
  const results = useCartListings(cart.listingIds);
  const createOrder = useCreateOrder();

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [province, setProvince] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState<ShippingCountry>("CA");

  if (cart.count === 0) {
    return (
      <StateMessage title="There is nothing to check out.">
        <Link to="/cards" className="text-sm text-brass underline">
          Browse the catalogue
        </Link>
      </StateMessage>
    );
  }

  const cards = results.flatMap((result) => (result.data ? [result.data] : []));
  const subtotal = sumAmounts(cards.map((card) => card.askingPrice));

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    createOrder.mutate(
      {
        email,
        displayName,
        listingIds: cart.listingIds,
        shippingAddress: {
          recipientName,
          street,
          city,
          province: province || null,
          postalCode,
          country,
        },
      },
      {
        onSuccess: (order) => {
          // Remember who placed it so the confirmation page need not ask again.
          rememberOrderEmail(order.publicRef, order.email);
          cart.clear();
          void navigate(`/orders/${order.publicRef}`);
        },
      },
    );
  }

  const conflict =
    createOrder.error instanceof ApiError && createOrder.error.status === 409;

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
      <form onSubmit={handleSubmit} className="flex flex-1 flex-col gap-5">
        <h1 className="text-lg font-medium text-ink">Checkout</h1>

        <section className="flex flex-col gap-3 rounded-lg border border-seam bg-surface p-4">
          <h2 className="text-sm font-medium text-ink">Your details</h2>
          <p className="text-xs text-muted">
            No account is created. Your email address and the order reference are how
            you find this order later.
          </p>

          <div>
            <label className={labelClass} htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className={`mt-1 ${fieldClass}`}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="displayName">
              Your name
            </label>
            <input
              id="displayName"
              required
              maxLength={100}
              autoComplete="name"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              className={`mt-1 ${fieldClass}`}
            />
          </div>
        </section>

        <section className="flex flex-col gap-3 rounded-lg border border-seam bg-surface p-4">
          <h2 className="text-sm font-medium text-ink">Shipping address</h2>

          <div>
            <label className={labelClass} htmlFor="recipientName">
              Recipient
            </label>
            <input
              id="recipientName"
              required
              maxLength={120}
              value={recipientName}
              onChange={(event) => setRecipientName(event.target.value)}
              className={`mt-1 ${fieldClass}`}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="street">
              Street
            </label>
            <input
              id="street"
              required
              maxLength={200}
              autoComplete="street-address"
              value={street}
              onChange={(event) => setStreet(event.target.value)}
              className={`mt-1 ${fieldClass}`}
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className={labelClass} htmlFor="city">
                City
              </label>
              <input
                id="city"
                required
                maxLength={100}
                value={city}
                onChange={(event) => setCity(event.target.value)}
                className={`mt-1 ${fieldClass}`}
              />
            </div>

            <div>
              <label className={labelClass} htmlFor="province">
                Province or state
              </label>
              <input
                id="province"
                maxLength={100}
                value={province}
                onChange={(event) => setProvince(event.target.value)}
                className={`mt-1 ${fieldClass}`}
              />
            </div>

            <div>
              <label className={labelClass} htmlFor="postalCode">
                Postal code
              </label>
              <input
                id="postalCode"
                required
                maxLength={20}
                autoComplete="postal-code"
                value={postalCode}
                onChange={(event) => setPostalCode(event.target.value)}
                className={`mt-1 ${fieldClass}`}
              />
            </div>

            <div>
              <label className={labelClass} htmlFor="country">
                Country
              </label>
              <select
                id="country"
                value={country}
                onChange={(event) =>
                  setCountry(event.target.value as ShippingCountry)
                }
                className={`mt-1 ${fieldClass}`}
              >
                {SHIPPING_COUNTRIES.map((code) => (
                  <option key={code} value={code}>
                    {COUNTRY_LABELS[code]}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {createOrder.isError ? (
          <div className="rounded-lg border border-brass/40 bg-brass/10 p-4 text-sm text-ink">
            <p>{createOrder.error.message}</p>
            {conflict ? (
              <Link to="/cart" className="mt-2 inline-block text-xs text-brass underline">
                Back to the cart
              </Link>
            ) : null}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={createOrder.isPending}
          className="rounded border border-brass/50 bg-brass/10 px-4 py-2 text-sm text-brass transition enabled:hover:bg-brass/20 disabled:opacity-50"
        >
          {createOrder.isPending ? "Reserving your cards\u2026" : "Place order"}
        </button>

        <p className="text-xs text-muted">
          Placing the order holds these cards for 30 minutes. You pay on the next
          page; nothing is charged yet.
        </p>
      </form>

      <aside className="rounded-lg border border-seam bg-surface p-4 lg:w-80">
        <h2 className="text-sm font-medium text-ink">
          {cart.count} card{cart.count === 1 ? "" : "s"}
        </h2>
        <ul className="mt-3 flex flex-col gap-2">
          {cards.map((card) => (
            <li key={card.listingId} className="flex justify-between gap-3 text-sm">
              <span className="text-muted">{card.cardName}</span>
              <span className="whitespace-nowrap text-ink">${card.askingPrice}</span>
            </li>
          ))}
        </ul>
        <div className="mt-3 flex justify-between border-t border-seam pt-3 text-sm">
          <span className="text-muted">Subtotal</span>
          <span className="text-ink">CAD ${subtotal}</span>
        </div>
        <p className="mt-2 text-xs text-muted">
          Shipping {country === "CA" ? "CA$15.00" : "CA$30.00"} is added to the total
          on the next page. No tax is charged.
        </p>
      </aside>
    </div>
  );
}
