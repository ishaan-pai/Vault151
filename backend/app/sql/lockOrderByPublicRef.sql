-- Load an order for payment, locking it so two concurrent Pay requests serialise.
-- The row lock is what makes the "already paid" check below trustworthy: without it
-- both requests could read AwaitingPayment before either writes.
select o.orderid,
       o.orderstatus,
       o.placedat,
       o.shippingfee,
       c.email
  from salesorder o
  join customer c
on c.customerid = o.customerid
 where o.publicref = :public_ref
   for update of o.orderstatus
