-- The same order row as orderByPublicRef.sql, without the email check.
--
-- Only used immediately after this process created or paid the order, where the
-- caller already proved they own it. Guest lookup must always use the email-checked
-- statement instead, or the reference alone would be enough to read someone's order.
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
