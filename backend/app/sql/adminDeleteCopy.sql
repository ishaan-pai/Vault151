-- Only ever run for a copy with no remaining listings, and after its grading row has
-- gone, because gradedcardcopy_copy_fk points here.
delete from cardcopy
 where copyid = :copy_id
