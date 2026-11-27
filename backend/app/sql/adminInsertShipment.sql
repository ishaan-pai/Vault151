-- shipment_order_uq allows one shipment per order, so recording a second dispatch for
-- the same order fails at the database rather than creating a duplicate.
insert into shipment ( orderid, carrier, trackingnumber, shippedat )
values ( :order_id, :carrier, :tracking_number, :shipped_at )
returning shipmentid into :shipment_id
