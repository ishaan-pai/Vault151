-- Can this listing be deleted?
--
-- orderline_listing_fk points at listing, so a listing that appears on any order
-- cannot be removed: deleting it would tear a hole in a real customer's order
-- history. The admin screen offers Disable instead when this returns anything above
-- zero. The foreign key would refuse anyway; asking first lets us say why.
select count(*) as line_count
  from orderline ol
 where ol.listingid = :listing_id
