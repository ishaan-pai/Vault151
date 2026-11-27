-- Whether a physical copy still has other listings, which decides if deleting this
-- listing should also remove the copy or leave it for relisting.
select count(*) as listing_count
  from listing l
 where l.copyid = :copy_id
