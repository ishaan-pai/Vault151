import { Link } from "react-router-dom";

import type { ListingSummary } from "../api/types";
import { AddToCartButton } from "./AddToCartButton";
import { Badge } from "./Badge";
import { CardImage } from "./CardImage";
import { Price } from "./Price";

/**
 * One listing in the grid.
 *
 * The tile is a plain container, with the window and title as links and the action
 * as its own button: a button nested inside an anchor is invalid markup and breaks
 * keyboard navigation.
 *
 * h-full plus the flex column is what makes every tile in a row the same height.
 * The grid stretches each tile to the tallest in its row, the title is clamped to
 * two lines so that height stays sane, and mt-auto pins price and action to the
 * bottom so they align across the row.
 */
export function CardTile({ listing }: { listing: ListingSummary }) {
  const href = `/cards/${listing.listingId}`;

  return (
    <div className="flex h-full flex-col rounded-lg border border-seam bg-surface transition hover:border-brass/40">
      <Link to={href} className="block p-3" tabIndex={-1} aria-hidden="true">
        <CardImage src={listing.imageUrl} alt={listing.cardName} />
      </Link>

      <div className="flex flex-1 flex-col gap-2 border-t border-seam p-3">
        <h3 className="min-h-10 text-sm leading-5 font-medium">
          <Link to={href} className="line-clamp-2 text-ink hover:text-brass">
            {listing.cardName}
          </Link>
        </h3>

        <p className="text-xs text-muted">
          {listing.setName} &middot; {listing.collectorNumber}
        </p>

        <div className="flex flex-wrap gap-1">
          <Badge>{listing.cardCondition}</Badge>
          {listing.grading ? (
            <Badge tone="brass">
              {listing.grading.company} {listing.grading.grade}
            </Badge>
          ) : (
            <Badge>Raw</Badge>
          )}
        </div>

        <Price
          amount={listing.askingPrice}
          currency={listing.currency}
          className="mt-auto pt-1 text-base font-semibold text-brass"
        />

        <AddToCartButton listingId={listing.listingId} />
      </div>
    </div>
  );
}
