-- Everyone the seller owes a message: unpaid orders, and parcels still in transit.
--
-- Assignment 5, query 2. UNION combines two unrelated populations into one contact
-- list and removes duplicates, so a customer who is both awaiting payment on one
-- order and awaiting delivery on another appears once rather than twice. UNION ALL
-- would list them twice.
select c.customerid,
       c.displayname,
       c.email
  from customer c,
       salesorder o
 where c.customerid = o.customerid
   and o.orderstatus = 'AwaitingPayment'
union
select c.customerid,
       c.displayname,
       c.email
  from customer c,
       salesorder o,
       shipment s
 where c.customerid = o.customerid
   and o.orderid = s.orderid
   and o.orderstatus = 'Shipped'
   and s.deliveredat is null
 order by displayname asc,
          customerid asc
