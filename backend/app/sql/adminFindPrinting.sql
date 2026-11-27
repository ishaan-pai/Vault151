-- cardprinting_version_uq is (setid, collectornumber, cardlanguage, variant), so a
-- second copy of the same card must reuse the existing printing rather than insert a
-- duplicate. Looking it up first turns a constraint violation into a normal path.
select cp.printingid
  from cardprinting cp
 where cp.setid = :set_id
   and cp.collectornumber = :collector_number
   and cp.cardlanguage = :card_language
   and cp.variant = :variant
