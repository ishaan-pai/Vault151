-- Sanity check for the app schema. Not run on boot; run manually:
--   docker exec cardshop-db bash -c 'sqlplus -s $APP_USER/$APP_USER_PASSWORD@//localhost/FREEPDB1 @/opt/cardshop/database/checks/verify.sql'
-- Safe to re-run: the one insert below is rolled back.
set pagesize 100 linesize 120 feedback off heading on
column check_name format a34
column result format a14

-- Object counts: 10 tables, 4 views (3 graded + CatalogueCardDetail), 8 sequences
select 'tables (expect 10)' check_name, to_char(count(*)) result from user_tables
union all select 'views (expect 4)', to_char(count(*)) from user_views
union all select 'sequences (expect 8)', to_char(count(*)) from user_sequences
-- The graded view and the view built on top of it must agree row for row
union all select 'ActiveCardCatalogue (expect 11)', to_char(count(*)) from activecardcatalogue
union all select 'CatalogueCardDetail (expect 11)', to_char(count(*)) from cataloguecarddetail
-- Grading is LEFT JOINed: no active listing is graded, so all 11 rows must
-- survive. An INNER join here would return 0.
union all select 'ungraded in cat. (expect 11)', to_char(count(*)) from cataloguecarddetail where grade is null
-- Home page = the 4 highest-priced active listings; dearest is Rayquaza V
union all select 'top catalogue price (exp 663)', to_char(max(asking_price_cad)) from cataloguecarddetail
-- The other two graded views must be populated for order lookup and receipts
union all select 'CustomerOrderItems (expect 8)', to_char(count(*)) from customerorderitems
union all select 'PaidOrderReceipts (expect 4)', to_char(count(*)) from paidorderreceipts
-- Every order can be looked up by its guest reference
union all select 'orders w/o publicref (expect 0)', to_char(count(*)) from salesorder where publicref is null;

-- Proves the sequence default works, then undoes it. The rollback does NOT give
-- the sequence value back, so each run returns a higher ID: the check is >= 1000,
-- not = 1000, so this file can be re-run against the same database.
insert into cardset ( setname, releasedate ) values ( '__verify__', sysdate );
select 'seq default (expect >=1000)' check_name,
       case
          when setid >= 1000 then
             'OK ' || setid
          else
             'FAIL ' || setid
       end result
  from cardset
 where setname = '__verify__';
rollback;
exit
