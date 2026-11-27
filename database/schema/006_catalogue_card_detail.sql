-- =============================================================================
-- 006_catalogue_card_detail.sql
-- WHAT: CatalogueCardDetail, a view built ON TOP OF the graded view
--       ActiveCardCatalogue.
-- WHY:  The catalogue and card-detail pages need four things
--       ActiveCardCatalogue does not expose: rarity, the copy's photo and
--       description, grading information, and SetID / ListedAt for filtering
--       and sorting. Selecting FROM ActiveCardCatalogue keeps the graded view
--       in the application's read path rather than running a second, parallel
--       query over the same tables.
-- REUSE CHECKED: ActiveCardCatalogue is reused directly and is the driving
--       row source here; it already applies the ListingStatus = 'Active'
--       filter, so that rule is defined in exactly one place. The alternative
--       was joining to it in the repository layer, which would scatter the same
--       SQL across endpoints.
-- NOTE: GradedCardCopy is LEFT JOINed so ungraded ("raw") cards still appear,
--       with the grade columns NULL. The home page's featured section is the
--       four highest-priced rows of this view, so no "featured" flag exists.
-- =============================================================================

create or replace view CatalogueCardDetail as
   select acc.listingid,
          acc.copyid,
          acc.cardname,
          acc.setname,
          acc.collectornumber,
          acc.cardlanguage,
          acc.variant,
          acc.cardcondition,
          acc.asking_price_cad,
          cp.setid,
          cp.rarity,
          cc.description,
          cc.imageurl,
          l.listedat,
          g.gradingcompany,
          g.grade,
          g.certificationnumber
     from activecardcatalogue acc
     join cardcopy cc
   on cc.copyid = acc.copyid
     join cardprinting cp
   on cp.printingid = cc.printingid
     join listing l
   on l.listingid = acc.listingid
     left join gradedcardcopy g
   on g.copyid = acc.copyid
with read only;
