-- One physical card. imageurl is null until a photo is attached, which the seller can
-- do at any time afterwards by editing the listing.
insert into cardcopy ( printingid, cardcondition, description, imageurl )
values ( :printing_id, :card_condition, :description, :image_url )
returning copyid into :copy_id
