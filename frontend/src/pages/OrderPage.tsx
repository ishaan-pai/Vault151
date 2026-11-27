import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../api/client";
import { useOrder, usePayOrder } from "../api/queries";
import { StateMessage } from "../components/StateMessage";
import { recallOrderEmail, rememberOrderEmail } from "../lib/orderMemory";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-seam py-2 last:border-0">
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="text-right text-sm text-ink">{value}</dd>
    </div>
  );
}

/**
 * The order page doubles as the confirmation, the payment step and the receipt,
 * because they are the same order in three states.
 */
export function OrderPage() {
  const { publicRef = "" } = useParams();
  const [email, setEmail] = useState(() => recallOrderEmail(publicRef));
  const [typedEmail, setTypedEmail] = useState("");

  const order = useOrder(publicRef, email);
  const pay = usePayOrder();

  // This device has not seen the order before, so ask who they are.
  if (!email) {
    return (
      <form
        className="mx-auto flex max-w-md flex-col gap-3 rounded-lg border border-seam bg-surface p-6"
        onSubmit={(event) => {
          event.preventDefault();
          rememberOrderEmail(publicRef, typedEmail);
          setEmail(typedEmail);
        }}
      >
        <h1 className="text-lg font-medium text-ink">Confirm it is you</h1>
        <p className="text-sm text-muted">
          Enter the email address used for order {publicRef.slice(0, 8)}&hellip;
        </p>
        <input
          type="email"
          required
          value={typedEmail}
          onChange={(event) => setTypedEmail(event.target.value)}
          className="rounded border border-seam bg-canvas px-3 py-2 text-sm text-ink"
        />
        <button
          type="submit"
          className="rounded border border-brass/50 bg-brass/10 px-4 py-2 text-sm text-brass"
        >
          Show my order
        </button>
      </form>
    );
  }

  if (order.isPending) return <StateMessage title="Finding your order&hellip;" />;

  if (order.isError) {
    const notFound = order.error instanceof ApiError && order.error.isNotFound;
    return (
      <StateMessage
        title={notFound ? "No order matches that reference and email." : "The shop is not answering."}
        detail={notFound ? undefined : order.error.message}
      >
        <Link to="/orders" className="text-sm text-brass underline">
          Try the lookup form
        </Link>
      </StateMessage>
    );
  }

  const data = order.data;
  const awaitingPayment = data.status === "AwaitingPayment";
  const paid = data.payment !== null;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <section className="rounded-lg border border-seam bg-surface p-6">
        <p className="text-xs text-muted">Order reference</p>
        <p className="mt-1 font-mono text-xl break-all text-brass">{data.publicRef}</p>
        <p className="mt-3 text-sm text-muted">
          Save this. With your email address, it is the only way back to this order -
          there is no account to sign in to.
        </p>
      </section>

      {awaitingPayment ? (
        <section className="rounded-lg border border-brass/40 bg-brass/10 p-6">
          <h1 className="text-base font-medium text-ink">Your cards are held</h1>
          <p className="mt-1 text-sm text-muted">
            {data.expiresAt
              ? `This hold lapses at ${new Date(data.expiresAt).toLocaleString()}, after which the cards return to the shop.`
              : "Pay to complete the order."}
          </p>

          {pay.isError ? (
            <p className="mt-3 text-sm text-ink">{pay.error.message}</p>
          ) : null}

          <button
            type="button"
            disabled={pay.isPending}
            onClick={() => pay.mutate(publicRef)}
            className="mt-4 rounded border border-brass/60 bg-brass/20 px-5 py-2 text-sm font-medium text-brass transition enabled:hover:bg-brass/30 disabled:opacity-50"
          >
            {pay.isPending ? "Taking payment\u2026" : `Pay CAD $${data.total}`}
          </button>
          <p className="mt-2 text-xs text-muted">
            A mock payment: no card details are taken and no money moves.
          </p>
        </section>
      ) : (
        <section className="rounded-lg border border-seam bg-surface p-6">
          <h1 className="text-base font-medium text-ink">
            {paid ? "Paid. Thank you." : `This order is ${data.status.toLowerCase()}.`}
          </h1>
          {paid && data.payment ? (
            <p className="mt-1 text-sm text-muted">
              Paid {new Date(data.payment.paidAt).toLocaleString()} by{" "}
              {data.payment.method}, reference {data.payment.reference}.
            </p>
          ) : (
            <p className="mt-1 text-sm text-muted">
              The hold lapsed before payment, so the cards went back to the shop.
            </p>
          )}
        </section>
      )}

      <section className="rounded-lg border border-seam bg-surface px-4 py-2">
        {data.items.map((item) => (
          <div
            key={item.lineNo}
            className="flex justify-between gap-4 border-b border-seam py-3 last:border-0"
          >
            <div>
              <Link
                to={`/cards/${item.listingId}`}
                className="text-sm text-ink hover:text-brass"
              >
                {item.cardName}
              </Link>
              <p className="text-xs text-muted">
                {item.variant} &middot; {item.cardCondition} &middot; {item.cardLanguage}
              </p>
            </div>
            <span className="whitespace-nowrap text-sm text-ink">
              ${item.agreedPrice}
            </span>
          </div>
        ))}
      </section>

      <dl className="rounded-lg border border-seam bg-surface px-4 py-2">
        <Row label="Subtotal" value={`${data.currency} $${data.subtotal}`} />
        <Row label="Shipping" value={`${data.currency} $${data.shippingFee}`} />
        <Row label="Total" value={`${data.currency} $${data.total}`} />
        <Row label="Status" value={data.status} />
        <Row label="Email" value={data.email} />
      </dl>

      <section className="rounded-lg border border-seam bg-surface p-4 text-sm text-muted">
        <p className="text-ink">{data.shippingAddress.recipientName}</p>
        <p>{data.shippingAddress.street}</p>
        <p>
          {data.shippingAddress.city}
          {data.shippingAddress.province ? `, ${data.shippingAddress.province}` : ""}{" "}
          {data.shippingAddress.postalCode}
        </p>
        <p>{data.shippingAddress.country}</p>
      </section>
    </div>
  );
}
