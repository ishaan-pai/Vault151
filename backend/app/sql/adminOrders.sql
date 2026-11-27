-- The order list for the admin area: one row per order, newest first, with the item
-- count and value rolled up so the list is useful without opening each order.
select o.orderid,
       o.publicref,
       o.orderstatus,
       o.placedat,
       o.shippingfee,
       c.displayname,
       c.email,
       count(ol.lineno) as card_count,
       nvl(sum(ol.agreedprice), 0) as subtotal,
       s.shipmentid,
       s.shippedat,
       s.deliveredat
  from salesorder o
  join customer c
on c.customerid = o.customerid
  left join orderline ol
on ol.orderid = o.orderid
  left join shipment s
on s.orderid = o.orderid
 where ( :status is null
         or o.orderstatus = :status )
 group by o.orderid, o.publicref, o.orderstatus, o.placedat, o.shippingfee,
          c.displayname, c.email, s.shipmentid, s.shippedat, s.deliveredat
 order by o.placedat desc,
          o.orderid desc
