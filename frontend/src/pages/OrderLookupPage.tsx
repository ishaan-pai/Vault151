import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { rememberOrderEmail } from "../lib/orderMemory";

export function OrderLookupPage() {
  const navigate = useNavigate();
  const [publicRef, setPublicRef] = useState("");
  const [email, setEmail] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const reference = publicRef.trim();
    rememberOrderEmail(reference, email.trim());
    void navigate(`/orders/${reference}`);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto flex max-w-md flex-col gap-4 rounded-lg border border-seam bg-surface p-6"
    >
      <h1 className="text-lg font-medium text-ink">Find your order</h1>
      <p className="text-sm text-muted">
        There are no accounts here. Your order reference and the email address you
        used are what identify an order.
      </p>

      <div>
        <label className="block text-xs text-muted" htmlFor="ref">
          Order reference
        </label>
        <input
          id="ref"
          required
          value={publicRef}
          onChange={(event) => setPublicRef(event.target.value)}
          className="mt-1 w-full rounded border border-seam bg-canvas px-3 py-2 font-mono text-sm text-ink"
        />
      </div>

      <div>
        <label className="block text-xs text-muted" htmlFor="lookup-email">
          Email
        </label>
        <input
          id="lookup-email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="mt-1 w-full rounded border border-seam bg-canvas px-3 py-2 text-sm text-ink"
        />
      </div>

      <button
        type="submit"
        className="rounded border border-brass/50 bg-brass/10 px-4 py-2 text-sm text-brass hover:bg-brass/20"
      >
        Find order
      </button>
    </form>
  );
}
