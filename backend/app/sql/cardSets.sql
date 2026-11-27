-- Every card set, for the catalogue's set filter.
--
-- Reads the cardset table rather than the catalogue view on purpose: the filter lists
-- all sets, including ones with nothing currently for sale. A shopper who picks a set
-- and sees no cards has learned something true - that none are in stock - which is
-- more useful than the set being silently absent from the list.
select cs.setid,
       cs.setname,
       cs.releasedate
  from cardset cs
 order by cs.releasedate desc,
          cs.setname asc
