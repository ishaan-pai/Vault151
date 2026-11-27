-- The listings on an order, so payment can move them Reserved -> Sold.
select ol.listingid
  from orderline ol
 where ol.orderid = :order_id
 order by ol.listingid asc
