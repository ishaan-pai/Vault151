-- Catalogue search, reading the graded view ActiveCardCatalogue through
-- CatalogueCardDetail, which is built on top of it.
--
-- Every filter is optional and every one of them is a bind variable: a NULL bind
-- disables that predicate rather than changing the statement. Nothing in this file is
-- ever assembled by string concatenation, so no caller can inject SQL.
--
-- count(*) over () returns the number of rows matching the filters BEFORE the OFFSET
-- clause trims the page, so one round trip yields both the page and the total.
--
-- __ORDER_BY__ is the single exception to "nothing is assembled": ORDER BY cannot be
-- parameterised in Oracle, so the repository substitutes one fragment chosen from a
-- fixed whitelist. The client sends a key such as "price_desc", never SQL.
select l.listingid,
       l.copyid,
       l.setid,
       l.cardname,
       l.setname,
       l.collectornumber,
       l.cardlanguage,
       l.variant,
       l.rarity,
       l.cardcondition,
       l.description,
       l.asking_price_cad,
       l.imageurl,
       l.listedat,
       l.gradingcompany,
       l.grade,
       l.certificationnumber,
       count(*) over () as total_items
  from cataloguecarddetail l
 where ( :set_id is null
         or l.setid = :set_id )
   and ( :rarity is null
         or l.rarity = :rarity )
   and ( :variant is null
         or l.variant = :variant )
   and ( :card_condition is null
         or l.cardcondition = :card_condition )
   -- 1 = graded only, 0 = raw only, NULL = both
   and ( :graded is null
         or ( :graded = 1
              and l.grade is not null )
         or ( :graded = 0
              and l.grade is null ) )
   and ( :min_price is null
         or l.asking_price_cad >= :min_price )
   and ( :max_price is null
         or l.asking_price_cad <= :max_price )
   -- Card name only, case-insensitive substring match
   and ( :q is null
         or lower(l.cardname) like '%' || lower(:q) || '%' )
 order by __ORDER_BY__
offset :row_offset rows fetch next :row_limit rows only
