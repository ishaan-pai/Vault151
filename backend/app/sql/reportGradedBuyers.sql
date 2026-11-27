-- Customers who have bought at least one graded card.
--
-- Assignment 5, query 1. A correlated EXISTS subquery: it refers to C.CustomerID
-- from the outer query, so it is evaluated per customer and stops at the first
-- match. That is what makes it the right tool for "has this customer ever..." -
-- a join would return one row per matching order and need a DISTINCT to undo.
select c.customerid,
       c.displayname,
       c.email
  from customer c
 where exists (
   select ol.orderid
     from salesorder o,
          orderline ol,
          listing l,
          gradedcardcopy g,
          payment p
    where o.customerid = c.customerid
      and o.orderid = ol.orderid
      and ol.listingid = l.listingid
      and l.copyid = g.copyid
      and o.orderid = p.orderid
      and o.orderstatus in ( 'Paid', 'Shipped', 'Delivered' )
)
 order by c.displayname asc,
          c.customerid asc
