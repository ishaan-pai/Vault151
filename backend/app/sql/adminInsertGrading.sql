-- gradedcardcopy is a one-to-one optional extension of cardcopy: its primary key IS
-- the copy's id, so a copy can carry at most one grading record and a raw card simply
-- has no row here.
insert into gradedcardcopy ( copyid, gradingcompany, grade, certificationnumber )
values ( :copy_id, :grading_company, :grade, :certification_number )
