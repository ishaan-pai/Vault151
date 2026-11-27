-- The cards on one order, from the graded view CustomerOrderItems.
--
-- The view covers pending and cancelled history as well as paid orders, which is
-- exactly what an order-status page needs. It exposes neither publicref nor email, so
-- the caller resolves the order id first via orderByPublicRef.sql.
select coi.lineno,
       coi.listingid,
       coi.copyid,
       coi.cardname,
       coi.cardlanguage,
       coi.variant,
       coi.cardcondition,
       coi.agreed_price_cad
  from customerorderitems coi
 where coi.orderid = :order_id
 order by coi.lineno asc
