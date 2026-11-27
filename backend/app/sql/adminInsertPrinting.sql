insert into cardprinting (
   setid, cardname, collectornumber, cardlanguage, variant, rarity
) values (
   :set_id, :card_name, :collector_number, :card_language, :variant, :rarity
)
returning printingid into :printing_id
