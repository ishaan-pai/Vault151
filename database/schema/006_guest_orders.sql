-- =============================================================================
-- 006_guest_orders.sql
-- WHAT: salesorder.publicref  random 32-char reference, unique, auto-filled
--       salesorder.expiresat  when an unpaid order's reservation lapses
-- WHY:  Guest checkout = no accounts, so lookup is (publicref + email).
--       orderid alone is sequential and guessable; publicref isn't. The
--       DEFAULT means every insert, seed rows included, gets one automatically.
--       expiresat lets the backend release listings stuck in 'Reserved' when a
--       guest abandons checkout. The mock payment is instant, but Stripe is
--       asynchronous, so this avoids a schema change when Stripe is added.
-- Guests reuse the customer table: one row per email (customer_email_uq).
-- =============================================================================

alter table salesorder add ( publicref varchar2(32) default rawtohex(sys_guid()) not null );
alter table salesorder add ( expiresat date );
alter table salesorder add constraint salesorder_publicref_uq unique ( publicref );
