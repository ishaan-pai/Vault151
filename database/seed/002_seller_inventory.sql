-- =============================================================================
-- 002_seller_inventory.sql
-- WHAT: The seller's real collection: 5 sets, 10 printings, 10 raw (ungraded)
--       Near Mint English copies, each with one Active listing (prices in CAD).
--       The 4 most valuable are featured on the home page.
-- WHY:  The assignment seed has only one Active listing, so the storefront
--       would be nearly empty. IDs start at 100 to stay visibly separate from
--       the assignment rows (1-10) and below sequence-generated IDs (1000+).
-- imageurl is NULL until real photos are uploaded (Step 7 admin).
-- =============================================================================

insert into cardset ( setid, setname, releasedate ) values ( 100, 'Evolving Skies', date '2021-08-27' );
insert into cardset ( setid, setname, releasedate ) values ( 101, 'Crown Zenith', date '2023-01-20' );
insert into cardset ( setid, setname, releasedate ) values ( 102, 'Paldean Fates', date '2024-01-26' );
insert into cardset ( setid, setname, releasedate ) values ( 103, 'Generations', date '2016-02-22' );
insert into cardset ( setid, setname, releasedate ) values ( 104, 'Astral Radiance', date '2022-05-27' );

-- Rayquaza V (Alternate Full Art) - Evolving Skies 194/203
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 100, 100, 'Rayquaza V', '194/203', 'English', 'Alternate Full Art', 'Ultra Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 100, 100, 'NearMint', 'Raw, Near Mint. Rayquaza V (Alternate Full Art), Evolving Skies 194/203.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 100, 100, 663.00, date '2026-11-18', 'Active', 1 );

-- Giratina VSTAR (Secret) - Crown Zenith GG69
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 101, 101, 'Giratina VSTAR', 'GG69', 'English', 'Secret', 'Secret Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 101, 101, 'NearMint', 'Raw, Near Mint. Giratina VSTAR (Secret), Crown Zenith GG69.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 101, 101, 375.00, date '2026-11-18', 'Active', 1 );

-- Charizard ex (Normal) - Paldean Fates 234/091
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 102, 102, 'Charizard ex', '234/091', 'English', 'Normal', 'Special Illustration Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 102, 102, 'NearMint', 'Raw, Near Mint. Charizard ex (Normal), Paldean Fates 234/091.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 102, 102, 355.00, date '2026-11-18', 'Active', 1 );

-- Arceus VSTAR (Secret) - Crown Zenith GG70
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 103, 101, 'Arceus VSTAR', 'GG70', 'English', 'Secret', 'Secret Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 103, 103, 'NearMint', 'Raw, Near Mint. Arceus VSTAR (Secret), Crown Zenith GG70.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 103, 103, 217.00, date '2026-11-18', 'Active', 1 );

-- Origin Forme Dialga VSTAR (Secret) - Crown Zenith GG68
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 104, 101, 'Origin Forme Dialga VSTAR', 'GG68', 'English', 'Secret', 'Secret Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 104, 104, 'NearMint', 'Raw, Near Mint. Origin Forme Dialga VSTAR (Secret), Crown Zenith GG68.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 104, 104, 167.00, date '2026-11-18', 'Active', 0 );

-- Origin Forme Palkia VSTAR (Secret) - Crown Zenith GG67
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 105, 101, 'Origin Forme Palkia VSTAR', 'GG67', 'English', 'Secret', 'Secret Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 105, 105, 'NearMint', 'Raw, Near Mint. Origin Forme Palkia VSTAR (Secret), Crown Zenith GG67.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 105, 105, 126.00, date '2026-11-18', 'Active', 0 );

-- M Gardevoir EX (Full Art) - Generations RC31
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 106, 103, 'M Gardevoir EX', 'RC31', 'English', 'Full Art', 'Ultra Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 106, 106, 'NearMint', 'Raw, Near Mint. M Gardevoir EX (Full Art), Generations RC31.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 106, 106, 152.00, date '2026-11-18', 'Active', 0 );

-- Gardevoir EX (Full Art) - Generations RC30
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 107, 103, 'Gardevoir EX', 'RC30', 'English', 'Full Art', 'Ultra Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 107, 107, 'NearMint', 'Raw, Near Mint. Gardevoir EX (Full Art), Generations RC30.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 107, 107, 149.00, date '2026-11-18', 'Active', 0 );

-- Sylveon EX (Normal) - Generations RC21
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 108, 103, 'Sylveon EX', 'RC21', 'English', 'Normal', 'Ultra Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 108, 108, 'NearMint', 'Raw, Near Mint. Sylveon EX (Normal), Generations RC21.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 108, 108, 140.00, date '2026-11-18', 'Active', 0 );

-- Origin Forme Palkia V (Alternate Full Art) - Astral Radiance 167/189
insert into cardprinting ( printingid, setid, cardname, collectornumber, cardlanguage, variant, rarity ) values ( 109, 104, 'Origin Forme Palkia V', '167/189', 'English', 'Alternate Full Art', 'Ultra Rare' );
insert into cardcopy ( copyid, printingid, cardcondition, description ) values ( 109, 109, 'NearMint', 'Raw, Near Mint. Origin Forme Palkia V (Alternate Full Art), Astral Radiance 167/189.' );
insert into listing ( listingid, copyid, askingprice, listedat, listingstatus, isfeatured ) values ( 109, 109, 125.00, date '2026-11-18', 'Active', 0 );

commit;
