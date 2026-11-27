-- Orders holding more than one card, which need more care when packing.
--
-- Assignment 5, query 4. HAVING filters on the aggregate itself: WHERE cannot see
-- COUNT, because WHERE is applied before rows are grouped and HAVING after.
--
-- The threshold is a bind variable rather than a literal 2, so the seller can ask
-- for three or more without the statement changing. It is the only one of the five
-- reports that takes a parameter.
select o.orderid,
       c.displayname,
       o.orderstatus,
       count(ol.lineno) as cardcount,
       sum(ol.agreedprice) as subtotal_cad
  from customer c,
       salesorder o,
       orderline ol
 where c.customerid = o.customerid
   and o.orderid = ol.orderid
   and o.orderstatus <> 'Cancelled'
 group by o.orderid,
          c.displayname,
          o.orderstatus
having count(ol.lineno) >= :min_cards
 order by o.orderid asc
