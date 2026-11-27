-- Recording a payment.
--
-- The baseline's payment_order_uq (unique on orderid) is the idempotency guard: a
-- double-clicked Pay button makes this insert fail rather than recording a second
-- payment, and the service answers with the payment that already exists. The database
-- enforces it, not application logic.
--
-- method carries the provider name ('mock' now, a card brand once Stripe is wired in)
-- and paymentreference carries the provider's own transaction id.
insert into payment ( orderid, paidat, amount, method, paymentreference )
values ( :order_id, :paid_at, :amount, :method, :payment_reference )
returning paymentid into :payment_id
