-- Cancel the unpaid orders whose cards releaseExpiredListings.sql just freed.
-- Cancelled is a baseline status, so no schema change was needed to express this.
update salesorder
   set orderstatus = 'Cancelled'
 where orderstatus = 'AwaitingPayment'
   and placedat < :cutoff
