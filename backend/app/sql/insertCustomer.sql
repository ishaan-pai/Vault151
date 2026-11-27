-- customerid comes from customer_seq via the column default, so the application
-- never invents an id; RETURNING hands back whatever the sequence assigned.
insert into customer ( displayname, email, joinedat )
values ( :display_name, :email, :joined_at )
returning customerid into :customer_id
