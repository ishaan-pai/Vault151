-- =============================================================================
-- 004_card_images.sql
-- WHAT: cardcopy.imageurl, nullable.
-- WHY:  Buyers of a specific physical card want to see THAT card (centering,
--       wear, slab), so the photo belongs to the copy, not the printing.
--       Stored as a URL (local /static path now, S3/CDN on AWS later), not a
--       BLOB, to keep the database small. NULL = frontend shows a placeholder.
-- =============================================================================

alter table cardcopy add ( imageurl varchar2(500) );
