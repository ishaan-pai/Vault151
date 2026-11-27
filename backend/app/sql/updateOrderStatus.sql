-- Moves an order through AwaitingPayment -> Paid, or -> Cancelled when it expires.
-- salesorder_status_ck in the baseline rejects anything outside the five allowed
-- values, so a typo fails at the database rather than wedging an order in limbo.
update salesorder
   set orderstatus = :status
 where orderid = :order_id
