-- Lock one listing so no concurrent checkout can take the same physical card.
--
-- FOR UPDATE holds the row until the transaction ends. The service locks the cart's
-- listings one at a time in ascending id order: locking in a consistent order is what
-- stops two carts holding half of each other's cards and deadlocking.
--
-- One row at a time rather than an IN list because binding a variable-length list in
-- Oracle needs a collection type, and a new database type is exactly what the schema
-- rules say to avoid. Carts here are a handful of rows.
select l.listingid,
       l.listingstatus,
       l.askingprice
  from listing l
 where l.listingid = :listing_id
   for update
