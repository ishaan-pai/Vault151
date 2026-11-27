-- Everything the admin edit screen needs, including the current status, which decides
-- whether editing is allowed at all.
select l.listingid,
       l.copyid,
       l.askingprice,
       l.listedat,
       l.listingstatus,
       cc.imageurl,
       cc.cardcondition,
       cc.description,
       cp.cardname,
       cp.collectornumber,
       cp.variant,
       cp.rarity,
       cs.setname
  from listing l
  join cardcopy cc
on cc.copyid = l.copyid
  join cardprinting cp
on cp.printingid = cc.printingid
  join cardset cs
on cs.setid = cp.setid
 where l.listingid = :listing_id
