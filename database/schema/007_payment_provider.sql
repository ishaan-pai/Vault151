-- =============================================================================
-- 007_payment_provider.sql
-- WHAT: payment.provider ('mock' | 'stripe', default 'mock') and a unique key
--       on (provider, paymentreference).
-- WHY:  paymentreference becomes the provider's transaction ID (a Stripe
--       PaymentIntent ID later). The unique key makes recording a payment
--       idempotent: Stripe can deliver the same webhook more than once, and
--       the DB rejects the duplicate instead of double-recording it.
--       Adding Stripe later = add a backend provider class + webhook route; no
--       migration needed.
-- =============================================================================

alter table payment add ( provider varchar2(20) default 'mock' not null );
alter table payment add constraint payment_provider_ck check ( provider in ( 'mock', 'stripe' ) );
alter table payment add constraint payment_provider_ref_uq unique ( provider, paymentreference );
