-- Both generated values come from the database, not the application: orderid from
-- salesorder_seq and publicref from its DEFAULT rawtohex(sys_guid()). The guest needs
-- publicref immediately, so it is returned rather than read back in a second query.
--
-- orderstatus defaults to 'AwaitingPayment'; it is spelled out here so the state the
-- order starts in is visible at the call site.
insert into salesorder (
   customerid, placedat, orderstatus, shippingfee,
   recipientname, street, city, province, postalcode, country
) values (
   :customer_id, :placed_at, 'AwaitingPayment', :shipping_fee,
   :recipient_name, :street, :city, :province, :postal_code, :country
)
returning orderid, publicref into :order_id, :public_ref
