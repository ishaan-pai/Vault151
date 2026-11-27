-- orderline is a weak entity keyed (orderid, lineno) with no quantity column:
-- every line is one specific physical card. agreedprice is copied from the listing at
-- checkout so a later price change cannot rewrite a placed order.
insert into orderline ( orderid, lineno, listingid, agreedprice )
values ( :order_id, :line_no, :listing_id, :agreed_price )
