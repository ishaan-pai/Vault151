import { useState } from "react";

import {
  useAdminOrders,
  useMarkDelivered,
  useRecordShipment,
} from "../../api/adminQueries";
import type { AdminOrderRow } from "../../api/adminTypes";
import { StateMessage } from "../../components/StateMessage";

function OrderActions({ order }: { order: AdminOrderRow }) {
  const recordShipment = useRecordShipment(order.publicRef);
  const markDelivered = useMarkDelivered(order.publicRef);
  const [carrier, setCarrier] = useState("Canada Post");
  const [tracking, setTracking] = useState("");

  const error = recordShipment.error ?? markDelivered.error;
  const fieldClass =
    "rounded border border-seam bg-canvas px-2 py-1.5 text-sm text-ink";

  if (order.shipment && order.shipment.deliveredAt) {
    return <p className="text-xs text-muted">Delivered.</p>;
  }

  if (order.shipment) {
    return (
      <div className="flex flex-col gap-2">
        <button
          type="button"
          disabled={markDelivered.isPending}
          onClick={() => markDelivered.mutate(undefined)}
          className="rounded border border-brass/50 bg-brass/10 px-3 py-1.5 text-sm text-brass transition enabled:hover:bg-brass/20 disabled:opacity-50"
        >
          {markDelivered.isPending ? "Saving\u2026" : "Mark delivered"}
        </button>
        {error ? <p className="text-xs text-danger">{error.message}</p> : null}
      </div>
    );
  }

  if (order.status !== "Paid") {
    // Anything that is not Paid has no action for the seller, but the reasons are
    // opposite: an awaiting order is still holding its cards, a cancelled one let
    // them go. Reporting both as "awaiting payment" would be a lie about stock.
    const explanation: Record<string, string> = {
      AwaitingPayment:
        "Awaiting payment. The cards are held until the reservation lapses.",
      Cancelled: "Cancelled. The hold lapsed and the cards went back to the shop.",
    };
    return (
      <p className="text-xs text-muted">
        {explanation[order.status] ?? `${order.status}. Nothing to do here.`}
      </p>
    );
  }

  return (
    <form
      className="flex flex-wrap items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        recordShipment.mutate({ carrier, trackingNumber: tracking });
      }}
    >
      <input
        aria-label="Carrier"
        value={carrier}
        onChange={(event) => setCarrier(event.target.value)}
        className={`${fieldClass} w-32`}
      />
      <input
        aria-label="Tracking number"
        required
        placeholder="Tracking"
        value={tracking}
        onChange={(event) => setTracking(event.target.value)}
        className={`${fieldClass} w-40`}
      />
      <button
        type="submit"
        disabled={recordShipment.isPending}
        className="rounded border border-brass/50 bg-brass/10 px-3 py-1.5 text-sm text-brass transition enabled:hover:bg-brass/20 disabled:opacity-50"
      >
        {recordShipment.isPending ? "Saving\u2026" : "Dispatch"}
      </button>
      {error ? <p className="w-full text-xs text-danger">{error.message}</p> : null}
    </form>
  );
}

export function AdminOrdersPage() {
  const orders = useAdminOrders();

  if (orders.isPending) return <StateMessage title="Loading orders&hellip;" />;
  if (orders.isError) {
    return <StateMessage title="Could not load orders." detail={orders.error.message} />;
  }
  if (orders.data.length === 0) {
    return <StateMessage title="No orders yet." />;
  }

  return (
    <ul className="flex flex-col gap-3">
      {orders.data.map((order) => (
        <li
          key={order.publicRef}
          className="flex flex-col gap-3 rounded-lg border border-seam bg-surface p-4"
        >
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <div>
              <p className="font-mono text-xs break-all text-muted">
                {order.publicRef}
              </p>
              <p className="mt-1 text-sm text-ink">
                {order.customerName}{" "}
                <span className="text-muted">&lt;{order.email}&gt;</span>
              </p>
              <p className="text-xs text-muted">
                {new Date(order.placedAt).toLocaleString()} &middot; {order.cardCount}{" "}
                card{order.cardCount === 1 ? "" : "s"}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-brass">CAD ${order.total}</p>
              <p className="text-xs text-muted">
                ${order.subtotal} + ${order.shippingFee} shipping
              </p>
              <p className="mt-1 text-xs text-ink">{order.status}</p>
            </div>
          </div>

          <div className="border-t border-seam pt-3">
            <OrderActions order={order} />
          </div>
        </li>
      ))}
    </ul>
  );
}
