-- =============================================================================
-- 008_storefront_view.sql
-- WHAT: storefront_listing, every Active listing with everything the
--       catalogue/detail pages display, grading info LEFT JOINed so raw cards
--       still appear (grade columns NULL).
-- WHY:  ActiveCardCatalogue (Assignment 4b) lacks image, featured, rarity and
--       grade. It stays exactly as submitted; this is a new view instead.
-- =============================================================================

create or replace view storefront_listing as
   select l.listingid,
          l.askingprice,
          l.listedat,
          l.isfeatured,
          cc.copyid,
          cc.cardcondition,
          cc.description,
          cc.imageurl,
          cp.printingid,
          cp.cardname,
          cp.collectornumber,
          cp.cardlanguage,
          cp.variant,
          cp.rarity,
          cs.setid,
          cs.setname,
          cs.releasedate,
          g.gradingcompany,
          g.grade,
          g.certificationnumber
     from listing l
     join cardcopy cc
   on cc.copyid = l.copyid
     join cardprinting cp
   on cp.printingid = cc.printingid
     join cardset cs
   on cs.setid = cp.setid
     left join gradedcardcopy g
   on g.copyid = cc.copyid
    where l.listingstatus = 'Active'
with read only;
