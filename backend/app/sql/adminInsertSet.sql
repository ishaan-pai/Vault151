-- setid comes from cardset_seq via the column default.
insert into cardset ( setname, releasedate )
values ( :set_name, :release_date )
returning setid into :set_id
