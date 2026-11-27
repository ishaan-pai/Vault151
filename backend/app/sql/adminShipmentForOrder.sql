select s.shipmentid,
       s.orderid,
       s.carrier,
       s.trackingnumber,
       s.shippedat,
       s.deliveredat
  from shipment s
 where s.orderid = :order_id
