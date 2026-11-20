# Changelog

Record of the restructuring into a 3-tier app (React → FastAPI → Oracle).
Schema-level detail lives in [`database/README.md`](database/README.md).

## Step 1: Project structure + local Oracle in Docker

**Added**
- `docker-compose.yml`: `db` service on `gvenzl/oracle-free:23-slim`, with a persistent volume and a healthcheck.
- `database/schema/001_tables.sql`, `002_views.sql`, `database/seed/001_sample_data.sql`: verbatim baselines from the assignment files.
- `database/init/00_run_all.sh`: first-boot loader that runs as the `cardshop` app user, not SYS.
- `.env.example` (committed template) and `.env` (local, gitignored, random passwords).
- `.gitignore` (was empty) and `.gitattributes` (forces LF on `.sh`/`.sql`/`.yml` for Linux containers).
- `database/README.md` and this file.

**Unchanged**
- All coursework files: `Assignment-*.sql`, `main.sql`, `README.md`, `LICENSE`.

## Step 2: Schema changes for the app

**Added** (all additive; baseline `001`/`002` untouched; details in `database/README.md`)
- `003_id_sequences.sql`: sequence-backed ID defaults starting at 1000.
- `004_card_images.sql`: `cardcopy.imageurl`.
- `005_featured_listings.sql`: `listing.isfeatured`.
- `006_guest_orders.sql`: `salesorder.publicref` (guest lookup key) and `salesorder.expiresat`.
- `007_payment_provider.sql`: `payment.provider` plus an idempotency key, for Stripe later.
- `008_storefront_view.sql`: `storefront_listing` view for the catalogue API.
- `seed/002_seller_inventory.sql`: the seller's 10 real cards, 4 featured.
- `checks/verify.sql`: manual sanity check.

**Decided**
- No admin table: the single seller's credentials come from `.env` (Step 7).
- Applying schema changes currently means a DB reset (`down -v`). A migration runner is planned before EC2 deploy.
