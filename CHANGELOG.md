# Changelog

Record of the restructuring into a 3-tier app (React → FastAPI → Oracle).
Schema detail, the feature-to-database mapping and the demo script live in
[`database/README.md`](database/README.md).

## Step 1: Project structure + local Oracle in Docker

**Added**
- `docker-compose.yml`: `db` service on `gvenzl/oracle-free:23-slim`, with a persistent volume and a healthcheck.
- `database/schema/001_tables.sql`, `002_views.sql`, `database/seed/001_sample_data.sql`: verbatim baselines from the assignment files.
- `database/init/00_run_all.sh`: first-boot loader that runs as the `cardshop` app user, not SYS.
- `.env.example` (committed template) and `.env` (local, gitignored, random passwords).
- `.gitignore` (was empty) and `.gitattributes` (forces LF on `.sh`/`.sql`/`.yml` for Linux containers).
- This file.

**Unchanged**
- All coursework files: `Assignment-*.sql`, `main.sql`, `README.md`, `LICENSE`.

## Step 2: Schema changes for the app

**Added** (all additive; baseline `001`/`002` untouched; details in [`database/README.md`](database/README.md))
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

### Step 2 wrap-up

**Changed**
- `seed/002_seller_inventory.sql`: all 10 `listedat` dates moved to `2026-11-26`.
- `checks/verify.sql`: the generated-ID check is now `>= 1000` rather than `= 1000`. A
  rolled-back insert does not return the sequence value, so the old check only passed on
  the first run against a given database; the file is now re-runnable.
- `README.md`: replaced the two-line stub with the project document — architecture,
  local setup, environment variables, the schema change log, and current status.
- This file: the Step 1 entry claimed a `database/README.md` that was never created, and
  two links pointed at it. They now point at the README.

**Decided**
- The baseline's one active demo listing (Demo Leaf Guardian, listing 1) **stays visible**
  in the storefront. It is a useful real row with a `NULL` `imageurl` for exercising
  front-end placeholder handling, and leaving it alone keeps the baseline query results
  intact. Storefront total stays at 11 active listings, 4 featured.
- **No `database/README.md`.** Schema documentation lives in the root `README.md`, which
  covers the whole project; this file stays the chronological per-step record.
- Card identification confirmed: Charizard ex = Paldean Fates 234/091 (Special
  Illustration Rare); Sylveon EX = Generations RC21, not the RC32 full art; the Crown
  Zenith golds are Galarian Gallery GG67–GG70, stored under set name "Crown Zenith".
  All prices are CAD.
- The README does not reference the coursework SQL files, which will be removed once the
  project is finished.

**Deferred**
- `00_run_all.sh` hardcodes the `FREEPDB1` service name while `.env.example` defines
  `DB_SERVICE`, which compose never passes to the container. Harmless today; folded into
  Step 3, which wires `DB_SERVICE` into the backend anyway.
- All 10 seller listings now share one `listedat`, so a "newest first" sort has a 10-way
  tie. Needs a tie-break (price or `listingid`) — a Step 4 sorting decision.

## Step 2 correction: build on the graded schema

**Verified 2026-11-26** against a fresh Oracle Free 23 container: the loader reported
`[cardshop-init] SUCCESS` and `checks/verify.sql` returned every expected value -
10 tables, 4 views, 8 sequences, `ActiveCardCatalogue` and `CatalogueCardDetail` both
11 rows, all 11 ungraded, top price 663, `CustomerOrderItems` 8, `PaidOrderReceipts` 4,
no order missing a `publicref`, and a sequence-generated ID of 1000.

The marked deliverable is the database work, so the application is built around the
graded schema and its views rather than around new objects. New standing rules: no new
table without first showing the existing ten cannot do the job; every proposed column or
view states what existing object was considered for reuse; reads go through the graded
views; every step plan carries a feature-to-database mapping; and the DB machinery stays
simple (a custom migration script, no scheduled jobs).

Everything here was re-evaluated against "does a graded feature actually need this".

**Removed** — redundant with objects already in the graded schema
- `005_featured_listings.sql` (`listing.isfeatured`). The home page is now the four
  highest-priced rows of the catalogue view, which is the same four cards and no schema.
- `salesorder.expiresat`. `placedat` is NOT NULL and already exists; reservation expiry
  is `placedat` plus a fixed window held in backend config.
- `007_payment_provider.sql` entirely. `payment.method` already names the method, and
  the baseline's `payment_order_uq` (one payment per order) is stronger idempotency than
  the unique key this added. Stripe later means a PaymentIntent ID in `paymentreference`
  and no migration.
- `008_storefront_view.sql`, a view running in parallel with `ActiveCardCatalogue` over
  the same tables.

**Added**
- `006_catalogue_card_detail.sql`: `CatalogueCardDetail`, selecting **from**
  `ActiveCardCatalogue` and joining back only for rarity, image, description, grading
  and `setid`/`listedat`. The graded view is now in the application's read path and the
  `Active` filter is defined in one place.
- `database/README.md`: object inventory, change log with the reuse rationale for each
  file, feature-to-database mapping, the Assignment 5 queries mapped to admin reports,
  and the demo script.

**Changed**
- Schema files renumbered to close the gaps: `006_guest_orders.sql` became
  `005_guest_order_reference.sql` (publicref only), and the catalogue view became `006`.
  Nothing had been applied to a database, so no migration was needed.
- `seed/002_seller_inventory.sql`: `isfeatured` dropped from all 10 inserts.
- `checks/verify.sql`: rewritten around the graded objects — asserts that
  `CatalogueCardDetail` and `ActiveCardCatalogue` agree row for row, that the left join
  preserves all 11 ungraded active cards, and that `CustomerOrderItems` (8 rows) and
  `PaidOrderReceipts` (4 rows) are populated.
- `README.md`: re-framed around the data model, with schema detail delegated to
  `database/README.md` instead of duplicated.

**Kept, with the reuse argument recorded**
- `003_id_sequences.sql`: every write path needs generated IDs, there was no sequence to
  extend, and `max(id) + 1` in the backend is unsafe under concurrent checkout.
- `004_card_images.sql`: `cardcopy.description` is human-readable prose, so overloading
  it with a URL would be worse modelling.
- `005` `salesorder.publicref`: `(orderid + email)` would work, but order IDs are
  sequential and a targeted buyer's email is guessable.

**Decided**
- The graded artifacts are the `Assignment-*.sql` files and `main.sql`; everything under
  `database/` is ours to restructure. Earlier notes treating `001`/`002`/`seed/001` as
  untouchable were wrong — they stay faithful copies of the graded DDL because the
  application's schema must match the graded one, not because the files are protected.
- `database/README.md` exists after all, holding the running feature-to-database mapping
  that becomes the TA demo script. This reverses the Step 2 wrap-up decision above.
- The root `README.md` does not reference the coursework SQL files, which will be
  removed when the project is finished. `database/README.md` does reference the
  Assignment 5 queries, because mapping them to admin reports is the point of that file.

**Superseded**
- The Step 2 wrap-up decisions about keeping `storefront_listing` and having no
  `database/README.md` no longer hold. The demo listing staying visible in the storefront
  is unaffected.

**Deferred**
- `00_run_all.sh` hardcodes the `FREEPDB1` service name while `.env.example` defines
  `DB_SERVICE`; folded into the backend step, which wires that variable in anyway.
- All 10 seller listings share one `listedat`, so a "newest first" sort needs a
  tie-break on price or `listingid` — a catalogue-API decision.

## Step 3: Backend skeleton

**Verified 2026-11-26.** `ruff check`, `ruff format --check` and `mypy --strict` clean
across 19 files; 5 unit tests pass with no database; the stack builds and both containers
report healthy; `/api/health` returns `{"status":"ok","database":"ok"}` and, with the
database stopped, `503` with `{"status":"degraded","database":"unreachable"}`; all 3
integration tests pass, including `ActiveCardCatalogue` and `CatalogueCardDetail`
agreeing row for row through the pool.

Three defects were found and fixed during verification: a module-level
`app = create_app()` that made importing `app.main` require a configured environment, a
test fixture passing `str` where `SecretStr` was declared (caught by mypy), and a
`conftest` fixture that closed its test client before returning it.

A runnable FastAPI application with no business endpoints. Decisions and the options
weighed for each are in [`DECISIONS.md`](DECISIONS.md) (3.1-3.13).

**Added**
- `backend/app/`: `config.py` (typed settings, password as `SecretStr`), `db.py`
  (thin-mode `oracledb` pool, context-managed connections that roll back on error),
  `errors.py` (`AppError` hierarchy plus handlers that log everything and leak nothing in
  production), `logging_setup.py` (plain lines in dev, single-line JSON otherwise),
  `dependencies.py`, `main.py` (app factory, lifespan-managed pool). The application is
  served through the factory (`app.main:create_app --factory`) rather than a
  module-level instance, so importing the module needs no configured environment - a
  test can import it without a database.
- `Settings` reads `../.env` then `.env`, so running uvicorn from `backend/` picks up the
  same file compose uses, while the container gets its values from the environment.
- `app/api/health.py`: `GET /api/health`, returning 200 after a real
  `select 1 from dual` and 503 when the pool cannot answer.
- `app/sql/`: SQL kept in its own `.sql` files with a cached loader, which strips the
  trailing semicolon Oracle rejects over the driver.
- `app/repositories/health.py`, `app/schemas/health.py`, and empty `services/` ready for
  the catalogue step.
- `backend/tests/`: unit tests against a stand-in database (no Docker), and integration
  tests marked `integration` that skip when no database is reachable. The integration
  suite asserts the graded `ActiveCardCatalogue` is readable and that
  `CatalogueCardDetail` agrees with it row for row.
- `backend/pyproject.toml` (uv, ruff, mypy strict, pytest), `Dockerfile`
  (`python:3.12-slim`, non-root), `.dockerignore`.
- `DECISIONS.md`: a running log of every decision on the project, the options considered,
  and why one won - backfilled for steps 2 and 3.

**Changed**
- `docker-compose.yml`: `backend` service, built from `./backend`, depending on
  `db` with `condition: service_healthy`, with its own healthcheck hitting `/api/health`.
  `DB_HOST: db` and `DB_PORT: 1521` are set per-service, which is the compose-network
  address rather than the published host port.
- `.env.example`: `APP_ENV`, `LOG_LEVEL`, `BACKEND_PORT`, `DB_POOL_MIN`, `DB_POOL_MAX`,
  `DB_POOL_INCREMENT`.
- `README.md`, `database/README.md`: backend layout, how to run it, and the mapping row
  for `/api/health`.

**Resolved**
- The deferred `DB_SERVICE` item: compose now passes it to the backend. The loader still
  hardcodes `FREEPDB1`, which is correct for a first-boot script that only ever talks to
  its own container.

**Flagged**
- `/api/health` touches no graded object. That is expected of a skeleton - it is the pipe
  the graded views run through from the catalogue step onwards.

**Deferred**
- The `uv` version in the Dockerfile is unpinned until `uv --version` is confirmed
  locally, so that the image and the development machine agree.
- Error response shape is minimal and settles in the catalogue step, where it is the one
  place that changes.

## Step 4: Catalogue API (read side)

**Verified 2026-11-26.** 47 tests pass - 30 unit, 17 integration, the latter asserting
real filter, sort and pagination results against the seeded catalogue. The stack builds
and both containers report healthy. Six curls confirmed: featured returns Rayquaza V 663,
Giratina 375, Charizard 355, Arceus 217; an unfiltered page reports `totalItems` 11 over
3 pages; `setId=101` returns the 4 Crown Zenith golds; `q=giratina` returns 1; the
withdrawn listing 2 is a 404 in the error envelope; and `pageSize=500` is a 422 naming
the `pageSize` field.

Two mypy findings were fixed during verification: `cursor.description` is Optional and
would have raised `TypeError` on a statement with no result set, and `DEFAULT_SORT` was
an untyped `str` because `SortKey` lived in the router while `SORT_FRAGMENTS` lived in
the repository - the two could have drifted. `SortKey` now sits beside the fragments it
maps to, typed as `dict[SortKey, str]`, so a sort key without a fragment is a type error
rather than a runtime `KeyError`. Also switched to `HTTP_422_UNPROCESSABLE_CONTENT`,
clearing three deprecation warnings.

Five read endpoints, all reading the graded `ActiveCardCatalogue` through
`CatalogueCardDetail`. No schema change: this step adds no database object at all.
Decisions and the options weighed are in [`DECISIONS.md`](DECISIONS.md) (4.1-4.11).

**Added**
- `GET /api/listings` - filter by set, rarity, variant, condition, graded/raw, price
  range and card-name search; sort by `price_desc` (default), `price_asc`, `name_asc` or
  `newest`; offset pagination with `page` and `pageSize`.
- `GET /api/listings/featured` - the four dearest active cards. Declared before the
  `{listing_id}` route so "featured" is not parsed as an id, with a test pinning that.
- `GET /api/listings/{listing_id}` - full detail; 404 when the listing is not Active,
  because the graded view simply does not contain it.
- `GET /api/sets` and `GET /api/filter-options` - the data behind the filter controls.
- `app/sql/listingsSearch.sql`, `listingById.sql`, `listingsFeatured.sql`,
  `cardSets.sql`, `filterOptions.sql`. Every filter is a null-guarded bind variable, so
  no statement is ever assembled from strings; `count(*) over ()` returns the filtered
  total alongside the page; `ORDER BY` is the one substituted fragment, chosen from a
  whitelist keyed by an endpoint enum.
- `app/repositories/catalogue.py`, `app/services/catalogue.py`,
  `app/schemas/catalogue.py`, `app/api/listings.py`, `app/api/sets.py`.
- `NotFoundError` (404) and a `RequestValidationError` handler that reshapes FastAPI's
  422 into the one error envelope, closing the Step 3 deferral.
- CORS middleware driven by `CORS_ORIGINS`.
- 25 unit tests (`test_catalogue_service.py`, `test_listings.py`) and 14 integration
  tests (`test_catalogue_integration.py`) covering every filter, all four sort
  fragments, pagination without gaps or repeats, and a withdrawn listing staying
  invisible. The suite is now 47 tests, 17 of them against a real database.

**Changed**
- `sql/health_check.sql` renamed to `healthCheck.sql`: `.sql` filenames are camelCase to
  match the API contract, while Python modules stay snake_case for PEP 8 and pytest.
- `.env.example` and `docker-compose.yml`: `DEFAULT_PAGE_SIZE`, `FEATURED_COUNT`,
  `CORS_ORIGINS`.
- Query parameters are camelCase (`pageSize`, `setId`, `minPrice`, `cardCondition`) via
  aliases, so request and response naming agree.

**Deferred**
- The `uv` version in the Dockerfile is still unpinned, pending `uv --version`.
- Starlette is deprecating `httpx` in its test client in favour of `httpx2`; harmless
  now, worth swapping before CI runs with warnings as errors.

## Step 5: Frontend skeleton and catalogue pages

**Verified 2026-11-26.** `npm run typecheck`, `lint`, `test` (6 passing) and `build` all
clean, and the site runs against the live API.

Three defects were fixed during verification: `buildQueryString` took
`Record<string, unknown>`, which an interface without an index signature cannot satisfy
(now generic over `T extends object`); `CataloguePage` imported a `DEFAULT_SORT` that
`types.ts` never exported; and `FilterPanel` referenced `React.ReactNode` without
importing it, which is an error in a module under `verbatimModuleSyntax`.

**Grid rebuilt** after review against reference screenshots of a comparable shop:

- Tiles are `h-full` in a stretching grid, with the card name clamped to two lines over
  a reserved minimum height and `mt-auto` pinning price and action to the bottom, so
  every tile in a row is the same height and prices line up. Previously the grid item
  was `flex` but the tile never received `h-full`, so tiles sized to their own content
  and rows looked ragged.
- One shared 5:7 white card window, with photos letterboxed by `object-contain`, so a
  tall scan, a wide slab photo and a missing image all occupy identical space. The
  "no image" text now sits inside that shared window instead of being its own
  differently-sized box, which was the other half of the inconsistency.
- Filters moved from a left sidebar to a horizontal bar above the grid, with sort and
  the result count on the right and a "Clear" link that appears only when something is
  filtered.
- The tile is no longer one large link. The window and title are links and the action
  is a separate element, because a button nested inside an anchor is invalid markup and
  breaks keyboard navigation. That action reads "View card" and occupies the slot
  "Add to cart" will take in the next step.

React 19 + TypeScript + Vite, styled with Tailwind v4, in `frontend/`. Three pages
against the real API, no database access of its own. Decisions in
[`DECISIONS.md`](DECISIONS.md) (5.1-5.12).

**Added**
- `src/api/types.ts`, `client.ts`, `queries.ts`: hand-written contract types, one fetch
  wrapper that turns the API's error envelope into a typed `ApiError`, and TanStack
  Query hooks. Prices stay strings end to end, so nothing can round them.
- `src/pages/HomePage.tsx` - the feature strip, which is simply the four dearest cards.
- `src/pages/CataloguePage.tsx` - filters by name, set, rarity, condition, price range
  and graded/raw, four sort orders, paginated. Filter state lives in the URL, so a
  filtered catalogue is shareable and the back button works; any filter change returns
  to page 1.
- `src/pages/CardDetailPage.tsx` - full detail, with a distinct message when the card is
  no longer for sale (a 404 from the API, because the graded view excludes it).
- `src/pages/NotFoundPage.tsx` and client-side routing in `App.tsx`.
- Components: `CardTile`, `CardGrid`, `CardImage`, `NoImage`, `FilterPanel`,
  `Pagination`, `Price`, `Badge`, `Header`, `StateMessage`.
- `src/index.css` - the palette as Tailwind theme tokens, plus a visible focus ring,
  which a dark theme needs explicitly.
- `Dockerfile` (multi-stage: Node builds, nginx serves) and `nginx.conf`, which proxies
  `/api` to the backend so the browser sees one origin.
- `src/api/client.test.ts` - six tests on query-string building, including that
  `graded=false` and `minPrice=0` survive rather than being dropped as falsy.

**Changed**
- `docker-compose.yml`: a `frontend` service on port 8080, waiting for the backend's
  healthcheck.
- `.env.example`: `FRONTEND_PORT`, and a note on why `VITE_API_BASE_URL` stays unset.

**Flagged**
- The shop shows "no image" on every card until photos are attached, since `imageurl`
  is NULL throughout the seed data. That is the intended state, not a defect.
- Brass `#C9A227` is mine, not the seller's: the supplied palette had no accent colour,
  and prices and the active filter state needed one.

**Deferred**
- `uv` still unpinned in the backend Dockerfile, pending `uv --version`.
- `httpx`/`httpx2` deprecation in the backend test client.
- No React hooks lint plugin yet: the flat-config wiring is version-sensitive and was
  not worth risking an unbuildable lint config in this step.

## Step 6a: Checkout, payment and order lookup (backend)

**Verified 2026-11-26.** `ruff`, `mypy --strict` (35 files) and 30 unit tests clean;
all 41 integration tests pass against a real Oracle database, including the two that
matter most: two threads racing for one card produce exactly one order and exactly one
`orderline`, and two simultaneous payments produce exactly one `payment` row. Also
confirmed: an expired reservation returns its card and cancels its order, a card freed
by expiry can be bought by someone else, a failed multi-card order leaves nothing
reserved, one customer row per email, and a sold card disappears from
`ActiveCardCatalogue` with no extra filter.

Two defects were fixed during verification, both mine and both in test or glue code:
`cursor.rowcount` is `Any` in the oracledb stubs so `release_expired` was returning
`Any` where `int` was declared, and - the interesting one - every test shared a single
module-level `ShippingAddress`. Pydantic assigns a nested model by reference rather
than copying it, so the test that sets an unsupported country mutated that shared
object and 13 later tests inherited it. The address is now built per call.

The write side. Three endpoints, no schema change: every column and constraint this
needed already existed in the graded schema. Decisions in
[`DECISIONS.md`](DECISIONS.md) (6.1-6.14).

**Added**
- `POST /api/orders` - one transaction that releases lapsed holds, locks each listing
  with `SELECT … FOR UPDATE` in ascending id order, confirms each is still `Active`,
  upserts the customer by email, inserts the order and its lines, and sets the
  listings `Reserved`. The order id comes from `salesorder_seq` and the guest
  reference from the `publicref` default, both read back with `RETURNING`.
- `POST /api/orders/{ref}/pay` - locks the order row, charges through the
  `PaymentProvider`, records the payment, marks the order `Paid` and its cards `Sold`.
  Calling it twice returns the first payment rather than charging again.
- `GET /api/orders/{ref}?email=` - guest lookup through the graded view
  `CustomerOrderItems`, requiring the reference *and* the email.
- `app/payments/`: the `PaymentProvider` protocol, `PaymentResult`,
  `PaymentFailedError` and `MockPaymentProvider`.
- `Database.transaction()` - commits on success, rolls back on any exception.
  Repositories never commit, so one service call is one transaction.
- `ConflictError` (409), for a request that was valid before the world moved on.
- 24 integration tests, including two genuinely concurrent ones: two threads racing
  for the same card produce exactly one order and one `orderline`, and two
  simultaneous payments produce exactly one `payment` row.

**Flagged**
- No tax is charged, and no tax column was added. The graded schema has nowhere to
  put one, and folding tax into `shippingfee` would make the receipt lie.
- The expiry tests backdate `placedat` with SQL rather than waiting 30 minutes.
- The test suite restores every listing status and deletes the rows it created
  (everything at or above id 1000, which is where the sequences start), so it can run
  repeatedly against the same seeded database.

**Deferred**
- Step 6b: the cart, checkout form and order-lookup pages on the frontend.
- `uv` still unpinned in the Dockerfile; `httpx`/`httpx2` deprecation; frontend
  toolchain versions behind current.

## Step 6b: Cart and checkout (frontend)

**Verified 2026-11-26.** Typecheck, lint and build clean; 11 frontend tests pass; and a
guest bought two cards end to end in the browser - cart, checkout, order reference,
mock payment, and the sold cards leaving the catalogue.

One defect fixed during verification: an unused callback parameter in `CartPage`.
The first attempt also returned a bare 404, which turned out to be the backend
container still running an image built before the order routes existed - the
integration tests had never forced a rebuild, because they connect straight to Oracle
rather than through the API.

The buying path, end to end. Decisions in [`DECISIONS.md`](DECISIONS.md) (6.15-6.19).

**Added**
- `cart/CartContext.tsx` - a `localStorage` cart holding listing ids and nothing else,
  so a cart left open overnight cannot show a stale price or offer a sold card. Reads
  and writes are wrapped, because storage throws in private browsing.
- `lib/money.ts` - integer-cent arithmetic with tests, so the basket total is exact.
- `lib/orderMemory.ts` - remembers which email placed which order, on this device, so
  a returning buyer is not asked to retype it.
- `pages/CartPage.tsx` - re-fetches every card, flags any that have sold and blocks
  checkout until they are removed.
- `pages/CheckoutPage.tsx` - guest details and shipping address, with a live summary.
- `pages/OrderPage.tsx` - confirmation, payment and receipt in one page, since they
  are one order in three states. Shows the reference prominently, the hold's expiry
  while unpaid, and the payment details once paid.
- `pages/OrderLookupPage.tsx` - reference plus email.
- `components/AddToCartButton.tsx`, replacing "View card" in the tile's action slot.
- Cart count in the header, and an add-to-cart on the card detail page.

**Flagged**
- Shipping rates appear as copy on the cart and checkout pages rather than being
  recomputed in the frontend; the authoritative total arrives with the created order.
- Paying invalidates every catalogue query, so a sold card disappears from any open
  listing page without a manual refresh.

## Step 7a: Seller admin (backend)

**Verified 2026-11-27.** `ruff`, `mypy --strict` (43 files), 52 unit tests and 63
integration tests all pass, and admin sign-in works end to end: argon2 verifies
against the stored hash, the httpOnly cookie is set, and it opens a protected route.

Two deployment defects surfaced during verification, neither visible in the test suite
because tests build their own Settings rather than going through the container:

- Docker Compose was interpolating the `$` segments of the argon2 hash
  (`$argon2id$v=19$m=...`) as variable substitutions, so the container received a
  mangled hash and admin sign-in could never have succeeded. Fixed by reading `.env`
  with Compose's `format: raw`, which passes values through literally.
- That fix then exposed a second one: raw format also stops Compose stripping inline
  `#` comments, so `DB_SERVICE` arrived as `FREEPDB1  # Oracle service name...` and
  the driver refused the connect string. `.env` and `.env.example` now keep comments
  on their own lines, which the template explains.

Inventory, listings, photos, orders and fulfilment. **No schema change** - the fourth
step running where the graded schema already had everything needed. Decisions in
[`DECISIONS.md`](DECISIONS.md) (7.1-7.12).

**Added**
- `app/security.py` - argon2id password hashing, JWT sessions in an httpOnly cookie,
  and an in-memory sign-in throttle.
- `scripts/hash_password.py` - generates `ADMIN_PASSWORD_HASH` without the plaintext
  touching a file or shell history.
- `app/media.py` - saves card photos, identifying the real file type from its leading
  bytes rather than its name. JPEG, PNG and WebP, 5 MB cap, stored as uploaded.
- `POST /api/admin/login` and `/logout`; every other admin route is guarded by one
  dependency declared on the router.
- `POST /api/admin/cards` - creates set, printing, copy, optional grading and listing
  in one transaction, reusing the set and printing when they already exist.
- `PATCH /api/admin/listings/{id}` (price), `POST .../status` (disable or re-enable),
  `DELETE .../{id}`, and `POST .../image` to attach a photo at any time after listing.
- `GET /api/admin/orders`, `POST .../orders/{ref}/shipment`, `POST .../delivered`.
- 22 auth tests (13 functions, one parametrised across all 10 admin routes asserting
  401), including one that forges a token with the wrong secret.
- 22 admin integration tests: adding a card appears in the catalogue, a second copy
  reuses its set and printing, a reserved card cannot be repriced, deleting unpicks
  grading and copy rows in foreign-key order, an ordered card refuses deletion, a
  disguised executable is rejected, and the dispatch/delivery rules hold.

**Changed**
- `docker-compose.yml` and `frontend/nginx.conf`: a `card-media` volume the backend
  writes and nginx serves directly at `/media`, with a 30-day cache.
- `.env.example`: `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `ADMIN_JWT_SECRET`,
  `MEDIA_DIR`, `MAX_UPLOAD_BYTES`.
- New dependencies: `argon2-cffi`, `pyjwt`, `python-multipart`.

**Deferred**
- The five Assignment 5 queries as admin reports. They are where the graded SQL
  features actually appear in the running product, so they should land before the TA
  demo.
- Step 7b: the admin UI.

## Step 7b: Seller admin (frontend)

**Verified 2026-11-27.** Sign-in, adding a card, attaching a photo, repricing,
disabling, deleting, and dispatch through to delivery all work in the browser against
the containerised stack.

Three defects were fixed during verification:

- Photo upload failed with a permission error. `/srv/media` did not exist in the
  image, so Docker created the named volume root-owned and the non-root process could
  not write to it. The directory is now created and owned at build time, and a failed
  write reports a plain message instead of putting a filesystem path on screen.
- The help text under a reserved or sold card still told the seller to disable it
  instead, when Disable was itself unavailable. It now explains each state: a reserved
  card is held by a buyer mid-checkout, a sold one needs its order record intact.
- The orders list labelled every non-paid order as awaiting payment, cancelled ones
  included. Those states mean opposite things for stock - one is holding cards, the
  other has released them - so each now says what it is.

The admin area at `/admin`, reachable from a discreet footer link. Decisions in
[`DECISIONS.md`](DECISIONS.md) (7.13-7.18).

**Added**
- `admin/AdminLayout.tsx` - asks the server whether a session exists and shows the
  sign-in form in place when it does not, since the httpOnly cookie is unreadable
  from the page by design.
- `pages/admin/AdminLoginPage.tsx`, `AdminInventoryPage.tsx`, `AdminAddCardPage.tsx`,
  `AdminListingPage.tsx`, `AdminOrdersPage.tsx`.
- `api/adminTypes.ts`, `adminClient.ts` (every call sends credentials, and leaves the
  `Content-Type` to the browser for the multipart upload), `adminQueries.ts`.
- Adding a card is one form covering set, printing, copy, optional grading and the
  listing; the backend reuses the set and printing when they already exist.
- The card page: reprice, add or replace the photo, Disable (reversible) and Delete
  (two-step confirmation), both in a muted red. Delete is greyed with an explanation
  when the card appears on an order, and repricing is replaced by an explanation once
  a card is reserved or sold.
- Orders list with dispatch and mark-delivered, each showing only the action the
  order's state allows.
- `--color-danger: #E0797F` in the theme, the second colour added beyond the three
  supplied.

**Changed**
- `frontend/nginx.conf`: `client_max_body_size 6m` on `/api/`. nginx defaults to 1 MB,
  so a 5 MB photo would have been rejected with a 413 before reaching the backend,
  which accepts it.
- Every inventory change invalidates the public catalogue queries, so the storefront
  cannot show a card the seller has just withdrawn, repriced or deleted.

## Step 7c: Admin reports

**Verified 2026-11-27.** `ruff`, `mypy --strict` (46 files), 52 unit tests and 79
integration tests pass, and all five reports render in the browser with their
`show query` toggles.

One defect was fixed during verification, and it would have been visible to a TA:
`SUM()` and `AVG()` produce a NUMBER with no declared scale, which the driver returns
as an int or float, so a total of 42.00 printed as `42` and an average would have
printed in full floating-point. Money columns are now formatted by their `_cad` name
suffix rather than by Python type. The formatting lives in the service rather than in
`TO_CHAR` inside the query, so the five statements stay identical to the graded
originals - which is the point of being able to show them.

The five Assignment 5 queries as pages at `/admin/reports`, run against live data.
This is the step that puts the graded SQL into the running product: `MINUS`,
`GROUP BY … HAVING`, correlated `EXISTS` and `UNION` appear nowhere else in the
application. No schema change. Decisions in [`DECISIONS.md`](DECISIONS.md) (7.19-7.22).

**Added**
- `sql/reportPaidNotShipped.sql`, `reportSalesBySet.sql`, `reportMultiCardOrders.sql`,
  `reportGradedBuyers.sql`, `reportFollowUps.sql`, each carrying a header explaining
  what its feature does and why it is the right tool.
- `GET /api/admin/reports` and `GET /api/admin/reports/{key}`. The response includes
  the statement that produced it, so the page can show its own workings.
- `services/reports.py` with a definition per report - title, description, and the
  SQL feature it demonstrates.
- `pages/admin/AdminReportsPage.tsx`: all five stacked, each with a "show query"
  toggle, and a threshold control on the multi-card report.
- 16 integration tests (8 functions, two parametrised across all five reports): every
  report compiles against the live schema and carries its
  SQL, plus one test per report proving it answers what it claims - a dispatched order
  leaving the MINUS result, an unpaid order absent from the aggregates, the bind
  variable changing the HAVING threshold, `EXISTS` finding only graded buyers, and
  `UNION` listing a doubly-qualifying customer exactly once.

## Step 9: CI

**Written, not yet verified.** The workflow can only run on GitHub, so nothing has
exercised it; the file is valid YAML and the local equivalents of every step pass.
Expect a round of fixes on the first push, most likely around action versions or the
Oracle service container's start-up.

**Added** `.github/workflows/ci.yml`, running on every push and pull request.

- **Backend**: `ruff check`, `ruff format --check`, `mypy`, unit tests, then the full
  integration suite against a `gvenzl/oracle-free` service container.
- **Frontend**: lint, typecheck, tests and a production build.
- **Images**: both Dockerfiles built, once the code in them has passed.

CI loads the schema by running `database/init/00_run_all.sh` itself, because a service
container never runs the image's entrypoint. The step greps the loader's output for
`SUCCESS`: the script reports failure in its text but still exits 0, so without that
check a broken schema would sail through as a green build.
