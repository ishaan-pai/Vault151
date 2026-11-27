-- Home page feature strip: the most expensive cards currently for sale.
--
-- There is deliberately no "featured" column in the schema. The seller's four best
-- cards are simply the four dearest active listings, which the data already knows, so
-- the home page needs no flag to maintain and no extra column to explain.
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
       l.certificationnumber
  from cataloguecarddetail l
 order by l.asking_price_cad desc,
          l.listingid desc
fetch first :row_limit rows only
