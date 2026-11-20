-- =============================================================================
-- 005_featured_listings.sql
-- WHAT: listing.isfeatured, 0/1, default 0.
-- WHY:  Lets the seller pick which listings appear on the home page.
--       NUMBER(1) + CHECK instead of BOOLEAN: BOOLEAN only exists in Oracle
--       23ai, and the app may also need to run on TMU's (older) Oracle server.
-- =============================================================================

alter table listing add ( isfeatured number(1) default 0 not null );
alter table listing add constraint listing_featured_ck check ( isfeatured in ( 0, 1 ) );
