-- =============================================================================
-- 003_id_sequences.sql
-- WHAT: One sequence per table that owns its own surrogate key, wired in as the
--       column DEFAULT (Oracle 12c+), starting at 1000.
-- WHY:  The baseline hardcodes every ID, so the API couldn't create rows.
--       Converting to IDENTITY would require dropping/recreating the tables;
--       a sequence default is additive. The backend omits the ID and reads it
--       back with RETURNING ... INTO. Seed rows keep their explicit IDs (<1000),
--       so the two can never collide.
-- NOT INCLUDED: gradedcardcopy (key = its cardcopy's ID) and orderline
--       (lineno is 1..n within an order, assigned by the backend).
-- =============================================================================

create sequence customer_seq     start with 1000 increment by 1 nocache;
create sequence cardset_seq      start with 1000 increment by 1 nocache;
create sequence cardprinting_seq start with 1000 increment by 1 nocache;
create sequence cardcopy_seq     start with 1000 increment by 1 nocache;
create sequence listing_seq      start with 1000 increment by 1 nocache;
create sequence salesorder_seq   start with 1000 increment by 1 nocache;
create sequence payment_seq      start with 1000 increment by 1 nocache;
create sequence shipment_seq     start with 1000 increment by 1 nocache;

alter table customer     modify ( customerid default customer_seq.nextval );
alter table cardset      modify ( setid      default cardset_seq.nextval );
alter table cardprinting modify ( printingid default cardprinting_seq.nextval );
alter table cardcopy     modify ( copyid     default cardcopy_seq.nextval );
alter table listing      modify ( listingid  default listing_seq.nextval );
alter table salesorder   modify ( orderid    default salesorder_seq.nextval );
alter table payment      modify ( paymentid  default payment_seq.nextval );
alter table shipment     modify ( shipmentid default shipment_seq.nextval );
