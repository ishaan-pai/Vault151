-- Look up a set by name before creating one, so adding two cards from the same set
-- does not create the set twice. cardset has no unique constraint on setname, so
-- this is the application keeping the data tidy rather than the database enforcing it.
select cs.setid
  from cardset cs
 where lower(cs.setname) = lower(:set_name)
