-- The admin opens orders by reference, the same identifier the guest holds, so a
-- customer email asking about "order 4F2A..." can be answered directly.
select o.orderid,
       o.publicref,
       o.orderstatus,
       o.placedat,
       o.shippingfee,
       o.recipientname,
       o.street,
       o.city,
       o.province,
       o.postalcode,
       o.country,
       c.displayname,
       c.email
  from salesorder o
  join customer c
on c.customerid = o.customerid
 where o.publicref = :public_ref
