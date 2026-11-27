-- =============================================================================
-- 005_guest_order_reference.sql
-- WHAT: salesorder.publicref  random 32-char reference, unique, auto-filled.
-- WHY:  Guest checkout has no accounts, so an order is looked up by
--       (publicref + email). OrderID alone is sequential and guessable; a
--       random reference is not. The DEFAULT means every insert, seed rows
--       included, gets one with no backend work.
-- REUSE CHECKED: (orderid + email) would also work, since guessing an order ID
--       still needs the matching email, but emails are guessable for a targeted
--       buyer. One defaulted column with a unique constraint is cheaper than
--       that risk. Guests reuse the customer table: one row per email
--       (customer_email_uq), so no new table is needed.
-- NOT INCLUDED: no expiry column. Reservation expiry is
--       salesorder.placedat + a fixed window held in backend config, and
--       placedat already exists and is NOT NULL.
-- =============================================================================

alter table salesorder add ( publicref varchar2(32) default rawtohex(sys_guid()) not null );
alter table salesorder add constraint salesorder_publicref_uq unique ( publicref );
