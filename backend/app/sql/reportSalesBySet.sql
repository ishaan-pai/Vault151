-- What each set has actually earned, by agreed price rather than list price.
--
-- Assignment 5, query 5. Aggregation across the full chain
-- cardset -> cardprinting -> cardcopy -> listing -> orderline -> salesorder -> payment,
-- with COUNT, SUM and AVG grouped by set. Shipping is excluded on purpose: it is
-- revenue from posting, not from cards.
select cs.setid,
       cs.setname,
       count(ol.lineno) as cardssold,
       sum(ol.agreedprice) as total_sales_cad,
       avg(ol.agreedprice) as average_price_cad
  from cardset cs,
       cardprinting cp,
       cardcopy cc,
       listing l,
       orderline ol,
       salesorder o,
       payment p
 where cs.setid = cp.setid
   and cp.printingid = cc.printingid
   and cc.copyid = l.copyid
   and l.listingid = ol.listingid
   and ol.orderid = o.orderid
   and o.orderid = p.orderid
   and o.orderstatus in ( 'Paid', 'Shipped', 'Delivered' )
 group by cs.setid,
          cs.setname
 order by cs.setid asc
