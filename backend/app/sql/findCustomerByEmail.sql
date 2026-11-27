-- Guests have no accounts: one customer row per email address, reused on return.
-- customer_email_uq makes the email the real identity.
select c.customerid
  from customer c
 where lower(c.email) = lower(:email)
