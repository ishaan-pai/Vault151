-- shipment_dates_ck refuses a delivery date earlier than the dispatch date, so the
-- timeline cannot be made nonsensical by a typo.
update shipment
   set deliveredat = :delivered_at
 where orderid = :order_id
