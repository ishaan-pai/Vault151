-- One listing's full detail, from the view built on the graded ActiveCardCatalogue.
-- Only Active listings are visible, because that filter lives in the graded view: a
-- sold or withdrawn listing simply returns no row, and the API turns that into a 404.
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
 where l.listingid = :listing_id
