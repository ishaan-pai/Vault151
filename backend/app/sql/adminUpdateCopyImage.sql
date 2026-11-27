-- The photo belongs to the physical copy, not the printing, so attaching one to a
-- live listing is an ordinary update with no schema change.
update cardcopy
   set imageurl = :image_url
 where copyid = :copy_id
