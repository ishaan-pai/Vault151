-- The existing payment for an order, used to answer a repeated Pay request with the
-- original result instead of an error.
select p.paymentid,
       p.orderid,
       p.paidat,
       p.amount,
       p.method,
       p.paymentreference
  from payment p
 where p.orderid = :order_id
