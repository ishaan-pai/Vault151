-- Guest order lookup: the reference alone is not enough, the email must match too.
-- publicref is random and unique, the email is known only to the buyer, and neither
-- is guessable from an order id.
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
   and lower(c.email) = lower(:email)
