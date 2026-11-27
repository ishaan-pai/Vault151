-- Puts a copy up for sale. listing_price_ck rejects a non-positive price and
-- listing_status_ck rejects anything but the four known statuses, so bad input fails
-- at the database rather than reaching the catalogue.
insert into listing ( copyid, askingprice, listedat, listingstatus )
values ( :copy_id, :asking_price, :listed_at, 'Active' )
returning listingid into :listing_id
