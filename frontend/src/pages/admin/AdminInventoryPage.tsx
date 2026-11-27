import { Link } from "react-router-dom";

import { useListings } from "../../api/queries";
import { CardImage } from "../../components/CardImage";
import { StateMessage } from "../../components/StateMessage";

/**
 * The seller's view of what is for sale.
 *
 * Reads the same public catalogue endpoint the shop uses, so what the seller sees
 * here is exactly what a buyer sees. Withdrawn cards are therefore absent: they are
 * reached from the card they were withdrawn from, or by re-enabling from its page.
 */
export function AdminInventoryPage() {
  const listings = useListings({ pageSize: 48, sort: "price_desc" });

  if (listings.isPending) return <StateMessage title="Loading inventory&hellip;" />;
  if (listings.isError) {
    return <StateMessage title="Could not load inventory." detail={listings.error.message} />;
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted">
        {listings.data.totalItems} card
        {listings.data.totalItems === 1 ? "" : "s"} listed for sale.
      </p>

      <ul className="flex flex-col gap-2">
        {listings.data.items.map((listing) => (
          <li key={listing.listingId}>
            <Link
              to={`/admin/listings/${listing.listingId}`}
              className="flex items-center gap-4 rounded-lg border border-seam bg-surface p-3 transition hover:border-brass/40"
            >
              <div className="w-12 shrink-0">
                <CardImage src={listing.imageUrl} alt={listing.cardName} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-ink">{listing.cardName}</p>
                <p className="truncate text-xs text-muted">
                  {listing.setName} &middot; {listing.collectorNumber} &middot;{" "}
                  {listing.cardCondition}
                  {listing.imageUrl ? "" : " \u00b7 no photo"}
                </p>
              </div>
              <span className="text-sm font-semibold text-brass">
                ${listing.askingPrice}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
