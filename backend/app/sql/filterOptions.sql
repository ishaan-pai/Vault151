-- The distinct values behind the catalogue's rarity, variant and condition filters.
--
-- Taken from the catalogue view, so the options offered are exactly the ones that can
-- return a card. UNION (not UNION ALL) removes the duplicates, since each value appears
-- once per listing that has it. One round trip instead of three.
select 'rarity' as option_kind,
       l.rarity as option_value
  from cataloguecarddetail l
union
select 'variant',
       l.variant
  from cataloguecarddetail l
union
select 'condition',
       l.cardcondition
  from cataloguecarddetail l
 order by option_kind asc,
          option_value asc
