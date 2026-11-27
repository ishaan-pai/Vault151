-- The receipt for a paid order, from the graded view PaidOrderReceipts.
-- One row per recorded payment, and payment_order_uq means at most one per order.
select por.paymentid,
       por.orderid,
       por.displayname,
       por.orderstatus,
       por.paidat,
       por.amount_cad,
       por.method,
       por.paymentreference
  from paidorderreceipts por
 where por.orderid = :order_id
