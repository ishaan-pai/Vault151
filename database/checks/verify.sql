-- Sanity check for the app schema. Not run on boot; run manually:
--   docker exec cardshop-db bash -c 'sqlplus -s $APP_USER/$APP_USER_PASSWORD@//localhost/FREEPDB1 @/opt/cardshop/database/checks/verify.sql'
set pagesize 100 linesize 120 feedback off heading on
column check_name format a32
column result format a12

select 'tables (expect 10)' check_name, to_char(count(*)) result from user_tables
union all select 'views (expect 4)', to_char(count(*)) from user_views
union all select 'sequences (expect 8)', to_char(count(*)) from user_sequences
union all select 'storefront rows (expect 11)', to_char(count(*)) from storefront_listing
union all select 'featured (expect 4)', to_char(count(*)) from storefront_listing where isfeatured = 1
union all select 'orders w/o publicref (exp 0)', to_char(count(*)) from salesorder where publicref is null
union all select 'mock payments (expect 4)', to_char(count(*)) from payment where provider = 'mock';

-- Proves the sequence default works, then undoes it
insert into cardset ( setname, releasedate ) values ( '__verify__', sysdate );
select 'generated setid (expect 1000)' check_name, to_char(setid) result from cardset where setname = '__verify__';
rollback;
exit
