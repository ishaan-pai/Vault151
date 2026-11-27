-- Return cards to the catalogue when an unpaid order has sat past its hold.
--
-- Runs inside checkout and on order read, never on a timer: the standing rule is no
-- DBMS_SCHEDULER and no background jobs, so expiry is evaluated whenever someone
-- actually looks. placedat is the only timestamp the schema has, which is why the
-- window is a backend constant rather than a column.
--
-- Must run BEFORE releaseExpiredOrders.sql, which flips the orders this reads.
update listing
   set listingstatus = 'Active'
 where listingstatus = 'Reserved'
   and listingid in (
   select ol.listingid
     from orderline ol
     join salesorder o
   on o.orderid = ol.orderid
    where o.orderstatus = 'AwaitingPayment'
      and o.placedat < :cutoff
)
