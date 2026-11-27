-- Paid orders with no shipment recorded: the seller's "what do I need to post?" list.
--
-- Assignment 5, query 3. MINUS subtracts one result set from another: every order
-- that has a payment, less every order that has a shipment. Expressing it as a
-- difference of two populations is clearer than a NOT EXISTS, and it is the only
-- place in the application that uses the operator.
select o.orderid,
       c.displayname,
       o.orderstatus,
       o.placedat
  from customer c,
       salesorder o,
       payment p
 where c.customerid = o.customerid
   and o.orderid = p.orderid
minus
select o.orderid,
       c.displayname,
       o.orderstatus,
       o.placedat
  from customer c,
       salesorder o,
       shipment s
 where c.customerid = o.customerid
   and o.orderid = s.orderid
 order by orderid asc
