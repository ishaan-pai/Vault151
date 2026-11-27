-- Moves a listing through Active -> Reserved -> Sold. The status is a bind variable;
-- listing_status_ck in the baseline rejects anything outside the four allowed values,
-- so a typo fails at the database rather than corrupting the catalogue.
update listing
   set listingstatus = :status
 where listingid = :listing_id
