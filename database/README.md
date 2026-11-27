# Database

The graded database work is the centre of this project; the application is built around
it rather than the other way round. This file records **which database objects serve
which feature**, and doubles as the demo script.

- [Design rules](#design-rules)
- [Objects](#objects)
- [Feature to database mapping](#feature-to-database-mapping)
- [Admin reports](#admin-reports)
- [Demo script](#demo-script)
- [Applying and checking](#applying-and-checking)

## Design rules

1. **The graded schema is the application's schema.** No new table is added without
   first showing that the existing ten cannot do the job. Every proposed column, view
   or sequence states whether an existing object could be reused or extended instead.
2. **Reads go through the graded views.** `ActiveCardCatalogue` backs the catalogue,
   `CustomerOrderItems` backs order lookup and admin order detail, and
   `PaidOrderReceipts` backs receipts. Where a view lacks a field, a small view is built
   *on top of it* — never a second view running in parallel over the same tables.
3. **Schema files are numbered and applied in order.** `001`–`002` are the graded
   baseline. Later files are additive, each with a header stating what changed, why, and
   which existing object was considered for reuse first. New columns are nullable or
   defaulted so unmodified seed data still loads.
4. **The machinery stays simple.** Migrations will be a small script plus a
   `schema_migrations` table, not Flyway or Liquibase. Expired reservations are released
   inside the checkout transaction or when an order is read — no scheduled jobs.

## Objects

**Ten tables.** `customer`, `cardset`, `cardprinting`, `cardcopy`, `gradedcardcopy`,
`listing`, `salesorder`, `orderline`, `payment`, `shipment`.

The chain `cardset → cardprinting → cardcopy → listing` separates *which card* from
*which physical copy of it* from *what is for sale*, which is what lets a single-seller
shop list one specific slabbed or raw card. `gradedcardcopy` is a one-to-one optional
extension of `cardcopy`, and `orderline` is a weak entity keyed `(orderid, lineno)` with
no quantity column, because every line is one physical card.

**Four views.** Three are graded — `ActiveCardCatalogue`, `CustomerOrderItems`,
`PaidOrderReceipts` — plus `CatalogueCardDetail`, which selects from
`ActiveCardCatalogue`.

**Eight sequences**, one per table that generates its own surrogate key, wired in as
column defaults from 1000. Seeded rows use IDs below 1000 and cannot collide.

### Change log

| File | Change | Reuse considered first |
| --- | --- | --- |
| `schema/001_tables.sql` | Baseline: 10 tables, primary and foreign keys, check constraints | — (graded baseline) |
| `schema/002_views.sql` | Baseline: `ActiveCardCatalogue`, `CustomerOrderItems`, `PaidOrderReceipts` | — (graded baseline) |
| `schema/003_id_sequences.sql` | 8 sequences from 1000, set as each surrogate key's default | No sequences existed to extend. The alternative, `max(id) + 1` in the backend, is unsafe under concurrent checkout |
| `schema/004_card_images.sql` | `cardcopy.imageurl`, nullable | `cardcopy.description` exists but is human-readable prose; overloading it with a URL is worse modelling. The photo belongs to the copy, not the printing, because buyers are judging *that* card's centring and wear |
| `schema/005_guest_order_reference.sql` | `salesorder.publicref`, unique, defaults to a random 32-character value | `(orderid + email)` would work, but order IDs are sequential and emails are guessable for a targeted buyer. Reservation expiry needed **no** column: `placedat` plus a fixed window in config already answers it |
| `schema/006_catalogue_card_detail.sql` | View `CatalogueCardDetail`, selecting from `ActiveCardCatalogue` | Reuses the graded view as its row source, inheriting its `Active` filter. Adds only rarity, image, description, grading and `setid`/`listedat`, which that view does not expose |
| `seed/001_sample_data.sql` | Baseline demo dataset across all ten tables | — (graded baseline) |
| `seed/002_seller_inventory.sql` | Seller's inventory: 5 sets, 10 printings, 10 near-mint copies, 10 active listings, CAD | The baseline has one active listing, so the storefront would be nearly empty. IDs start at 100, clear of both seeded and generated rows |

Three objects written earlier were removed as redundant with the graded schema:
`listing.isfeatured` (the home page is the four highest-priced rows of
`CatalogueCardDetail`), `salesorder.expiresat` (`placedat` plus a fixed window), and
`payment.provider` with its unique key (`payment.method` already names the method, and
the baseline's `payment_order_uq` already makes recording a payment idempotent).
A fourth, the parallel view `storefront_listing`, became `CatalogueCardDetail`.

## Feature to database mapping

Anything in the **Extra** column is a non-graded object; everything else is graded work.

| Feature / endpoint | Tables and views | Notes | Extra |
| --- | --- | --- | --- |
| `POST /api/admin/cards` | `cardset`, `cardprinting`, `cardcopy`, `gradedcardcopy`, `listing` | One transaction. Reuses the set and printing when they exist, because `cardprinting_version_uq` forbids a duplicate printing | sequences |
| `PATCH /api/admin/listings/{id}` | `listing` | Price only, and only while `Active` or `Withdrawn` | — |
| `POST .../listings/{id}/status` | `listing` | Disable or re-enable. `listing_status_ck` rejects any other value | — |
| `DELETE .../listings/{id}` | `listing`, `gradedcardcopy`, `cardcopy` | Refused when `orderline` references the listing, which protects the order's history. Removes the copy only when no listing remains | — |
| `POST .../listings/{id}/image` | `cardcopy.imageurl` | A photo can be attached at any time after listing | `imageurl` |
| `GET /api/admin/orders` | `salesorder`, `customer`, `orderline`, `shipment` | Rolled up with `GROUP BY` and a left join, so one row per order carries its item count and value | — |
| `POST .../orders/{ref}/shipment` | `shipment`, `salesorder` | `shipment_order_uq` allows one dispatch per order | sequences |
| `POST .../orders/{ref}/delivered` | `shipment`, `salesorder` | `shipment_dates_ck` refuses a delivery before its dispatch | — |
| `POST /api/orders` | `listing` (`SELECT … FOR UPDATE`), `customer`, `salesorder`, `orderline` | One transaction: release lapsed holds, lock each listing in ascending id order, confirm `Active`, upsert the customer by email, insert the order and lines, set listings `Reserved`. Ids and `publicref` come from the database via `RETURNING` | sequences, `publicref` |
| `POST /api/orders/{ref}/pay` | `payment`, `salesorder`, `listing`, **`PaidOrderReceipts`** | `payment_order_uq` makes a repeated Pay a no-op; listings move to `Sold`, which removes them from `ActiveCardCatalogue` with no extra filter | sequences |
| `GET /api/orders/{ref}` | **`CustomerOrderItems`** + `salesorder` + `customer` | The view carries neither `publicref` nor email, so the repository joins back for both. Reference *and* email must match | `publicref` |
| Reservation expiry | `listing`, `salesorder` | `placedat` plus a config window, evaluated inside checkout and on order read. No scheduled job | — |
| `GET /api/health` | **none** — `select 1 from dual` | Proves the pool can hand out a working connection. The only endpoint that touches no graded object | — |
| Admin inventory (`/admin`) | via `GET /api/listings` | The seller sees exactly what a buyer sees | — |
| Admin add card (`/admin/add`) | via `POST /api/admin/cards` | One form for set, printing, copy, grading and listing | — |
| Admin card (`/admin/listings/:id`) | via the admin listing, status, delete and image endpoints | — | — |
| Admin reports (`/admin/reports`) | via `GET /api/admin/reports/{key}` | The five graded queries; the response carries the SQL so the page can show its workings | — |
| Admin orders (`/admin/orders`) | via `GET /api/admin/orders` and the dispatch endpoints | — | — |
| Cart page (`/cart`) | via `GET /api/listings/{id}` per card | The cart stores ids only, so prices and availability are always re-fetched | — |
| Checkout (`/checkout`) | via `POST /api/orders` | — | — |
| Order page (`/orders/:ref`) | via `GET /api/orders/{ref}` and `POST /api/orders/{ref}/pay` | Confirmation, payment and receipt are one page, because they are one order in three states | — |
| Home page (`/`) | via `GET /api/listings/featured` | The frontend holds no SQL; every page reads through the API below | — |
| Catalogue page (`/cards`) | via `GET /api/listings`, `/api/sets`, `/api/filter-options` | Filters live in the URL query string | — |
| Card page (`/cards/:id`) | via `GET /api/listings/{id}` | — | — |
| `GET /api/listings/featured` | **`CatalogueCardDetail`** → **`ActiveCardCatalogue`** | `order by asking_price_cad desc fetch first :row_limit rows only`. No `featured` column exists | — |
| `GET /api/listings` | **`CatalogueCardDetail`** → **`ActiveCardCatalogue`** | `sql/listingsSearch.sql`. Every filter a null-guarded bind; `count(*) over ()` returns the total in the same round trip; `ORDER BY` from a fixed whitelist | `imageurl` |
| `GET /api/listings/{id}` | **`CatalogueCardDetail`** → **`ActiveCardCatalogue`** | `sql/listingById.sql`. A sold or withdrawn listing is absent from the graded view, so it 404s | `imageurl` |
| `GET /api/sets` | **`cardset`** | `sql/cardSets.sql`. All 8 sets, including the 2 with nothing listed, so an empty filter result is informative | — |
| `GET /api/filter-options` | **`CatalogueCardDetail`** | `sql/filterOptions.sql`. `UNION` of the distinct rarities, variants and conditions | — |
| Checkout — create order | `listing` (`SELECT … FOR UPDATE`), `customer`, `salesorder`, `orderline` | One transaction: lock listings, confirm still `Active`, upsert customer by email, insert order and lines, set listings `Reserved`. Expired reservations released here | sequences, `publicref` |
| Mock payment | `payment`, `salesorder` | `payment_order_uq` rejects a double-clicked Pay button | sequences |
| Order confirmation / receipt | **`PaidOrderReceipts`** | — | — |
| Guest order lookup | **`CustomerOrderItems`**, joined to `salesorder` and `customer` | The view exposes neither `publicref` nor `email`, so the repository joins back for both | `publicref` |
| Admin — order detail | **`CustomerOrderItems`** | Includes pending and cancelled history | — |
| Admin — add set / printing / copy / listing | `cardset`, `cardprinting`, `cardcopy`, `gradedcardcopy`, `listing` | `cardprinting_version_uq` prevents duplicate printings | sequences, `imageurl` |
| Admin — record shipment, mark delivered | `shipment`, `salesorder` | `shipment_dates_ck` enforces `deliveredat >= shippedat` | sequences |

## Admin reports

The Assignment 5 queries are the admin reporting pages at `/admin/reports`, run
against live data. Each page names the feature it demonstrates and can show the exact
statement behind it, so this is the demo: every graded query feature appears in the
running product rather than in a SQL*Plus session beside it.

| Report | Source query | SQL file | Feature shown |
| --- | --- | --- | --- |
| Paid orders with no shipment | A5 Q3 | `reportPaidNotShipped.sql` | `MINUS` |
| Sales by set | A5 Q5 | `reportSalesBySet.sql` | `GROUP BY` with `COUNT`, `SUM`, `AVG` |
| Orders with two or more cards | A5 Q4 | `reportMultiCardOrders.sql` | `GROUP BY … HAVING`, threshold bound as `:min_cards` |
| Customers who bought graded cards | A5 Q1 | `reportGradedBuyers.sql` | Correlated `EXISTS` subquery |
| Payment and delivery follow-ups | A5 Q2 | `reportFollowUps.sql` | `UNION` of two populations |

## Demo script

A walk through the database features behind the running site.

1. **Constraints.** Try to insert a listing with a negative price (`listing_price_ck`),
   an invalid card condition (`cardcopy_condition_ck`), or a second payment for one
   order (`payment_order_uq`). Each is rejected by the database, not the application.
2. **Sequences and defaults.** Add a card in the admin area; show that no ID was sent by
   the application and `cardset_seq`/`cardcopy_seq` supplied it, and that `publicref`
   was filled by its `DEFAULT`.
3. **The graded views in the read path.** Open the catalogue, then run
   `ActiveCardCatalogue` in SQL*Plus and show the same rows.
   `CatalogueCardDetail` selects from it, so the `Active` rule is defined once.
4. **Left join semantics.** All active listings are raw cards, so every row of
   `CatalogueCardDetail` has `NULL` grade columns — proof the join preserves them where
   an inner join would return nothing.
5. **Transactions and locking.** Start a checkout for a card in two browsers at once.
   `SELECT … FOR UPDATE` serialises them; the second buyer is told the card is gone, and
   no `orderline` row is written for it.
6. **The order lifecycle.** Place an order, show the listings move to `Reserved`, pay,
   then show `PaidOrderReceipts` and `CustomerOrderItems` for the same order.
7. **Reporting.** Run each of the five admin reports above and name the SQL feature each
   one demonstrates.

## Applying and checking

The loader `init/00_run_all.sh` runs on the container's **first boot only**, applying
every `schema/*.sql` then every `seed/*.sql` in filename order, connected as the
least-privilege app user rather than `SYS`. Applying a change today therefore means
discarding the volume and rebuilding — a migration runner comes later.

```powershell
docker compose down -v          # destroys all local data
docker compose up -d db
docker compose logs -f db       # wait for: [cardshop-init] SUCCESS
docker exec cardshop-db bash -c 'sqlplus -s $APP_USER/$APP_USER_PASSWORD@//localhost/FREEPDB1 @/opt/cardshop/database/checks/verify.sql'
```

`checks/verify.sql` asserts the object counts, that `CatalogueCardDetail` and
`ActiveCardCatalogue` agree row for row, that the left join preserves ungraded cards,
that the other two graded views are populated, and that sequence defaults work. It is
safe to re-run.
